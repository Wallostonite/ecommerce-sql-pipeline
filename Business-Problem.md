# Business Problem Documentation: ShopStream Global Revenue Forecasting & Customer Segmentation Data Foundation

> **Document Owner:** Data Analytics Team
> **Sponsor:** Chief Data Officer, ShopStream Global
> **Status:** Draft → Ready for Execution
> **Target Audience:** Data Analyst, Data Engineering, Finance, Marketing/CRM, Product Leadership

---

## 1. Executive Summary

ShopStream Global is experiencing rapid marketplace growth, but strategic decision-making is constrained by fragmented, siloed data. The Chief Data Officer has identified an urgent need for a unified, order-level dataset to power accurate revenue forecasting and actionable customer segmentation. This document defines the business problem, outlines the data foundation initiative, and establishes success criteria for delivering a production-ready extract (`raw-data.csv`) that will serve as the single source of truth for downstream ETL, predictive modeling, and commercial strategy.

---

## 2. Business Context & Background

- **Marketplace Model:** ShopStream connects global third-party sellers with consumers across multiple regions and product categories.
- **Current State:** Transactional, customer, product, seller, and review data reside in separate Supabase tables within the `ecommerce` schema. Reporting relies on manual extracts or stale aggregates.
- **Pain Points:**
  - Forecasting accuracy suffers from delayed, incomplete, or inconsistently joined data.
  - Marketing lacks granular customer behavior signals to drive retention and lifecycle campaigns.
  - Seller performance and product health are evaluated in isolation, missing cross-functional correlations (e.g., review sentiment → return rates → LTV).
- **Trigger:** CDO mandate to establish a reproducible, automated data pipeline that delivers a fully joined, validation-ready flat file for Module 05 ETL.

---

## 3. Problem Statement

ShopStream Global lacks a centralized, order-granular dataset that unifies transactional history, customer profiles, product attributes, seller metadata, and post-purchase feedback. This fragmentation creates data latency, increases analytical overhead, and limits the organization's ability to:

1. Forecast revenue with statistical rigor
2. Segment customers by behavioral and value-based attributes
3. Optimize seller onboarding, category strategy, and customer experience initiatives

Without a reliable data foundation, predictive models, marketing automation, and financial planning operate on incomplete signals, leading to suboptimal resource allocation and missed growth opportunities.

---

## 4. Business Objectives

| Objective                                   | Business Impact                                                                |
| ------------------------------------------- | ------------------------------------------------------------------------------ |
| Deliver a unified, order-level dataset      | Enable accurate, granular revenue forecasting & reduce planning cycle time     |
| Standardize join logic & data quality rules | Eliminate manual reconciliation & reduce reporting errors by ≥30%             |
| Provide baseline customer & seller metrics  | Empower Marketing & Finance with actionable segmentation & performance KPIs    |
| Automate extraction via `run.py`          | Ensure reproducibility, auditability, and seamless handoff to Data Engineering |

---

## 5. Key Business Questions to Answer

- Which customer segments drive the highest revenue, and how do purchasing patterns differ by region or category?
- How do product review scores correlate with return rates and long-term customer lifetime value (LTV)?
- Which sellers consistently outperform, and what attributes (category, region, pricing, verification) drive success?
- What historical order trends can reliably inform next-quarter revenue forecasts?
- How can we identify at-risk vs. high-potential customers for targeted retention or upsell campaigns?

---

## 6. Scope & Boundaries

| ✅ In Scope                                                                                                                  | ❌ Out of Scope                                                     |
| ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| Extraction & joining of `orders`, `customers`, `products`, `sellers`, `reviews` from Supabase `ecommerce` schema | Advanced feature engineering, model training, or dashboard creation |
| Output:`data/raw-data.csv` (1 row/order, UTF-8, snake_case headers)                                                        | Real-time streaming, CDC, or data warehouse migration               |
| Automated execution via `python run.py`                                                                                    | PII masking, GDPR compliance workflows (handled downstream in ETL)  |
| Baseline aggregations & validation queries                                                                                   | Cross-system data reconciliation or historical backfilling          |

---

## 7. Stakeholders & Responsibilities

