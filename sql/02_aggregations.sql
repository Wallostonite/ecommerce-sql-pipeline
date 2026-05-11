-- ============================================================
-- 02_aggregations.sql  —  Business-level aggregations
-- Schema: {industry}   (replaced at runtime by SQLQueryRunner)
-- ============================================================

-- Revenue by seller
SELECT
    s.seller_id,
    s.owner_name,
    SUM(o.total_amount)           AS total_revenue,
    COUNT(o.order_id)             AS total_orders,
    ROUND(AVG(o.total_amount), 2) AS avg_order_value
FROM {industry}.orders   o
JOIN {industry}.products p ON o.product_id  = p.product_id
JOIN {industry}.sellers  s ON p.seller_id   = s.seller_id
GROUP BY s.seller_id, s.owner_name
ORDER BY total_revenue DESC;

-- Return rate by product category
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
ORDER BY return_rate_pct DESC;

-- Average rating per seller
SELECT
    s.seller_id,
    s.owner_name,
    ROUND(AVG(r.rating), 2) AS avg_rating,
    COUNT(r.review_id)      AS total_reviews
FROM {industry}.sellers  s
JOIN {industry}.products p ON p.seller_id   = s.seller_id
JOIN {industry}.orders   o ON o.product_id  = p.product_id
JOIN {industry}.reviews  r ON r.order_id    = o.order_id
GROUP BY s.seller_id, s.owner_name
ORDER BY avg_rating DESC;
