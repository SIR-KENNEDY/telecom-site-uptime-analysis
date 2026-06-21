"""
site_risk_scorer.py
===================
Computes a composite risk score for each telecom site based on:
  - Total downtime hours
  - Number of critical events
  - MTTR (Mean Time To Resolve)
  - SLA breach frequency
  - Tenant count impact

Outputs ranked risk list and flags sites for immediate attention.
Run after generate_data.py
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

BASE    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW     = os.path.join(BASE, "data", "raw")
OUTPUTS = os.path.join(BASE, "outputs")
os.makedirs(OUTPUTS, exist_ok=True)

df    = pd.read_csv(f"{RAW}/downtime_events.csv", parse_dates=["start_time","end_time"])
sites = pd.read_csv(f"{RAW}/site_inventory.csv")

print("="*55)
print("  TELECOM SITE RISK SCORING ENGINE")
print("="*55)

# ── PER-SITE METRICS ──────────────────────────────────────────────
metrics = df.groupby("site_id").agg(
    total_events      = ("root_cause", "count"),
    critical_events   = ("severity", lambda x: (x == "Critical").sum()  if "severity" in df.columns else 0),
    total_hrs         = ("duration_hrs", "sum"),
    avg_mttr_hrs      = ("duration_hrs", "mean"),
    max_event_hrs     = ("duration_hrs", "max"),
    auto_clear_rate   = ("auto_cleared", "mean"),
).reset_index()

# Merge site metadata
metrics = metrics.merge(sites[["site_id","region","technology","tenant_count"]], on="site_id", how="left")

# ── NORMALISE & SCORE (0–100) ─────────────────────────────────────
def normalise(series):
    mn, mx = series.min(), series.max()
    return (series - mn) / (mx - mn + 1e-9)

metrics["score_downtime"]  = normalise(metrics["total_hrs"])         * 35
metrics["score_events"]    = normalise(metrics["total_events"])      * 25
metrics["score_mttr"]      = normalise(metrics["avg_mttr_hrs"])      * 20
metrics["score_max_event"] = normalise(metrics["max_event_hrs"])     * 10
metrics["score_tenants"]   = normalise(metrics["tenant_count"])      * 10

metrics["risk_score"] = (
    metrics["score_downtime"]  +
    metrics["score_events"]    +
    metrics["score_mttr"]      +
    metrics["score_max_event"] +
    metrics["score_tenants"]
).round(2)

bins   = [0, 30, 55, 75, 100]
labels = ["Low", "Medium", "High", "Critical"]
metrics["risk_tier"] = pd.cut(metrics["risk_score"], bins=bins, labels=labels)
metrics = metrics.sort_values("risk_score", ascending=False).reset_index(drop=True)

print(f"\nTop 15 Highest Risk Sites:")
print(metrics[["site_id","region","technology","total_hrs","total_events","risk_score","risk_tier"]].head(15).to_string(index=False))

metrics.to_csv(f"{OUTPUTS}/site_risk_scores.csv", index=False)

# ── SUMMARY BY REGION ─────────────────────────────────────────────
region_risk = metrics.groupby("region").agg(
    sites=("site_id","count"),
    avg_risk=("risk_score","mean"),
    critical_sites=("risk_tier", lambda x: (x=="Critical").sum()),
    high_sites=("risk_tier", lambda x: (x=="High").sum()),
).sort_values("avg_risk", ascending=False).reset_index()
print("\nRisk Summary by Region:")
print(region_risk.to_string(index=False))

# ── CHART ─────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle("Telecom Site Risk Assessment", fontsize=14, fontweight="bold")

tier_colors = {"Critical":"#e74c3c","High":"#e67e22","Medium":"#f1c40f","Low":"#27ae60"}
tier_counts = metrics["risk_tier"].value_counts()
axes[0].bar(tier_counts.index, tier_counts.values,
            color=[tier_colors.get(t,"steelblue") for t in tier_counts.index])
axes[0].set_title("Sites by Risk Tier")
axes[0].set_ylabel("Number of Sites")

top15 = metrics.head(15)
bar_colors = [tier_colors.get(str(t),"steelblue") for t in top15["risk_tier"]]
axes[1].barh(top15["site_id"][::-1], top15["risk_score"][::-1], color=bar_colors[::-1])
axes[1].set_xlabel("Risk Score")
axes[1].set_title("Top 15 Highest Risk Sites")
axes[1].axvline(75, color="red", linestyle="--", alpha=0.7, label="Critical threshold")
axes[1].legend()

plt.tight_layout()
plt.savefig(f"{OUTPUTS}/site_risk_chart.png", dpi=150, bbox_inches="tight")
print(f"\n✅ Risk scoring complete. Output saved.")
