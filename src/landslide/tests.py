# -*- coding: utf-8 -*-

#  Copyright 2010 Adam Zapletal
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import sys
import os
import re
import unittest
import codecs
import tempfile

from landslide.generator import HTMLGenerator as Generator
from landslide.parser import Parser
from landslide.macro import (Macro, CodeHighlightingMacro,
                             EmbedImagesMacro, FixImagePathsMacro,
                             FxMacro, NotesMacro)

import logging
logging.basicConfig()

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'samples')
if (not os.path.exists(SAMPLES_DIR)):
    raise IOError('Sample source files not found, cannot run tests')


class GeneratorTest(unittest.TestCase):

    def setUp(self):
        self.destination_file = tempfile.NamedTemporaryFile()

    def tearDown(self):
        self.destination_file.close()

    def test___init__(self):
        self.assertRaises(IOError, Generator, None)
        self.assertRaises(IOError, Generator, 'foo.md')

    def test_get_toc(self):
        base_dir = os.path.join(SAMPLES_DIR, 'example1', 'slides.md')
        g = Generator(base_dir, destination_file=self.destination_file)
        g.add_toc_entry('Section 1', 1, 1)
        g.add_toc_entry('Section 1.1', 2, 2)
        g.add_toc_entry('Section 1.2', 2, 3)
        g.add_toc_entry('Section 2', 1, 4)
        g.add_toc_entry('Section 2.1', 2, 5)
        g.add_toc_entry('Section 3', 1, 6)
        toc = g.toc
        self.assertEqual(len(toc), 3)
        self.assertEqual(toc[0]['title'], 'Section 1')
        self.assertEqual(len(toc[0]['sub']), 2)
        self.assertEqual(toc[0]['sub'][1]['title'], 'Section 1.2')
        self.assertEqual(toc[1]['title'], 'Section 2')
        self.assertEqual(len(toc[1]['sub']), 1)
        self.assertEqual(toc[2]['title'], 'Section 3')
        self.assertEqual(len(toc[2]['sub']), 0)

    def test_get_slide_vars(self):
        g = Generator(os.path.join(SAMPLES_DIR, 'example1', 'slides.md'),
                      destination_file=self.destination_file)
        svars = g.get_slide_vars("<h1>heading</h1>\n<p>foo</p>\n<p>bar</p>\n")
        self.assertEqual(svars['title'], 'heading')
        self.assertEqual(svars['level'], 1)
        self.assertEqual(svars['header'], '<h1>heading</h1>')
        self.assertEqual(svars['content'], '<p>foo</p>\n<p>bar</p>')
        self.assertEqual(svars['source'], {})
        self.assertEqual(svars['classes'], [])

    def test_unicode(self):
        g = Generator(os.path.join(SAMPLES_DIR, 'example3', 'slides.rst'),
                      destination_file=self.destination_file)
        g.execute()
        s = g.render()
        self.assertTrue(s.find('<pre>') != -1)
        self.assertEqual(len(re.findall('<pre><span', s)), 3)

    def test_inputencoding(self):
        g = Generator(os.path.join(SAMPLES_DIR, 'example3', 'slides.koi8_r.rst'),
                      encoding='koi8_r',
                      destination_file=self.destination_file)
        content = g.render()
        # check that the string is utf_8
        self.assertTrue(re.findall(u'русский', content, flags=re.UNICODE))
        g.execute()
        file_contents = codecs.open(g.destination_file.name, encoding='utf-8').read()
        # check that the file was properly encoded in utf_8
        self.assertTrue(re.findall(u'русский', file_contents, flags=re.UNICODE))

    def test_get_template_vars(self):
        g = Generator(os.path.join(SAMPLES_DIR, 'example1', 'slides.md'),
                      destination_file=self.destination_file)
        svars = g.get_template_vars([{'title': "slide1", 'level': 1},
                                     {'title': "slide2", 'level': 1},
                                     {'title': None, 'level': 1},
                                    ])
        self.assertEqual(svars['head_title'], 'slide1')


    def test_process_macros(self):
        g = Generator(os.path.join(SAMPLES_DIR, 'example1', 'slides.md'),
                      destination_file=self.destination_file)
        # Notes
        r = g.process_macros('<p>foo</p>\n<p>.notes: bar</p>\n<p>baz</p>')
        self.assertEqual(r[0].find('<p class="notes">bar</p>'), 11)
        self.assertEqual(r[1], [u'has_notes'])
        # FXs
        content = '<p>foo</p>\n<p>.fx: blah blob</p>\n<p>baz</p>'
        r = g.process_macros(content)
        self.assertEqual(r[0], '<p>foo</p>\n<p>baz</p>')
        self.assertEqual(r[1][0], 'blah')
        self.assertEqual(r[1][1], 'blob')

    def test_register_macro(self):
        g = Generator(os.path.join(SAMPLES_DIR, 'example1', 'slides.md'),
                      destination_file=self.destination_file)

        class SampleMacro(Macro):
            pass

        g.register_macro(SampleMacro)
        self.assertTrue(SampleMacro in g.macros)

        def plop(foo):
            pass

        self.assertRaises(TypeError, g.register_macro, plop)


