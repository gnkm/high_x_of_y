# high_x_of_y

High x of y is one of the methods to estimate the power demand and is described in [ERAB guidline](https://www.meti.go.jp/press/2020/06/20200601001/20200601001-1.pdf).

This script calculate high x of y of time series data like following.

| datetime         | demand | dr_invoked_unit |
|:----------------:|-------:|----------------:|
| 2021-11-01 00:00 |    189 |               0 |
| 2021-11-01 00:30 |    156 |               0 |
| ...              |    ... |               0 |
| 2021-11-30 24:00 |    203 |               0 |

# Usage

```
docker compose run highxofy python -m highxofy \
  data/input/sample_demand.csv \
  data/output/sample_highxofy.csv
```
