# ================================================================
# src/data_extractor.py
# ================================================================
# CONTEXT:
#   SQLQueryRunner can run any query. DataExtractor runs ONE specific
#   query: the production five-table join in 03_five_table_join.sql.
#
#   DataExtractor is the DELIVERY of this module.
#   Its output — raw-data.csv — is the INPUT to Module 05 ETL.
#
# THE PIPELINE CONNECTION:
#   DataExtractor → raw-data.csv → Module 05 ETLPipeline
#
# SEPARATION OF CONCERNS:
#   SQLQueryRunner  handles HOW to connect and execute SQL
#   DataExtractor   handles WHAT to run and WHERE to save it
#   run.py          handles orchestration (calling both in order)
#
# OFFLINE MODE:
#   If DB_AVAILABLE is False, _synthetic_raw_data() generates a
#   realistic ecommerce dataset so the rest of the pipeline can
#   still be demonstrated without a live database connection.
#   The synthetic data includes intentional quality issues
#   (nulls, negative values, mismatched totals) that Module 05
#   ETL is designed to detect and fix.
# ================================================================

import sys
import pathlib

# ── Path bootstrap ────────────────────────────────────────────────
_root = pathlib.Path(__file__).resolve().parent
while not (_root / "config.py").exists() and _root != _root.parent:
    _root = _root.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import pandas as pd
from config import INDUSTRY, RAW_DATA_PATH, DB_AVAILABLE, logger
from src.query_runner import SQLQueryRunner


