"""Chronos-based forecasting using Amazon's pre-trained time series foundation model."""

import pandas as pd
import numpy as np
import torch
from chronos import ChronosPipeline
from typing import Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class ChronosForecaster:
    """
    Chronos forecasting model for iPhone 14 ratings and prices.

    Uses Amazon's pre-trained Chronos model (zero-shot forecasting).
    """

    def __init__(self, model_size: str = "tiny"):
        """
        Initialize Chronos forecaster.

        Args:
            model_size: Model size - "tiny" (8M), "mini" (20M), "small" (46M), "base" (200M)
                       For laptop CPU, use "tiny" or "mini"
        """
        self.model_size = model_size
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipeline = None
        self.rating_bounds = (4.2, 4.8)  # iPhone 14 rating bounds

        print(f"Initializing Chronos forecaster (size: {model_size}, device: {self.device})...")

    def _load_model(self):
        """Load the Chronos model (lazy loading)."""
        if self.pipeline is None:
            print(f"Loading Chronos-{self.model_size} model...")
            model_name = f"amazon/chronos-t5-{self.model_size}"

            self.pipeline = ChronosPipeline.from_pretrained(
                model_name,
                device_map=self.device,
                torch_dtype=torch.bfloat16 if self.device == "cuda" else torch.float32,
            )
            print("[OK] Model loaded successfully!")

    def forecast_rating(
        self,
        df: pd.DataFrame,
        forecast_horizon: int = 30,
        num_samples: int = 100,
        date_col: str = 'date',
        rating_col: str = 'rating'
    ) -> pd.DataFrame:
        """
        Forecast iPhone 14 ratings for next N days.

        Args:
            df: DataFrame with historical ratings
            forecast_horizon: Number of days to forecast
            num_samples: Number of samples for confidence intervals
            date_col: Date column name
            rating_col: Rating column name

        Returns:
            DataFrame with forecasted ratings and confidence intervals
        """
        self._load_model()

        print(f"\nForecasting ratings for next {forecast_horizon} days...")

        # Prepare data
        df_sorted = df.sort_values(date_col).reset_index(drop=True)
        historical_ratings = df_sorted[rating_col].values.astype(np.float32)

        # Context length (use last 365 days or all data if less)
        context_length = min(365, len(historical_ratings))
        context = torch.tensor(historical_ratings[-context_length:])

        # Generate forecast
        print("Generating forecast samples...")
        forecast_samples = self.pipeline.predict(
            context,
            prediction_length=forecast_horizon,
            num_samples=num_samples
        )

        # Convert to numpy and apply bounds
        forecast_array = forecast_samples.numpy()

        # Ensure correct shape (num_samples, forecast_horizon)
        if forecast_array.ndim == 3:
            forecast_array = forecast_array.squeeze(0)  # Remove batch dimension

        # Clip to rating bounds (4.2 to 4.8)
        forecast_array = np.clip(
            forecast_array,
            self.rating_bounds[0],
            self.rating_bounds[1]
        )

        # Calculate statistics
        forecast_mean = np.median(forecast_array, axis=0).flatten()
        forecast_lower = np.quantile(forecast_array, 0.1, axis=0).flatten()  # 10th percentile
        forecast_upper = np.quantile(forecast_array, 0.9, axis=0).flatten()  # 90th percentile

        # Create future dates
        last_date = df_sorted[date_col].max()
        future_dates = pd.date_range(
            start=last_date + pd.Timedelta(days=1),
            periods=forecast_horizon,
            freq='D'
        )

        # Create forecast DataFrame - ensure all arrays are 1D
        forecast_df = pd.DataFrame({
            'date': future_dates,
            'rating_forecast': np.asarray(forecast_mean).ravel(),
            'rating_lower_80': np.asarray(forecast_lower).ravel(),
            'rating_upper_80': np.asarray(forecast_upper).ravel(),
            'model': 'Chronos'
        })

        print(f"[OK] Rating forecast complete!")
        print(f"  Forecast range: {forecast_mean.min():.2f} to {forecast_mean.max():.2f}")
        print(f"  Mean forecast: {forecast_mean.mean():.2f}")

        return forecast_df

    def forecast_price(
        self,
        df: pd.DataFrame,
        forecast_horizon: int = 30,
        num_samples: int = 100,
        date_col: str = 'date',
        price_col: str = 'current_price'
    ) -> pd.DataFrame:
        """
        Forecast iPhone 14 prices for next N days.

        Args:
            df: DataFrame with historical prices
            forecast_horizon: Number of days to forecast
            num_samples: Number of samples for confidence intervals
            date_col: Date column name
            price_col: Price column name

        Returns:
            DataFrame with forecasted prices and confidence intervals
        """
        self._load_model()

        print(f"\nForecasting prices for next {forecast_horizon} days...")

        # Prepare data
        df_sorted = df.sort_values(date_col).reset_index(drop=True)
        historical_prices = df_sorted[price_col].values.astype(np.float32)

        # Context length (use last 365 days or all data if less)
        context_length = min(365, len(historical_prices))
        context = torch.tensor(historical_prices[-context_length:])

        # Generate forecast
        print("Generating forecast samples...")
        forecast_samples = self.pipeline.predict(
            context,
            prediction_length=forecast_horizon,
            num_samples=num_samples
        )

        # Convert to numpy
        forecast_array = forecast_samples.numpy()

        # Ensure correct shape (num_samples, forecast_horizon)
        if forecast_array.ndim == 3:
            forecast_array = forecast_array.squeeze(0)  # Remove batch dimension

        # Apply floor (price can't go below certain threshold)
        min_price = historical_prices.min() * 0.9  # 10% below minimum
        forecast_array = np.clip(forecast_array, min_price, None)

        # Calculate statistics
        forecast_mean = np.median(forecast_array, axis=0).flatten()
        forecast_lower = np.quantile(forecast_array, 0.1, axis=0).flatten()
        forecast_upper = np.quantile(forecast_array, 0.9, axis=0).flatten()

        # Create future dates
        last_date = df_sorted[date_col].max()
        future_dates = pd.date_range(
            start=last_date + pd.Timedelta(days=1),
            periods=forecast_horizon,
            freq='D'
        )

        # Create forecast DataFrame - ensure all arrays are 1D
        forecast_df = pd.DataFrame({
            'date': future_dates,
            'price_forecast': np.asarray(forecast_mean).ravel().astype(int),
            'price_lower_80': np.asarray(forecast_lower).ravel().astype(int),
            'price_upper_80': np.asarray(forecast_upper).ravel().astype(int),
            'model': 'Chronos'
        })

        print(f"[OK] Price forecast complete!")
        print(f"  Forecast range: Rs.{forecast_mean.min():,.0f} to Rs.{forecast_mean.max():,.0f}")
        print(f"  Mean forecast: Rs.{forecast_mean.mean():,.0f}")

        return forecast_df

    def forecast_both(
        self,
        df: pd.DataFrame,
        forecast_horizon: int = 30,
        num_samples: int = 100
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Forecast both ratings and prices.

        Args:
            df: DataFrame with historical data
            forecast_horizon: Number of days to forecast
            num_samples: Number of samples for confidence intervals

        Returns:
            Tuple of (rating_forecast_df, price_forecast_df)
        """
        rating_forecast = self.forecast_rating(
            df,
            forecast_horizon=forecast_horizon,
            num_samples=num_samples
        )

        price_forecast = self.forecast_price(
            df,
            forecast_horizon=forecast_horizon,
            num_samples=num_samples
        )

        return rating_forecast, price_forecast


# Example usage
if __name__ == "__main__":
    from forecasting.utils import load_timeseries_data, generate_sample_data
    import os

    # Generate sample data if needed
    csv_path = "cleaned_product_timeseries.csv"
    if not os.path.exists(csv_path):
        print("Sample data not found. Generating...")
        df = generate_sample_data(csv_path)
    else:
        df = load_timeseries_data(csv_path)

    # Initialize forecaster
    forecaster = ChronosForecaster(model_size="tiny")

    # Forecast ratings and prices
    rating_forecast, price_forecast = forecaster.forecast_both(
        df,
        forecast_horizon=30,
        num_samples=100
    )

    # Display results
    print("\n--- RATING FORECAST (Next 30 Days) ---")
    print(rating_forecast.head(10))

    print("\n--- PRICE FORECAST (Next 30 Days) ---")
    print(price_forecast.head(10))

    # Save results
    rating_forecast.to_csv("forecasts/chronos_rating_forecast.csv", index=False)
    price_forecast.to_csv("forecasts/chronos_price_forecast.csv", index=False)
    print("\n[OK] Forecasts saved to forecasts/ directory")
