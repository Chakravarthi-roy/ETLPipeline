-- Business-insight queries for the Office Products review dataset
-- Run with: sqlite3 data/office_products.db < sql/queries.sql

-- 1. Top products by B2B signal volume and satisfaction
SELECT
    p.product_title,
    p.store,
    COUNT(*) AS b2b_review_count,
    ROUND(AVG(r.rating), 2) AS avg_rating,
    SUM(CASE WHEN r.is_positive THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS pct_positive
FROM fact_reviews r
JOIN dim_products p ON r.parent_asin = p.parent_asin
WHERE r.mentions_b2b_context = 1
GROUP BY p.parent_asin
HAVING COUNT(*) >= 20
ORDER BY b2b_review_count DESC
LIMIT 20;

-- 2. Verified purchase rate and rating: business buyers vs. general
SELECT
    verified_purchase,
    COUNT(*) AS review_count,
    ROUND(AVG(rating), 2) AS avg_rating,
    ROUND(AVG(helpful_vote), 2) AS avg_helpful_votes
FROM fact_reviews
GROUP BY verified_purchase;

-- 3. Repeat reviewers, proxy for repeat/bulk business buyers
SELECT
    user_id,
    COUNT(DISTINCT parent_asin) AS distinct_products_reviewed,
    ROUND(AVG(rating), 2) AS avg_rating_given
FROM fact_reviews
GROUP BY user_id
HAVING COUNT(DISTINCT parent_asin) >= 3
ORDER BY distinct_products_reviewed DESC
LIMIT 20;

-- 4. Yearly trend: review volume and average rating
SELECT
    review_year,
    COUNT(*) AS review_count,
    ROUND(AVG(rating), 2) AS avg_rating,
    SUM(mentions_b2b_context) AS b2b_context_reviews
FROM fact_reviews
GROUP BY review_year
ORDER BY review_year;

-- 5. Price tier vs. satisfaction
SELECT
    CASE
        WHEN p.price IS NULL THEN 'Unknown'
        WHEN p.price < 10 THEN 'Under $10'
        WHEN p.price < 30 THEN '$10-$30'
        WHEN p.price < 75 THEN '$30-$75'
        ELSE '$75+'
    END AS price_tier,
    COUNT(*) AS review_count,
    ROUND(AVG(r.rating), 2) AS avg_rating
FROM fact_reviews r
JOIN dim_products p ON r.parent_asin = p.parent_asin
GROUP BY price_tier
ORDER BY MIN(p.price);

-- 6. High volume but low satisfaction products, candidates for quality investigation
SELECT
    p.product_title,
    p.store,
    COUNT(*) AS review_count,
    ROUND(AVG(r.rating), 2) AS avg_rating
FROM fact_reviews r
JOIN dim_products p ON r.parent_asin = p.parent_asin
GROUP BY p.parent_asin
HAVING COUNT(*) >= 50 AND AVG(r.rating) < 3.0
ORDER BY review_count DESC
LIMIT 20;