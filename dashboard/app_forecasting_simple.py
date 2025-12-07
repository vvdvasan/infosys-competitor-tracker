"""Simple Streamlit dashboard with Prophet forecasting only."""

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
from forecasting.prophet_forecaster import ProphetForecaster
from forecasting.utils import load_timeseries_data, generate_sample_data

# Page configuration
st.set_page_config(
    page_title="E-commerce Intelligence Dashboard",
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
                    product_data = scraper.scrape_product(product_url)
                    if product_data:
                        db_manager.insert_product(product_data)
                        st.success(f"✅ Scraped: {product_data.get('Product_Name', 'Unknown')}")

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
            pending_reviews = db_manager.get_unanalyzed_reviews(limit=20)

            if pending_reviews:
                progress_bar = st.progress(0)
                status_text = st.empty()

                results = []
                for i, review in enumerate(pending_reviews):
                    status_text.text(f"Analyzing review {i+1}/{len(pending_reviews)}")

                    sentiment_result = groq_analyzer.analyze_sentiment(review['text'])
                    sentiment_result['review_id'] = review['review_id']
                    results.append(sentiment_result)

                    progress_bar.progress((i + 1) / len(pending_reviews))

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

# Main content area
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Overview",
    "🎯 Sentiment Analysis",
    "📦 Products",
    "📝 Reviews",
    "🔮 AI Forecasting"
])

with tab1:
    stats = db_manager.get_sentiment_statistics()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Products", stats['overall']['total_products'] or 0)

    with col2:
        st.metric("Total Reviews", stats['overall']['total_reviews'] or 0)

    with col3:
        st.metric("Avg Rating", f"{stats['overall']['avg_rating']:.1f}" if stats['overall']['avg_rating'] else "N/A")

    with col4:
        total_analyzed = sum(stats['sentiment_distribution'].values())
        st.metric("Reviews Analyzed", total_analyzed)

    st.markdown("---")

    if stats['sentiment_distribution']:
        col1, col2 = st.columns(2)

        with col1:
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

with tab3:
    st.header("📦 Product Information")

    with sqlite3.connect(db_manager.db_path) as conn:
        query = """
            SELECT
                product_name as 'Product Name',
                brand as 'Brand',
                price as 'Price (₹)',
                mrp as 'MRP (₹)',
                discount as 'Discount',
                rating as 'Rating',
                review_count as 'Reviews',
                stock_status as 'Stock Status',
                scraped_at as 'Last Updated'
            FROM products
            ORDER BY updated_at DESC
        """
        df_products = pd.read_sql_query(query, conn)

    if not df_products.empty:
        st.dataframe(df_products, use_container_width=True, hide_index=True)

        if len(df_products) > 1:
            st.subheader("💰 Price Comparison")
            fig_price = px.bar(
                df_products,
                x='Product Name',
                y=['Price (₹)', 'MRP (₹)'],
                title="Product Prices Comparison",
                barmode='group'
            )
            st.plotly_chart(fig_price, use_container_width=True)
    else:
        st.info("No products scraped yet. Use the sidebar to add products.")

with tab4:
    st.header("📝 Review Analysis")

    sentiment_filter = st.selectbox(
        "Filter by Sentiment",
        ["All", "POSITIVE", "NEGATIVE", "NEUTRAL"]
    )

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

