# 📓 Telecom Site Uptime Analysis — Guide

## What This Project Does
Analyses downtime patterns across a 100-site telecom portfolio to answer:
- Which sites have the worst availability?
- What causes most downtime (Power, Transmission, Vandalism, etc.)?
- Which regions have the highest MTTR?
- Which sites are chronic underperformers needing urgent intervention?

---

## Scripts & Order of Execution
```
1. python scripts/generate_data.py      # Creates downtime event dataset
2. python scripts/uptime_analysis.py    # Availability %, root cause Pareto
3. python scripts/site_risk_scorer.py   # Composite risk score per site
4. python scripts/mttr_benchmarking.py  # MTTR/MTBF by region & cause
```

---

## Key Metrics Explained

### Site Availability %
```
Availability = (Total minutes in month - Downtime minutes) / Total minutes × 100
SLA Target: 99.5% per month
```
A site with 99.5% availability can have at most **3.65 hours of downtime** per 30-day month.

### MTTR (Mean Time To Resolve)
Average hours from alarm start to alarm clearance. Lower is better.

### MTBF (Mean Time Between Failures)
Average days between downtime events at a site. Higher is better — indicates more reliable infrastructure.

### Risk Score
Composite 0–100 score based on total downtime, event frequency, MTTR, severity, and tenant count.
- **Critical (75–100):** Immediate intervention required
- **High (55–74):** Schedule preventive maintenance
- **Medium (30–54):** Monitor closely
- **Low (0–29):** Performing well

---

## Sample Findings (Synthetic Data)
- Power Failure accounts for ~43% of all downtime hours
- Vandalism events take 4× longer to resolve than power failures
- Region with highest MTTR consistently has oldest infrastructure (4G sites perform better)
- Top 12% of sites account for ~48% of total portfolio downtime

---

## Recommendations
1. Prioritise power backup upgrades at Critical-tier sites
2. Install anti-vandal barriers at high-theft regions
3. Set MTTR KPI targets per root cause category for field engineers
4. Review preventive maintenance schedules for sites with MTBF < 7 days
