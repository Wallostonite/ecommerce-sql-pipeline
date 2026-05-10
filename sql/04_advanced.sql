-- ============================================================
-- 04_advanced.sql  —  CTE + Window function
-- Schema: ecommerce
-- ============================================================

-- ── CTE: total revenue per seller with order count ───────────
WITH seller_revenue AS (
    SELECT
        s.seller_id,
        s.seller_name,
        SUM(o.order_value)  AS total_revenue,
        COUNT(o.order_id)   AS order_count
    FROM ecommerce.sellers  s
    JOIN ecommerce.products p ON p.seller_id  = s.seller_id
    JOIN ecommerce.orders   o ON o.product_id = p.product_id
    GROUP BY s.seller_id, s.seller_name
)
SELECT
    seller_id,
    seller_name,
    total_revenue,
    order_count,
    ROUND(total_revenue / NULLIF(order_count, 0), 2) AS revenue_per_order
FROM seller_revenue
ORDER BY total_revenue DESC;


-- ── Window function: rank customers by total spend ───────────
SELECT
    c.customer_id,
    c.customer_name,
    c.segment,
    SUM(o.order_value)                                         AS total_spend,
    RANK() OVER (ORDER BY SUM(o.order_value) DESC)             AS spend_rank,
    RANK() OVER (
        PARTITION BY c.segment
        ORDER BY SUM(o.order_value) DESC
    )                                                          AS spend_rank_within_segment
FROM ecommerce.customers c
JOIN ecommerce.orders    o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.customer_name, c.segment
ORDER BY spend_rank;
