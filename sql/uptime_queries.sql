-- ═══════════════════════════════════════════════════════
-- Telecom Site Uptime — SQL Query Collection
-- Compatible with PostgreSQL 13+
-- ═══════════════════════════════════════════════════════

-- 1. Monthly availability per site with SLA breach flag
WITH monthly_downtime AS (
    SELECT
        site_id,
        DATE_TRUNC('month', start_time)                              AS month,
        SUM(duration_hrs * 60)                                       AS downtime_mins
    FROM downtime_events
    WHERE severity IN ('Critical', 'Major')
    GROUP BY site_id, DATE_TRUNC('month', start_time)
)
SELECT
    m.site_id, s.region, m.month,
    ROUND(m.downtime_mins / 60, 2)                                   AS downtime_hrs,
    ROUND((43800 - m.downtime_mins) / 43800 * 100, 3)               AS availability_pct,
    CASE WHEN (43800 - m.downtime_mins) / 43800 * 100 < 99.5
         THEN 'SLA BREACH' ELSE 'OK' END                            AS sla_status,
    LAG(ROUND((43800 - m.downtime_mins) / 43800 * 100, 3))
        OVER (PARTITION BY m.site_id ORDER BY m.month)              AS prev_month_pct
FROM monthly_downtime m
JOIN site_inventory s USING (site_id)
ORDER BY m.site_id, m.month;

-- 2. MTTR by root cause with percentile breakdown
SELECT
    root_cause,
    COUNT(*)                                                          AS event_count,
    ROUND(AVG(duration_hrs), 2)                                      AS avg_mttr_hrs,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_hrs)::numeric, 2)
                                                                     AS median_mttr_hrs,
    ROUND(PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY duration_hrs)::numeric, 2)
                                                                     AS p90_mttr_hrs,
    ROUND(SUM(duration_hrs), 1)                                      AS total_downtime_hrs,
    ROUND(SUM(duration_hrs) / SUM(SUM(duration_hrs)) OVER () * 100, 1)
                                                                     AS share_of_total_pct
FROM downtime_events
GROUP BY root_cause
ORDER BY total_downtime_hrs DESC;

-- 3. Sites with 3+ SLA breaches in rolling 6 months
WITH site_monthly AS (
    SELECT
        site_id,
        DATE_TRUNC('month', start_time)                              AS month,
        SUM(duration_hrs * 60)                                       AS downtime_mins,
        CASE WHEN (43800 - SUM(duration_hrs * 60)) / 43800 * 100 < 99.5
             THEN 1 ELSE 0 END                                       AS sla_breach
    FROM downtime_events
    GROUP BY site_id, DATE_TRUNC('month', start_time)
),
rolling AS (
    SELECT
        site_id, month, sla_breach,
        SUM(sla_breach) OVER (
            PARTITION BY site_id
            ORDER BY month
            ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
        )                                                            AS breaches_last_6m
    FROM site_monthly
)
SELECT DISTINCT site_id, MAX(breaches_last_6m) AS max_rolling_breaches
FROM rolling
WHERE breaches_last_6m >= 3
GROUP BY site_id
ORDER BY max_rolling_breaches DESC;

-- 4. Engineer response time leaderboard
SELECT
    engineer_id,
    COUNT(*)                                                          AS jobs_attended,
    ROUND(AVG(EXTRACT(EPOCH FROM (arrival_time - dispatch_time))/60), 1)
                                                                     AS avg_response_mins,
    ROUND(MIN(EXTRACT(EPOCH FROM (arrival_time - dispatch_time))/60), 1)
                                                                     AS best_response_mins,
    SUM(CASE WHEN resolution_code = 'FIXED' THEN 1 ELSE 0 END)      AS fixed_count,
    ROUND(SUM(CASE WHEN resolution_code = 'FIXED' THEN 1 ELSE 0 END)*100.0/COUNT(*), 1)
                                                                     AS resolution_rate_pct,
    RANK() OVER (ORDER BY AVG(EXTRACT(EPOCH FROM (arrival_time - dispatch_time))/60))
                                                                     AS response_rank
FROM field_dispatch
WHERE dispatch_time IS NOT NULL AND arrival_time IS NOT NULL
GROUP BY engineer_id
HAVING COUNT(*) >= 5
ORDER BY response_rank;
