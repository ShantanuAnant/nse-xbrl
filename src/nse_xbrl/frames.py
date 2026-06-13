"""
Optional pandas helper for working with batches of :class:`~nse_xbrl.models.FilingResult`.

Requires the ``pandas`` extra::

    pip install nse-xbrl[pandas]
"""
from __future__ import annotations

from dataclasses import fields
from typing import TYPE_CHECKING

from .models import FilingResult

if TYPE_CHECKING:
    import pandas as pd


def to_dataframe(results: list[FilingResult]) -> "pd.DataFrame":
    """
    Convert a list of :class:`FilingResult` into a tidy ``pandas.DataFrame``,
    one row per filing.

    ``raw_facts`` is dropped (it's a nested dict, not a scalar column). All
    other dataclass fields -- including the computed properties
    (``q_ebitda``, ``shares_outstanding``, etc.) -- become columns.
    """
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError(
            "pandas is required for to_dataframe(); install with `pip install nse-xbrl[pandas]`"
        ) from e

    computed_props = ["q_ebitda", "ytd_ebitda", "shares_outstanding",
                       "debt_equity_ratio", "book_value_per_share"]
    field_names = [f.name for f in fields(FilingResult) if f.name != "raw_facts"]

    rows = []
    for r in results:
        row = {name: getattr(r, name) for name in field_names}
        for prop in computed_props:
            row[prop] = getattr(r, prop)
        rows.append(row)

    return pd.DataFrame(rows)
