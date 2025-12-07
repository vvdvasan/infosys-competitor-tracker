"""Utility functions for time series forecasting."""

import pandas as pd
import numpy as np
from typing import Tuple, Optional
from datetime import datetime, timedelta


def load_timeseries_data(csv_path: str) -> pd.DataFrame:
    """
    Load and validate time series data from CSV.

    Args:
        csv_path: Path to cleaned_product_timeseries.csv

    Returns:
        DataFrame with validated time series data
    """
    df = pd.read_csv(csv_path)

    # Convert date column to datetime
    df['date'] = pd.to_datetime(df['date'])

    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)

    # Validate required columns
    required_cols = ['date', 'current_price', 'rating']
    missing_cols = set(required_cols) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    print(f"[OK] Loaded {len(df)} rows from {df['date'].min()} to {df['date'].max()}")
    print(f"[OK] Price range: Rs.{df['current_price'].min():,.0f} to Rs.{df['current_price'].max():,.0f}")
    print(f"[OK] Rating range: {df['rating'].min():.1f} to {df['rating'].max():.1f}")

    return df


def prepare_forecast_data(
    df: pd.DataFrame,
    target_col: str,
    date_col: str = 'date'
) -> pd.DataFrame:
    """
    Prepare data for forecasting models.

    Args:
        df: Input DataFrame
        target_col: Column to forecast ('rating' or 'current_price')
        date_col: Date column name

    Returns:
        DataFrame ready for forecasting
    """
    forecast_df = df[[date_col, target_col]].copy()
    forecast_df = forecast_df.dropna()

    return forecast_df


