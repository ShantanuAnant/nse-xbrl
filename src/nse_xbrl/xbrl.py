"""
Parser for NSE "Integrated Filing - Financials" XBRL documents (IFIndAs taxonomy).

Two-step pipeline:

1. :func:`parse_xbrl` -- generic XBRL parsing. Walks the document once and
   returns every ``(tag, contextRef) -> value`` fact plus the resolved
   contexts (duration / instant periods). No knowledge of *which* tags
   matter -- this works for any IFIndAs-style document.

2. :func:`build_result_fields` -- maps the generic facts onto the
   field names defined in :mod:`nse_xbrl.tags`, producing a flat dict
   ready to construct a :class:`nse_xbrl.models.FilingResult`.

All monetary values are returned as ``float``, in whatever unit the filer
used (almost always absolute INR -- check the ``unitRef``/``decimals``
attributes on the source element if you need to be sure). EPS values are
INR per share.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import date, datetime
from typing import Optional

from dateutil.parser import parse as _parse_dt

from .tags import (
    BALANCE_SHEET_TAGS,
    CASH_FLOW_TAGS,
    CONTEXT_BALANCE_SHEET,
    CONTEXT_BALANCE_SHEET_PRIOR_YEAR,
    CONTEXT_CURRENT_QUARTER,
    CONTEXT_YEAR_TO_DATE,
    INCOME_STATEMENT_TAGS,
    PRIOR_YEAR_BALANCE_SHEET_TAGS,
    SHARED_TAGS,
)

XBRLI_NS = "http://www.xbrl.org/2003/instance"
LINKBASE_NS = "http://www.xbrl.org/2003/linkbase"

# Contexts whose facts are kept in ``raw_facts`` (everything else is dropped
# to keep the payload small -- dimensional/segment-breakdown contexts can
# number in the hundreds for diversified companies).
_MAIN_CONTEXTS = {
    CONTEXT_CURRENT_QUARTER,
    CONTEXT_YEAR_TO_DATE,
    CONTEXT_BALANCE_SHEET,
    CONTEXT_BALANCE_SHEET_PRIOR_YEAR,
}


def _safe_float(val: Optional[str]) -> Optional[float]:
    if not val or not val.strip():
        return None
    try:
        return float(val.strip())
    except (ValueError, TypeError):
        return None


def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return _parse_dt(s.strip()).date()
    except (ValueError, OverflowError):
        return None


def parse_xbrl(xml_text: str) -> dict:
    """
    Parse an IFIndAs XBRL document into contexts + facts.

    Returns a dict with two keys:

    ``contexts``
        ``{context_id: {"type": "duration" | "instant", ...}}``.
        Duration contexts have ``start``/``end`` dates; instant contexts
        have an ``instant`` date.

    ``facts``
        ``{tag_local_name: {context_id: raw_value_string}}``.
        Tag names have their XML namespace stripped (e.g.
        ``{http://www.bseindia.com/...}RevenueFromOperations`` becomes
        ``RevenueFromOperations``), so this works regardless of which
        taxonomy namespace prefix the filer used.

    Raises ``xml.etree.ElementTree.ParseError`` if ``xml_text`` is not
    well-formed XML.
    """
    root = ET.fromstring(xml_text)

    # ── Contexts ──────────────────────────────────────────────────────────
    contexts: dict = {}
    for ctx in root.findall(f"{{{XBRLI_NS}}}context"):
        cid = ctx.get("id", "")
        period = ctx.find(f"{{{XBRLI_NS}}}period")
        if period is None:
            continue
        instant = period.find(f"{{{XBRLI_NS}}}instant")
        start = period.find(f"{{{XBRLI_NS}}}startDate")
        end = period.find(f"{{{XBRLI_NS}}}endDate")
        if instant is not None:
            contexts[cid] = {"type": "instant", "instant": _parse_date(instant.text)}
        elif start is not None and end is not None:
            contexts[cid] = {
                "type": "duration",
                "start": _parse_date(start.text),
                "end": _parse_date(end.text),
            }

    # ── Facts ─────────────────────────────────────────────────────────────
    facts: dict = {}
    for elem in root:
        tag = elem.tag
        if tag.startswith(f"{{{XBRLI_NS}}}") or tag.startswith(f"{{{LINKBASE_NS}}}"):
            continue  # schema / context / linkbase elements, not facts
        ctx_ref = elem.get("contextRef", "")
        if not ctx_ref:
            continue
        local = tag.split("}", 1)[-1] if "}" in tag else tag
        facts.setdefault(local, {})[ctx_ref] = (elem.text or "").strip()

    return {"contexts": contexts, "facts": facts}


def _get(facts: dict, tag: str, ctx: str) -> Optional[float]:
    return _safe_float(facts.get(tag, {}).get(ctx))


def build_result_fields(parsed: dict) -> dict:
    """
    Map parsed XBRL facts onto :class:`nse_xbrl.models.FilingResult` fields.

    ``parsed`` is the dict returned by :func:`parse_xbrl`. The result dict
    has keys matching ``FilingResult`` field names (``q_revenue``,
    ``bs_total_assets``, ``cf_capex``, ``period_end``, etc.) plus a
    ``raw_facts`` key containing every fact restricted to the four main
    contexts, for anything not covered by the standard mapping.
    """
    ctx = parsed["contexts"]
    facts = parsed["facts"]

    fields: dict = {}

    # ── Period dates ──────────────────────────────────────────────────────
    if CONTEXT_CURRENT_QUARTER in ctx:
        fields["period_start"] = ctx[CONTEXT_CURRENT_QUARTER].get("start")
        fields["period_end"] = ctx[CONTEXT_CURRENT_QUARTER].get("end")
    if CONTEXT_YEAR_TO_DATE in ctx:
        fields["ytd_start"] = ctx[CONTEXT_YEAR_TO_DATE].get("start")
        fields["ytd_end"] = ctx[CONTEXT_YEAR_TO_DATE].get("end")
    if CONTEXT_BALANCE_SHEET in ctx:
        fields["bs_date"] = ctx[CONTEXT_BALANCE_SHEET].get("instant")
    if CONTEXT_BALANCE_SHEET_PRIOR_YEAR in ctx:
        fields["py_bs_date"] = ctx[CONTEXT_BALANCE_SHEET_PRIOR_YEAR].get("instant")

    # ── Income Statement: quarter (OneD) + YTD (FourD) ──────────────────────
    for suffix, tag in INCOME_STATEMENT_TAGS.items():
        fields[f"q_{suffix}"] = _get(facts, tag, CONTEXT_CURRENT_QUARTER)
        fields[f"ytd_{suffix}"] = _get(facts, tag, CONTEXT_YEAR_TO_DATE)

    # ── Shared capital-structure fields ─────────────────────────────────────
    for field, tag in SHARED_TAGS.items():
        fields[field] = (
            _get(facts, tag, CONTEXT_CURRENT_QUARTER)
            or _get(facts, tag, CONTEXT_YEAR_TO_DATE)
        )

    # ── Balance Sheet: current (OneI) + prior year (PY_I) ────────────────────
    for suffix, tag in BALANCE_SHEET_TAGS.items():
        fields[f"bs_{suffix}"] = _get(facts, tag, CONTEXT_BALANCE_SHEET)
    for suffix, tag in PRIOR_YEAR_BALANCE_SHEET_TAGS.items():
        fields[f"py_{suffix}"] = _get(facts, tag, CONTEXT_BALANCE_SHEET_PRIOR_YEAR)

    # ── Cash Flow (YTD / FourD) ───────────────────────────────────────────────
    for suffix, tag in CASH_FLOW_TAGS.items():
        fields[f"cf_{suffix}"] = _get(facts, tag, CONTEXT_YEAR_TO_DATE)

    # ── Raw facts, restricted to the 4 main contexts ─────────────────────────
    raw: dict = {}
    for tag, ctx_vals in facts.items():
        filtered = {k: v for k, v in ctx_vals.items() if k in _MAIN_CONTEXTS}
        if filtered:
            raw[tag] = filtered
    fields["raw_facts"] = raw

    return fields
