# P03 ⭐⭐⭐ — Ecommerce SQL
## The Darko Method 2026 | Student Project

---

## Your Brief

**Company:** ShopStream Global
**Your role:** Data Analyst

ShopStream's Chief Data Officer needs a comprehensive raw data extract combining
orders, customer profiles, product details, seller information, and review scores
into one flat file for revenue forecasting and customer segmentation.

Your job is to connect to the Supabase database, write SQL queries against the
`ecommerce` schema, and produce `raw-data.csv`.

**Schema:** `ecommerce`
**Key tables:** `orders`, `customers`, `products`, `sellers`, `reviews`

**Deliverable:** `data/raw-data.csv` — a fully joined five-table extract,
ready for Module 05 ETL.

---

## Success Criteria

- [ ] All five tables queried and understood individually
- [ ] Aggregation queries show: revenue by seller, return rates by product category,
  average review score per seller
- [ ] A five-table join produces one row per order with customer, product, seller,
  and review data
- [ ] At least two advanced queries: one CTE, one window function ranking customers
  by total spend
- [ ] `python run.py` saves `raw-data.csv`
- [ ] Project pushed to GitHub

---

> Build your project from scratch using the teaching project as your reference.
