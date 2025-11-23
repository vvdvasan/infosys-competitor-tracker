"""Streamlit dashboard for sentiment analysis visualization."""

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

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentiment_analysis.config import Config
from sentiment_analysis.database.db_manager import DatabaseManager
from sentiment_analysis.api.groq_client import GroqSentimentAnalyzer
from sentiment_analysis.scraper.amazon_scraper import AmazonScraper

# Page configuration
st.set_page_config(
    page_title="E-commerce Competitor Sentiment Tracker",
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
st.title("🛍️ Real-Time Competitor Strategy Tracker")
st.markdown("### E-commerce Sentiment Analysis Dashboard")
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

# Main content area
tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "🎯 Sentiment Analysis", "📦 Products", "📝 Reviews"])

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

    # Load products
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
        st.dataframe(
            df_products,
            use_container_width=True,
            hide_index=True
        )

        # Price comparison
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
