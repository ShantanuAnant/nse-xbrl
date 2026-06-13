from datetime import date
from pathlib import Path

import pytest

from nse_xbrl import FilingResult, build_result_fields, parse_xbrl

FIXTURE = Path(__file__).parent / "fixtures" / "sample_filing.xml"


@pytest.fixture(scope="module")
def xml_text():
    return FIXTURE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def parsed(xml_text):
    return parse_xbrl(xml_text)


def test_parse_xbrl_contexts(parsed):
    contexts = parsed["contexts"]

    assert contexts["OneD"]["type"] == "duration"
    assert contexts["OneD"]["start"] == date(2025, 10, 1)
    assert contexts["OneD"]["end"] == date(2025, 12, 31)

    assert contexts["FourD"]["type"] == "duration"
    assert contexts["FourD"]["start"] == date(2025, 4, 1)
    assert contexts["FourD"]["end"] == date(2025, 12, 31)

    assert contexts["OneI"]["type"] == "instant"
    assert contexts["OneI"]["instant"] == date(2025, 12, 31)

    assert contexts["PY_I"]["type"] == "instant"
    assert contexts["PY_I"]["instant"] == date(2024, 3, 31)


def test_parse_xbrl_facts_strip_namespace(parsed):
    facts = parsed["facts"]
    assert "RevenueFromOperations" in facts
    assert facts["RevenueFromOperations"]["OneD"] == "125000000000"
    assert facts["RevenueFromOperations"]["FourD"] == "370000000000"


def test_build_result_fields_income_statement(parsed):
    fields = build_result_fields(parsed)

    assert fields["q_revenue"] == 125_000_000_000
    assert fields["q_other_income"] == 2_500_000_000
    assert fields["q_total_income"] == 127_500_000_000
    assert fields["q_pbt"] == 31_500_000_000
    assert fields["q_pat"] == 24_000_000_000
    assert fields["q_diluted_eps"] == pytest.approx(17.35)

    assert fields["ytd_revenue"] == 370_000_000_000
    assert fields["ytd_pat"] == 70_000_000_000


def test_build_result_fields_balance_sheet(parsed):
    fields = build_result_fields(parsed)

    assert fields["bs_total_assets"] == 950_000_000_000
    assert fields["bs_equity"] == 550_000_000_000
    assert fields["bs_current_fin_liab"] == 50_000_000_000

    assert fields["py_total_assets"] == 880_000_000_000
    assert fields["py_equity"] == 490_000_000_000


def test_build_result_fields_cash_flow_and_dates(parsed):
    fields = build_result_fields(parsed)

    assert fields["cf_capex"] == -35_000_000_000
    assert fields["cf_net_change_in_cash"] == 5_000_000_000

    assert fields["period_start"] == date(2025, 10, 1)
    assert fields["period_end"] == date(2025, 12, 31)
    assert fields["bs_date"] == date(2025, 12, 31)
    assert fields["py_bs_date"] == date(2024, 3, 31)


def test_raw_facts_excludes_segment_contexts(parsed):
    fields = build_result_fields(parsed)
    raw = fields["raw_facts"]

    # The segment-dimensional fact (OneD_SegmentA) must not leak into raw_facts.
    assert "OneD_SegmentA" not in raw.get("RevenueFromOperations", {})
    # But the four main-context values are retained.
    assert raw["RevenueFromOperations"]["OneD"] == "125000000000"
    assert raw["RevenueFromOperations"]["FourD"] == "370000000000"


def test_filing_result_from_xbrl(xml_text):
    result = FilingResult.from_xbrl(xml_text, symbol="TEST", is_consolidated=True)

    assert result.symbol == "TEST"
    assert result.is_consolidated is True
    assert result.q_revenue == 125_000_000_000
    assert result.bs_total_assets == 950_000_000_000


def test_computed_properties(xml_text):
    result = FilingResult.from_xbrl(xml_text)

    # q_ebitda = q_ebit + q_depreciation
    assert result.q_ebitda == pytest.approx(31_500_000_000 + 5_000_000_000)

    # shares_outstanding = paid_up_equity / face_value
    assert result.shares_outstanding == pytest.approx(13_500_000_000 / 10)

    # debt_equity_ratio = (current + noncurrent financial liabilities) / equity
    expected_de = (50_000_000_000 + 120_000_000_000) / 550_000_000_000
    assert result.debt_equity_ratio == pytest.approx(expected_de)

    # book_value_per_share = equity / shares_outstanding
    expected_bvps = 550_000_000_000 / (13_500_000_000 / 10)
    assert result.book_value_per_share == pytest.approx(expected_bvps)
