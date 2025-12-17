"""Enhanced Streamlit dashboard with time series forecasting."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import sys
import os
import numpy as np

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentiment_analysis.config import Config
from sentiment_analysis.database.db_manager import DatabaseManager
from sentiment_analysis.api.groq_client import GroqSentimentAnalyzer
from sentiment_analysis.scraper.amazon_scraper import AmazonScraper

# Import forecasting modules
from forecasting.chronos_forecaster import ChronosForecaster
from forecasting.prophet_forecaster import ProphetForecaster
from forecasting.utils import load_timeseries_data, generate_sample_data

# Page configuration
st.set_page_config(
    page_title="E-commerce Competitor Sentiment & Forecast Tracker",
    page_icon="📊",
    layout="wide"
)

# Initialize components
@st.cache_resource
def init_components():
    """Initialize database and API clients."""
    db_manager = DatabaseManager()
    groq_analyzer = GroqSentimentAnalyzer()
    return db_manager, groq_analyzer

@st.cache_resource
def init_forecasting_models():
    """Initialize forecasting models (cached for performance)."""
    chronos = ChronosForecaster(model_size="tiny")
    prophet = ProphetForecaster()
    return chronos, prophet

db_manager, groq_analyzer = init_components()

# Title and description
st.title("🛍️ E-Commerce Intelligence Dashboard")
st.markdown("### Real-Time Sentiment Analysis & AI-Powered Forecasting")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("📋 Control Panel")

    # Scraping section
    st.subheader("🔍 Data Collection")
    product_url = st.text_input(
        "Amazon Product URL",
        placeholder="https://www.amazon.in/dp/..."
    )

    if st.button("🚀 Scrape Product", type="primary"):
        if product_url:
            with st.spinner("Scraping product data..."):
                scraper = AmazonScraper()
                try:
                    # Scrape product
                    product_data = scraper.scrape_product(product_url)
                    if product_data:
                        db_manager.insert_product(product_data)
                        st.success(f"✅ Scraped: {product_data.get('Product_Name', 'Unknown')}")

                        # Scrape reviews
                        with st.spinner("Scraping reviews..."):
                            reviews = scraper.scrape_reviews(product_url, max_pages=5)
                            if reviews:
                                db_manager.insert_reviews(reviews)
                                st.success(f"✅ Scraped {len(reviews)} reviews")
                            else:
                                st.warning("No reviews found")
                    else:
                        st.error("Failed to scrape product")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                finally:
                    scraper.close()
        else:
            st.warning("Please enter a product URL")

    # Analysis section
    st.subheader("🧠 Sentiment Analysis")

    if st.button("🔄 Analyze Pending Reviews"):
        with st.spinner("Analyzing sentiments..."):
            # Get unanalyzed reviews
            pending_reviews = db_manager.get_unanalyzed_reviews(limit=20)

            if pending_reviews:
                progress_bar = st.progress(0)
                status_text = st.empty()

                results = []
                for i, review in enumerate(pending_reviews):
                    status_text.text(f"Analyzing review {i+1}/{len(pending_reviews)}")

                    # Analyze sentiment
                    sentiment_result = groq_analyzer.analyze_sentiment(review['text'])
                    sentiment_result['review_id'] = review['review_id']
                    results.append(sentiment_result)

                    progress_bar.progress((i + 1) / len(pending_reviews))

                # Save results
                db_manager.insert_sentiment_results(results)
                st.success(f"✅ Analyzed {len(results)} reviews")
                status_text.empty()
                progress_bar.empty()
            else:
                st.info("No pending reviews to analyze")

    # API Usage
    st.subheader("📊 API Usage")
    usage = groq_analyzer.rate_limiter.get_current_usage()
    st.metric("Requests Used", f"{usage['requests_used']}/{Config.GROQ_RPM}")
    st.metric("Tokens Used", f"{usage['tokens_used']}/{Config.GROQ_TPM}")

# Main content area - 5 tabs now!
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Overview",
    "🎯 Sentiment Analysis",
    "📦 Products",
    "📝 Reviews",
    "🔮 AI Forecasting"  # NEW TAB!
])

with tab1:
    # Get statistics
    stats = db_manager.get_sentiment_statistics()

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Products",
            stats['overall']['total_products'] or 0
        )

    with col2:
        st.metric(
            "Total Reviews",
            stats['overall']['total_reviews'] or 0
        )

    with col3:
        st.metric(
            "Avg Rating",
            f"{stats['overall']['avg_rating']:.1f}" if stats['overall']['avg_rating'] else "N/A"
        )

    with col4:
        total_analyzed = sum(stats['sentiment_distribution'].values())
        st.metric(
            "Reviews Analyzed",
            total_analyzed
        )

    st.markdown("---")

    # Sentiment distribution charts
    if stats['sentiment_distribution']:
        col1, col2 = st.columns(2)

        with col1:
            # Pie chart
            fig_pie = px.pie(
                values=list(stats['sentiment_distribution'].values()),
                names=list(stats['sentiment_distribution'].keys()),
                title="Overall Sentiment Distribution",
                color_discrete_map={
                    'POSITIVE': '#00CC88',
                    'NEGATIVE': '#FF4444',
                    'NEUTRAL': '#FFAA00'
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # Bar chart
            df_sentiment = pd.DataFrame(
                list(stats['sentiment_distribution'].items()),
                columns=['Sentiment', 'Count']
            )
            fig_bar = px.bar(
                df_sentiment,
                x='Sentiment',
                y='Count',
                title="Sentiment Counts",
                color='Sentiment',
                color_discrete_map={
                    'POSITIVE': '#00CC88',
                    'NEGATIVE': '#FF4444',
                    'NEUTRAL': '#FFAA00'
                }
            )
            st.plotly_chart(fig_bar, use_container_width=True)

with tab2:
    st.header("🎯 Detailed Sentiment Analysis")

    # Time-based analysis
    with sqlite3.connect(db_manager.db_path) as conn:
        query = """
            SELECT
                DATE(sa.analyzed_at) as date,
                sa.sentiment,
                COUNT(*) as count
            FROM sentiment_analysis sa
            WHERE sa.sentiment IN ('POSITIVE', 'NEGATIVE', 'NEUTRAL')
                AND sa.analyzed_at IS NOT NULL
            GROUP BY DATE(sa.analyzed_at), sa.sentiment
            ORDER BY date
        """
        df_timeline = pd.read_sql_query(query, conn)

    if not df_timeline.empty:
        fig_timeline = px.line(
            df_timeline,
            x='date',
            y='count',
            color='sentiment',
            title="Sentiment Trends Over Time",
            color_discrete_map={
                'POSITIVE': '#00CC88',
                'NEGATIVE': '#FF4444',
                'NEUTRAL': '#FFAA00'
            }
        )
        st.plotly_chart(fig_timeline, use_container_width=True)

    # Product-wise sentiment
    st.subheader("📦 Product-wise Sentiment")

    with sqlite3.connect(db_manager.db_path) as conn:
        query = """
            SELECT
                p.product_name,
                p.brand,
                sa.sentiment,
                COUNT(*) as count,
                p.rating as product_rating
            FROM sentiment_analysis sa
            JOIN reviews r ON sa.review_id = r.review_id
            JOIN products p ON r.product_asin = p.product_asin
            WHERE sa.sentiment IN ('POSITIVE', 'NEGATIVE', 'NEUTRAL')
            GROUP BY p.product_asin, sa.sentiment
            ORDER BY p.product_name
        """
        df_product_sentiment = pd.read_sql_query(query, conn)

    if not df_product_sentiment.empty:
        # Pivot for better visualization
        df_pivot = df_product_sentiment.pivot_table(
            index='product_name',
            columns='sentiment',
            values='count',
            fill_value=0
        )

        fig_stacked = px.bar(
            df_pivot.reset_index(),
            x='product_name',
            y=['POSITIVE', 'NEGATIVE', 'NEUTRAL'] if all(col in df_pivot.columns for col in ['POSITIVE', 'NEGATIVE', 'NEUTRAL']) else df_pivot.columns.tolist(),
            title="Sentiment Distribution by Product",
            color_discrete_map={
                'POSITIVE': '#00CC88',
                'NEGATIVE': '#FF4444',
                'NEUTRAL': '#FFAA00'
            }
        )
        st.plotly_chart(fig_stacked, use_container_width=True)

with tab3:
    st.header("📦 Product Information")

    # Create clean product data (from analyzed CSV data)
    df_products = pd.DataFrame({
        'Product': ['Apple iPhone 14'],
        'Brand': ['Apple'],
        'Current Price (₹)': [54900],
        'MRP (₹)': [59900],
        'Discount (%)': [8.3],
        'Rating': [4.5],
        'Reviews': [86]
    })

    # Display as clean metrics cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Current Price", f"₹{df_products['Current Price (₹)'].values[0]:,.0f}")
    with col2:
        st.metric("Original MRP", f"₹{df_products['MRP (₹)'].values[0]:,.0f}")
    with col3:
        st.metric("Rating", f"{df_products['Rating'].values[0]} ⭐")
    with col4:
        st.metric("Reviews", f"{int(df_products['Reviews'].values[0])}")

    st.markdown("---")

    # Show simple table with essential info
    st.dataframe(
        df_products,
        use_container_width=True,
        hide_index=True
    )

with tab4:
    st.header("📝 Review Analysis")

    # Sentiment filter
    sentiment_filter = st.selectbox(
        "Filter by Sentiment",
        ["All", "POSITIVE", "NEGATIVE", "NEUTRAL"]
    )

    # Load reviews with sentiment
    with sqlite3.connect(db_manager.db_path) as conn:
        query = """
            SELECT
                r.reviewer_name,
                r.rating,
                r.title,
                r.text,
                r.date,
                r.verified_purchase,
                sa.sentiment,
                sa.confidence,
                p.product_name
            FROM reviews r
            LEFT JOIN sentiment_analysis sa ON r.review_id = sa.review_id
            JOIN products p ON r.product_asin = p.product_asin
            WHERE 1=1
        """

        if sentiment_filter != "All":
            query += f" AND sa.sentiment = '{sentiment_filter}'"

        query += " ORDER BY r.scraped_at DESC LIMIT 100"

        df_reviews = pd.read_sql_query(query, conn)

    if not df_reviews.empty:
        # Display reviews
        for _, review in df_reviews.iterrows():
            with st.expander(f"{review['title'][:50]}..." if review['title'] else "Review"):
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.write(f"**Reviewer:** {review['reviewer_name']}")
                    st.write(f"**Product:** {review['product_name']}")

                with col2:
                    st.write(f"**Rating:** {'⭐' * int(float(review['rating']))} ({review['rating']})")
                    st.write(f"**Date:** {review['date']}")

                with col3:
                    if review['sentiment']:
                        sentiment_color = {
                            'POSITIVE': '🟢',
                            'NEGATIVE': '🔴',
                            'NEUTRAL': '🟡'
                        }.get(review['sentiment'], '⚪')
                        st.write(f"**Sentiment:** {sentiment_color} {review['sentiment']}")
                        if review['confidence']:
                            st.write(f"**Confidence:** {review['confidence']:.2%}")

                st.markdown("---")
                st.write(review['text'])

                if review['verified_purchase']:
                    st.caption("✅ Verified Purchase")
    else:
        st.info("No reviews found. Scrape some products first!")

    # Word Cloud
    if not df_reviews.empty and df_reviews['text'].notna().any():
        st.subheader("☁️ Review Word Cloud")

        text = ' '.join(df_reviews['text'].dropna())

        if text:
            wordcloud = WordCloud(
                width=800,
                height=400,
                background_color='white',
                colormap='viridis'
            ).generate(text)

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)

# ============================================================================
# 🔮 NEW FORECASTING TAB!
# ============================================================================
with tab5:
    st.header("🔮 AI-Powered Time Series Forecasting")
    st.markdown("**Predict iPhone 14 ratings and prices using cutting-edge AI models**")
    st.markdown("---")

    # Configuration section
    col1, col2, col3 = st.columns(3)

    with col1:
        forecast_horizon = st.selectbox(
            "Forecast Horizon",
            [7, 14, 30],
            index=2,
            help="Number of days to forecast into the future"
        )

    with col2:
        use_sample_data = st.checkbox(
            "Use Sample Data",
            value=True,
            help="Generate sample iPhone 14 data for demonstration"
        )

    with col3:
        run_both_models = st.checkbox(
            "Compare Models",
            value=True,
            help="Run both Chronos and Prophet for comparison"
        )

    # File upload
    uploaded_file = None
    if not use_sample_data:
        uploaded_file = st.file_uploader(
            "Upload Time Series CSV",
            type=['csv'],
            help="Upload cleaned_product_timeseries.csv with columns: date, rating, current_price"
        )

    # Run forecast button
    if st.button("🚀 Generate Forecast", type="primary"):
        try:
            with st.spinner("Loading data..."):
                # Load or generate data
                if use_sample_data:
                    if not os.path.exists("cleaned_product_timeseries.csv"):
                        st.info("Generating sample iPhone 14 data...")
                        df = generate_sample_data("cleaned_product_timeseries.csv")
                    else:
                        df = load_timeseries_data("cleaned_product_timeseries.csv")
                elif uploaded_file:
                    df = pd.read_csv(uploaded_file)
                    df['date'] = pd.to_datetime(df['date'])
                else:
                    st.error("Please upload a CSV file or use sample data")
                    st.stop()

            # Display data info
            st.success(f"✓ Loaded {len(df)} days of data ({df['date'].min().date()} to {df['date'].max().date()})")

            # Show data preview
            with st.expander("📊 View Data Preview"):
                st.dataframe(df.head(20), use_container_width=True)
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Average Rating", f"{df['rating'].mean():.2f}")
                with col2:
                    st.metric("Average Price", f"₹{df['current_price'].mean():,.0f}")
                with col3:
                    st.metric("Data Points", len(df))

            st.markdown("---")

            # Initialize models and forecast
            if run_both_models:
                st.subheader("🤖 Model Comparison: Chronos vs Prophet")

                # Chronos forecasting
                with st.spinner("Running Chronos model (Amazon's Foundation Model)..."):
                    chronos_forecaster = ChronosForecaster(model_size="tiny")
                    chronos_rating, chronos_price = chronos_forecaster.forecast_both(
                        df,
                        forecast_horizon=forecast_horizon,
                        num_samples=100
                    )

                # Prophet forecasting
                with st.spinner("Running Prophet model (Facebook's Interpretable Model)..."):
                    prophet_forecaster = ProphetForecaster()
                    prophet_rating, _, prophet_price, _ = prophet_forecaster.forecast_both(
                        df,
                        forecast_horizon=forecast_horizon,
                        include_history=False
                    )

                # RATING FORECAST COMPARISON
                st.subheader("⭐ Rating Forecast Comparison")

                # Combine historical and forecasted data
                fig_rating = go.Figure()

                # Historical data
                fig_rating.add_trace(go.Scatter(
                    x=df['date'],
                    y=df['rating'],
                    mode='lines',
                    name='Historical',
                    line=dict(color='gray', width=2)
                ))

                # Chronos forecast
                fig_rating.add_trace(go.Scatter(
                    x=chronos_rating['date'],
                    y=chronos_rating['rating_forecast'],
                    mode='lines',
                    name='Chronos Forecast',
                    line=dict(color='blue', width=2, dash='dash')
                ))

                fig_rating.add_trace(go.Scatter(
                    x=chronos_rating['date'].tolist() + chronos_rating['date'].tolist()[::-1],
                    y=chronos_rating['rating_upper_80'].tolist() + chronos_rating['rating_lower_80'].tolist()[::-1],
                    fill='toself',
                    fillcolor='rgba(0, 100, 255, 0.2)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name='Chronos 80% CI',
                    showlegend=True
                ))

                # Prophet forecast
                fig_rating.add_trace(go.Scatter(
                    x=prophet_rating['date'],
                    y=prophet_rating['rating_forecast'],
                    mode='lines',
                    name='Prophet Forecast',
                    line=dict(color='green', width=2, dash='dot')
                ))

                fig_rating.add_trace(go.Scatter(
                    x=prophet_rating['date'].tolist() + prophet_rating['date'].tolist()[::-1],
                    y=prophet_rating['rating_upper_80'].tolist() + prophet_rating['rating_lower_80'].tolist()[::-1],
                    fill='toself',
                    fillcolor='rgba(0, 255, 100, 0.2)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name='Prophet 80% CI',
                    showlegend=True
                ))

                fig_rating.update_layout(
                    title=f"iPhone 14 Rating Forecast - Next {forecast_horizon} Days",
                    xaxis_title="Date",
                    yaxis_title="Rating (out of 5)",
                    hovermode='x unified',
                    height=500
                )

                st.plotly_chart(fig_rating, use_container_width=True)

                # PRICE FORECAST COMPARISON
                st.subheader("💰 Price Forecast Comparison")

                fig_price = go.Figure()

                # Historical data
                fig_price.add_trace(go.Scatter(
                    x=df['date'],
                    y=df['current_price'],
                    mode='lines',
                    name='Historical',
                    line=dict(color='gray', width=2)
                ))

                # Chronos forecast
                fig_price.add_trace(go.Scatter(
                    x=chronos_price['date'],
                    y=chronos_price['price_forecast'],
                    mode='lines',
                    name='Chronos Forecast',
                    line=dict(color='blue', width=2, dash='dash')
                ))

                fig_price.add_trace(go.Scatter(
                    x=chronos_price['date'].tolist() + chronos_price['date'].tolist()[::-1],
                    y=chronos_price['price_upper_80'].tolist() + chronos_price['price_lower_80'].tolist()[::-1],
                    fill='toself',
                    fillcolor='rgba(0, 100, 255, 0.2)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name='Chronos 80% CI',
                    showlegend=True
                ))

                # Prophet forecast
                fig_price.add_trace(go.Scatter(
                    x=prophet_price['date'],
                    y=prophet_price['price_forecast'],
                    mode='lines',
                    name='Prophet Forecast',
                    line=dict(color='green', width=2, dash='dot')
                ))

                fig_price.add_trace(go.Scatter(
                    x=prophet_price['date'].tolist() + prophet_price['date'].tolist()[::-1],
                    y=prophet_price['price_upper_80'].tolist() + prophet_price['price_lower_80'].tolist()[::-1],
                    fill='toself',
                    fillcolor='rgba(0, 255, 100, 0.2)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name='Prophet 80% CI',
                    showlegend=True
                ))

                fig_price.update_layout(
                    title=f"iPhone 14 Price Forecast - Next {forecast_horizon} Days",
                    xaxis_title="Date",
                    yaxis_title="Price (₹)",
                    hovermode='x unified',
                    height=500
                )

                st.plotly_chart(fig_price, use_container_width=True)

                # ========================================
                # 📊 MODEL EVALUATION METRICS (NEW!)
                # ========================================
                st.markdown("---")
                st.subheader("📊 Model Performance Evaluation")
                st.markdown("**Comparing model accuracy using industry-standard metrics**")

                # Calculate metrics using train-test split
                split_idx = int(len(df) * 0.8)
                train_df = df.iloc[:split_idx].copy()
                test_df = df.iloc[split_idx:].copy()

                if len(test_df) > 0:
                    with st.expander("ℹ️ How Metrics Are Calculated", expanded=False):
                        st.markdown(f"""
                        **Train-Test Split:** 80% training ({len(train_df)} points), 20% testing ({len(test_df)} points)

                        **Metrics Explained:**
                        - **MAPE (Mean Absolute Percentage Error):** Average error as percentage. Lower is better. <5% is excellent.
                        - **MAE (Mean Absolute Error):** Average absolute difference. Lower is better. Measured in price/rating units.
                        - **RMSE (Root Mean Squared Error):** Penalizes large errors via squaring. Lower is better.
                        - **R² Score:** Variance explained by model (0-1 scale). Higher is better. 1.0 = perfect prediction.
                        """)

                    try:
                        # Import sklearn metrics
                        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

                        # Re-train models on training data only
                        test_horizon = len(test_df)

                        with st.spinner("Calculating evaluation metrics..."):
                            # Chronos on test data
                            chronos_test_forecaster = ChronosForecaster(model_size="tiny")
                            _, chronos_test_price = chronos_test_forecaster.forecast_both(
                                train_df,
                                forecast_horizon=test_horizon,
                                num_samples=50
                            )

                            # Prophet on test data
                            prophet_test_forecaster = ProphetForecaster()
                            _, _, prophet_test_price, _ = prophet_test_forecaster.forecast_both(
                                train_df,
                                forecast_horizon=test_horizon,
                                include_history=False
                            )

                            # Get actual values
                            actual_prices = test_df['current_price'].values

                            # Get predictions (align lengths)
                            chronos_pred = chronos_test_price['price_forecast'].values[:len(actual_prices)]
                            prophet_pred = prophet_test_price['price_forecast'].values[:len(actual_prices)]

                            # Calculate metrics for Chronos
                            chronos_mae = mean_absolute_error(actual_prices, chronos_pred)
                            chronos_rmse = np.sqrt(mean_squared_error(actual_prices, chronos_pred))
                            chronos_mape = np.mean(np.abs((actual_prices - chronos_pred) / actual_prices)) * 100
                            chronos_r2 = r2_score(actual_prices, chronos_pred)

                            # Calculate metrics for Prophet
                            prophet_mae = mean_absolute_error(actual_prices, prophet_pred)
                            prophet_rmse = np.sqrt(mean_squared_error(actual_prices, prophet_pred))
                            prophet_mape = np.mean(np.abs((actual_prices - prophet_pred) / actual_prices)) * 100
                            prophet_r2 = r2_score(actual_prices, prophet_pred)

                            # Display metrics in columns
                            st.markdown("### 🏆 Price Forecast Accuracy")

                            col1, col2, col3, col4 = st.columns(4)

                            with col1:
                                st.metric(
                                    "MAPE (%)",
                                    "Lower is better",
                                    help="Mean Absolute Percentage Error"
                                )
                                st.metric("🔵 Chronos", f"{chronos_mape:.2f}%",
                                         delta=f"{prophet_mape - chronos_mape:.2f}%" if chronos_mape < prophet_mape else None,
                                         delta_color="normal" if chronos_mape < prophet_mape else "inverse")
                                st.metric("🟢 Prophet", f"{prophet_mape:.2f}%")

                                if chronos_mape < prophet_mape:
                                    st.success("✅ Chronos wins!")
                                else:
                                    st.success("✅ Prophet wins!")

                            with col2:
                                st.metric(
                                    "MAE (₹)",
                                    "Lower is better",
                                    help="Mean Absolute Error"
                                )
                                st.metric("🔵 Chronos", f"₹{chronos_mae:,.0f}",
                                         delta=f"₹{prophet_mae - chronos_mae:,.0f}" if chronos_mae < prophet_mae else None,
                                         delta_color="normal" if chronos_mae < prophet_mae else "inverse")
                                st.metric("🟢 Prophet", f"₹{prophet_mae:,.0f}")

                                if chronos_mae < prophet_mae:
                                    st.success("✅ Chronos wins!")
                                else:
                                    st.success("✅ Prophet wins!")

                            with col3:
                                st.metric(
                                    "RMSE (₹)",
                                    "Lower is better",
                                    help="Root Mean Squared Error"
                                )
                                st.metric("🔵 Chronos", f"₹{chronos_rmse:,.0f}",
                                         delta=f"₹{prophet_rmse - chronos_rmse:,.0f}" if chronos_rmse < prophet_rmse else None,
                                         delta_color="normal" if chronos_rmse < prophet_rmse else "inverse")
                                st.metric("🟢 Prophet", f"₹{prophet_rmse:,.0f}")

                                if chronos_rmse < prophet_rmse:
                                    st.success("✅ Chronos wins!")
                                else:
                                    st.success("✅ Prophet wins!")

                            with col4:
                                st.metric(
                                    "R² Score",
                                    "Higher is better",
                                    help="Coefficient of Determination (0-1)"
                                )
                                st.metric("🔵 Chronos", f"{chronos_r2:.3f}",
                                         delta=f"{chronos_r2 - prophet_r2:.3f}" if chronos_r2 > prophet_r2 else None,
                                         delta_color="normal" if chronos_r2 > prophet_r2 else "inverse")
                                st.metric("🟢 Prophet", f"{prophet_r2:.3f}")

                                if chronos_r2 > prophet_r2:
                                    st.success("✅ Chronos wins!")
                                else:
                                    st.success("✅ Prophet wins!")

                            # Winner announcement
                            st.markdown("---")
                            wins_chronos = sum([
                                chronos_mape < prophet_mape,
                                chronos_mae < prophet_mae,
                                chronos_rmse < prophet_rmse,
                                chronos_r2 > prophet_r2
                            ])

                            if wins_chronos >= 3:
                                st.success(f"🏆 **RECOMMENDED MODEL: Chronos** (won {wins_chronos}/4 metrics)")
                                st.info(f"💡 Chronos achieved **{chronos_mape:.2f}% MAPE** - meaning {100-chronos_mape:.2f}% accuracy on unseen test data!")
                            else:
                                st.success(f"🏆 **RECOMMENDED MODEL: Prophet** (won {4-wins_chronos}/4 metrics)")
                                st.info(f"💡 Prophet achieved **{prophet_mape:.2f}% MAPE** - meaning {100-prophet_mape:.2f}% accuracy on unseen test data!")

                    except Exception as e:
                        st.warning(f"Could not calculate evaluation metrics: {str(e)}")
                        st.info("Showing forecast results without evaluation metrics.")

                # Forecast tables
                st.markdown("---")
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("📅 Rating Forecasts")
                    comparison_rating = pd.DataFrame({
                        'Date': chronos_rating['date'].dt.date,
                        'Chronos': chronos_rating['rating_forecast'].round(2),
                        'Prophet': prophet_rating['rating_forecast'].round(2),
                        'Difference': (chronos_rating['rating_forecast'] - prophet_rating['rating_forecast']).round(2)
                    })
                    st.dataframe(comparison_rating, use_container_width=True, height=300)

                with col2:
                    st.subheader("📅 Price Forecasts")
                    comparison_price = pd.DataFrame({
                        'Date': chronos_price['date'].dt.date,
                        'Chronos (₹)': chronos_price['price_forecast'],
                        'Prophet (₹)': prophet_price['price_forecast'],
                        'Difference (₹)': chronos_price['price_forecast'] - prophet_price['price_forecast']
                    })
                    st.dataframe(comparison_price, use_container_width=True, height=300)

                # Key insights
                st.markdown("---")
                st.subheader("🎯 Key Insights")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    avg_chronos_rating = chronos_rating['rating_forecast'].mean()
                    st.metric(
                        "Chronos Avg Rating",
                        f"{avg_chronos_rating:.2f}",
                        delta=f"{avg_chronos_rating - df['rating'].mean():.2f}"
                    )

                with col2:
                    avg_prophet_rating = prophet_rating['rating_forecast'].mean()
                    st.metric(
                        "Prophet Avg Rating",
                        f"{avg_prophet_rating:.2f}",
                        delta=f"{avg_prophet_rating - df['rating'].mean():.2f}"
                    )

                with col3:
                    avg_chronos_price = chronos_price['price_forecast'].mean()
                    st.metric(
                        "Chronos Avg Price",
                        f"₹{avg_chronos_price:,.0f}",
                        delta=f"₹{avg_chronos_price - df['current_price'].mean():,.0f}"
                    )

                with col4:
                    avg_prophet_price = prophet_price['price_forecast'].mean()
                    st.metric(
                        "Prophet Avg Price",
                        f"₹{avg_prophet_price:,.0f}",
                        delta=f"₹{avg_prophet_price - df['current_price'].mean():,.0f}"
                    )

                # ========================================
                # 📥 CSV EXPORT SECTION (Teammate's Request!)
                # ========================================
                st.markdown("---")
                st.subheader("📥 Download Forecast Data (CSV)")

                col1, col2, col3 = st.columns(3)

                with col1:
                    # Combined forecast CSV (both models)
                    combined_rating = pd.DataFrame({
                        'date': chronos_rating['date'].dt.date,
                        'historical_rating': [df['rating'].iloc[-1]] * len(chronos_rating),
                        'chronos_forecast': chronos_rating['rating_forecast'].round(2),
                        'chronos_lower_80': chronos_rating['rating_lower_80'].round(2),
                        'chronos_upper_80': chronos_rating['rating_upper_80'].round(2),
                        'prophet_forecast': prophet_rating['rating_forecast'].round(2),
                        'prophet_lower_80': prophet_rating['rating_lower_80'].round(2),
                        'prophet_upper_80': prophet_rating['rating_upper_80'].round(2),
                    })

                    csv_rating = combined_rating.to_csv(index=False)
                    st.download_button(
                        label="📊 Rating Forecasts",
                        data=csv_rating,
                        file_name=f"iphone14_rating_forecast_{forecast_horizon}days.csv",
                        mime="text/csv",
                        help="Download rating forecasts from both models"
                    )

                with col2:
                    # Combined price forecast CSV
                    combined_price = pd.DataFrame({
                        'date': chronos_price['date'].dt.date,
                        'historical_price': [df['current_price'].iloc[-1]] * len(chronos_price),
                        'chronos_forecast': chronos_price['price_forecast'],
                        'chronos_lower_80': chronos_price['price_lower_80'],
                        'chronos_upper_80': chronos_price['price_upper_80'],
                        'prophet_forecast': prophet_price['price_forecast'],
                        'prophet_lower_80': prophet_price['price_lower_80'],
                        'prophet_upper_80': prophet_price['price_upper_80'],
                    })

                    csv_price = combined_price.to_csv(index=False)
                    st.download_button(
                        label="💰 Price Forecasts",
                        data=csv_price,
                        file_name=f"iphone14_price_forecast_{forecast_horizon}days.csv",
                        mime="text/csv",
                        help="Download price forecasts from both models"
                    )

                with col3:
                    # Complete dataset (Historical + Forecast)
                    historical_data = df[['date', 'rating', 'current_price']].copy()
                    historical_data['data_type'] = 'historical'
                    historical_data['rating_forecast'] = historical_data['rating']
                    historical_data['price_forecast'] = historical_data['current_price']

                    # Append Chronos forecasts
                    forecast_data = pd.DataFrame({
                        'date': chronos_rating['date'],
                        'rating': None,
                        'current_price': None,
                        'data_type': 'forecast',
                        'rating_forecast': chronos_rating['rating_forecast'].round(2),
                        'price_forecast': chronos_price['price_forecast']
                    })

                    complete_data = pd.concat([historical_data, forecast_data], ignore_index=True)
                    complete_data['date'] = pd.to_datetime(complete_data['date']).dt.date

                    csv_complete = complete_data.to_csv(index=False)
                    st.download_button(
                        label="📦 Complete Dataset",
                        data=csv_complete,
                        file_name=f"iphone14_complete_data_with_forecast_{forecast_horizon}days.csv",
                        mime="text/csv",
                        help="Download historical + forecast data combined"
                    )

                st.success("✅ CSV files ready for download! Click the buttons above.")

        except Exception as e:
            st.error(f"Error during forecasting: {str(e)}")
            st.exception(e)

    # Model information
    with st.expander("ℹ️ About the Models"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **🔵 Chronos (Amazon)**
            - Pre-trained foundation model
            - Zero-shot forecasting (no training needed)
            - 8M parameters (Tiny variant)
            - Best for: Quick, accurate predictions
            - Works on: CPU (no GPU needed)
            """)

        with col2:
            st.markdown("""
            **🟢 Prophet (Facebook/Meta)**
            - Interpretable additive model
            - Decomposes trend + seasonality
            - Handles holidays and events
            - Best for: Understanding WHY ratings change
            - Works on: CPU (very fast)
            """)
