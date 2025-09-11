
OilShift: Detecting Structural Shifts in Brent Crude Oil Prices (1987–2022)
OilShift is a data-driven investigation into how major geopolitical and economic events have influenced Brent crude oil prices over the past 35 years. By applying Bayesian change point detection, the project identifies key structural shifts in market behavior, offering strategic insights for investors, policymakers, and energy analysts navigating oil price volatility.


Project Objectives
- Analyze long-term trends in Brent crude oil prices from 1987 to 2022
- Detect structural changes using Bayesian modeling techniques
- Correlate price shifts with major global events
- Deliver actionable insights through interactive visualizations and reporting

Milestone Progress
- ✅ Phase 1: Completed exploratory data analysis (EDA) and preprocessing
- 🔜 Phase 2: Implement Bayesian change point detection using PyMC3
- 🔜 Phase 3: Build an interactive dashboard with Flask and React
- 🔜 Phase 4: Finalize report and presentation materials


OilShift/
│
├── data/
│   ├── raw/                  # Original datasets (BrentOilPrices.csv, key_events.csv)
│   └── processed/            # Cleaned data and log returns
│
├── notebooks/
│   └── 01_eda.ipynb          # Exploratory Data Analysis notebook
│
├── scripts/
│   └── data_preprocessing.py # Data cleaning and transformation script
│
├── results/
│   ├── plots/                # Visualizations (price trends, volatility, event overlays)
│   └── summary_table.csv     # Summary statistics from EDA
│
├── docs/
│   └── interim_report.pdf    # Project documentation and interim findings
│
├── requirements.txt          # Python dependencies
└── README.md                 # Project overview and setup instructions




Setup Instructions
- Clone the repository
git clone https://github.com/your-username/OilShift.git
cd OilShift


- Install dependencies:
pip install -r requirements.txt
Required packages:
- pandas==2.0.3
- numpy==1.24.3
- matplotlib==3.7.2
- seaborn==0.12.2
- statsmodels==0.14.0
- Verify data files:
Ensure the following files exist in data/raw/:
- BrentOilPrices.csv
- key_events.csv
- Run the EDA notebook:


jupyter notebook notebooks/01_eda.ipynb
Outputs will be saved to data/processed/ and results/.






EDA Highlights
- Price Series:
Non-stationary (ADF = -1.9939, p = 0.2893).
Notable peaks in 2008 (~$143.95), sharp declines in 2014 and 2020.
- Log Returns:
Stationary (ADF = -16.4271, p < 0.0001).
Used to assess volatility and structural changes.
- Volatility Clusters:
30-day rolling standard deviation reveals spikes during global crises (e.g., 2008 financial crash, COVID-19).
- Event Overlay:
12 major geopolitical and economic events mapped to price movements.



Summary Statistics
- Mean Price: $48.42
- Standard Deviation: $32.86
- Minimum Price: $9.10
- Maximum Price: $143.95
- Mean Log Return: 0.000179
- Std Dev Log Return: 0.025532
- Total Observations: 9,011
Visuals and detailed metrics are available in results/plots/ and results/summary_table.csv.