def evaluate_forecast(
    actual: pd.Series,
    predicted: pd.Series,
    model_name: str = "Model"
) -> dict:
    """
    Calculate forecast accuracy metrics.

    Args:
        actual: Actual values
        predicted: Predicted values
        model_name: Name of the model for display

    Returns:
        Dictionary with accuracy metrics
    """
    # Align series
    actual, predicted = actual.align(predicted, join='inner')

    # Calculate metrics
    mae = np.mean(np.abs(actual - predicted))
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
    mape = np.mean(np.abs((actual - predicted) / actual)) * 100

    # R-squared
    ss_res = np.sum((actual - predicted) ** 2)
    ss_tot = np.sum((actual - np.mean(actual)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

    metrics = {
        'model': model_name,
        'mae': round(mae, 4),
        'rmse': round(rmse, 4),
        'mape': round(mape, 2),
        'r2_score': round(r2, 4)
    }

    print(f"\n{model_name} Accuracy Metrics:")
    print(f"  MAE (Mean Absolute Error): {metrics['mae']:.4f}")
    print(f"  RMSE (Root Mean Squared Error): {metrics['rmse']:.4f}")
    print(f"  MAPE (Mean Absolute Percentage Error): {metrics['mape']:.2f}%")
    print(f"  R² Score: {metrics['r2_score']:.4f}")

    return metrics


def create_indian_holidays() -> pd.DataFrame:
    """
    Create DataFrame of Indian e-commerce holidays.

    Returns:
        DataFrame with holiday dates and names
    """
    holidays = []

    # Big Billion Days (Flipkart) - typically late Sept/early Oct
    # Adding for 2022-2025
    big_billion_days = [
        ('2022-09-23', '2022-09-30', 'Big Billion Days 2022'),
        ('2023-10-08', '2023-10-15', 'Big Billion Days 2023'),
        ('2024-09-27', '2024-10-06', 'Big Billion Days 2024'),
        ('2025-09-26', '2025-10-05', 'Big Billion Days 2025'),
    ]

    for start, end, name in big_billion_days:
        date_range = pd.date_range(start, end)
        for date in date_range:
            holidays.append({
                'ds': date,
                'holiday': 'Big Billion Days',
                'lower_window': 0,
                'upper_window': 0
            })

    # Diwali (dates vary each year)
    diwali_dates = [
        ('2022-10-24', 'Diwali 2022'),
        ('2023-11-12', 'Diwali 2023'),
        ('2024-11-01', 'Diwali 2024'),
        ('2025-10-20', 'Diwali 2025'),
    ]

    for date, name in diwali_dates:
        # Diwali + 7 days pre-shopping window
        diwali_date = pd.to_datetime(date)
        for i in range(-7, 1):
            holidays.append({
                'ds': diwali_date + timedelta(days=i),
                'holiday': 'Diwali',
                'lower_window': 0,
                'upper_window': 0
            })

    # Republic Day Sale (Jan 26)
    for year in [2023, 2024, 2025]:
        for i in range(-3, 1):
            holidays.append({
                'ds': pd.to_datetime(f'{year}-01-26') + timedelta(days=i),
                'holiday': 'Republic Day Sale',
                'lower_window': 0,
                'upper_window': 0
            })

    # Independence Day Sale (Aug 15)
    for year in [2023, 2024, 2025]:
        for i in range(-3, 1):
            holidays.append({
                'ds': pd.to_datetime(f'{year}-08-15') + timedelta(days=i),
                'holiday': 'Independence Day Sale',
                'lower_window': 0,
                'upper_window': 0
            })

    return pd.DataFrame(holidays)


def generate_sample_data(
    output_path: str = "cleaned_product_timeseries.csv",
    start_date: str = "2022-09-15",
    end_date: str = "2025-11-16"
) -> pd.DataFrame:
    """
    Generate sample iPhone 14 time series data for testing.

    Args:
        output_path: Where to save the CSV
        start_date: Start date for data
        end_date: End date for data

    Returns:
        Generated DataFrame
    """
    print("Generating sample iPhone 14 time series data...")

    # Create date range
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    n_days = len(dates)

    # Price trend: Start at 79,900, gradually decrease to 54,900
    initial_price = 79900
    final_price = 54900
    price_trend = np.linspace(initial_price, final_price, n_days)

    # Add seasonal fluctuations to price
    seasonal_price = 2000 * np.sin(np.linspace(0, 8*np.pi, n_days))
    noise_price = np.random.normal(0, 500, n_days)
    current_price = price_trend + seasonal_price + noise_price
    current_price = np.clip(current_price, final_price, initial_price)

    # Original price (slightly higher)
    original_price = current_price * np.random.uniform(1.0, 1.08, n_days)

    # Rating trend: fluctuate between 4.2 and 4.8
    rating_trend = 4.5 + 0.15 * np.sin(np.linspace(0, 10*np.pi, n_days))
    rating_noise = np.random.normal(0, 0.05, n_days)
    rating = rating_trend + rating_noise
    rating = np.clip(rating, 4.2, 4.8)

    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'product_name': 'Apple iPhone 14',
        'current_price': current_price.astype(int),
        'original_price': original_price.astype(int),
        'discount_price': (original_price - current_price).astype(int),
        'rating': np.round(rating, 1),
        'year': dates.year,
        'month': dates.month,
        'quarter': dates.quarter,
        'day_of_week': dates.dayofweek,
        'is_weekend': dates.dayofweek.isin([5, 6]).astype(int),
        'day_of_year': dates.dayofyear
    })

    # Calculate price change metrics
    df['price_change'] = df['current_price'].diff().fillna(0)
    df['price_change_pct'] = df['current_price'].pct_change().fillna(0) * 100
    df['days_since_last_change'] = (df['price_change'] != 0).cumsum()
    df['discount_percentage'] = ((df['original_price'] - df['current_price']) / df['original_price'] * 100).round(2)

    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"[OK] Generated {len(df)} rows and saved to {output_path}")
    print(f"[OK] Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"[OK] Price range: Rs.{df['current_price'].min():,.0f} to Rs.{df['current_price'].max():,.0f}")
    print(f"[OK] Rating range: {df['rating'].min():.1f} to {df['rating'].max():.1f}")

    return df
