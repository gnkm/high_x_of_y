"""Calculate high x of y.
"""

import sys  # noqa: F401  # pylint: disable=unused-import
import toml
from typing import Any, Dict, List, MutableMapping, Union  # noqa: F401  # pylint: disable=unused-import

import icecream  # noqa: F401  # pylint: disable=unused-import
import pandas as pd


CONFIG_FILE: str = 'configs/config.toml'
PUBLIC_HOLIDAYS_FILE: str = 'configs/public_holidays.csv'

# day of weeks
MON = 0
TUE = 1
WED = 2
THU = 3
FRI = 4
SAT = 5
SUN = 6

CONFIGS: MutableMapping[str, Any] = toml.load(CONFIG_FILE)
UNIT_NUM_PER_DAY: int = CONFIGS['unit_num_per_day']


def calculate(df_demand: pd.DataFrame) -> pd.DataFrame:
    """Return dataframe contain high x of y result.

    Args:
        df_demand (pd.DataFrame): Original data. i.e. historical data.

    Returns:
        pd.DataFrame: dataframe contain high x of y result.
    """
    df_org = _add_columns(df_demand)
    dfs_org: Dict[str, pd.DataFrame] = {}
    dfs_org['weekday'] = df_org.query('is_weekday == True')
    dfs_org['holiday'] = df_org.query('is_weekday == False')
    dfs_calced: List[pd.DataFrame] = []
    for day_type, df_day_type in dfs_org.items():
        x = CONFIGS[day_type]['x']
        y = CONFIGS[day_type]['y']
        df_calced = _high_x_of_y(df_day_type, x, y)
        dfs_calced.append(df_calced)

    df = pd.concat(dfs_calced)

    return df


def _add_columns(df_demand: pd.DataFrame) -> pd.DataFrame:
    """Return a dataframe contains following columns.

    - datetime
    - demand
    - invoked
    - date
    - day_of_week
    - is_pub_holiday
    - is_weekday
    - unit_num

    Args:
        df_demand (pd.DataFrame): contain demand.

    Returns:
        pd.DataFrame: contain demand and holidays.
    """
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
    df = _add_unit_num_column(df, UNIT_NUM_PER_DAY)

    return df


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


def _add_unit_num_column(df: pd.DataFrame, unit_num_per_day: int) -> pd.DataFrame:
    """Return dataframe added unit num columns.
    When `UNIT_NUM_PER_DAY` is 48, return `[1, 2, ..., 48, 1, 2, ...]`.
    Args:
        df (pd.DataFrame):
        UNIT_NUM_PER_DAY (int)
    Returns:
        pd.DataFrame: dataframe added unit num columns.
    """
    elements: List[int] = []
    for i in range(1, df.shape[0] + 1):
        mod = i % unit_num_per_day
        if mod != 0:
            elements.append(mod)
        else:
            elements.append(unit_num_per_day)
    df_elements: pd.DataFrame = pd.DataFrame({'unit_num': elements})
    df_ret = pd.concat([df, df_elements], axis='columns')
    return df_ret


def _high_x_of_y(df: pd.DataFrame, x: int, y:int) -> pd.DataFrame:
    """Calculate high x of y.

    Args:
        df (pd.DataFrame)

    Returns:
        pd.DataFrame: Dataframe contain high x of y.
    """
    # In ERAB guidline, set this value at 30.
    days_ago: int = 2 * y
    unit_num_per_day: int = UNIT_NUM_PER_DAY

    df_calced = df.copy()

    for go_back_day in range(1, days_ago + 1):
        column_name: str = f'demand_{go_back_day}_days_ago'
        _df = df.copy()
        df_calced[column_name] = _df.shift(go_back_day * unit_num_per_day).loc[:, 'demand']

    return df_calced
