-- 01_clean.sql
-- Builds clean tables from a raw Upworthy package CSV.
-- Expects a view named `raw` (created in src/load.py) pointing at one CSV.

-- 1. Raw packages, with the possibly-broken-randomization window flagged.
--    The archive team discourages using tests from 2013-06-25 to 2014-01-10.
CREATE OR REPLACE TABLE packages AS
SELECT
    clickability_test_id                       AS test_id,
    created_at,
    test_week,
    headline,
    eyecatcher_id                              AS image_id,
    impressions,
    clicks,
    significance                               AS upworthy_significance,
    first_place,
    winner,
    created_at BETWEEN TIMESTAMP '2013-06-25' AND TIMESTAMP '2014-01-11'
                                               AS bad_randomization
FROM raw
WHERE impressions > 0
  AND headline IS NOT NULL;

-- 2. Arms: viewers only saw the headline and image. Lede, excerpt and share
--    text were not part of the test, so packages with the same headline and
--    image inside a test are the same stimulus. Merge them into one arm.
CREATE OR REPLACE TABLE arms AS
SELECT
    test_id,
    image_id,
    headline,
    MIN(created_at)                 AS created_at,
    ANY_VALUE(bad_randomization)    AS bad_randomization,
    SUM(impressions)                AS impressions,
    SUM(clicks)                     AS clicks,
    SUM(clicks) / SUM(impressions)  AS ctr,
    BOOL_OR(winner)                 AS winner,
    BOOL_OR(first_place)            AS first_place,
    MAX(upworthy_significance)      AS upworthy_significance,
    COUNT(*)                        AS n_packages_merged
FROM packages
GROUP BY test_id, image_id, headline;

-- 3. Headline-only comparisons: within one test, hold the image fixed and
--    compare headlines. A "stratum" is (test, image) with 2+ distinct headlines.
CREATE OR REPLACE TABLE headline_strata AS
SELECT a.*
FROM arms a
JOIN (
    SELECT test_id, image_id
    FROM arms
    WHERE NOT bad_randomization
    GROUP BY test_id, image_id
    HAVING COUNT(DISTINCT headline) >= 2
) s USING (test_id, image_id)
WHERE NOT a.bad_randomization;
