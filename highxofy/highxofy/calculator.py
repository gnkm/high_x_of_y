"""Calculate high x of y.
"""

import sys  # noqa: F401  # pylint: disable=unused-import
from typing import Any, Dict, List, MutableMapping, Union  # noqa: F401  # pylint: disable=unused-import

import icecream  # noqa: F401  # pylint: disable=unused-import
import pandas as pd


PUBLIC_HOLIDAYS_FILE: str = 'configs/public_holidays.csv'

# day of weeks
MON = 0
TUE = 1
WED = 2
THU = 3
FRI = 4
SAT = 5
SUN = 6


def calculate(df_demand: pd.DataFrame) -> pd.DataFrame:
    """Return dataframe contain high x of y result.

    Args:
        df_demand (pd.DataFrame): Original data. i.e. historical data.

    Returns:
        pd.DataFrame: dataframe contain high x of y result.
    """
    df = _add_df_holidays(df_demand)

    return df


def _add_df_holidays(df_demand: pd.DataFrame) -> pd.DataFrame:
    """Return a dataframe contains demand and holidays.

    Args:
        df_demand (pd.DataFrame): contain demand.

    Returns:
        pd.DataFrame: contain demand and holidays.
    """
    def _applied_is_weekday(row: pd.Series) -> bool:
        """Return whether weekday or not.

        Args:
            row (pd.Series): one record of dataframe.

        Returns:
            bool: weekday: True, otherwise: False
        """
        if row['day_of_week'] in [SAT, SUN]:
            return False
        if row['is_pub_holiday']:
            return False
        return True


    df_holidays = pd.read_csv(PUBLIC_HOLIDAYS_FILE, parse_dates=['date'])
    df_holidays['is_pub_holiday'] = True

    df_demand['date'] = pd.to_datetime(df_demand['datetime'].dt.date)
    df_demand['day_of_week'] = df_demand['datetime'].dt.dayofweek
    df = df_demand.merge(
        df_holidays,
        how='left',
        on='date'
    )
    df = df.fillna({'is_pub_holiday': False})
    df['is_weekday'] = df.apply(_applied_is_weekday, axis='columns')

    return df
