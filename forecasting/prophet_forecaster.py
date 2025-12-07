"""Prophet-based forecasting with trend and seasonality decomposition."""

import pandas as pd
import numpy as np
from prophet import Prophet
from typing import Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class ProphetForecaster:
    """
    Prophet forecasting model for iPhone 14 ratings and prices.

    Provides interpretable forecasts with trend, seasonality, and holiday effects.
    """

    def __init__(self):
        """Initialize Prophet forecaster."""
        self.rating_model = None
        self.price_model = None
        self.rating_bounds = (4.2, 4.8)
        self.holidays = self._create_indian_holidays()

        print("Initializing Prophet forecaster...")
        print(f"[OK] Loaded {len(self.holidays)} holiday dates")

    def _create_indian_holidays(self) -> pd.DataFrame:
        """Create DataFrame of Indian e-commerce holidays."""
        from forecasting.utils import create_indian_holidays
        return create_indian_holidays()

    def forecast_rating(
        self,
        df: pd.DataFrame,
        forecast_horizon: int = 30,
        date_col: str = 'date',
        rating_col: str = 'rating',
        include_history: bool = True
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Forecast iPhone 14 ratings using Prophet.

        Args:
            df: DataFrame with historical ratings
            forecast_horizon: Number of days to forecast
            date_col: Date column name
            rating_col: Rating column name
            include_history: Include historical fit in results

        Returns:
            Tuple of (forecast_df, components_df)
        """
        print(f"\nForecasting ratings with Prophet (horizon: {forecast_horizon} days)...")

        # Prepare data in Prophet format (ds, y)
        prophet_df = df[[date_col, rating_col]].copy()
        prophet_df.columns = ['ds', 'y']
        prophet_df = prophet_df.sort_values('ds').reset_index(drop=True)

        # Initialize Prophet model with logistic growth (for bounded forecasts)
        self.rating_model = Prophet(
            growth='logistic',  # Logistic growth for bounded values
            seasonality_mode='multiplicative',
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            holidays=self.holidays,
            seasonality_prior_scale=10.0,
            holidays_prior_scale=10.0,
            changepoint_prior_scale=0.05,
            interval_width=0.80  # 80% confidence interval
        )

        # Set capacity (upper bound) and floor (lower bound)
        prophet_df['cap'] = self.rating_bounds[1]  # 4.8
        prophet_df['floor'] = self.rating_bounds[0]  # 4.2

        # Fit model
        print("Training Prophet model...")
        self.rating_model.fit(prophet_df)

        # Create future DataFrame
        future = self.rating_model.make_future_dataframe(
            periods=forecast_horizon,
            freq='D',
            include_history=include_history
        )
        future['cap'] = self.rating_bounds[1]
        future['floor'] = self.rating_bounds[0]

        # Generate forecast
        print("Generating forecast...")
        forecast = self.rating_model.predict(future)

        # Get components
        components = self._extract_components(forecast, 'rating')

        # Filter to only future dates if not including history
        if not include_history:
            last_date = prophet_df['ds'].max()
            forecast = forecast[forecast['ds'] > last_date].copy()

        # Create clean forecast DataFrame
        forecast_df = pd.DataFrame({
            'date': forecast['ds'],
            'rating_forecast': forecast['yhat'].clip(
                self.rating_bounds[0],
                self.rating_bounds[1]
            ),
            'rating_lower_80': forecast['yhat_lower'].clip(
                self.rating_bounds[0],
                self.rating_bounds[1]
            ),
            'rating_upper_80': forecast['yhat_upper'].clip(
                self.rating_bounds[0],
                self.rating_bounds[1]
            ),
            'trend': forecast['trend'],
            'model': 'Prophet'
        })

        print(f"[OK] Rating forecast complete!")
        print(f"  Forecast range: {forecast_df['rating_forecast'].min():.2f} to {forecast_df['rating_forecast'].max():.2f}")
        print(f"  Mean forecast: {forecast_df['rating_forecast'].mean():.2f}")

        return forecast_df, components

    def forecast_price(
        self,
        df: pd.DataFrame,
        forecast_horizon: int = 30,
        date_col: str = 'date',
        price_col: str = 'current_price',
        include_history: bool = True
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Forecast iPhone 14 prices using Prophet.

        Args:
            df: DataFrame with historical prices
            forecast_horizon: Number of days to forecast
            date_col: Date column name
            price_col: Price column name
            include_history: Include historical fit in results

        Returns:
            Tuple of (forecast_df, components_df)
        """
        print(f"\nForecasting prices with Prophet (horizon: {forecast_horizon} days)...")

        # Prepare data
        prophet_df = df[[date_col, price_col]].copy()
        prophet_df.columns = ['ds', 'y']
        prophet_df = prophet_df.sort_values('ds').reset_index(drop=True)

        # Initialize Prophet model
        self.price_model = Prophet(
            growth='linear',  # Linear growth for prices
            seasonality_mode='additive',
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            holidays=self.holidays,
            seasonality_prior_scale=15.0,
            holidays_prior_scale=15.0,
            changepoint_prior_scale=0.1,
            interval_width=0.80
        )

        # Add monthly seasonality for sales patterns
        self.price_model.add_seasonality(
            name='monthly',
            period=30.5,
            fourier_order=5
        )

        # Fit model
        print("Training Prophet model...")
        self.price_model.fit(prophet_df)

        # Create future DataFrame
        future = self.price_model.make_future_dataframe(
            periods=forecast_horizon,
            freq='D',
            include_history=include_history
        )

        # Generate forecast
        print("Generating forecast...")
        forecast = self.price_model.predict(future)

        # Get components
        components = self._extract_components(forecast, 'price')

        # Filter to future dates if not including history
        if not include_history:
            last_date = prophet_df['ds'].max()
            forecast = forecast[forecast['ds'] > last_date].copy()

        # Apply floor (minimum price threshold)
        min_price = prophet_df['y'].min() * 0.9

        # Create clean forecast DataFrame
        forecast_df = pd.DataFrame({
            'date': forecast['ds'],
            'price_forecast': forecast['yhat'].clip(min_price, None).astype(int),
            'price_lower_80': forecast['yhat_lower'].clip(min_price, None).astype(int),
            'price_upper_80': forecast['yhat_upper'].clip(min_price, None).astype(int),
            'trend': forecast['trend'].astype(int),
            'model': 'Prophet'
        })

        print(f"[OK] Price forecast complete!")
        print(f"  Forecast range: Rs.{forecast_df['price_forecast'].min():,.0f} to Rs.{forecast_df['price_forecast'].max():,.0f}")
        print(f"  Mean forecast: Rs.{forecast_df['price_forecast'].mean():,.0f}")

        return forecast_df, components

    def _extract_components(
        self,
        forecast: pd.DataFrame,
        target_type: str = 'rating'
    ) -> pd.DataFrame:
        """
        Extract trend and seasonality components.

        Args:
            forecast: Prophet forecast DataFrame
            target_type: 'rating' or 'price'

        Returns:
            DataFrame with decomposed components
        """
        components = pd.DataFrame({
            'date': forecast['ds'],
            'trend': forecast['trend'],
            'yearly': forecast.get('yearly', 0),
            'weekly': forecast.get('weekly', 0),
            'holidays': forecast.get('holidays', 0),
        })

        if 'monthly' in forecast.columns:
            components['monthly'] = forecast['monthly']

        components['target_type'] = target_type
        return components

    def forecast_both(
        self,
        df: pd.DataFrame,
        forecast_horizon: int = 30,
        include_history: bool = False
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Forecast both ratings and prices with components.

        Args:
            df: DataFrame with historical data
            forecast_horizon: Number of days to forecast
            include_history: Include historical fit

        Returns:
            Tuple of (rating_forecast, rating_components, price_forecast, price_components)
        """
        rating_forecast, rating_components = self.forecast_rating(
            df,
            forecast_horizon=forecast_horizon,
            include_history=include_history
        )

        price_forecast, price_components = self.forecast_price(
            df,
            forecast_horizon=forecast_horizon,
            include_history=include_history
        )

        return rating_forecast, rating_components, price_forecast, price_components

    def plot_components(self, target_type: str = 'rating'):
        """
        Plot Prophet components (trend, seasonality, holidays).

        Args:
            target_type: 'rating' or 'price'
        """
        import matplotlib.pyplot as plt

        model = self.rating_model if target_type == 'rating' else self.price_model

        if model is None:
            print(f"Error: {target_type} model not trained yet!")
            return

        fig = model.plot_components()
        plt.tight_layout()
        return fig


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
    forecaster = ProphetForecaster()

    # Forecast ratings and prices
    rating_forecast, rating_components, price_forecast, price_components = forecaster.forecast_both(
        df,
        forecast_horizon=30,
        include_history=False
    )

    # Display results
    print("\n--- RATING FORECAST (Next 30 Days) ---")
    print(rating_forecast.head(10))

    print("\n--- PRICE FORECAST (Next 30 Days) ---")
    print(price_forecast.head(10))

    print("\n--- RATING COMPONENTS ---")
    print(rating_components.head(10))

    # Save results
    os.makedirs("forecasts", exist_ok=True)
    rating_forecast.to_csv("forecasts/prophet_rating_forecast.csv", index=False)
    price_forecast.to_csv("forecasts/prophet_price_forecast.csv", index=False)
    rating_components.to_csv("forecasts/prophet_rating_components.csv", index=False)
    price_components.to_csv("forecasts/prophet_price_components.csv", index=False)

    print("\n[OK] Forecasts saved to forecasts/ directory")
