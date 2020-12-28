""" Options from cmd line """

import logging
import argparse
import textwrap
import hackimposition
from hackimposition import ImposerPageTemplate, ImposerAlgo
from hackimposition import __PRGM__, __VERSION__, __COPYRIGHT__

logger = logging.getLogger(hackimposition.__name__)


def _positive_int(text):
    if int(text) > 0:
        return int(text)
    raise argparse.ArgumentTypeError("Argument must be a positive integer.")


def _commandline_parser():
    """Return a command line parser."""
    parser = argparse.ArgumentParser(
        prog=__PRGM__,
        description=textwrap.dedent(hackimposition.__doc__),
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=__PRGM__ + " " + __VERSION__ + "   " + __COPYRIGHT__,
    )

    parser.add_argument(
        "--version",
        help="Show version",
        action="version",
        version="%(prog)s " + __VERSION__,
    )

    parser.add_argument(
        "-v",
        "--verbose",
        help="Verbose mode.",
        action="store_true"
    )

    parser.add_argument(
        "infile",
        metavar="FILE",
        help="PDF file to process",
        type=str
    )

    parser.add_argument(
        "--outfile",
        "-o",
        metavar="FILE",
        help=('Destination file. Default is "-impose" appended to first source file.'),
        type=str,
    )

    parser.add_argument(
        "--last",
        "-l",
        metavar="N",
        help=(
            "Number of pages to keep as last pages. Useful, for instance, "
            "to keep the back cover as a back cover."
        ),
        type=_positive_int,
        default=0,
    )

    parser.add_argument(
        '--global_w',
        '-W',
        metavar="R+",
        help="output width",
        type=float
    )

    parser.add_argument(
        '--global_h',
        '-H',
        metavar="R+",
        help="output height",
        type=float
    )

    parser.add_argument(
        '--int_margin',
        '-I',
        metavar="R+",
        help="internal margin",
        type=float
    )

    parser.add_argument(
        '--ext_margin',
        '-E',
        metavar="R+",
        help="external margin",
        type=float
    )

    parser.add_argument(
        '--dec_margin',
        '-d',
        metavar="R+",
        help="margin for cutting guides",
        type=float
    )

    parser.add_argument(
        '--dec_line_coef',
        metavar="[0, 1]",
        type=float,
        help="margin length coefficient for cutting guides"
    )

    parser.add_argument(
        '--dec_keep_overflow',
        action="store_true",
        help="the surplus margin is added to the internal margin"
    )

    parser.add_argument(
        '--display_debug',
        action="store_true",
        help="draw the pattern in the template"
    )

    return parser


def process_args(argv):
    """ process args """

    opts = _commandline_parser().parse_args(argv)

    logger.setLevel(logging.DEBUG if opts.verbose else logging.INFO)

    # create template
    template = ImposerPageTemplate()
    for key, val in opts.__dict__.items():
        if val is not None and key in template.__dict__.keys():
            logger.debug(f"\tSet {key}: {val}")
            template.__dict__[key] = val

    # creat algo
    algo = ImposerAlgo(2, 2)

    # filenames
    infile = opts.infile
    outfile = opts.outfile if opts.outfile else (
        "{}-impose.pdf".format(".".join(infile.split(".")[:-1])))

    return (template, algo, infile, outfile)
