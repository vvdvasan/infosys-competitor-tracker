"""Quick test script for forecasting functionality."""

import os
import sys
from forecasting.utils import generate_sample_data, load_timeseries_data
from forecasting.chronos_forecaster import ChronosForecaster
from forecasting.prophet_forecaster import ProphetForecaster

def main():
    print("=" * 60)
    print("TESTING TIME SERIES FORECASTING")
    print("=" * 60)

    # Step 1: Generate or load data
    csv_path = "cleaned_product_timeseries.csv"
    if not os.path.exists(csv_path):
        print("\n[1/5] Generating sample iPhone 14 data...")
        df = generate_sample_data(csv_path)
    else:
        print("\n[1/5] Loading existing data...")
        df = load_timeseries_data(csv_path)

    print(f"\n[OK] Data loaded: {len(df)} rows")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"  Rating range: {df['rating'].min():.1f} to {df['rating'].max():.1f}")
    print(f"  Price range: Rs.{df['current_price'].min():,.0f} to Rs.{df['current_price'].max():,.0f}")

    # Step 2: Test Chronos forecaster
    print("\n[2/5] Testing Chronos forecaster...")
    print("(This may take 2-3 minutes on first run to download the model)")
    chronos = ChronosForecaster(model_size="tiny")

    print("\n  Forecasting ratings...")
    chronos_rating_forecast = chronos.forecast_rating(df, forecast_horizon=7, num_samples=50)

    print("\n  Forecasting prices...")
    chronos_price_forecast = chronos.forecast_price(df, forecast_horizon=7, num_samples=50)

    print("\n[OK] Chronos forecasts complete!")
    print(f"  Rating forecast: {chronos_rating_forecast['rating_forecast'].iloc[0]:.2f} to {chronos_rating_forecast['rating_forecast'].iloc[-1]:.2f}")
    print(f"  Price forecast: Rs.{chronos_price_forecast['price_forecast'].iloc[0]:,.0f} to Rs.{chronos_price_forecast['price_forecast'].iloc[-1]:,.0f}")

    # Step 3: Test Prophet forecaster
    print("\n[3/5] Testing Prophet forecaster...")
    prophet = ProphetForecaster()

    prophet_rating_forecast, rating_components = prophet.forecast_rating(
        df,
        forecast_horizon=7,
        include_history=False
    )

    prophet_price_forecast, price_components = prophet.forecast_price(
        df,
        forecast_horizon=7,
        include_history=False
    )

    print("\n[OK] Prophet forecasts complete!")
    print(f"  Rating forecast: {prophet_rating_forecast['rating_forecast'].iloc[0]:.2f} to {prophet_rating_forecast['rating_forecast'].iloc[-1]:.2f}")
    print(f"  Price forecast: Rs.{prophet_price_forecast['price_forecast'].iloc[0]:,.0f} to Rs.{prophet_price_forecast['price_forecast'].iloc[-1]:,.0f}")

    # Step 4: Save results
    print("\n[4/5] Saving forecast results...")
    os.makedirs("forecasts", exist_ok=True)

    chronos_rating_forecast.to_csv("forecasts/chronos_rating_forecast.csv", index=False)
    chronos_price_forecast.to_csv("forecasts/chronos_price_forecast.csv", index=False)
    prophet_rating_forecast.to_csv("forecasts/prophet_rating_forecast.csv", index=False)
    prophet_price_forecast.to_csv("forecasts/prophet_price_forecast.csv", index=False)

    print("[OK] Results saved to forecasts/ directory")

    # Step 5: Display summary
    print("\n[5/5] Forecast Summary:")
    print("\n  RATING COMPARISON (Next 7 Days):")
    print(f"    Chronos: {chronos_rating_forecast['rating_forecast'].mean():.2f} (avg)")
    print(f"    Prophet: {prophet_rating_forecast['rating_forecast'].mean():.2f} (avg)")
    print(f"    Historical: {df['rating'].mean():.2f} (avg)")

    print("\n  PRICE COMPARISON (Next 7 Days):")
    print(f"    Chronos: Rs.{chronos_price_forecast['price_forecast'].mean():,.0f} (avg)")
    print(f"    Prophet: Rs.{prophet_price_forecast['price_forecast'].mean():,.0f} (avg)")
    print(f"    Historical: Rs.{df['current_price'].mean():,.0f} (avg)")

    print("\n" + "=" * 60)
    print("[OK] ALL TESTS PASSED!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Run the dashboard: streamlit run dashboard/app_with_forecasting.py")
    print("  2. Navigate to the 'AI Forecasting' tab")
    print("  3. Click 'Generate Forecast'")
    print("\nEnjoy your AI-powered forecasting!")

if __name__ == "__main__":
    main()