class DataExtractor:
    """
    Runs the production five-table join and saves raw-data.csv.

    This class has one job: extract the ShopStream order data and
    persist it. SQLQueryRunner handles connection and execution.
    DataExtractor owns the business logic of which query to run,
    where to save it, and what quality checks to surface.

    Usage (method chaining):
        DataExtractor().extract().save().report()
    """

    def __init__(self):
        self.industry = INDUSTRY
        self.runner   = SQLQueryRunner()
        self.raw_df   = None     # populated by extract()
        self._status  = "ready"

    # ── Core methods ──────────────────────────────────────────────

    def extract(self) -> "DataExtractor":
        """
        Run 03_five_table_join.sql and load the results into self.raw_df.

        If the database is unavailable, falls back to _synthetic_raw_data()
        so the pipeline can be demonstrated offline.

        Returns self so calls can be chained: .extract().save().report()
        """
        logger.info(f"[EXTRACT] Starting extraction — schema: {self.industry}")

        if DB_AVAILABLE:
            self.raw_df = self.runner.run_file("03_five_table_join.sql")
        else:
            logger.warning("[EXTRACT] DB unavailable — generating synthetic raw data")
            self.raw_df = self._synthetic_raw_data()

        if self.raw_df is None or len(self.raw_df) == 0:
            logger.warning("[EXTRACT] Query returned 0 rows — falling back to synthetic data")
            self.raw_df = self._synthetic_raw_data()

        self._status = "extracted"
        logger.info(
            f"[EXTRACT] {len(self.raw_df):,} rows × {self.raw_df.shape[1]} columns extracted"
        )
        return self

    def save(self) -> "DataExtractor":
        """
        Save self.raw_df to data/raw-data.csv.

        This file is the handoff to Module 05 ETL. It is saved UTF-8
        encoded to handle international customer and seller names.

        Returns self for chaining.
        """
        if self.raw_df is None or len(self.raw_df) == 0:
            logger.error("[EXTRACT] No data to save — run extract() first.")
            return self

        self.raw_df.to_csv(RAW_DATA_PATH, index=False, encoding="utf-8")
        file_size_kb = RAW_DATA_PATH.stat().st_size / 1024
        logger.info(
            f"[EXTRACT] Saved {len(self.raw_df):,} rows → "
            f"{RAW_DATA_PATH.name} ({file_size_kb:.1f} KB)"
        )
        self._status = "saved"
        return self

    def report(self) -> None:
        """
        Print a plain-English summary of the extraction results.

        Surfaces raw data quality issues intentionally — these are
        expected inputs for the Module 05 ETL cleaning step.
        """
        if self.raw_df is None:
            print("No data extracted. Run extract() first.")
            return

        df = self.raw_df

        print()
        print("=" * 60)
        print(f"  EXTRACTION COMPLETE | SHOPSTREAM GLOBAL")
        print("=" * 60)
        print(f"  Rows extracted  :  {len(df):,}")
        print(f"  Columns         :  {df.shape[1]}")
        print(f"  Output file     :  {RAW_DATA_PATH.name}")
        if RAW_DATA_PATH.exists():
            print(f"  File size       :  {RAW_DATA_PATH.stat().st_size / 1024:.1f} KB")

        # ── Quick shape checks ────────────────────────────────────
        if "order_date" in df.columns:
            dates = pd.to_datetime(df["order_date"], errors="coerce")
            print(f"  Date range      :  {dates.min().date()} → {dates.max().date()}")

        if "seller_country" in df.columns:
            print(f"  Markets         :  {df['seller_country'].nunique()} countries")

        if "owner_name" in df.columns:
            print(f"  Sellers         :  {df['owner_name'].nunique():,}")

        if "customer_id" in df.columns:
            print(f"  Customers       :  {df['customer_id'].nunique():,}")

        # ── Data quality issues (intentional — Module 05 will fix) ─
        print()
        print("  DATA QUALITY ISSUES IN RAW DATA")
        print("  (expected — Module 05 ETL will handle these):")

        nulls = df.isna().sum()
        for col in nulls[nulls > 0].index:
            pct = round(nulls[col] / len(df) * 100, 1)
            print(f"    NULL {col:<28} {nulls[col]:>6,} rows  ({pct}%)")

        if "total_amount" in df.columns:
            neg = (df["total_amount"] < 0).sum()
            if neg:
                print(f"    Negative total_amount            {neg:>6,} rows")

        if "rating" in df.columns:
            out_of_range = (~df["rating"].between(1, 5)).sum()
            if out_of_range:
                print(f"    rating out of 1–5 range          {out_of_range:>6,} rows")

        if "product_price" in df.columns and "total_amount" in df.columns:
            mismatch = (df["total_amount"] > df["product_price"] * 10).sum()
            if mismatch:
                print(f"    total_amount >> product_price    {mismatch:>6,} rows  (possible data entry error)")

        print()
        print("  NEXT STEP: run the Module 05 ETL pipeline:")
        print("    python module-05-data-engineering-and-etl/run.py")
        print("=" * 60)

    # ── Synthetic fallback ────────────────────────────────────────

    @staticmethod
    def _synthetic_raw_data(n: int = 300) -> pd.DataFrame:
        """
        Generate synthetic ShopStream ecommerce data matching the
        03_five_table_join.sql output column-for-column.

        Column names match the ACTUAL database schema:
          total_amount  (not order_value)
          first_name / last_name  (not customer_name)
          owner_name    (not seller_name)
          rating        (not review_score)
          review_text   (not review_comment)
          seller_category  (not seller_city — sellers table has category, not city)

        Intentional data quality issues for Module 05 practice:
          - NULL review fields     (~25% — orders without a review, mirrors LEFT JOIN)
          - NULL customer_email    (~6%  — missing contact data)
          - NULL customer_city     (~9%  — city pool includes None)
          - Negative total_amount  (~2%  — data entry error)
          - rating out of 1–5      (~1%  — bad import)
          - total_amount >> product_price  (~3%  — possible duplicate charge)
        """
        import random
        import datetime
        import numpy as np

        random.seed(42)
        np.random.seed(42)

        # ── Sample data pools ─────────────────────────────────────
        first_names      = ["Amara", "Luca", "Sofia", "James", "Yuki", "Fatima",
                            "Carlos", "Mei", "Omar", "Elena", "Kwame", "Priya"]
        last_names       = ["Osei", "Rossi", "Müller", "Thompson", "Tanaka",
                            "Al-Hassan", "Rivera", "Chen", "Khalid", "Petrova",
                            "Asante", "Sharma"]
        segments         = ["VIP", "Standard", "New", "At Risk", "Loyal"]
        categories       = ["Electronics", "Fashion", "Home & Garden",
                            "Health & Beauty", "Sports", "Books & Media"]
        product_names    = {
            "Electronics":    ["Wireless Headphones", "Smart Watch", "Bluetooth Speaker", "USB-C Hub"],
            "Fashion":        ["Leather Jacket", "Running Shoes", "Silk Scarf", "Canvas Tote"],
            "Home & Garden":  ["Air Purifier", "Ceramic Planter", "LED Desk Lamp", "Coffee Maker"],
            "Health & Beauty":["Vitamin D Drops", "Moisturiser SPF50", "Yoga Mat", "Foam Roller"],
            "Sports":         ["Resistance Bands", "Water Bottle", "Cycling Gloves", "Jump Rope"],
            "Books & Media":  ["SQL for Analysts", "Python Crash Course", "Data Viz Handbook", "Noise-Cancel Earbuds"],
        }
        # owner_name  — sellers.owner_name in the actual DB
        owner_names      = ["NovaTech GmbH", "SunMarket Ltd", "PeakGoods Inc",
                            "BlueStar Trading", "OceanDirect", "UrbanSupply Co",
                            "EastWest Exports", "Horizon Retail"]
        # seller_category — sellers.category in the actual DB (no seller_city column)
        seller_cats      = ["Electronics", "Fashion", "Home & Garden",
                            "Health & Beauty", "Sports", "Books & Media"]
        seller_countries = ["Germany", "Singapore", "Brazil", "Canada",
                            "UAE", "Nigeria", "Netherlands", "South Korea"]
        cust_cities      = ["London", "Paris", "New York", "Sydney", "Tokyo",
                            "Lagos", "Toronto", "Dubai", "Berlin", "Mumbai", None]
        cust_countries   = ["UK", "France", "USA", "Australia", "Japan",
                            "Nigeria", "Canada", "UAE", "Germany", "India"]
        statuses         = ["delivered", "delivered", "delivered",
                            "delivered", "shipped", "processing",
                            "returned", "cancelled"]
        review_texts     = [
            "Exactly as described, fast delivery.",
            "Great quality, would buy again.",
            "Packaging was damaged but product fine.",
            "Seller was very responsive.",
            "Took longer than expected.",
            "Perfect gift, recipient loved it.",
            "Not as pictured — returning.",
            "Good value for money.",
            None,
        ]

        today = datetime.date.today()
        rows  = []

        for i in range(1, n + 1):
            # Seller
            s_idx          = random.randint(0, len(owner_names) - 1)
            seller_id      = s_idx + 1
            owner_name     = owner_names[s_idx]
            seller_cat     = seller_cats[s_idx % len(seller_cats)]
            seller_country = seller_countries[s_idx]

            # Product
            cat           = random.choice(categories)
            prod_name     = random.choice(product_names[cat])
            product_id    = random.randint(1000, 9999)
            product_price = round(random.uniform(10, 800), 2)

            # Customer
            c_idx        = random.randint(0, len(first_names) - 1)
            customer_id  = random.randint(100, 999)
            first_name   = first_names[c_idx]
            last_name    = last_names[random.randint(0, len(last_names) - 1)]
            cust_email   = f"{first_name.lower()}{customer_id}@mail.com" \
                           if random.random() > 0.06 else None
            cust_city    = random.choice(cust_cities)
            cust_country = random.choice(cust_countries)
            cust_segment = random.choice(segments)

            # Order — column is total_amount in the actual DB
            order_date    = today - datetime.timedelta(days=random.randint(0, 365))
            total_amount  = round(product_price * random.uniform(0.9, 1.1), 2)
            if random.random() < 0.02:     # ~2% negative — data entry error
                total_amount = -abs(total_amount)
            order_status  = random.choice(statuses)

            # Review (LEFT JOIN — ~25% of orders have no review)
            has_review  = random.random() > 0.25
            review_id   = random.randint(50000, 99999) if has_review else None
            rating      = random.randint(1, 5) if has_review else None
            if rating and random.random() < 0.01:   # ~1% out-of-range
                rating = random.choice([0, 6, 7])
            review_text = random.choice(review_texts) if has_review else None

            rows.append({
                # Order  — matches o.order_id, o.order_date, o.total_amount, o.status AS order_status
                "order_id":          f"ORD-{i:07d}",
                "order_date":        order_date.isoformat(),
                "total_amount":      total_amount,
                "order_status":      order_status,
                # Customer  — matches c.customer_id, c.first_name, c.last_name, c.email AS customer_email …
                "customer_id":       customer_id,
                "first_name":        first_name,
                "last_name":         last_name,
                "customer_email":    cust_email,
                "customer_city":     cust_city,
                "customer_country":  cust_country,
                "customer_segment":  cust_segment,
                # Product  — matches p.product_id, p.product_name, p.category AS product_category, p.price AS product_price
                "product_id":        product_id,
                "product_name":      prod_name,
                "product_category":  cat,
                "product_price":     product_price,
                # Seller  — matches s.seller_id, s.owner_name, s.country AS seller_country, s.category AS seller_category
                "seller_id":         seller_id,
                "owner_name":        owner_name,
                "seller_country":    seller_country,
                "seller_category":   seller_cat,
                # Review  — matches r.review_id, r.rating, r.review_text
                "review_id":         review_id,
                "rating":            rating,
                "review_text":       review_text,
                # Pipeline metadata
                "source_schema":     "ecommerce",
                "extracted_date":    today.isoformat(),
            })

        df = pd.DataFrame(rows)

        # ~3% where total_amount is 10× product_price (possible duplicate charge)
        bump_idx = np.random.choice(n, size=max(1, int(n * 0.03)), replace=False)
        for idx in bump_idx:
            df.loc[idx, "total_amount"] = round(df.loc[idx, "product_price"] * random.uniform(11, 15), 2)

        return df

    # ── Dunder methods ────────────────────────────────────────────

    def __str__(self) -> str:
        return f"DataExtractor(schema={self.industry!r}, status={self._status!r})"

    def __repr__(self) -> str:
        return f"DataExtractor(schema={self.industry!r})"
