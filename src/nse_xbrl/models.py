"""
Typed result container for a parsed NSE Integrated Filing.

Field naming convention (matches the XBRL contexts):

==========  ===================================================
prefix      meaning
==========  ===================================================
``q_``      current quarter / period      (context ``OneD``)
``ytd_``    year-to-date / full year      (context ``FourD``)
``bs_``     balance sheet, current date   (context ``OneI``)
``py_``     balance sheet, prior year     (context ``PY_I``)
``cf_``     cash flow, year-to-date       (context ``FourD``)
==========  ===================================================

All monetary fields are ``Optional[float]`` in absolute INR (NSE XBRL
typically reports with ``decimals="-7"``, i.e. precision to the nearest
₹10 million -- divide by 1e5 for lakhs or 1e7 for crores). EPS fields are
INR per share. Any field absent from the filing is ``None``.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import date
from typing import Optional

from .xbrl import build_result_fields, parse_xbrl

_F = Optional[float]


@dataclass
class FilingResult:
    """Parsed financials for one NSE Integrated Filing."""

    # ── Filing metadata (not present in the XBRL itself; set by the caller
    #    or by NSEClient from the filing listing) ───────────────────────────
    symbol: str = ""
    company_name: str = ""
    seq_id: str = ""
    is_audited: bool = False
    is_consolidated: bool = False
    xbrl_url: str = ""

    # ── Period dates ─────────────────────────────────────────────────────
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    ytd_start: Optional[date] = None
    ytd_end: Optional[date] = None
    bs_date: Optional[date] = None
    py_bs_date: Optional[date] = None

    # ── Income Statement — current quarter (OneD) ───────────────────────────
    q_revenue: _F = None
    q_other_income: _F = None
    q_total_income: _F = None
    q_employee_expense: _F = None
    q_cost_of_materials: _F = None
    q_purchase_stock_trade: _F = None
    q_changes_inventories: _F = None
    q_depreciation: _F = None
    q_finance_costs: _F = None
    q_other_expenses: _F = None
    q_total_expenses: _F = None
    q_exceptional_items: _F = None
    q_ebit: _F = None
    q_pbt: _F = None
    q_current_tax: _F = None
    q_deferred_tax: _F = None
    q_total_tax: _F = None
    q_pat: _F = None
    q_pat_owners: _F = None
    q_pat_nci: _F = None
    q_oci: _F = None
    q_total_comprehensive: _F = None
    q_diluted_eps: _F = None
    q_basic_eps: _F = None

    # ── Income Statement — year to date (FourD) ─────────────────────────────
    ytd_revenue: _F = None
    ytd_other_income: _F = None
    ytd_total_income: _F = None
    ytd_employee_expense: _F = None
    ytd_cost_of_materials: _F = None
    ytd_purchase_stock_trade: _F = None
    ytd_changes_inventories: _F = None
    ytd_depreciation: _F = None
    ytd_finance_costs: _F = None
    ytd_other_expenses: _F = None
    ytd_total_expenses: _F = None
    ytd_exceptional_items: _F = None
    ytd_ebit: _F = None
    ytd_pbt: _F = None
    ytd_current_tax: _F = None
    ytd_deferred_tax: _F = None
    ytd_total_tax: _F = None
    ytd_pat: _F = None
    ytd_pat_owners: _F = None
    ytd_pat_nci: _F = None
    ytd_oci: _F = None
    ytd_total_comprehensive: _F = None
    ytd_diluted_eps: _F = None
    ytd_basic_eps: _F = None

    # ── Capital structure (shared) ──────────────────────────────────────────
    paid_up_equity: _F = None
    face_value: _F = None

    # ── Balance Sheet — current (OneI) ───────────────────────────────────────
    bs_total_assets: _F = None
    bs_noncurrent_assets: _F = None
    bs_ppe: _F = None
    bs_goodwill: _F = None
    bs_other_intangibles: _F = None
    bs_noncurrent_investments: _F = None
    bs_noncurrent_fin_assets: _F = None
    bs_deferred_tax_assets: _F = None
    bs_other_noncurrent_assets: _F = None
    bs_current_assets: _F = None
    bs_inventories: _F = None
    bs_trade_receivables: _F = None
    bs_current_investments: _F = None
    bs_current_fin_assets: _F = None
    bs_other_current_assets: _F = None
    bs_equity: _F = None
    bs_equity_share_capital: _F = None
    bs_other_equity: _F = None
    bs_equity_owners: _F = None
    bs_nci: _F = None
    bs_total_liabilities: _F = None
    bs_noncurrent_liabilities: _F = None
    bs_noncurrent_fin_liab: _F = None
    bs_deferred_tax_liabilities: _F = None
    bs_other_noncurrent_liab: _F = None
    bs_current_liabilities: _F = None
    bs_trade_payables: _F = None
    bs_current_fin_liab: _F = None
    bs_other_current_liab: _F = None
    bs_provisions_current: _F = None
    bs_current_tax_liab: _F = None

    # ── Balance Sheet — prior year (PY_I) ─────────────────────────────────────
    py_total_assets: _F = None
    py_noncurrent_assets: _F = None
    py_current_assets: _F = None
    py_equity: _F = None
    py_equity_share_capital: _F = None
    py_other_equity: _F = None
    py_noncurrent_liabilities: _F = None
    py_current_liabilities: _F = None
    py_trade_receivables: _F = None
    py_trade_payables: _F = None
    py_inventories: _F = None
    py_ppe: _F = None

    # ── Cash Flow — year to date (FourD) ───────────────────────────────────────
    cf_tax_paid: _F = None
    cf_capex: _F = None
    cf_dividends_paid: _F = None
    cf_interest_received: _F = None
    cf_net_change_in_cash: _F = None
    cf_fx_effect: _F = None
    cf_other_investing: _F = None
    cf_other_financing: _F = None

    # ── Full raw facts (everything not covered above, for the 4 main contexts) ──
    raw_facts: dict = field(default_factory=dict, repr=False)

    # ── Constructors ─────────────────────────────────────────────────────────

    @classmethod
    def from_xbrl(cls, xml_text: str, **meta) -> "FilingResult":
        """
        Parse an XBRL document string directly into a ``FilingResult``.

        ``**meta`` lets you attach filing metadata that isn't part of the
        XBRL itself (``symbol``, ``company_name``, ``seq_id``,
        ``is_consolidated``, ``is_audited``, ``xbrl_url``)::

            result = FilingResult.from_xbrl(xml_text, symbol="RELIANCE",
                                             is_consolidated=True)
        """
        parsed = parse_xbrl(xml_text)
        data = build_result_fields(parsed)
        valid = {f.name for f in fields(cls)}
        data = {k: v for k, v in data.items() if k in valid}
        data.update({k: v for k, v in meta.items() if k in valid})
        return cls(**data)

    # ── Computed helpers (mirroring common ratio definitions) ─────────────────

    @property
    def q_ebitda(self) -> _F:
        """Quarter EBITDA = EBIT + Depreciation."""
        if self.q_ebit is not None and self.q_depreciation is not None:
            return self.q_ebit + self.q_depreciation
        return None

    @property
    def ytd_ebitda(self) -> _F:
        """YTD EBITDA = EBIT + Depreciation."""
        if self.ytd_ebit is not None and self.ytd_depreciation is not None:
            return self.ytd_ebit + self.ytd_depreciation
        return None

    @property
    def shares_outstanding(self) -> _F:
        """Shares outstanding = paid_up_equity / face_value."""
        if self.paid_up_equity and self.face_value and self.face_value > 0:
            return self.paid_up_equity / self.face_value
        return None

    @property
    def debt_equity_ratio(self) -> _F:
        """(Current + Non-current financial liabilities) / Total Equity, from the balance sheet."""
        if self.bs_equity:
            debt = (self.bs_current_fin_liab or 0) + (self.bs_noncurrent_fin_liab or 0)
            return debt / self.bs_equity
        return None

    @property
    def book_value_per_share(self) -> _F:
        """Total equity / shares outstanding."""
        shares = self.shares_outstanding
        if self.bs_equity is not None and shares:
            return self.bs_equity / shares
        return None