class CodeHighlightingMacroTest(unittest.TestCase):
    def setUp(self):
        self.sample_html = '''<p>Let me give you this snippet:</p>
<pre class="literal-block">
!python
def foo():
    &quot;just a test&quot;
    print bar
</pre>
<p>Then this one:</p>
<pre class="literal-block">
!php
<?php
echo $bar;
?>
</pre>
<p>Then this other one:</p>
<pre class="literal-block">
!xml
<foo>
    <bar glop="yataa">baz</bar>
</foo>
</pre>
<p>End here.</p>'''

    def test_parsing_code_blocks(self):
        m = CodeHighlightingMacro()
        blocks = m.code_blocks_re.findall(self.sample_html)
        self.assertEquals(len(blocks), 3)
        self.assertEquals(blocks[0][2], 'python')
        self.assertTrue(blocks[0][3].startswith('def foo():'))
        self.assertEquals(blocks[1][2], 'php')
        self.assertTrue(blocks[1][3].startswith('<?php'))
        self.assertEquals(blocks[2][2], 'xml')
        self.assertTrue(blocks[2][3].startswith('<foo>'))

    def test_descape(self):
        m = CodeHighlightingMacro()
        self.assertEqual(m.descape('foo'), 'foo')
        self.assertEqual(m.descape('&gt;'), '>')
        self.assertEqual(m.descape('&lt;'), '<')
        self.assertEqual(m.descape('&amp;lt;'), '&lt;')
        self.assertEqual(m.descape('&lt;span&gt;'), '<span>')
        self.assertEqual(m.descape('&lt;spam&amp;eggs&gt;'), '<spam&eggs>')

    def test_process(self):
        m = CodeHighlightingMacro()
        hl = m.process("<pre><code>!php\n$foo;</code></pre>")
        self.assertTrue(hl[0].startswith('<div class="highlight"><pre'))
        self.assertEquals(hl[1][0], u'has_code')
        input = "<p>Nothing to declare</p>"
        self.assertEqual(m.process(input)[0], input)
        self.assertEqual(m.process(input)[1], [])

    def test_process_rst_code_blocks(self):
        m = CodeHighlightingMacro()
        hl = m.process(self.sample_html)
        self.assertTrue(hl[0].startswith('<p>Let me give you this'))
        self.assertTrue(hl[0].find('<p>Then this one') > 0)
        self.assertTrue(hl[0].find('<p>Then this other one') > 0)
        self.assertTrue(hl[0].find('<div class="highlight"><pre') > 0)
        self.assertEquals(hl[1][0], u'has_code')


class EmbedImagesMacroTest(unittest.TestCase):
    def test_process(self):
        base_dir = os.path.join(SAMPLES_DIR, 'example1', 'slides.md')
        m = EmbedImagesMacro(True)
        m.process('<img src="toto.jpg"/>', '.')
        content, classes = m.process('<img src="monkey.jpg"/>', base_dir)
        self.assertTrue(re.match(r'<img src="data:image/jpeg;base64,(.+?)"/>',
                        content))


class FixImagePathsMacroTest(unittest.TestCase):
    def test_process(self):
        base_dir = os.path.join(SAMPLES_DIR, 'example1', 'slides.md')
        m = FixImagePathsMacro(False)
        content, classes = m.process('<img src="monkey.jpg"/>', base_dir)
        self.assertTrue(re.match(r'<img src="file://.*?/monkey.jpg" />',
                                 content))


class FxMacroTest(unittest.TestCase):
    def test_process(self):
        m = FxMacro()
        content = '<p>foo</p>\n<p>.fx: blah blob</p>\n<p>baz</p>'
        r = m.process(content)
        self.assertEqual(r[0], '<p>foo</p>\n<p>baz</p>')
        self.assertEqual(r[1][0], 'blah')
        self.assertEqual(r[1][1], 'blob')


class NotesMacroTest(unittest.TestCase):
    def test_process(self):
        m = NotesMacro()
        r = m.process('<p>foo</p>\n<p>.notes: bar</p>\n<p>baz</p>')
        self.assertEqual(r[0].find('<p class="notes">bar</p>'), 11)
        self.assertEqual(r[1], [u'has_notes'])


class ParserTest(unittest.TestCase):
    def test___init__(self):
        self.assertEqual(Parser('.md').format, 'markdown')
        self.assertEqual(Parser('.markdown').format, 'markdown')
        self.assertEqual(Parser('.rst').format, 'restructuredtext')
        self.assertRaises(NotImplementedError, Parser, '.txt')


if __name__ == '__main__':
    unittest.main()
