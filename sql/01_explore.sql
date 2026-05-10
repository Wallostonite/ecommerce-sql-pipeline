-- ============================================================
-- 01_explore.sql  —  Individual table exploration
-- Schema: ecommerce
-- ============================================================

-- Orders
SELECT * FROM ecommerce.orders LIMIT 10;
SELECT COUNT(*) AS total_orders FROM ecommerce.orders;

-- Customers
SELECT * FROM ecommerce.customers LIMIT 10;
SELECT COUNT(*) AS total_customers FROM ecommerce.customers;

-- Products
SELECT * FROM ecommerce.products LIMIT 10;
SELECT COUNT(*) AS total_products FROM ecommerce.products;

-- Sellers
SELECT * FROM ecommerce.sellers LIMIT 10;
SELECT COUNT(*) AS total_sellers FROM ecommerce.sellers;

-- Reviews
SELECT * FROM ecommerce.reviews LIMIT 10;
SELECT COUNT(*) AS total_reviews FROM ecommerce.reviews;
