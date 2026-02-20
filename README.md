# NYC Taxi Data Dashboard

## Overview

This project presents an interactive dashboard that explores NYC taxi trip data, including trip distances, fare patterns, and trends. The dashboard allows users to visualize key metrics, explore distributions, and gain insights into taxi usage patterns through interactive charts and filters.

## Features

* Data cleaning and validation pipeline
* Feature engineering (trip duration, speed, time-based features)
* SQL Analysis
* Interactive visualizations
* Insights and interpretations for each chart

## Project Structure

```
├── assignment1_dashboard/      # Streamlit dashboard app.py
├── data/                       # Directory created by Notebook
│   ├── raw/                    # Raw datasets
│   └── clean/                  # Processed datasets
├── assignment1.ipynb           # Exploration and analysis notebooks
├── README.md             
└── requirements.txt            # Dependencies
```

## Setup Instructions

### 1. Clone the repository

```
git clone https://github.com/JJ-ama-LL/Data-Pipeline-and-Visualization-Dashboard.git
cd Data-Pipeline-and-Visualization-Dashboard
```

### 2. Install dependencies

```
pip install -r requirements.txt
```

### 3. Run the Jupyter Notebook

### 4. Run the Streamlit app

```
cd assignment1_dashboard
streamlit run app.py
```

The dashboard will open in your browser.

## Data

Raw taxi trip data and zone lookup files should be placed in the `data/raw` directory. The app will automatically generate cleaned data if it does not already exist.

## Deployed Dashboard

`https://nyc-yellow-taxi-data-dashboard.streamlit.app`

## Insights

Each visualization includes brief interpretations highlighting key patterns in taxi demand, trip behavior, and fare distributions.

## Author

Jamal Mohammed
