"""
uptime_analysis.py — Computes availability KPIs, root cause Pareto, site risk ranking.
Run after generate_data.py
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW      = os.path.join(BASE, "data", "raw")
PROC     = os.path.join(BASE, "data", "processed")
OUTPUTS  = os.path.join(BASE, "outputs")
os.makedirs(PROC, exist_ok=True)
os.makedirs(OUTPUTS, exist_ok=True)

df    = pd.read_csv(f"{RAW}/downtime_events.csv", parse_dates=["start_time","end_time"])
sites = pd.read_csv(f"{RAW}/site_inventory.csv")
df["month"] = df["start_time"].dt.to_period("M")
TOTAL_MINS  = 43800   # ~30-day month in minutes

print("=" * 55)
print("  TELECOM UPTIME ANALYSIS")
print("=" * 55)

# ── 1. MONTHLY AVAILABILITY ───────────────────────────────────────
print("\n[1] Monthly Site Availability")
monthly = df.groupby(["site_id","month"]).agg(
    downtime_hrs=("duration_hrs","sum")
).reset_index()
monthly["downtime_mins"]  = monthly["downtime_hrs"] * 60
monthly["availability_pct"] = ((TOTAL_MINS - monthly["downtime_mins"]) / TOTAL_MINS * 100).round(3)
monthly["sla_breach"]       = monthly["availability_pct"] < 99.5
monthly.to_csv(f"{PROC}/site_availability_monthly.csv", index=False)
print(f"  SLA breaches detected: {monthly['sla_breach'].sum()}")
print(f"  Sites with 3+ breaches: {(monthly.groupby('site_id')['sla_breach'].sum() >= 3).sum()}")

# ── 2. ROOT CAUSE ANALYSIS ────────────────────────────────────────
print("\n[2] Root Cause Breakdown")
rc = df.groupby("root_cause").agg(
    events=("site_id","count"),
    total_hrs=("duration_hrs","sum"),
    avg_hrs=("duration_hrs","mean"),
).sort_values("total_hrs", ascending=False).reset_index()
rc["share_pct"]     = (rc["total_hrs"] / rc["total_hrs"].sum() * 100).round(1)
rc["cumulative_pct"] = rc["share_pct"].cumsum()
rc.to_csv(f"{OUTPUTS}/root_cause_summary.csv", index=False)
print(rc[["root_cause","events","total_hrs","share_pct","cumulative_pct"]].to_string(index=False))

# ── 3. SITE RISK RANKING ──────────────────────────────────────────
print("\n[3] Site Risk Ranking (Top 10)")
risk = df.groupby("site_id").agg(
    events=("root_cause","count"),
    total_hrs=("duration_hrs","sum"),
    avg_hrs=("duration_hrs","mean"),
).reset_index()
risk["risk_score"] = (
    (risk["total_hrs"] / risk["total_hrs"].max()) * 60 +
    (risk["events"]    / risk["events"].max())    * 40
).round(2)
risk = risk.sort_values("risk_score", ascending=False)
risk.to_csv(f"{OUTPUTS}/site_risk_ranking.csv", index=False)
print(risk.head(10).to_string(index=False))

# ── 4. CHARTS ─────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle("Telecom Site Uptime Analysis", fontsize=14, fontweight="bold")

# Pareto
ax2 = axes[0].twinx()
axes[0].bar(rc["root_cause"], rc["total_hrs"], color="steelblue", alpha=0.8)
ax2.plot(rc["root_cause"], rc["cumulative_pct"], color="red", marker="o", linewidth=2)
ax2.axhline(80, linestyle="--", color="gray", alpha=0.6, label="80% line")
axes[0].set_ylabel("Total Downtime (hrs)")
ax2.set_ylabel("Cumulative %")
axes[0].set_title("Pareto: Downtime by Root Cause")
axes[0].tick_params(axis="x", rotation=30)

# Availability distribution
avail = monthly.groupby("site_id")["availability_pct"].mean()
axes[1].hist(avail, bins=20, color="steelblue", edgecolor="white", alpha=0.85)
axes[1].axvline(99.5, color="red", linestyle="--", label="SLA 99.5%")
axes[1].set_xlabel("Average Availability (%)")
axes[1].set_ylabel("Number of Sites")
axes[1].set_title("Distribution of Site Availability")
axes[1].legend()

plt.tight_layout()
plt.savefig(f"{OUTPUTS}/uptime_analysis_charts.png", dpi=150, bbox_inches="tight")
print(f"\n✅ Charts saved to {OUTPUTS}/")
