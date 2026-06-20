# 📡 Telecom Site Uptime & Downtime Root Cause Analysis

![Python](https://img.shields.io/badge/Python-3.10-blue) ![Pandas](https://img.shields.io/badge/Pandas-2.0-green) ![Domain](https://img.shields.io/badge/Domain-Telecom_NOC-orange)

## Overview
Analyses **5,000+ simulated downtime events** across 100 telecom sites over 18 months. Computes availability KPIs, performs root cause breakdown, ranks chronic underperforming sites, and generates a Pareto analysis for maintenance prioritisation.

## Business Problem
Every minute of telecom site downtime affects network coverage and SLA commitments. This project answers:
- Which sites go down most? 
- What causes the most downtime?
- Where should preventive maintenance focus?

## How to Run
```bash
pip install -r requirements.txt
python scripts/generate_data.py
python scripts/uptime_analysis.py
```

## Key Outputs
- Monthly availability % per site with SLA breach flags
- MTTR (Mean Time To Resolve) by region and root cause
- Pareto chart: top failure causes by total downtime
- Risk-ranked site list for maintenance prioritisation

## Skills Demonstrated
`Time-Series Analysis` `KPI Engineering` `Root Cause Analysis` `Pandas` `Matplotlib` `Seaborn` `Telecom Domain`

---
*Kennedy Onuorah | [LinkedIn](https://www.linkedin.com/in/kennedy-onuorah-7a3793128)*
