import argparse
import sys

import pandas as pd
import icecream  # noqa: F401  # pylint: disable=unused-import


def main():
    parser = make_parser()
    args = parser.parse_args()
    csv_file = args.csv_file
    sys.exit()


def make_parser():
    parser = argparse.ArgumentParser(description='Calculate high x of y.')
    parser.add_argument(
        'csv_file',
        help='original data'
    )

    return parser


if __name__ == '__main__':
    main()
