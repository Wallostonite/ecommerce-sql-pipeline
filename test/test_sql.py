# ================================================================
# tests/test_sql.py — Unit Tests for the ShopStream ecommerce pipeline
# ================================================================

import sys, pathlib
try:
    _root = pathlib.Path(__file__).resolve().parent.parent
except NameError:
    _root = pathlib.Path.cwd().parent

if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import pandas as pd
import config
from src.query_runner   import SQLQueryRunner
from src.data_extractor import DataExtractor


# ── SQL File Tests ────────────────────────────────────────────────

def test_sql_files_exist():
    """All four SQL query files must exist in the queries/ directory."""
    expected = [
        "01_explore.sql",
        "02_aggregations.sql",
        "03_five_table_join.sql",
        "04_advanced.sql",
    ]
    for fname in expected:
        assert (config.SQL_DIR / fname).exists(), f"SQL file missing: {fname}"


def test_sql_files_contain_select_keyword():
    """Each SQL file must contain at least one SELECT statement."""
    for fname in [
        "01_explore.sql",
        "02_aggregations.sql",
        "03_five_table_join.sql",
        "04_advanced.sql",
    ]:
        content = (config.SQL_DIR / fname).read_text()
        assert "SELECT" in content.upper(), f"No SELECT found in {fname}"


def test_all_sql_files_contain_industry_placeholder():
    """
    Every SQL file must use {industry} instead of a hardcoded schema name.
    This ensures SQLQueryRunner can inject the correct schema at runtime.
    """
    for fname in [
        "01_explore.sql",
        "02_aggregations.sql",
        "03_five_table_join.sql",
        "04_advanced.sql",
    ]:
        content = (config.SQL_DIR / fname).read_text()
        assert "{industry}" in content, (
            f"{fname} must use {{industry}} placeholder — "
            f"do not hardcode 'ecommerce' directly in SQL files"
        )


def test_join_sql_contains_left_join():
    """
    03_five_table_join.sql must use a LEFT JOIN for the reviews table.
    An INNER JOIN would silently drop orders without reviews.
    """
    content = (config.SQL_DIR / "03_five_table_join.sql").read_text().upper()
    assert "LEFT JOIN" in content, (
        "03_five_table_join.sql must LEFT JOIN reviews — "
        "orders without reviews must be preserved in the extract"
    )


def test_aggregation_sql_contains_group_by():
    """02_aggregations.sql must use GROUP BY for aggregation logic."""
    content = (config.SQL_DIR / "02_aggregations.sql").read_text().upper()
    assert "GROUP BY" in content, "02_aggregations.sql must contain GROUP BY"


def test_advanced_sql_contains_cte_and_window_function():
    """04_advanced.sql must contain both a CTE (WITH) and a window function (OVER)."""
    content = (config.SQL_DIR / "04_advanced.sql").read_text().upper()
    assert "WITH " in content, "04_advanced.sql must contain a CTE (WITH clause)"
    assert " OVER " in content, "04_advanced.sql must contain a window function (OVER clause)"


# ── SQLQueryRunner Tests ──────────────────────────────────────────

def test_query_runner_returns_dataframe():
    """SQLQueryRunner.run() must always return a DataFrame (never crashes)."""
    runner = SQLQueryRunner()
    df = runner.run("SELECT 1 AS test_col")
    assert isinstance(df, pd.DataFrame), "run() must always return a DataFrame"


def test_query_runner_handles_bad_sql_gracefully():
    """A broken query should return an empty DataFrame, not raise an exception."""
    runner = SQLQueryRunner()
    df = runner.run("THIS IS NOT VALID SQL AT ALL")
    assert isinstance(df, pd.DataFrame), (
        "run() should return an empty DataFrame on SQL error, not raise an exception"
    )


def test_query_runner_history_records_each_run():
    """Every query run must be appended to the history log."""
    runner = SQLQueryRunner()
    initial_count = len(runner.history)
    runner.run("SELECT 1")
    runner.run("SELECT 2")
    assert len(runner.history) == initial_count + 2, (
        "history should record one entry per query run"
    )


def test_query_runner_history_entry_has_required_keys():
    """Each history entry must contain the expected audit fields."""
    runner = SQLQueryRunner()
    runner.run("SELECT 1 AS x")
    entry = runner.history[-1]
    for key in ("sql_preview", "rows", "cols", "duration_ms", "status"):
        assert key in entry, f"History entry missing key: {key}"


def test_query_runner_missing_file_returns_empty_dataframe():
    """run_file() with a non-existent filename must return an empty DataFrame."""
    runner = SQLQueryRunner()
    df = runner.run_file("does_not_exist.sql")
    assert isinstance(df, pd.DataFrame), "run_file() should return empty DataFrame for missing file"
    assert df.empty, "run_file() should return empty DataFrame for missing file"


# ── DataExtractor Synthetic Data Tests ───────────────────────────

