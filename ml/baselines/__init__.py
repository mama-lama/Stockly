from .moving_average import add_moving_average_baseline
from .naive import add_last_value_baseline

__all__ = [
    "add_last_value_baseline",
    "add_moving_average_baseline",
]
