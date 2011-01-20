#!/usr/bin/env python
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
from optparse import OptionParser
from landslide.generator import get_generator

import logging
logger = logging.getLogger("landslide")
logger.setLevel(logging.DEBUG)

def _parse_options():
    """parses ``landslide`` args options"""

    parser = OptionParser(
        usage="%prog [options] input.md ...",
        description="Generates an HTML5 or PDF "
                    "slideshow from Markdown or other formats",
        epilog="Note: PDF export requires the `prince` program: "
               "http://princexml.com/"
        )

    parser.add_option(
        "-b", "--debug",
        action="store_true",
        dest="debug",
        help="Will display debugging info",
        default=False
    )

    parser.add_option(
        "-d", "--destination",
        dest="destination_file",
        help="The path to the to the destination file: .html or "
             ".pdf extensions allowed (default: presentation.html)",
        metavar="FILE",
        default="presentation.html"
    )

    parser.add_option(
        "-e", "--encoding",
        dest="encoding",
        help="The encoding of your files (defaults to UTF-8)",
        metavar="ENCODING",
        default="utf8"
    )

    parser.add_option(
        "-i", "--embed",
        action="store_true",
        dest="embed",
        help="Embed stylesheet and Javascript contents, "
             "base64-encoded images in presentation to make a "
             "standalone document",
        default=False
    )

    parser.add_option(
        "-t", "--theme",
        dest="theme",
        help="A theme name, or path to a landslide theme directory",
        default='default'
    )

    parser.add_option(
        "-o", "--direct-ouput",
        action="store_true",
        dest="direct",
        help="Prints the generated HTML code to stdout; won't work "
             "with PDF export",
        default=False
    )

    parser.add_option(
        "-q", "--quiet",
        action="store_true",
        dest="quiet",
        help="Won't write anything to stdout (silent mode)",
        default=False
    )

    parser.add_option(
        "-v", "--verbose",
        action="store_true",
        dest="verbose",
        help="Write informational messages to stdout (enabled by "
        "default)",
        default=True
    )

    (options, args) = parser.parse_args()

    if not args:
        parser.print_help()
        sys.exit(1)

    return options, args[0]

def main():
    options, input_file = _parse_options()
    log_handler = logging.StreamHandler(sys.stderr if options.direct else sys.stdout)
    log_handler.setLevel(logging.WARNING)
    if options.verbose:
        log_handler.setLevel(logging.INFO)
    if options.debug:
        log_handler.setLevel(logging.DEBUG)
    if options.quiet:
        log_handler.setLevel(logging.CRITICAL)
    logger.addHandler(log_handler)

    if options.direct:
        output = sys.stdout
        format = "html"
    else:
        output = options.destination_file
        format = options.destination_file.rsplit('.', 1)[1]

    generator_class = get_generator(format)
    generator = generator_class(input_file,
                    destination_file=output,
                    theme=options.theme,
                    direct=options.direct,
                    embed=options.embed,
                    encoding=options.encoding)
    generator.execute()
    logger.info("Done.    Output written to %s",
                output if not options.direct else "stdout")

if __name__ == '__main__':
    main()
