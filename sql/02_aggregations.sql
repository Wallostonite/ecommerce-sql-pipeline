-- ============================================================
-- 02_aggregations.sql  —  Business-level aggregations
-- Schema: ecommerce
-- ============================================================

-- Revenue by seller
SELECT
    s.seller_id,
    s.seller_name,
    SUM(o.order_value)          AS total_revenue,
    COUNT(o.order_id)           AS total_orders,
    ROUND(AVG(o.order_value), 2) AS avg_order_value
FROM ecommerce.orders   o
JOIN ecommerce.products p ON o.product_id  = p.product_id
JOIN ecommerce.sellers  s ON p.seller_id   = s.seller_id
GROUP BY s.seller_id, s.seller_name
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
FROM ecommerce.orders   o
JOIN ecommerce.products p ON o.product_id = p.product_id
GROUP BY p.category
ORDER BY return_rate_pct DESC;

-- Average review score per seller
SELECT
    s.seller_id,
    s.seller_name,
    ROUND(AVG(r.review_score), 2) AS avg_review_score,
    COUNT(r.review_id)            AS total_reviews
FROM ecommerce.sellers  s
JOIN ecommerce.products p ON p.seller_id   = s.seller_id
JOIN ecommerce.orders   o ON o.product_id  = p.product_id
JOIN ecommerce.reviews  r ON r.order_id    = o.order_id
GROUP BY s.seller_id, s.seller_name
ORDER BY avg_review_score DESC;