| Role                           | Responsibility                                                             |
| ------------------------------ | -------------------------------------------------------------------------- |
| **Chief Data Officer**   | Strategic sponsor, prioritization, business alignment                      |
| **Data Analyst**         | SQL development, query validation, pipeline automation, QA                 |
| **Data Engineering**     | Consumes `raw-data.csv` for Module 05 ETL, schema validation, scheduling |
| **Finance / RevOps**     | Defines forecasting requirements, validates revenue metrics                |
| **Marketing / CRM**      | Defines segmentation criteria, consumes customer behavior features         |
| **Product / Seller Ops** | Reviews category/seller performance insights, provides feedback loops      |

---

## 8. Success Metrics & KPIs

| Metric                       | Target                                                                   | Measurement Method                            |
| ---------------------------- | ------------------------------------------------------------------------ | --------------------------------------------- |
| **Data Completeness**  | 100% of historical orders represented                                    | Row count match vs.`orders` table           |
| **Join Accuracy**      | 0% fan-out duplication                                                   | `COUNT(*)` after join == source order count |
| **Critical Null Rate** | ≤2% on `customer_id`, `product_id`, `seller_id`, `total_amount` | Automated validation script                   |
| **Pipeline Runtime**   | <5 minutes for current volume                                            | `time python run.py`                        |
| **ETL Readiness**      | Passes schema & dtype validation                                         | Module 05 ingestion test                      |
| **Business Adoption**  | Forecasting model MAPE <15% (future module)                              | Finance validation post-ETL                   |

---

## 9. Data Requirements & Deliverables

- **Format:** `CSV`, UTF-8 encoded, comma-delimited, header row included
- **Granularity:** One row per `order_id`
- **Key Joins:**
  - `orders` → `customers` (1:1)
  - `orders` → `products` (1:1)
  - `orders` → `sellers` (1:1)
  - `orders` → `reviews` (N:1 → aggregated via CTE to preserve 1 row/order)
- **Advanced Logic Included:**
  - CTE for review aggregation & pre-filtering
  - Window function for customer spend ranking (documented for downstream segmentation)
- **Deliverables:**
  - `data/raw-data.csv`
  - `queries/main_extract.sql`
  - `run.py` (automated extraction script)
  - Validation queries (revenue by seller, return rate by category, avg review by seller)

---

## 10. Assumptions & Constraints

- Supabase read access is stable, performant, and scoped to the `ecommerce` schema.
- Schema structure remains static during extraction; any changes require version control & re-validation.
- Historical data quality is sufficient for baseline analysis; missing reviews are treated as `NULL` (not imputed).
- Privacy & compliance (PII handling, consent flags) will be addressed in the Module 05 ETL layer.
- Dataset volume fits within standard pandas memory constraints for local execution.

---

## 11. Next Steps & Timeline

| Phase                   | Action                                                           | Owner              | ETA     |
| ----------------------- | ---------------------------------------------------------------- | ------------------ | ------- |
| 1. Query Development    | Write & validate 5-table join + aggregations                     | Data Analyst       | Day 1-2 |
| 2. Automation & QA      | Build `run.py`, run validation checks, fix duplicates/nulls    | Data Analyst       | Day 3   |
| 3. Code Review & GitHub | Push to repo, open PR, attach QA report                          | Data Analyst       | Day 4   |
| 4. ETL Handoff          | Deliver `raw-data.csv`, align with Data Eng on Module 05 specs | Data Analyst + Eng | Day 5   |
| 5. Business Validation  | Finance & Marketing confirm metric alignment                     | CDO + Stakeholders | Day 6-7 |

---

## 12. Approval & Sign-Off

| Role                  | Name | Signature | Date |
| --------------------- | ---- | --------- | ---- |
| Chief Data Officer    |      |           |      |
| Data Analytics Lead   |      |           |      |
| Data Engineering Lead |      |           |      |
| Data Analyst (Author) |      |           |      |

---

📎 **Attachments / References:**

- `run.py` execution guide
- `queries/main_extract.sql`
- Validation checklist & QA script
- Module 05 ETL Specification (future)

> 💡 **Note for Team Members:** This document should live in your project wiki or repository root. Update the `[Status]`, `ETA`, and `Sign-Off` fields as the project progresses. All downstream work (forecasting, segmentation, seller scoring) depends on the integrity of this extract. Treat `raw-data.csv` as a contract between Analytics and Engineering.
>
