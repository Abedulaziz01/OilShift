Through Bayesian Analysis
📊 Overview
OilShift investigates the impact of major geopolitical and economic events on Brent crude oil prices from 1987 to 2022, leveraging Bayesian change point detection to uncover structural shifts in market behavior. The project aims to provide strategic insights for investors, policymakers, and energy stakeholders navigating oil price volatility.
🔧 Project Milestones

- ✅ Phase 1: Comprehensive exploratory data analysis and preprocessing completed
- 🔜 Phase 2: Bayesian modeling implementation using PyMC3
- 🔜 Phase 3: Deployment of an interactive dashboard built with Flask + React
- 🔜 Phase 4: Final report and slides

---

## 🗂️ Repository Structure

```
OilShift/
├── data/
│   ├── raw/
│   │   ├── BrentOilPrices.csv
│   │   └── key_events.csv
│   └── processed/
│       ├── brent_oil_prices_cleaned.csv
│       └── log_returns.csv
│
├── notebooks/
│   └── 01_eda.ipynb
│
├── scripts/
│   └── data_preprocessing.py
│
├── results/
│   ├── plots/
│   │   ├── raw_price_trend.png
│   │   ├── log_returns.png
│   │   ├── volatility.png
│   │   └── price_with_events.png
│   └── summary_table.csv
│
├── docs/
│   └── interim_report.pdf
│
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup Instructions

1️⃣ **Clone the repository:**

```bash
git clone https://github.com/your-username/OilShift.git
cd OilShift
```

2️⃣ **Install dependencies:**

```bash
pip install -r requirements.txt
```

> 📦 **Dependencies:** pandas==2.0.3, numpy==1.24.3, matplotlib==3.7.2, seaborn==0.12.2, statsmodels==0.14.0

3️⃣ **Verify data:**
Ensure `data/raw/BrentOilPrices.csv` and `data/raw/key_events.csv` exist.

4️⃣ **Run EDA notebook:**

```bash
jupyter notebook notebooks/01_eda.ipynb
```

Outputs are saved to `data/processed/` and `results/`.

---

## 🔍 Task 1: EDA Summary

- **Price Series:** Non-stationary. ADF: -1.9939 (p = 0.2893). Peaks (2008 \~\$143.95), drops (2014, 2020).
- **Log Returns:** Stationary. ADF: -16.4271 (p < 0.0001). Used for volatility insights.
- **Volatility:** 30-day rolling std shows clustering during crises (2008, 2020).
- **Events:** 12 key events overlaid for context.

**Summary Stats:**

| Metric             | Value    |
| ------------------ | -------- |
| Mean Price         | \$48.42  |
| Std Dev Price      | \$32.86  |
| Min Price          | \$9.10   |
| Max Price          | \$143.95 |
| Mean Log Return    | 0.000179 |
| Std Dev Log Return | 0.025532 |
| Total Rows         | 9,011    |

See `results/plots/` and `results/summary_table.csv` for visuals and details.

---

## 🗓️ Next Steps

- [ ] **Task 2:** Bayesian change point modeling in PyMC3
- [ ] **Task 3:** Flask/React interactive dashboard
- [ ] **Final:** Comprehensive report & slides

---

## 📚 Data Sources

- **Brent Oil Prices:** EIA or equivalent
- **Key Events:** Compiled from OPEC, EIA, BBC, Reuters

## 📬 Contact

_Questions?_ Reach out at \[smucav@gmail.com].
