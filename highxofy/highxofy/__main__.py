import argparse
import sys

import pandas as pd
import icecream  # noqa: F401  # pylint: disable=unused-import

from highxofy import calculator


PUBLIC_HOLIDAYS_FILE: str = 'configs/public_holidays.csv'


def main():
    """Dump result file in output directory.
    """
    parser = make_parser()
    args = parser.parse_args()
    input_file = args.input_file
    output_file = args.output_file
    df_demand = pd.read_csv(input_file, parse_dates=['datetime'])
    df_holidays = pd.read_csv(PUBLIC_HOLIDAYS_FILE, parse_dates=['date'])
    df_calculated = calculator.calculate(df_demand, df_holidays)
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
