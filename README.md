# 🛒 Ecommerce SQL Data Pipeline

> A production-style SQL extraction & automation pipeline that consolidates fragmented ecommerce data into a unified, analysis-ready dataset. Built to demonstrate advanced querying, relational data modeling, and Python automation.

## 📖 Overview
This project simulates a real-world data analyst/engineer workflow: connecting to a live PostgreSQL database, writing optimized SQL to join and aggregate data across five core tables, and automating the export process via Python. The final output (`raw-data.csv`) serves as the foundational dataset for downstream revenue forecasting, customer segmentation, and BI reporting.

## 🛠 Tech Stack
- **Database:** PostgreSQL (hosted on Supabase)
- **Query Language:** Advanced SQL (CTEs, Window Functions, Multi-table Joins, Aggregations)
- **Automation:** Python (`psycopg2`, `pandas`, `csv`)
- **Environment:** `.env` for secure credential management
- **Version Control:** Git & GitHub

## 📊 Database Schema
All queries target the `ecommerce` schema:
| Table        | Purpose                                  |
|--------------|------------------------------------------|
| `orders`     | Transaction records, dates, status       |
| `customers`  | Demographics, account details, location  |
| `products`   | SKUs, categories, pricing, inventory     |
| `sellers`    | Vendor profiles, onboarding, regions     |
| `reviews`    | Customer feedback, ratings, timestamps   |

## ✨ Key Features & SQL Techniques
- **Five-Table Consolidation:** One row per order, enriched with customer, product, seller, and review context
- **Business Metrics Aggregation:**
  - Revenue by seller
  - Return rates by product category
  - Average review scores per seller
- **Advanced Query Patterns:**
  - ✅ Common Table Expressions (CTEs) for modular, readable logic
  - ✅ Window functions (`RANK()`, `SUM() OVER()`) to rank customers by lifetime spend
- **Automated Export:** Python script executes queries, manages connections, and writes a clean `raw-data.csv`

## 🚀 How to Run Locally
1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ecommerce-sql-pipeline.git
   cd ecommerce-sql-pipeline