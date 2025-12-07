# 🔮 Time Series Forecasting Implementation Guide

## Quick Start (5 Minutes)

### Step 1: Install Required Packages

```bash
pip install chronos-forecasting prophet torch pandas numpy plotly scipy
```

**Or use the requirements file:**
```bash
pip install -r requirements-forecasting.txt
```

### Step 2: Test the Installation

```bash
python test_forecasting.py
```

This will:
- Generate sample iPhone 14 data (1,160 days)
- Test Chronos forecasting (ratings + prices)
- Test Prophet forecasting (ratings + prices)
- Save results to `forecasts/` directory

**Expected time:** 3-5 minutes on first run (model download)

### Step 3: Run the Dashboard

```bash
streamlit run dashboard/app_with_forecasting.py
```

Then:
1. Click on the **"🔮 AI Forecasting"** tab
2. Select forecast horizon (7/14/30 days)
3. Check **"Use Sample Data"**
4. Click **"🚀 Generate Forecast"**

---

## 📁 Project Structure

```
project/
├── forecasting/
│   ├── __init__.py                  # Module initialization
│   ├── chronos_forecaster.py        # Chronos (Amazon) forecaster
│   ├── prophet_forecaster.py        # Prophet (Facebook) forecaster
│   └── utils.py                     # Utility functions
├── forecasts/                       # Forecast outputs (auto-created)
│   ├── chronos_rating_forecast.csv
│   ├── chronos_price_forecast.csv
│   ├── prophet_rating_forecast.csv
│   └── prophet_price_forecast.csv
├── dashboard/
│   ├── app.py                       # Original dashboard
│   └── app_with_forecasting.py      # NEW: Enhanced dashboard with forecasting
├── cleaned_product_timeseries.csv   # Your data (or generated)
├── test_forecasting.py              # Quick test script
└── requirements-forecasting.txt     # Forecasting dependencies
```

---

## 🎯 What Gets Forecasted?

### 1. iPhone 14 Ratings (4.2 to 4.8 scale)
- **Chronos:** Pre-trained zero-shot model with confidence intervals
- **Prophet:** Interpretable model showing trend + seasonality + holidays

### 2. iPhone 14 Prices (₹54,900 - ₹79,900)
- **Chronos:** Foundation model predictions with uncertainty bands
- **Prophet:** Decomposed into trend, yearly, weekly, monthly, holiday effects

---

## 🔧 Using Your Own Data

### CSV Format Required:

```csv
date,product_name,current_price,rating
2022-09-15,Apple iPhone 14,79900,4.8
2022-09-16,Apple iPhone 14,79899,4.3
...
2025-11-16,Apple iPhone 14,54900,4.5
```

**Minimum required columns:**
- `date` (YYYY-MM-DD format)
- `current_price` (integer)
- `rating` (float between 4.2 and 4.8)

### Upload Steps:
1. Open dashboard
2. Go to "🔮 AI Forecasting" tab
3. Uncheck "Use Sample Data"
4. Upload your CSV
5. Click "Generate Forecast"

---

## 🤖 Models Explained

### Chronos (Amazon)
- **Type:** Pre-trained foundation model
- **Size:** Tiny (8M parameters) - works on laptop CPU
- **Speed:** 1-2 minutes for 30-day forecast
- **Pros:**
  - Zero-shot (no training needed)
  - Excellent accuracy
  - Handles complex patterns
- **Cons:**
  - Less interpretable
  - Slower than Prophet

### Prophet (Facebook/Meta)
- **Type:** Additive decomposition model
- **Speed:** 10-20 seconds for 30-day forecast
- **Pros:**
  - Highly interpretable (shows WHY ratings change)
  - Handles holidays (Big Billion Days, Diwali, etc.)
  - Very fast
  - Bounded forecasts (logistic growth for ratings)
- **Cons:**
  - May miss complex non-linear patterns

---

## 📊 Dashboard Features

### Forecasting Tab Includes:

1. **Configuration Panel**
   - Forecast horizon selector (7/14/30 days)
   - Sample data toggle
   - Model comparison toggle

2. **Interactive Charts**
   - Rating forecast with 80% confidence intervals
   - Price forecast with uncertainty bands
   - Historical vs predicted comparison

