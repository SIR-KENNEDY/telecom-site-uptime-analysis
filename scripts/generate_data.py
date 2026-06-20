"""
generate_data.py — Generates synthetic telecom site downtime event log.
Run FIRST before uptime_analysis.py
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(99)
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW  = os.path.join(BASE, "data", "raw")
os.makedirs(RAW, exist_ok=True)

CAUSES   = ["Power Failure","Transmission Fault","Equipment Fault","Vandalism","Weather","Planned Maintenance"]
WEIGHTS  = [0.40, 0.20, 0.18, 0.08, 0.07, 0.07]
REGIONS  = ["Lagos","Abuja","Port Harcourt","Kano","Enugu","Ibadan"]
N_SITES  = 100
START    = datetime(2022, 7, 1)

sites = pd.DataFrame({
    "site_id":       [f"SITE_{str(i).zfill(3)}" for i in range(1, N_SITES+1)],
    "region":        np.random.choice(REGIONS, N_SITES),
    "technology":    np.random.choice(["2G","3G","4G","4G+"], N_SITES, p=[0.1,0.2,0.5,0.2]),
    "tenant_count":  np.random.choice([1,2,3], N_SITES, p=[0.5,0.35,0.15]),
})

events = []
for _, s in sites.iterrows():
    n = np.random.randint(30, 80)
    for _ in range(n):
        cause  = np.random.choice(CAUSES, p=WEIGHTS)
        start  = START + timedelta(hours=int(np.random.randint(0, 13140)))
        dur    = max(0.25, np.random.exponential(3.5))
        if cause == "Vandalism":           dur *= 4
        if cause == "Planned Maintenance": dur  = np.random.uniform(2, 8)
        events.append({
            "site_id": s.site_id, "region": s.region,
            "technology": s.technology, "tenant_count": s.tenant_count,
            "root_cause": cause,
            "start_time": start,
            "end_time":   start + timedelta(hours=dur),
            "duration_hrs": round(dur, 2),
            "engineer_id":  f"ENG{np.random.randint(10, 50)}",
            "auto_cleared": int(np.random.random() < 0.30),
        })

df = pd.DataFrame(events)
sites.to_csv(f"{RAW}/site_inventory.csv", index=False)
df.to_csv(f"{RAW}/downtime_events.csv", index=False)
print(f"✅ Generated {len(df):,} downtime events across {N_SITES} sites.")
