"""
mttr_benchmarking.py
====================
Computes Mean Time To Resolve (MTTR) and Mean Time Between Failures (MTBF)
per site, region, and root cause. Benchmarks against SLA targets.

Run after generate_data.py
"""
import pandas as pd
import numpy as np
import os

BASE    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW     = os.path.join(BASE, "data", "raw")
OUTPUTS = os.path.join(BASE, "outputs")
os.makedirs(OUTPUTS, exist_ok=True)

df    = pd.read_csv(f"{RAW}/downtime_events.csv", parse_dates=["start_time","end_time"])
sites = pd.read_csv(f"{RAW}/site_inventory.csv")
df    = df.merge(sites[["site_id","region","technology"]], on="site_id", how="left")
df    = df.sort_values(["site_id","start_time"])

print("="*55)
print("  MTTR & MTBF BENCHMARKING")
print("="*55)

# ── MTTR BY ROOT CAUSE ────────────────────────────────────────────
print("\n[MTTR by Root Cause]")
mttr_rc = df.groupby("root_cause").agg(
    events      = ("duration_hrs","count"),
    mttr_mean   = ("duration_hrs","mean"),
    mttr_median = ("duration_hrs","median"),
    mttr_p90    = ("duration_hrs", lambda x: np.percentile(x,90)),
    mttr_max    = ("duration_hrs","max"),
).round(2).sort_values("mttr_mean", ascending=False)
print(mttr_rc.to_string())
mttr_rc.to_csv(f"{OUTPUTS}/mttr_by_root_cause.csv")

# ── MTTR BY REGION ────────────────────────────────────────────────
print("\n[MTTR by Region]")
mttr_region = df.groupby("region").agg(
    events=("duration_hrs","count"),
    mttr_mean=("duration_hrs","mean"),
    mttr_median=("duration_hrs","median"),
    sla_breaches=("duration_hrs", lambda x: (x > 3).sum()),
).reset_index()
mttr_region["sla_breach_pct"] = (mttr_region["sla_breaches"]/mttr_region["events"]*100).round(1)
mttr_region = mttr_region.sort_values("sla_breach_pct", ascending=False)
print(mttr_region.to_string(index=False))
mttr_region.to_csv(f"{OUTPUTS}/mttr_by_region.csv", index=False)

# ── MTBF PER SITE ─────────────────────────────────────────────────
print("\n[MTBF — Top 10 Most Reliable Sites]")
total_days = (df["start_time"].max() - df["start_time"].min()).days
mtbf = df.groupby("site_id").agg(
    events=("duration_hrs","count"),
    total_downtime_hrs=("duration_hrs","sum"),
).reset_index()
mtbf["mtbf_days"]    = (total_days / mtbf["events"]).round(1)
mtbf["availability"] = ((total_days*24 - mtbf["total_downtime_hrs"]) / (total_days*24) * 100).round(3)
mtbf = mtbf.sort_values("mtbf_days", ascending=False)
print(mtbf.head(10).to_string(index=False))
mtbf.to_csv(f"{OUTPUTS}/site_mtbf.csv", index=False)
print("\n✅ MTTR/MTBF benchmarking complete.")
