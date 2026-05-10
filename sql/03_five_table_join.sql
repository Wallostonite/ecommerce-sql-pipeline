-- ============================================================
-- 03_five_table_join.sql  —  One row per order, all five tables
-- Schema: ecommerce
-- ============================================================

SELECT
    -- Order
    o.order_id,
    o.order_date,
    o.order_value,
    o.status            AS order_status,

    -- Customer
    c.customer_id,
    c.customer_name,
    c.email             AS customer_email,
    c.city              AS customer_city,
    c.country           AS customer_country,
    c.segment           AS customer_segment,

    -- Product
    p.product_id,
    p.product_name,
    p.category          AS product_category,
    p.price             AS product_price,

    -- Seller
    s.seller_id,
    s.seller_name,
    s.city              AS seller_city,
    s.country           AS seller_country,

    -- Review
    r.review_id,
    r.review_score,
    r.review_comment

FROM ecommerce.orders   o
JOIN ecommerce.customers c ON o.customer_id = c.customer_id
JOIN ecommerce.products  p ON o.product_id  = p.product_id
JOIN ecommerce.sellers   s ON p.seller_id   = s.seller_id
LEFT JOIN ecommerce.reviews r ON r.order_id = o.order_id
ORDER BY o.order_date DESC;
