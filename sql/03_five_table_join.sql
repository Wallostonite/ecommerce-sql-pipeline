-- ============================================================
-- 03_five_table_join.sql  —  One row per order, all five tables
-- Schema: {industry}   (replaced at runtime by SQLQueryRunner)
-- ============================================================

SELECT
    -- Order
    o.order_id,
    o.order_date,
    o.total_amount,
    o.status            AS order_status,

    -- Customer
    c.customer_id,
    c.first_name,
    c.last_name,
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
    s.owner_name,
    s.country           AS seller_country,
    s.category          AS seller_category,

    -- Review
    r.review_id,
    r.rating,
    r.review_text

FROM {industry}.orders   o
JOIN {industry}.customers c ON o.customer_id = c.customer_id
JOIN {industry}.products  p ON o.product_id  = p.product_id
JOIN {industry}.sellers   s ON p.seller_id   = s.seller_id
LEFT JOIN {industry}.reviews r ON r.order_id = o.order_id
ORDER BY o.order_date DESC;
