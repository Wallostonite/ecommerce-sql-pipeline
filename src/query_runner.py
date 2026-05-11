# ================================================================
# src/query_runner.py
# ================================================================
# CONTEXT:
#   We wrote SQL in .sql files inside queries/.
#   This module executes those files from Python and returns
#   pandas DataFrames we can inspect, transform, and save.
#
# THE ANALOGY:
#   Think of SQLQueryRunner as a translator.
#   You hand it a SQL query (a string or a filename).
#   It sends that query to PostgreSQL via the SQLAlchemy engine.
#   PostgreSQL sends back rows of data.
#   SQLQueryRunner catches those rows and packages them as a DataFrame.
#
# KEY pandas FUNCTION: pd.read_sql()
#   pd.read_sql(sql_string, engine) executes SQL and returns a DataFrame.
#   This is the bridge between a relational database and Python analysis.
#
# WHY A CLASS AND NOT JUST pd.read_sql() DIRECTLY?
#   The class adds:
#     - Error handling  (what if the query fails?)
#     - Logging         (track what ran and when)
#     - Timing          (how long did each query take?)
#     - Query loading   (read from .sql files, not inline strings)
#     - {industry} swap (schema name injected at runtime)
#   These extras make it production-grade rather than just a script.
#
# {industry} PLACEHOLDER:
#   Every .sql file uses {industry} instead of hardcoding "ecommerce".
#   The run() method replaces {industry} with self.industry at runtime.
#   This makes the SQL files reusable if the schema is ever renamed
#   or if the same query structure is needed for a different schema.
# ================================================================

import sys
import pathlib
import time

# ── Path bootstrap ────────────────────────────────────────────────
# Make sure the project root is on sys.path so `config` can be imported
# regardless of where Python is invoked from.
_root = pathlib.Path(__file__).resolve().parent
while not (_root / "config.py").exists() and _root != _root.parent:
    _root = _root.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import pandas as pd
from config import engine, DB_AVAILABLE, SQL_DIR, INDUSTRY, logger


