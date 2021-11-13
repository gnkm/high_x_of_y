import argparse
import sys

import pandas as pd
import icecream  # noqa: F401  # pylint: disable=unused-import

from highxofy import calculator


def main():
    """Dump result file in output directory.
    """
    parser = make_parser()
    args = parser.parse_args()
    input_file = args.input_file
    output_file = args.output_file
    df_org = pd.read_csv(input_file)
    df_calculated = calculator.calculate(df_org)
    df_calculated.to_csv(output_file, index=False)
    sys.exit()


def make_parser() -> argparse.ArgumentParser:
    """Return ArgumentParser.

    Returns:
        argparse.ArgumentParser: parser defined args
    """
    parser = argparse.ArgumentParser(description='Calculate high x of y.')
    parser.add_argument(
        'input_file',
        help='original data'
    )
    parser.add_argument(
        'output_file',
        help='calculated result file'
    )

    return parser


if __name__ == '__main__':
    main()
