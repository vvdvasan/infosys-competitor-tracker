"""
Cross-platform price comparison dashboard (Buyhatke-style).

Features:
- Price history visualization
- Amazon vs Flipkart comparison
- Buy recommendations
- Price drop alerts
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from price_tracker.price_history_manager import PriceHistoryManager

# Page configuration
st.set_page_config(
    page_title="Price Comparison - iPhone 14",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Buyhatke-style appearance
st.markdown("""
<style>
    .price-card {
        padding: 20px;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        margin: 10px 0;
    }
    .recommendation-box {
        padding: 30px;
        border-radius: 15px;
        background: #f8f9fa;
        border: 2px solid #e9ecef;
        margin: 20px 0;
    }
    .buy-now {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        font-weight: bold;
    }
    .wait {
        background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%);
        color: white;
        font-weight: bold;
    }
    .good-deal {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize price history manager
@st.cache_resource
def get_price_manager():
    return PriceHistoryManager()

price_manager = get_price_manager()

# Title and header
st.title("📊 Cross-Platform Price Comparison")
st.subheader("iPhone 14 (128GB) - Amazon vs Flipkart")

# Sidebar - Product selection
with st.sidebar:
    st.header("⚙️ Settings")

    product_id = st.selectbox(
        "Product",
        ["iphone14_128gb", "iphone14_256gb"],
        index=0
    )

    st.markdown("---")
    st.markdown("### 📈 Time Range")
    time_range = st.radio(
        "Select Range",
        ["7 Days", "30 Days", "90 Days", "All Time"],
        index=2
    )

    days_map = {
        "7 Days": 7,
        "30 Days": 30,
        "90 Days": 90,
        "All Time": None
    }
    selected_days = days_map[time_range]

    st.markdown("---")
    st.markdown("### 🔔 Price Alerts")
    alert_enabled = st.checkbox("Enable price drop alerts")
    if alert_enabled:
        alert_price = st.number_input(
            "Alert me when price drops to:",
            min_value=40000,
            max_value=80000,
            value=55000,
            step=1000
        )

# Main content
tab1, tab2, tab3 = st.tabs(["📊 Price Comparison", "📈 Price History", "🎯 Buy Recommendations"])

# ====================================
# TAB 1: PRICE COMPARISON
# ====================================
with tab1:
    st.markdown("## Amazon vs Flipkart - Live Comparison")

    # Get comparison data
    comparison = price_manager.compare_platforms(product_id)

    if not comparison["platforms"]:
        st.warning("No price data available. Please run data collection first.")
    else:
        # Platform comparison cards
        col1, col2, col3 = st.columns(3)

        # Amazon stats
        amazon_data = comparison["platforms"].get("amazon", {})
        flipkart_data = comparison["platforms"].get("flipkart", {})

        with col1:
            st.markdown("### 🟠 Amazon")
            if amazon_data.get("current_price"):
                st.metric(
                    "Current Price",
                    f"Rs.{amazon_data['current_price']:,.0f}",
                    delta=f"{amazon_data['deal_score']:.0f}/100 Deal Score"
                )
                st.metric("Lowest Ever", f"Rs.{amazon_data.get('lowest_price', 0):,.0f}")
                st.metric("Highest Ever", f"Rs.{amazon_data.get('highest_price', 0):,.0f}")

                # Recommendation badge
                rec = amazon_data.get("recommendation", "").replace("_", " ").upper()
                if "BUY" in rec:
                    st.success(f"✅ {rec}")
                elif "WAIT" in rec:
                    st.error(f"⏳ {rec}")
                else:
                    st.info(f"💭 {rec}")
            else:
                st.info("No Amazon data available")

        with col2:
            st.markdown("### 🟦 Flipkart")
            if flipkart_data.get("current_price"):
                st.metric(
                    "Current Price",
                    f"Rs.{flipkart_data['current_price']:,.0f}",
                    delta=f"{flipkart_data['deal_score']:.0f}/100 Deal Score"
                )
                st.metric("Lowest Ever", f"Rs.{flipkart_data.get('lowest_price', 0):,.0f}")
                st.metric("Highest Ever", f"Rs.{flipkart_data.get('highest_price', 0):,.0f}")

                # Recommendation badge
                rec = flipkart_data.get("recommendation", "").replace("_", " ").upper()
                if "BUY" in rec:
                    st.success(f"✅ {rec}")
                elif "WAIT" in rec:
                    st.error(f"⏳ {rec}")
                else:
                    st.info(f"💭 {rec}")
            else:
                st.info("No Flipkart data available")

        with col3:
            st.markdown("### 🏆 Best Deal")
            best = comparison.get("best_deal", "").upper()
            diff = comparison.get("price_difference", 0)

            if best:
                st.success(f"### {best}")
                st.metric("Price Difference", f"Rs.{diff:,.0f}")

                if best == "AMAZON":
                    current = amazon_data.get("current_price", 0)
                else:
                    current = flipkart_data.get("current_price", 0)

                st.metric("Best Price", f"Rs.{current:,.0f}")

                # Calculate savings
                other_price = flipkart_data.get("current_price", 0) if best == "AMAZON" else amazon_data.get("current_price", 0)
                if other_price and current:
                    savings_pct = ((other_price - current) / other_price) * 100
                    st.metric("You Save", f"{savings_pct:.1f}%")

# ====================================
# TAB 2: PRICE HISTORY
# ====================================
with tab2:
    st.markdown("## 📈 Price History Visualization")

    # Platform selection for history
    platform_view = st.radio(
        "Select Platform",
        ["Both", "Amazon", "Flipkart"],
        horizontal=True
    )

    # Create price history chart
    fig = go.Figure()

    platforms_to_show = []
    if platform_view == "Both":
        platforms_to_show = ["amazon", "flipkart"]
    else:
        platforms_to_show = [platform_view.lower()]

    for platform in platforms_to_show:
        history_df = price_manager.get_price_history_dataframe(
            product_id, platform, days=selected_days
        )

        if not history_df.empty:
            color = "#FF9900" if platform == "amazon" else "#047BD5"
            fig.add_trace(go.Scatter(
                x=history_df['timestamp'],
                y=history_df['price'],
                mode='lines+markers',
                name=platform.capitalize(),
                line=dict(color=color, width=3),
                marker=dict(size=6)
            ))

    # Update layout
    fig.update_layout(
        title=f"Price History - Last {time_range}",
        xaxis_title="Date",
        yaxis_title="Price (Rs.)",
        hovermode='x unified',
        template="plotly_white",
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # Price statistics table
    st.markdown("### 📊 Price Statistics")

    stats_data = []
    for platform in ["amazon", "flipkart"]:
        stats = price_manager.get_price_statistics(product_id, platform, days=selected_days)
        if stats.get("current_price"):
            stats_data.append({
                "Platform": platform.capitalize(),
                "Current": f"Rs.{stats['current_price']:,.0f}",
                "Highest": f"Rs.{stats['highest_price']:,.0f}",
                "Lowest": f"Rs.{stats['lowest_price']:,.0f}",
                "Average": f"Rs.{stats['average_price']:,.0f}",
                "Records": stats['total_records']
            })

    if stats_data:
        st.dataframe(pd.DataFrame(stats_data), use_container_width=True)

# ====================================
# TAB 3: BUY RECOMMENDATIONS
# ====================================
with tab3:
    st.markdown("## 🎯 Should You Buy This Now?")

    # Time period selector (like Buyhatke)
    st.markdown("### Select based on how soon you need the item")
    time_selector = st.radio(
        "Time Period",
        ["2-3 Days", "1 Week", "1 Month"],
        horizontal=True
    )

    days_for_rec = {"2-3 Days": 3, "1 Week": 7, "1 Month": 30}
    rec_days = days_for_rec[time_selector]

    st.markdown("---")

    # Get recommendations for both platforms
    col1, col2 = st.columns(2)

    for idx, platform in enumerate(["amazon", "flipkart"]):
        recommendation = price_manager.get_buy_recommendation(
            product_id, platform, days=rec_days
        )

        with col1 if idx == 0 else col2:
            st.markdown(f"### {platform.capitalize()}")

            action = recommendation.get("action", "insufficient_data")
            confidence = recommendation.get("confidence", 0)
            deal_score = recommendation.get("deal_score", 0)
            reason = recommendation.get("reason", "Not enough data")

            # Deal score gauge
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = deal_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Deal Score"},
                delta = {'reference': 50},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps' : [
                        {'range': [0, 30], 'color': "lightcoral"},
                        {'range': [30, 70], 'color': "lightyellow"},
                        {'range': [70, 100], 'color': "lightgreen"}],
                    'threshold' : {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 80}}))

            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)

            # Recommendation
            if "buy" in action.lower():
                st.success(f"✅ **{action.replace('_', ' ').upper()}**")
            elif "wait" in action.lower():
                st.error(f"⏳ **{action.replace('_', ' ').upper()}**")
            else:
                st.info(f"💭 **{action.replace('_', ' ').upper()}**")

            st.markdown(f"**Confidence:** {confidence}%")
            st.markdown(f"**Reason:** {reason}")

            # Savings information
            savings = recommendation.get("savings", {})
            if savings.get("vs_highest"):
                st.markdown("### 💰 Potential Savings")
                st.write(f"vs Highest: Rs.{savings['vs_highest']:,}")
                st.write(f"vs Average: Rs.{savings['vs_average']:,}")
                st.write(f"Optimal Price: Rs.{recommendation.get('optimal_price_point', 0):,}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>Price data updated automatically | Powered by AI Forecasting</p>
    <p>Similar to Buyhatke/Pricehatke but with custom AI predictions!</p>
</div>
""", unsafe_allow_html=True)