class SQLQueryRunner:
    """
    Executes SQL queries against the ShopStream Supabase PostgreSQL database.
    Returns results as pandas DataFrames.

    Attributes
    ──────────
    industry   str           the configured schema name  (default: "ecommerce")
    history    list[dict]    audit log of every query run (sql preview, rows,
                             cols, duration, status)
    """

    def __init__(self):
        self.industry = INDUSTRY
        self.history  = []
        logger.info(f"SQLQueryRunner ready — schema: {self.industry} | db_available: {DB_AVAILABLE}")

    # ── Core execution ────────────────────────────────────────────

    def run(self, sql: str, params: dict = None) -> pd.DataFrame:
        """
        Execute a SQL string and return results as a DataFrame.

        Args:
            sql     SQL query string. Use {industry} instead of a hardcoded
                    schema name — it will be replaced with self.industry.
            params  optional dict for parameterised queries
                    e.g. params={"category": "Electronics"}
                    used as WHERE category = :category in the SQL.

        Returns:
            pd.DataFrame — empty DataFrame if the query fails or db is offline.
        """
        if not DB_AVAILABLE or engine is None:
            logger.warning("[SQL] Database not available — returning empty DataFrame.")
            return pd.DataFrame()

        # Inject the schema name into the SQL string
        sql = sql.replace("{industry}", self.industry)

        start_time = time.time()

        try:
            df = pd.read_sql(sql, engine, params=params)

            duration_ms = round((time.time() - start_time) * 1000, 1)

            self.history.append({
                "sql_preview": sql[:80].strip(),
                "rows":        len(df),
                "cols":        len(df.columns),
                "duration_ms": duration_ms,
                "status":      "success",
            })

            logger.info(
                f"[SQL] {len(df):,} rows × {len(df.columns)} cols | {duration_ms}ms"
            )
            return df

        except Exception as e:
            self.history.append({
                "sql_preview": sql[:80].strip(),
                "rows":        0,
                "cols":        0,
                "duration_ms": round((time.time() - start_time) * 1000, 1),
                "status":      f"error: {str(e)[:100]}",
            })
            logger.error(f"[SQL] Query failed: {e}")
            return pd.DataFrame()

    def run_file(self, filename: str) -> pd.DataFrame:
        """
        Load a .sql file from the queries/ directory and execute it.

        Args:
            filename   name of the file, e.g. "03_five_table_join.sql"

        Returns:
            pd.DataFrame with results. Empty DataFrame if the file is missing
            or the query fails.
        """
        sql_path = SQL_DIR / filename

        if not sql_path.exists():
            logger.error(f"[SQL] File not found: {sql_path}")
            return pd.DataFrame()

        logger.info(f"[SQL] Loading: {filename}")
        sql_text = sql_path.read_text(encoding="utf-8")
        return self.run(sql_text)

    # ── Demo methods (one per .sql file) ─────────────────────────

    def demo_explore(self) -> None:
        """
        Run row-count checks against all five tables.
        Mirrors queries/01_explore.sql.
        Confirms the database connection is live and all tables exist.
        """
        tables = ["orders", "customers", "products", "sellers", "reviews"]

        print("\n── Table row counts:")
        for table in tables:
            sql = f"SELECT COUNT(*) AS total FROM {{industry}}.{table}"
            df  = self.run(sql)
            if not df.empty:
                print(f"   {table:<12} {df['total'].iloc[0]:>10,} rows")

    def demo_aggregations(self) -> None:
        """
        Run the three core business aggregations.
        Mirrors queries/02_aggregations.sql.
        """
        # Revenue by seller (top 10)
        sql_revenue = """
            SELECT
                s.owner_name,
                SUM(o.total_amount)           AS total_revenue,
                COUNT(o.order_id)            AS total_orders,
                ROUND(AVG(o.total_amount), 2) AS avg_total_amount
            FROM {industry}.orders   o
            JOIN {industry}.products p ON o.product_id  = p.product_id
            JOIN {industry}.sellers  s ON p.seller_id   = s.seller_id
            GROUP BY s.seller_id, s.owner_name
            ORDER BY total_revenue DESC
            LIMIT 10
        """
        print("\n── Top 10 Sellers by Revenue:")
        df = self.run(sql_revenue)
        if not df.empty:
            print(df.to_string(index=False))

        # Return rate by product category
        sql_returns = """
            SELECT
                p.category,
                COUNT(o.order_id)                                           AS total_orders,
                SUM(CASE WHEN o.status = 'returned' THEN 1 ELSE 0 END)     AS returns,
                ROUND(
                    100.0 * SUM(CASE WHEN o.status = 'returned' THEN 1 ELSE 0 END)
                    / NULLIF(COUNT(o.order_id), 0), 2
                )                                                           AS return_rate_pct
            FROM {industry}.orders   o
            JOIN {industry}.products p ON o.product_id = p.product_id
            GROUP BY p.category
            ORDER BY return_rate_pct DESC
        """
        print("\n── Return Rate by Product Category:")
        df = self.run(sql_returns)
        if not df.empty:
            print(df.to_string(index=False))

        # Average review score per seller
        sql_reviews = """
            SELECT
                s.owner_name,
                ROUND(AVG(r.rating), 2) AS avg_rating,
                COUNT(r.review_id)            AS total_reviews
            FROM {industry}.sellers  s
            JOIN {industry}.products p ON p.seller_id  = s.seller_id
            JOIN {industry}.orders   o ON o.product_id = p.product_id
            JOIN {industry}.reviews  r ON r.order_id   = o.order_id
            GROUP BY s.seller_id, s.owner_name
            ORDER BY avg_rating DESC
            LIMIT 10
        """
        print("\n── Top 10 Sellers by Avg Review Score:")
        df = self.run(sql_reviews)
        if not df.empty:
            print(df.to_string(index=False))

    def demo_joins(self) -> None:
        """
        Preview the five-table join (first 10 rows).
        Mirrors queries/03_five_table_join.sql.
        """
        sql = """
            SELECT
                o.order_id,
                o.order_date,
                o.total_amount,
                o.status          AS order_status,
                c.first_name,
                c.last_name,
                c.segment         AS customer_segment,
                p.product_name,
                p.category        AS product_category,
                s.owner_name,
                r.rating
            FROM {industry}.orders   o
            JOIN {industry}.customers c ON o.customer_id = c.customer_id
            JOIN {industry}.products  p ON o.product_id  = p.product_id
            JOIN {industry}.sellers   s ON p.seller_id   = s.seller_id
            LEFT JOIN {industry}.reviews r ON r.order_id = o.order_id
            ORDER BY o.order_date DESC
            LIMIT 10
        """
        print("\n── Five-Table Join Preview (10 rows):")
        df = self.run(sql)
        if not df.empty:
            print(df.to_string(index=False))

    def demo_advanced(self) -> None:
        """
        Run the CTE and window function queries.
        Mirrors queries/04_advanced.sql.
        """
        # CTE — seller revenue summary
        sql_cte = """
            WITH seller_revenue AS (
                SELECT
                    s.seller_id,
                    s.owner_name,
                    SUM(o.total_amount)  AS total_revenue,
                    COUNT(o.order_id)   AS order_count
                FROM {industry}.sellers  s
                JOIN {industry}.products p ON p.seller_id  = s.seller_id
                JOIN {industry}.orders   o ON o.product_id = p.product_id
                GROUP BY s.seller_id, s.owner_name
            )
            SELECT
                owner_name,
                total_revenue,
                order_count,
                ROUND(total_revenue / NULLIF(order_count, 0), 2) AS revenue_per_order
            FROM seller_revenue
            ORDER BY total_revenue DESC
            LIMIT 10
        """
        print("\n── CTE — Seller Revenue Summary (top 10):")
        df = self.run(sql_cte)
        if not df.empty:
            print(df.to_string(index=False))

        # Window function — customer spend ranking
        sql_window = """
            SELECT
                c.first_name,
                c.last_name,
                c.segment,
                SUM(o.total_amount)                             AS total_spend,
                RANK() OVER (ORDER BY SUM(o.total_amount) DESC) AS spend_rank,
                RANK() OVER (
                    PARTITION BY c.segment
                    ORDER BY SUM(o.total_amount) DESC
                )                                              AS rank_within_segment
            FROM {industry}.customers c
            JOIN {industry}.orders    o ON o.customer_id = c.customer_id
            GROUP BY c.customer_id, c.first_name, c.first_name, c.segment
            ORDER BY spend_rank
            LIMIT 15
        """
        print("\n── Window Function — Customer Spend Rankings (top 15):")
        df = self.run(sql_window)
        if not df.empty:
            print(df.to_string(index=False))

    # ── Audit log ─────────────────────────────────────────────────

    def history_summary(self) -> pd.DataFrame:
        """Return the query history as a DataFrame for inspection."""
        return pd.DataFrame(self.history)

    # ── Dunder methods ────────────────────────────────────────────

    def __str__(self) -> str:
        return (
            f"SQLQueryRunner(schema={self.industry!r}, "
            f"queries_run={len(self.history)})"
        )

    def __repr__(self) -> str:
        return f"SQLQueryRunner(schema={self.industry!r})"