3. **Forecast Tables**
   - Daily predictions from both models
   - Side-by-side comparison
   - Difference calculations

4. **Key Insights**
   - Average forecasted rating
   - Average forecasted price
   - Delta from historical average

5. **Model Information**
   - Technical details
   - Use cases
   - Performance characteristics

---

## 🚀 Advanced Usage

### Customize Forecast Horizon

```python
from forecasting.chronos_forecaster import ChronosForecaster
from forecasting.utils import load_timeseries_data

df = load_timeseries_data("cleaned_product_timeseries.csv")
forecaster = ChronosForecaster(model_size="tiny")

# Forecast next 60 days
rating_forecast = forecaster.forecast_rating(df, forecast_horizon=60)
```

### Use Larger Chronos Model

```python
# For better accuracy (requires more memory)
forecaster = ChronosForecaster(model_size="small")  # 46M params
```

### Access Prophet Components

```python
from forecasting.prophet_forecaster import ProphetForecaster

prophet = ProphetForecaster()
rating_forecast, components = prophet.forecast_rating(df, forecast_horizon=30)

# Components include:
# - trend
# - yearly seasonality
# - weekly seasonality
# - monthly seasonality
# - holiday effects
```

---

## 🎓 Indian E-commerce Holidays Included

The Prophet model automatically accounts for:

- **Big Billion Days** (Flipkart): Late Sept/Early Oct
- **Diwali:** Oct/Nov (dates vary)
- **Republic Day Sale:** Jan 26
- **Independence Day Sale:** Aug 15

These events significantly impact:
- Prices (temporary discounts)
- Ratings (increased review volume)

---

## 💡 Tips for Best Results

1. **Data Quality:**
   - At least 365 days of historical data recommended
   - Daily frequency (no gaps)
   - Clean outliers before forecasting

2. **Model Selection:**
   - Use **Chronos** for accuracy
   - Use **Prophet** for interpretability
   - **Compare both** for best insights

3. **Forecast Horizon:**
   - Short-term (7-14 days): More accurate
   - Long-term (30+ days): Higher uncertainty

4. **Performance:**
   - First run downloads Chronos model (~200MB)
   - Subsequent runs use cached model
   - Chronos: 1-2 min, Prophet: 10-20 sec

---

## 🐛 Troubleshooting

### Issue: Chronos model download fails
**Solution:**
```bash
pip install --upgrade chronos-forecasting torch
```

### Issue: Prophet installation error on Windows
**Solution:**
```bash
pip install prophet --no-cache-dir
# Or use conda:
conda install -c conda-forge prophet
```

### Issue: "No module named 'forecasting'"
**Solution:**
Make sure you're running from the project root directory

### Issue: Rating forecasts outside bounds (4.2-4.8)
**Solution:**
The models automatically clip to bounds, but check your input data for outliers

---

## 📈 Next Steps

1. ✅ **Test with sample data** (done via test_forecasting.py)
2. ✅ **Run dashboard** (app_with_forecasting.py)
3. ⏭️ **Upload your real CSV data**
4. ⏭️ **Compare Chronos vs Prophet**
5. ⏭️ **Present to your mentor** (show the forecasting tab!)

---

## 🎉 Congratulations!

You now have:
- **Chronos:** State-of-the-art Amazon foundation model
- **Prophet:** Industry-standard interpretable forecasting
- **Interactive dashboard:** Professional visualizations
- **Production-ready code:** Clean, documented, testable

**Total implementation time:** 2 days ✓
**Your mentor will be impressed!** 🚀

---

## 📧 What to Tell Your Mentor

> "I've implemented AI-powered time series forecasting for the iPhone 14 product using two cutting-edge models:
>
> 1. **Chronos** - Amazon's pre-trained foundation model (zero-shot forecasting)
> 2. **Prophet** - Facebook's interpretable model with trend/seasonality decomposition
>
> The system forecasts both ratings and prices for the next 30 days with 80% confidence intervals. It's integrated into an interactive Streamlit dashboard with model comparison and visualization.
>
> Tech stack: Python, PyTorch, Chronos, Prophet, Plotly, Streamlit"

Good luck with your presentation! 🎓