# ============================================================================
# 🔮 FORECASTING TAB - PROPHET ONLY (SIMPLE & RELIABLE)
# ============================================================================
with tab5:
    st.header("🔮 AI-Powered Price & Rating Forecasting")
    st.markdown("**Predict iPhone 14 trends using Facebook's Prophet AI model**")
    st.markdown("---")

    # Configuration
    col1, col2 = st.columns(2)

    with col1:
        forecast_horizon = st.selectbox(
            "Forecast Horizon",
            [7, 14, 30],
            index=2,
            help="Number of days to forecast"
        )

    with col2:
        use_sample_data = st.checkbox(
            "Use Sample Data",
            value=True,
            help="Generate demo iPhone 14 data"
        )

    # File upload
    uploaded_file = None
    if not use_sample_data:
        uploaded_file = st.file_uploader(
            "Upload Time Series CSV",
            type=['csv'],
            help="CSV with columns: date, rating, current_price"
        )

    # Generate forecast button
    if st.button("🚀 Generate Forecast", type="primary"):
        try:
            with st.spinner("Loading data..."):
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
                    st.error("Please upload a CSV or use sample data")
                    st.stop()

            # Show data info
            st.success(f"✓ Loaded {len(df)} days ({df['date'].min().date()} to {df['date'].max().date()})")

            with st.expander("📊 Data Preview"):
                st.dataframe(df.head(20), use_container_width=True)
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Avg Rating", f"{df['rating'].mean():.2f}")
                with col2:
                    st.metric("Avg Price", f"₹{df['current_price'].mean():,.0f}")
                with col3:
                    st.metric("Data Points", len(df))

            st.markdown("---")

            # Run Prophet forecasting
            with st.spinner("Running Prophet AI model..."):
                prophet_forecaster = ProphetForecaster()

                # Forecast both ratings and prices
                rating_forecast, _, price_forecast, _ = prophet_forecaster.forecast_both(
                    df,
                    forecast_horizon=forecast_horizon,
                    include_history=False
                )

            # RATING FORECAST CHART
            st.subheader("⭐ Rating Forecast")

            fig_rating = go.Figure()

            # Historical
            fig_rating.add_trace(go.Scatter(
                x=df['date'],
                y=df['rating'],
                mode='lines',
                name='Historical',
                line=dict(color='gray', width=2)
            ))

            # Prophet forecast
            fig_rating.add_trace(go.Scatter(
                x=rating_forecast['date'],
                y=rating_forecast['rating_forecast'],
                mode='lines',
                name='Prophet Forecast',
                line=dict(color='#00CC88', width=3, dash='dot')
            ))

            # Confidence interval
            fig_rating.add_trace(go.Scatter(
                x=rating_forecast['date'].tolist() + rating_forecast['date'].tolist()[::-1],
                y=rating_forecast['rating_upper_80'].tolist() + rating_forecast['rating_lower_80'].tolist()[::-1],
                fill='toself',
                fillcolor='rgba(0, 204, 136, 0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                name='80% Confidence',
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

            # PRICE FORECAST CHART
            st.subheader("💰 Price Forecast")

            fig_price = go.Figure()

            # Historical
            fig_price.add_trace(go.Scatter(
                x=df['date'],
                y=df['current_price'],
                mode='lines',
                name='Historical',
                line=dict(color='gray', width=2)
            ))

            # Prophet forecast
            fig_price.add_trace(go.Scatter(
                x=price_forecast['date'],
                y=price_forecast['price_forecast'],
                mode='lines',
                name='Prophet Forecast',
                line=dict(color='#00CC88', width=3, dash='dot')
            ))

            # Confidence interval
            fig_price.add_trace(go.Scatter(
                x=price_forecast['date'].tolist() + price_forecast['date'].tolist()[::-1],
                y=price_forecast['price_upper_80'].tolist() + price_forecast['price_lower_80'].tolist()[::-1],
                fill='toself',
                fillcolor='rgba(0, 204, 136, 0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                name='80% Confidence',
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

            # FORECAST TABLES
            st.markdown("---")
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📅 Rating Forecasts")
                forecast_table_rating = pd.DataFrame({
                    'Date': rating_forecast['date'].dt.date,
                    'Rating': rating_forecast['rating_forecast'].round(2),
                    'Lower Bound': rating_forecast['rating_lower_80'].round(2),
                    'Upper Bound': rating_forecast['rating_upper_80'].round(2)
                })
                st.dataframe(forecast_table_rating, use_container_width=True, height=300)

            with col2:
                st.subheader("📅 Price Forecasts")
                forecast_table_price = pd.DataFrame({
                    'Date': price_forecast['date'].dt.date,
                    'Price (₹)': price_forecast['price_forecast'],
                    'Lower Bound': price_forecast['price_lower_80'],
                    'Upper Bound': price_forecast['price_upper_80']
                })
                st.dataframe(forecast_table_price, use_container_width=True, height=300)

            # KEY INSIGHTS
            st.markdown("---")
            st.subheader("🎯 Key Insights")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                avg_forecast_rating = rating_forecast['rating_forecast'].mean()
                st.metric(
                    "Avg Forecast Rating",
                    f"{avg_forecast_rating:.2f}",
                    delta=f"{avg_forecast_rating - df['rating'].mean():.2f}"
                )

            with col2:
                trend_rating = "📈 Up" if rating_forecast['rating_forecast'].iloc[-1] > rating_forecast['rating_forecast'].iloc[0] else "📉 Down"
                st.metric(
                    "Rating Trend",
                    trend_rating
                )

            with col3:
                avg_forecast_price = price_forecast['price_forecast'].mean()
                st.metric(
                    "Avg Forecast Price",
                    f"₹{avg_forecast_price:,.0f}",
                    delta=f"₹{avg_forecast_price - df['current_price'].mean():,.0f}"
                )

            with col4:
                trend_price = "📈 Up" if price_forecast['price_forecast'].iloc[-1] > price_forecast['price_forecast'].iloc[0] else "📉 Down"
                st.metric(
                    "Price Trend",
                    trend_price
                )

        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.exception(e)

    # Model info
    with st.expander("ℹ️ About Prophet AI"):
        st.markdown("""
        **🟢 Prophet (Facebook/Meta)**
        - Industry-standard forecasting model
        - Decomposes trends into: trend + seasonality + holidays
        - Accounts for Indian e-commerce events (Big Billion Days, Diwali)
        - Provides 80% confidence intervals
        - Fast & reliable (runs in 10-20 seconds)

        **What it predicts:**
        - iPhone 14 ratings (4.2 to 4.8)
        - iPhone 14 prices (₹)
        - Confidence bounds for uncertainty

        **Indian holidays included:**
        - Big Billion Days (Sept/Oct)
        - Diwali (Oct/Nov)
        - Republic Day Sale (Jan 26)
        - Independence Day Sale (Aug 15)
        """)
