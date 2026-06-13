"""
XBRL tag -> field mappings for NSE "Integrated Filing - Financials" (IFIndAs taxonomy).

NSE moved all post-2024 quarterly/annual financial filings to a combined
"Integrated Filing" XBRL document. Each document contains four key contexts:

    OneD   duration   current quarter / period           (e.g. Q3 FY26: Oct-Dec 2025)
    FourD  duration   full year / year-to-date           (e.g. Apr 2025 - Dec 2025)
    OneI   instant    balance sheet date (current)       (e.g. 2025-12-31)
    PY_I   instant    balance sheet date (prior year)     (e.g. 2024-12-31)

Every fact element in the XBRL is tagged with a `contextRef` pointing at one
of these. The dictionaries below map a short, human-friendly field name to
the XBRL element's *local* tag name (namespace-stripped) -- e.g.
``RevenueFromOperations`` regardless of whether the document uses the
``in-bse-fin``, ``in-capmkt``, or ``in-ind-as`` namespace prefix for it.

These tag names come from the IFRS/Ind-AS XBRL taxonomy and are notoriously
hard to find documentation for -- this mapping is itself one of the more
useful artifacts in this package.
"""

# ── Income Statement ───────────────────────────────────────────────────────
# Applied to both `q_<field>` (context OneD) and `ytd_<field>` (context FourD).
INCOME_STATEMENT_TAGS = {
    "revenue":              "RevenueFromOperations",
    "other_income":         "OtherIncome",
    "total_income":         "Income",
    "employee_expense":     "EmployeeBenefitExpense",
    "cost_of_materials":    "CostOfMaterialsConsumed",
    "purchase_stock_trade": "PurchasesOfStockInTrade",
    "changes_inventories":  "ChangesInInventoriesOfFinishedGoodsWorkInProgressAndStockInTrade",
    "depreciation":         "DepreciationDepletionAndAmortisationExpense",
    "finance_costs":        "FinanceCosts",
    "other_expenses":       "OtherExpenses",
    "total_expenses":       "Expenses",
    "exceptional_items":    "ExceptionalItemsBeforeTax",
    "ebit":                 "ProfitBeforeExceptionalItemsAndTax",
    "pbt":                  "ProfitBeforeTax",
    "current_tax":          "CurrentTax",
    "deferred_tax":         "DeferredTax",
    "total_tax":            "TaxExpense",
    "pat":                  "ProfitLossForPeriod",
    "pat_owners":           "ProfitOrLossAttributableToOwnersOfParent",
    "pat_nci":              "ProfitOrLossAttributableToNonControllingInterests",
    "oci":                  "OtherComprehensiveIncome",
    "total_comprehensive":  "ComprehensiveIncomeForThePeriod",
    "diluted_eps":          "DilutedEarningsLossPerShareFromContinuingOperations",
    "basic_eps":            "BasicEarningsLossPerShareFromContinuingOperations",
}

# ── Balance Sheet (current period, context OneI) ──────────────────────────
BALANCE_SHEET_TAGS = {
    "total_assets":             "EquityAndLiabilities",
    "noncurrent_assets":        "NoncurrentAssets",
    "ppe":                      "PropertyPlantAndEquipment",
    "goodwill":                 "Goodwill",
    "other_intangibles":        "OtherIntangibleAssets",
    "noncurrent_investments":   "NoncurrentInvestments",
    "noncurrent_fin_assets":    "NoncurrentFinancialAssets",
    "deferred_tax_assets":      "DeferredTaxAssetsNet",
    "other_noncurrent_assets":  "OtherNoncurrentAssets",
    "current_assets":           "CurrentAssets",
    "inventories":              "Inventories",
    "trade_receivables":        "TradeReceivablesCurrent",
    "current_investments":      "CurrentInvestments",
    "current_fin_assets":       "CurrentFinancialAssets",
    "other_current_assets":     "OtherCurrentAssets",
    "equity":                   "Equity",
    "equity_share_capital":     "EquityShareCapital",
    "other_equity":             "OtherEquity",
    "equity_owners":            "EquityAttributableToOwnersOfParent",
    "nci":                      "NonControllingInterest",
    "total_liabilities":        "Liabilities",
    "noncurrent_liabilities":   "NoncurrentLiabilities",
    "noncurrent_fin_liab":      "NoncurrentFinancialLiabilities",
    "deferred_tax_liabilities": "DeferredTaxLiabilitiesNet",
    "other_noncurrent_liab":    "OtherNoncurrentLiabilities",
    "current_liabilities":      "CurrentLiabilities",
    "trade_payables":           "TradePayablesCurrent",
    "current_fin_liab":         "CurrentFinancialLiabilities",
    "other_current_liab":       "OtherCurrentLiabilities",
    "provisions_current":       "ProvisionsCurrent",
    "current_tax_liab":         "CurrentTaxLiabilities",
}

# ── Balance Sheet (prior year, context PY_I) ───────────────────────────────
# NSE only reliably tags a subset of BS lines for the prior-year instant.
PRIOR_YEAR_BALANCE_SHEET_TAGS = {
    "total_assets":           "EquityAndLiabilities",
    "noncurrent_assets":      "NoncurrentAssets",
    "current_assets":         "CurrentAssets",
    "equity":                 "Equity",
    "equity_share_capital":   "EquityShareCapital",
    "other_equity":           "OtherEquity",
    "noncurrent_liabilities": "NoncurrentLiabilities",
    "current_liabilities":    "CurrentLiabilities",
    "trade_receivables":      "TradeReceivablesCurrent",
    "trade_payables":         "TradePayablesCurrent",
    "inventories":            "Inventories",
    "ppe":                    "PropertyPlantAndEquipment",
}

# ── Cash Flow (full year / YTD, context FourD) ──────────────────────────────
# NSE's Integrated Filing only carries a handful of cash-flow line items --
# not a full cash flow statement.
CASH_FLOW_TAGS = {
    "tax_paid":           "IncomeTaxesPaidRefundClassifiedAsOperatingActivities",
    "capex":              "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
    "dividends_paid":     "DividendsPaidClassifiedAsFinancingActivities",
    "interest_received":  "InterestReceivedClassifiedAsInvestingActivities",
    "net_change_in_cash": "IncreaseDecreaseInCashAndCashEquivalents",
    "fx_effect":          "EffectOfExchangeRateChangesOnCashAndCashEquivalents",
    "other_investing":    "OtherInflowsOutflowsOfCashClassifiedAsInvestingActivities",
    "other_financing":    "OtherInflowsOutflowsOfCashClassifiedAsFinancingActivities",
}

# ── Shared / capital structure tags ─────────────────────────────────────────
# Present under OneD and/or FourD depending on the filer.
SHARED_TAGS = {
    "paid_up_equity": "PaidUpValueOfEquityShareCapital",
    "face_value":     "FaceValueOfEquityShareCapital",
}

# Context IDs used by the IFIndAs Integrated Filing taxonomy.
CONTEXT_CURRENT_QUARTER = "OneD"
CONTEXT_YEAR_TO_DATE = "FourD"
CONTEXT_BALANCE_SHEET = "OneI"
CONTEXT_BALANCE_SHEET_PRIOR_YEAR = "PY_I"
