"""Calculate high x of y.

Todo:
    Load configs in `__main__.py` for making it easier to test.
"""

import sys  # noqa: F401  # pylint: disable=unused-import
import toml
from typing import Any, Dict, List, MutableMapping, Union  # noqa: F401  # pylint: disable=unused-import

import icecream  # noqa: F401  # pylint: disable=unused-import
import numpy as np
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

    Todo:
        Change arguments for making it easier to test.

    Args:
        df_demand (pd.DataFrame): Original data. i.e. historical data.
        df_holiday (pd.DataFrame): Holidays dataframe.

    Returns:
        pd.DataFrame: dataframe contain high x of y result.
    """
    df_base = _make_df_base(df_demand, df_holidays)
    df_bases: Dict[str, pd.DataFrame] = {}
    df_bases['weekday'] = df_base.query('is_weekday == True')
    df_bases['holiday'] = df_base.query('is_weekday == False')
    df_calceds: List[pd.DataFrame] = []
    for day_type, df_day_type in df_bases.items():
        x = CONFIGS[day_type]['x']
        y = CONFIGS[day_type]['y']
        df_calced = _mean_high_x_of_y(df_day_type, x, y)
        df_calceds.append(df_calced)

    df = pd.concat(df_calceds)

    return df


def _make_df_base(df_demand: pd.DataFrame, df_holidays: pd.DataFrame) -> pd.DataFrame:
    """Return a dataframe contains following columns.

    - datetime
    - demand
    @todo: not deal as int but bool
    - dr_invoked_unit: 0: not invoked, 1 invoked
    - dr_invoked_day: 0: not invoked, otherwise invoked
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
    """Return dataframe contain mean_high_x_of_y column.

    Note:
        Main logic is `_mean_high_x_of_y_per_row()`.

    Args:
        df (pd.DataFrame): DataFrame made by `_make_df_base()`.

    Returns:
        pd.DataFrame: Dataframe contain average of high x of y.
    """
    unit_num_per_day: int = UNIT_NUM_PER_DAY

    df_calced = df.copy()

    for go_back_day in range(1, MAX_GO_BACK_DAYS + 1):
        column_name_demand: str = f'demand_{go_back_day}_days_ago'
        column_name_dr_invoked_day: str = f'dr_invoked_day_{go_back_day}_days_ago'
        _df = df.copy()
        df_calced[column_name_demand] = _df.shift(go_back_day * unit_num_per_day).loc[:, 'demand']
        df_calced[column_name_dr_invoked_day] = _df.shift(go_back_day * unit_num_per_day).loc[:, 'dr_invoked_day']

    df_calced['mean_high_x_of_y'] = df_calced.apply(_mean_high_x_of_y_per_unit, args=[x, y], axis='columns')

    return df_calced


def _mean_high_x_of_y_per_unit(unit_data: pd.Series, x: int, y:int) -> int:
    """Return mean of high x of y.

    Args:
        unit_data (pd.Series): data per unit
        x (int): x of "high x of y"
        y (int): y of "high x of y"

    Returns:
        int: mean of high x of y

    Examples:
        `df['mean_high_x_of_y'] = df.apply(_mean_high_x_of_y_per_unit, args=[x, y], axis='columns')`
    """
    y_candidates: List = []
    days_of_y: List = _get_days_of_y(unit_data, y, y_candidates)
    demands_of_x: List = _get_demands_of_x(unit_data, x, days_of_y)

    return int(sum(demands_of_x) / len(demands_of_x))


def _get_days_of_y(unit_data: pd.Series, y: int, y_candidates: List) -> List:
    """Return list of days contained y(of high x of y).

    Args:
        unit_data (pd.Series): data per unit
        y (int): y of "high x of y"
        y_candidates (List): list of candidates of days contained y(of "high x of y").

    Returns:
        List: list of days contained y(of high x of y).
    """
    days_of_y = [1, 2, 3, 4, 5]
    return days_of_y


def _get_demands_of_x(unit_data: pd.Series, x, days_of_y: List) -> List:
    demands_of_x = [10, 20, 30, 40]
    return demands_of_x


def _not_necessary():
    """When demand of `days_ago` days ago is target of calculating mean, return True.

    If the demand value `go_back_day` days before the row date is in the top x of the y days and
    is `EXCLUDED_CRITERION_RATIO` or more of the average value for the y days,
    it is included in the calculation of the average value, that is, return True.

    Args:
        row (pd.Series): [description]
        days_ago (int): target day judged whether the day is adopted or not.
        x (int): x of "high x of y"
        y (int): y of "high x of y"

    Returns:
        bool: [description]

    Examples:
        `df[column] = df.apply(_applied_is_calced_target, args=[go_back_day, x, y], axis='columns')`
    """
    pass
