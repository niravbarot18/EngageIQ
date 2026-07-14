# Customer Engagement & Product Utilization Analytics for Retention Strategy

Behavioral churn analytics for a European retail bank — reframing customer retention around **engagement and product depth**, not just demographics or wealth.

---

## Overview

Banks often assume that financially strong customers — those with high balances or high salaries — are automatically loyal. This project tests that assumption against a real 10,000-customer dataset from a European retail bank and finds it largely false.

Using engagement classification, product utilization analysis, and a composite relationship-strength score, this project identifies **which behaviors actually drive churn**, and delivers those insights as a research paper, an executive summary, and a live interactive dashboard.

**The headline finding:** churn isn't lowest for customers with the fewest or the most products — it's lowest at exactly **two products** (7.6%) and then collapses to **83–100%** at three or four. High-balance customers who are disengaged churn *worse* than average customers, not better. Credit card ownership, often assumed to build loyalty, shows almost no effect at all.

---

## Key Results at a Glance

| Metric | Value |
|---|---|
| Overall churn rate | 20.4% |
| Churn — active vs inactive members | 14.3% vs 26.9% |
| Churn — 1 / 2 / 3 / 4 products | 27.7% / 7.6% / 82.7% / 100% |
| Churn — high-balance & disengaged customers | 30.5% (highest-risk segment) |
| Credit card ownership effect on churn | ~0.6 pp (negligible) |
| Churn across Relationship Strength Index quartiles | ~35% → <10% |

---

## Repository Structure

```
EngageIQ/
│   ├── app.py                    # Streamlit dashboard source
│   ├── requirements.txt          # Python dependencies
│   └── data/
│       └── European_Bank.csv     # Source dataset (10,000 customers)
└── PROJECT_README.md             # This file
```

---

## Methodology

1. **Data Ingestion & Validation** — confirmed zero missing values, binary field consistency, churn label accuracy across 10,000 records.
2. **Engagement Classification** — segmented customers into 4 profiles: Active & Engaged, Inactive & Disengaged, Active/Low-Product, Inactive/High-Balance.
3. **Product Utilization Analysis** — churn rate by exact product count, single- vs multi-product comparison.
4. **Financial Commitment vs. Engagement Analysis** — balance/salary cross-tabulated with activity status to isolate "silent churn" risk.
5. **Retention Strength Assessment** — built and validated a composite Relationship Strength Index (RSI) combining activity, capped product count, card ownership, and tenure.

## KPIs Defined

- **Engagement Retention Ratio** — retention rate (active) ÷ retention rate (inactive)
- **Product Depth Index** — churn trend across product count (non-monotonic; peaks at 2)
- **High-Balance Disengagement Rate** — share of top-quartile-balance customers who are inactive
- **Credit Card Stickiness Score** — churn(no card) − churn(has card)
- **Relationship Strength Index (RSI)** — composite 0–10 score validated against actual churn

---

## Running the Dashboard

```bash
cd streamlit_dashboard
pip install -r requirements.txt
streamlit run app.py
```

The app loads `data/European_Bank.csv` automatically. Use the sidebar to filter by geography, engagement status, product count, and balance/salary thresholds — all four dashboard modules update live.

---

## Dataset

| Column | Description |
|---|---|
| CustomerId, Surname | Identifiers |
| CreditScore | Customer creditworthiness |
| Geography, Gender, Age | Demographics |
| Tenure | Years with the bank |
| Balance, EstimatedSalary | Financial standing |
| NumOfProducts, HasCrCard, IsActiveMember | Engagement & product fields |
| Exited | Churn indicator (target) |

Source: European Central Bank retail customer dataset, 10,000 records, no missing values.

---

## Recommendations Summary

1. Cap proactive cross-selling at 2 products unless a documented customer need justifies more.
2. Build a standing outreach list for high-balance, inactive customers — the highest-risk, not lowest-risk, segment.
3. Redirect card-ownership retention incentives toward engagement-driving programs.
4. Operationalize RSI as a single risk score in CRM/relationship-manager tools.
5. Investigate Germany's elevated churn rate (32.4% vs ~16% elsewhere) as a separate market-level issue.

## Limitations

- Cross-sectional snapshot, not a time series — doesn't capture engagement trends leading up to churn.
- "High balance" and other thresholds are defined relative to this sample and should be validated against the bank's actual risk appetite before operational use.
- Findings are strong statistical associations; causal validation (e.g., customer interviews for the 3+ product segment) is recommended before major policy changes.

---
