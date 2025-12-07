@echo off
echo ========================================
echo Installing Time Series Forecasting
echo ========================================
echo.

echo [1/3] Installing required packages...
pip install chronos-forecasting prophet torch pandas numpy plotly scipy

echo.
echo [2/3] Testing installation...
python test_forecasting.py

echo.
echo [3/3] Installation complete!
echo.
echo ========================================
echo Next steps:
echo   1. Run: streamlit run dashboard\app_with_forecasting.py
echo   2. Navigate to "AI Forecasting" tab
echo   3. Click "Generate Forecast"
echo ========================================
pause