def test_extractor_synthetic_data_has_required_columns():
    """Synthetic fallback data must contain all 23 expected ecommerce columns."""
    raw = DataExtractor._synthetic_raw_data(50)

    assert isinstance(raw, pd.DataFrame), "Expected DataFrame output"
    assert len(raw) == 50, f"Expected 50 rows, got {len(raw)}"

    required = [
        # Order
        "order_id", "order_date", "total_amount", "order_status",
        # Customer
        "customer_id", "first_name", "last_name", "customer_email",
        "customer_city", "customer_country", "customer_segment",
        # Product
        "product_id", "product_name", "product_category", "product_price",
        # Seller  (sellers table has category, not city)
        "seller_id", "owner_name", "seller_country", "seller_category",
        # Review (nullable — LEFT JOIN)
        "review_id", "rating", "review_text",
        # Pipeline metadata
        "source_schema", "extracted_date",
    ]

    for col in required:
        assert col in raw.columns, f"Synthetic data missing column: {col}"


def test_extractor_synthetic_data_correct_row_count():
    """_synthetic_raw_data(n) must return exactly n rows."""
    for n in [10, 100, 500]:
        raw = DataExtractor._synthetic_raw_data(n)
        assert len(raw) == n, f"Expected {n} rows, got {len(raw)}"


def test_extractor_synthetic_data_has_quality_issues():
    """
    Synthetic data must contain the intentional data quality issues
    that Module 05 ETL is designed to detect and fix.
    """
    raw = DataExtractor._synthetic_raw_data(300)

    # ~25% of orders have no review (LEFT JOIN behaviour)
    null_reviews = raw["rating"].isna().sum()
    assert null_reviews > 0, (
        "Synthetic data should have NULL rating rows — "
        "mirrors the LEFT JOIN on reviews"
    )

    # ~2% negative total_amount (data entry error)
    neg_orders = (raw["total_amount"] < 0).sum()
    assert neg_orders > 0, "Synthetic data should have some negative total_amount rows"

    # ~6% NULL customer_email
    null_emails = raw["customer_email"].isna().sum()
    assert null_emails > 0, "Synthetic data should have some NULL customer_email rows"

    # ~3% total_amount >> product_price (possible duplicate charge)
    overcharge = (raw["total_amount"] > raw["product_price"] * 10).sum()
    assert overcharge > 0, (
        "Synthetic data should have some rows where total_amount >> product_price"
    )


def test_extractor_synthetic_data_is_deterministic():
    """Two calls to _synthetic_raw_data(n) must produce identical DataFrames."""
    df1 = DataExtractor._synthetic_raw_data(100)
    df2 = DataExtractor._synthetic_raw_data(100)
    pd.testing.assert_frame_equal(df1, df2, check_like=False)


def test_extractor_synthetic_data_review_scores_plausible():
    """
    review_score must be 1–5 for rows that have a review.
    Rows without a review should be null, not 0.
    """
    raw = DataExtractor._synthetic_raw_data(200)
    has_review = raw["rating"].dropna()  # rating is the actual DB column name

    # The intentional out-of-range injection is ~1%, so most scored rows are 1–5
    in_range = has_review.between(1, 5).sum()
    assert in_range / len(has_review) > 0.95, (
        "At least 95% of non-null review scores should be between 1 and 5"
    )

    # No zeros — a missing review should be null, not 0
    zeros = (raw["rating"] == 0).sum()
    assert zeros == 0, "rating should be null for missing reviews, not 0"


# ── DataExtractor Save / Load Tests ──────────────────────────────

def test_extractor_save_creates_csv(tmp_path, monkeypatch):
    """DataExtractor.save() must create raw-data.csv at the configured path."""
    target_path = tmp_path / "raw-data.csv"

    # Patch the namespace where save() resolves RAW_DATA_PATH
    # (data_extractor.py uses: from config import RAW_DATA_PATH)
    monkeypatch.setattr("src.data_extractor.RAW_DATA_PATH", target_path)

    extractor = DataExtractor()
    extractor.raw_df = DataExtractor._synthetic_raw_data(50)
    extractor._status = "extracted"
    extractor.save()

    assert target_path.exists(), f"save() should create raw-data.csv at {target_path}"

    reloaded = pd.read_csv(target_path)
    assert len(reloaded) == 50, "Saved CSV should have the correct row count"

    # Verify the full ecommerce schema is preserved after save/load
    for col in ["order_id", "total_amount", "first_name", "last_name",
                "owner_name", "rating"]:
        assert col in reloaded.columns, f"Saved CSV missing column: {col}"


def test_extractor_save_without_extract_does_not_crash():
    """Calling save() before extract() should log an error but not raise an exception."""
    extractor = DataExtractor()
    try:
        extractor.save()   # raw_df is None — should warn, not crash
    except Exception as e:
        assert False, f"save() before extract() should not raise: {e}"


def test_extractor_chaining_returns_self():
    """extract() and save() must return self to support method chaining."""
    extractor = DataExtractor()
    result = extractor.extract()
    assert result is extractor, "extract() must return self"


if __name__ == "__main__":
    import pytest
    pytest.main(["-v", "--tb=short", __file__])
