-- ============================================================
-- 01_explore.sql  —  Individual table exploration
-- Schema: {industry}   (replaced at runtime by SQLQueryRunner)
-- ============================================================

-- Orders
SELECT * FROM {industry}.orders LIMIT 10;
SELECT COUNT(*) AS total_orders FROM {industry}.orders;

-- Customers
SELECT * FROM {industry}.customers LIMIT 10;
SELECT COUNT(*) AS total_customers FROM {industry}.customers;

-- Products
SELECT * FROM {industry}.products LIMIT 10;
SELECT COUNT(*) AS total_products FROM {industry}.products;

-- Sellers
SELECT * FROM {industry}.sellers LIMIT 10;
SELECT COUNT(*) AS total_sellers FROM {industry}.sellers;

-- Reviews
SELECT * FROM {industry}.reviews LIMIT 10;
SELECT COUNT(*) AS total_reviews FROM {industry}.reviews;
