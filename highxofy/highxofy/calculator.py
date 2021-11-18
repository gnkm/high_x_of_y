"""Calculate high x of y.
"""

import sys  # noqa: F401  # pylint: disable=unused-import
import toml
from typing import Any, Dict, List, MutableMapping, Union  # noqa: F401  # pylint: disable=unused-import

import icecream  # noqa: F401  # pylint: disable=unused-import
import pandas as pd


CONFIG_FILE: str = 'configs/config.toml'

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
EXCLUDED_CRITERION_RATIO: float = CONFIGS['excluded_criterion_ratio']
MAX_GO_BACK_DAYS: int = CONFIGS['max_go_back_days']


def calculate(df_demand: pd.DataFrame, df_holidays: pd.DataFrame) -> pd.DataFrame:
    """Return dataframe contain high x of y result.

    Args:
        df_demand (pd.DataFrame): Original data. i.e. historical data.
        df_holiday (pd.DataFrame): Holidays dataframe.

    Returns:
        pd.DataFrame: dataframe contain high x of y result.
    """
    df_base = _add_columns(df_demand, df_holidays)
    dfs_base: Dict[str, pd.DataFrame] = {}
    dfs_base['weekday'] = df_base.query('is_weekday == True')
    dfs_base['holiday'] = df_base.query('is_weekday == False')
    dfs_calced: List[pd.DataFrame] = []
    for day_type, df_day_type in dfs_base.items():
        x = CONFIGS[day_type]['x']
        y = CONFIGS[day_type]['y']
        df_calced = _mean_high_x_of_y(df_day_type, x, y)
        dfs_calced.append(df_calced)

    df = pd.concat(dfs_calced)

    return df


def _add_columns(df_demand: pd.DataFrame, df_holidays: pd.DataFrame) -> pd.DataFrame:
    """Return a dataframe contains following columns.

    - datetime
    - demand
    - dr_invoked_unit
    - dr_invoked_day
    - date
    - day_of_week
    - is_pub_holiday
    - is_weekday
    - unit_num
    - mean_daily_demand_for_dr

    Args:
        df_demand (pd.DataFrame): contain demand.
        df_holidays (pd.DataFrame): contain holidays.

    Returns:
        pd.DataFrame: contain demand and holidays.
    """
    df_holidays['is_pub_holiday'] = True

    df_demand['date'] = pd.to_datetime(df_demand['datetime'].dt.date)
    df_demand['day_of_week'] = df_demand['datetime'].dt.dayofweek

    df_invoked_days = df_demand.groupby('date').sum()[['dr_invoked_unit']] \
        .reset_index() \
        .rename(columns={'dr_invoked_unit': 'dr_invoked_day'})

    df = df_demand.merge(
        df_invoked_days,
        how='left',
        on='date'
    )

    df_demand_means_per_invoked_day = df_demand.query('dr_invoked_unit != 0') [['date', 'demand']].groupby('date').mean() \
        .reset_index() \
        .rename(columns={'demand': 'mean_daily_demand_for_dr'})

    df = df.merge(
        df_demand_means_per_invoked_day,
        how='left',
        on='date'
    )

    df = df.merge(
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


def _mean_high_x_of_y(df: pd.DataFrame, x: int, y:int) -> pd.DataFrame:
    """Calculate mean of high x of y.

    Args:
        df (pd.DataFrame)

    Returns:
        pd.DataFrame: Dataframe contain mean high x of y.
    """
    unit_num_per_day: int = UNIT_NUM_PER_DAY

    df_calced = df.copy()

    for go_back_day in range(1, MAX_GO_BACK_DAYS + 1):
        column_name_demand: str = f'demand_{go_back_day}_days_ago'
        column_name_dr_invoked_day: str = f'dr_invoked_day_{go_back_day}_days_ago'
        _df = df.copy()
        df_calced[column_name_demand] = _df.shift(go_back_day * unit_num_per_day).loc[:, 'demand']
        df_calced[column_name_dr_invoked_day] = _df.shift(go_back_day * unit_num_per_day).loc[:, 'dr_invoked_day']

    for go_back_day in range(1, max_go_back_days + 1):
        _df = df.copy()
        column_name_is_calced_target: str = f'is_calced_target_{go_back_day}_days_ago'
        _df[column_name_is_calced_target] = _df.apply(_applied_is_calced_target, args=[go_back_day, x, y], axis='columns')

    return df_calced


def _applied_is_calced_target(row: pd.Series, go_back_day: int, x: int, y:int) -> bool:
    """When demand of `go_back_day` days ago is target of calculating mean, return True.

    If the demand value `go_back_day` days before the row date is in the top x of the y days and
    is 25% or more of the average value for the y days,
    it is included in the calculation of the average value, that is, return True.

    Args:
        row (pd.Series): [description]
        go_back_day (int): [description]
        x (int): x of "high x of y"
        y (int): y of "high x of y"

    Returns:
        bool: [description]

    Examples:
        `df[column] = df.apply(_applied_is_calced_target, args=[go_back_day, x, y], axis='columns')`
    """
    return True
