-- ============================================================
-- 04_advanced.sql  —  CTE + Window function
-- Schema: {industry}   (replaced at runtime by SQLQueryRunner)
-- ============================================================

-- ── CTE: total revenue per seller with order count ───────────
WITH seller_revenue AS (
    SELECT
        s.seller_id,
        s.owner_name,
        SUM(o.total_amount)  AS total_revenue,
        COUNT(o.order_id)    AS order_count
    FROM {industry}.sellers  s
    JOIN {industry}.products p ON p.seller_id  = s.seller_id
    JOIN {industry}.orders   o ON o.product_id = p.product_id
    GROUP BY s.seller_id, s.owner_name
)
SELECT
    seller_id,
    owner_name,
    total_revenue,
    order_count,
    ROUND(total_revenue / NULLIF(order_count, 0), 2) AS revenue_per_order
FROM seller_revenue
ORDER BY total_revenue DESC;


-- ── Window function: rank customers by total spend ───────────
SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    c.segment,
    SUM(o.total_amount)                                         AS total_spend,
    RANK() OVER (ORDER BY SUM(o.total_amount) DESC)             AS spend_rank,
    RANK() OVER (
        PARTITION BY c.segment
        ORDER BY SUM(o.total_amount) DESC
    )                                                          AS spend_rank_within_segment
FROM {industry}.customers c
JOIN {industry}.orders    o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.segment
ORDER BY spend_rank;
