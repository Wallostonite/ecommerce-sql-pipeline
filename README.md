# ShopStream Global — Ecommerce Raw Data Extract

**Domain:** Retail & Ecommerce  
**Stack:** Python · PostgreSQL · Supabase · pandas  
**Deliverable:** `data/raw-data.csv` — flat five-table extract for revenue forecasting and customer segmentation

---

## Business Problem

ShopStream Global is a multi-vendor ecommerce marketplace operating across 12 countries. The business runs on a transactional PostgreSQL database that captures every order, customer interaction, seller listing, and post-purchase review in near real-time.

The Chief Data Officer needs a **single, analysis-ready flat file** that combines all five core operational tables into one extract. The downstream use cases are:

- **Revenue forecasting** — finance needs seller-level and category-level revenue trends
- **Customer segmentation** — marketing needs spend behaviour and demographics in one row
- **Seller performance scoring** — operations needs review scores alongside fulfilment data
- **Return rate analysis** — product team needs return rates broken down by category

Currently, analysts pull these tables separately and join them manually in spreadsheets — a slow, error-prone process. This project replaces that workflow with a single repeatable script.

---

## Database Schema

**Host:** Supabase (PostgreSQL)  
**Schema:** `ecommerce`

```
orders
├── order_id        PK
├── customer_id     FK → customers
├── product_id      FK → products
├── order_date
├── order_value
└── status

customers
├── customer_id     PK
├── customer_name
├── email
├── city
├── country
└── segment

products
├── product_id      PK
├── seller_id       FK → sellers
├── product_name
├── category
└── price

sellers
├── seller_id       PK
├── seller_name
├── city
└── country

reviews
├── review_id       PK
├── order_id        FK → orders
├── review_score
└── review_comment
```

---

## Project Structure

```
P03-ecommerce-sql/
├── data/
│   └── raw-data.csv          # output — one row per order, all five tables joined
├── queries/
│   ├── 01_explore.sql        # row counts and previews for each table
│   ├── 02_aggregations.sql   # revenue by seller, return rates, avg review per seller
│   ├── 03_five_table_join.sql # production join query
│   └── 04_advanced.sql       # CTE + window function (customer spend ranking)
├── .env.example              # credential template
├── requirements.txt
└── run.py                    # entry point — connects, queries, saves CSV
```

---

## Queries

### Exploration (`01_explore.sql`)
Row counts and sample rows for all five tables to verify connectivity and understand data shape before writing joins.

### Aggregations (`02_aggregations.sql`)
Three business-level aggregations:
- **Revenue by seller** — total revenue, order count, average order value
- **Return rate by product category** — percentage of orders with `status = 'returned'`
- **Average review score per seller** — reputation metric across all their listed products

### Five-Table Join (`03_five_table_join.sql`)
The core extract query. Produces one row per order with fields from all five tables. Reviews are left-joined so orders without a review are still included.

### Advanced Queries (`04_advanced.sql`)
- **CTE** — seller revenue summary with revenue-per-order calculation
- **Window function** — customers ranked by total spend globally and within their segment using `RANK() OVER (...)`

---

## Setup

**1. Clone and install dependencies**

```bash
git clone <your-repo-url>
cd P03-ecommerce-sql
pip install -r requirements.txt
```

**2. Configure credentials**

```bash
cp .env.example .env
```

Open `.env` and fill in your Supabase connection details:

```
SUPABASE_HOST=db.<your-project-ref>.supabase.co
SUPABASE_PORT=5432
SUPABASE_DB=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=<your-password>
SUPABASE_SCHEMA=ecommerce
```

**3. Run the extract**

```bash
python run.py
```

Output is saved to `data/raw-data.csv`.

---

## Output

`raw-data.csv` contains one row per order with 21 columns:

| Column | Source Table | Description |
|---|---|---|
| `order_id` | orders | Unique order identifier |
| `order_date` | orders | Date the order was placed |
| `order_value` | orders | Total order value in USD |
| `order_status` | orders | Current fulfilment status |
| `customer_id` | customers | Unique customer identifier |
| `customer_name` | customers | Full name |
| `customer_email` | customers | Contact email |
| `customer_city` | customers | City of residence |
| `customer_country` | customers | Country of residence |
| `customer_segment` | customers | Marketing segment (e.g. VIP, Standard) |
| `product_id` | products | Unique product identifier |
| `product_name` | products | Product display name |
| `product_category` | products | Top-level category |
| `product_price` | products | Listed unit price |
| `seller_id` | sellers | Unique seller identifier |
| `seller_name` | sellers | Seller / merchant name |
| `seller_city` | sellers | Seller location city |
| `seller_country` | sellers | Seller location country |
| `review_id` | reviews | Review identifier (null if no review) |
| `review_score` | reviews | 1–5 star rating |
| `review_comment` | reviews | Free-text review body |

---

## Key Design Decisions

**LEFT JOIN on reviews** — not every order receives a review. Using an inner join would silently drop unreviewed orders from the extract and undercount revenue. The left join preserves all orders and leaves review fields null where absent.

**Schema-qualified table names** — all queries use `ecommerce.<table>` rather than relying on a `search_path` setting. This makes the queries portable across database connections and avoids ambiguity when running against a Supabase instance that also has a `public` schema.

**pandas for CSV export** — `pd.read_sql_query` handles type inference and null representation consistently across platforms, avoiding edge cases with the `csv` module when review comments contain commas or newlines.

---

## Next Steps

This extract feeds directly into the Module 05 ETL pipeline where it will be:

1. Cleaned — nulls handled, data types enforced
2. Enriched — exchange rates applied to normalise `order_value` to a single currency
3. Loaded — written to the analytics warehouse for dashboarding and ML feature engineering
