"""
Amazon Sales Analytics Dashboard
Run with: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')

# Page config
st.set_page_config(
    page_title="Amazon Sales Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main {padding: 0rem 1rem;}
    .stMetric {background-color: #f0f2f6; padding: 10px; border-radius: 10px;}
    .st-emotion-cache-1kyxreq {justify-content: center;}
</style>
""", unsafe_allow_html=True)

# Title
st.title("📊 Amazon Sales Analytics Dashboard")
st.markdown("*Interactive analysis of Amazon transactions*")

# Load data with error handling
@st.cache_data(ttl=3600)
def load_data():
    """Load and cache data from CSV"""
    try:
        df = pd.read_csv('data/Amazon.csv')
        df.columns = df.columns.str.lower()
        df['orderdate'] = pd.to_datetime(df['orderdate'])
        return df, None
    except FileNotFoundError:
        return None, "❌ Data file not found: data/Amazon.csv"
    except Exception as e:
        return None, f"❌ Error loading data: {str(e)}"

# Load data
df, error = load_data()

if error:
    st.error(error)
    st.info("💡 Make sure you have the data/Amazon.csv file in place.")
    st.stop()

# Success message (hidden after first load)
# st.success(f"✅ Loaded {len(df):,} transactions")

# KPIs Section
st.markdown("---")
kpi_cols = st.columns(5)

with kpi_cols[0]:
    total_revenue = df['totalamount'].sum()
    st.metric(
        "💰 Total Revenue",
        f"${total_revenue/1e6:.1f}M",
        help="Total revenue across all transactions"
    )

with kpi_cols[1]:
    st.metric(
        "📦 Total Orders",
        f"{len(df):,}",
        help="Total number of orders"
    )

with kpi_cols[2]:
    avg_order = df['totalamount'].mean()
    st.metric(
        "💵 Avg Order",
        f"${avg_order:.0f}",
        help="Average order value"
    )

with kpi_cols[3]:
    unique_customers = df['customerid'].nunique()
    st.metric(
        "👥 Customers",
        f"{unique_customers:,}",
        help="Unique customers"
    )

with kpi_cols[4]:
    delivered_rate = (df['orderstatus'] == 'Delivered').mean() * 100
    st.metric(
        "✅ Delivery Rate",
        f"{delivered_rate:.0f}%",
        help="Percentage delivered"
    )

st.markdown("---")

# Charts Section - Row 1
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("💰 Revenue by Category")
    try:
        cat_revenue = df.groupby('category')['totalamount'].sum().sort_values(ascending=True)
        fig1 = px.bar(
            x=cat_revenue.values,
            y=cat_revenue.index,
            orientation='h',
            color=cat_revenue.values,
            color_continuous_scale='Blues',
            labels={'x': 'Revenue ($)', 'y': ''}
        )
        fig1.update_layout(height=350, coloraxis_showscale=False, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig1, use_container_width=True)
    except Exception as e:
        st.error(f"Chart error: {e}")

with right_col:
    st.subheader("📋 Order Status")
    try:
        status_counts = df['orderstatus'].value_counts()
        colors = {'Delivered': '#2ecc71', 'Shipped': '#3498db', 
                  'Pending': '#f39c12', 'Returned': '#e74c3c', 'Cancelled': '#9b59b6'}
        fig2 = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            color=status_counts.index,
            color_discrete_map=colors,
            hole=0.4
        )
        fig2.update_layout(height=350, showlegend=True, 
                          legend=dict(orientation="h", yanchor="bottom", y=-0.15),
                          margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig2, use_container_width=True)
    except Exception as e:
        st.error(f"Chart error: {e}")

# Charts Section - Row 2
left_col2, right_col2 = st.columns(2)

with left_col2:
    st.subheader("📈 Monthly Trend")
    try:
        df['month'] = df['orderdate'].dt.to_period('M').astype(str)
        monthly = df.groupby('month')['totalamount'].sum().reset_index()
        fig3 = px.line(
            monthly, x='month', y='totalamount',
            markers=True,
            labels={'month': '', 'totalamount': 'Revenue ($)'}
        )
        fig3.update_layout(height=350, xaxis_tickangle=-45, 
                          margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig3, use_container_width=True)
    except Exception as e:
        st.error(f"Chart error: {e}")

with right_col2:
    st.subheader("💳 Payment Methods")
    try:
        payment_counts = df['paymentmethod'].value_counts()
        fig4 = px.bar(
            x=payment_counts.index,
            y=payment_counts.values,
            color=payment_counts.values,
            color_continuous_scale='Viridis',
            labels={'x': '', 'y': 'Count'}
        )
        fig4.update_layout(height=350, xaxis_tickangle=-30, 
                          coloraxis_showscale=False,
                          margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig4, use_container_width=True)
    except Exception as e:
        st.error(f"Chart error: {e}")

# Geographic Analysis
st.markdown("---")
st.subheader("🗺️ Geographic Analysis")

geo_col1, geo_col2 = st.columns(2)

with geo_col1:
    try:
        state_revenue = df.groupby('state')['totalamount'].sum().sort_values(ascending=False).head(10)
        fig5 = px.bar(
            x=state_revenue.index,
            y=state_revenue.values,
            color=state_revenue.values,
            color_continuous_scale='Greens',
            labels={'x': 'State', 'y': 'Revenue ($)'}
        )
        fig5.update_layout(height=300, coloraxis_showscale=False,
                          margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig5, use_container_width=True)
    except Exception as e:
        st.error(f"Chart error: {e}")

with geo_col2:
    try:
        country_revenue = df.groupby('country')['totalamount'].sum().sort_values(ascending=False)
        fig6 = px.pie(
            values=country_revenue.values,
            names=country_revenue.index,
            hole=0.3
        )
        fig6.update_layout(height=300, showlegend=True,
                          margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig6, use_container_width=True)
    except Exception as e:
        st.error(f"Chart error: {e}")

# Customer Analysis
st.markdown("---")
st.subheader("👥 Customer Insights")

try:
    customer_stats = df.groupby('customerid').agg({
        'totalamount': ['sum', 'mean', 'count']
    }).round(2)
    customer_stats.columns = ['lifetime_value', 'avg_order', 'order_count']
    
    cust_cols = st.columns(4)
    with cust_cols[0]:
        st.metric("Avg LTV", f"${customer_stats['lifetime_value'].mean():,.0f}")
    with cust_cols[1]:
        st.metric("Avg Orders/Customer", f"{customer_stats['order_count'].mean():.1f}")
    with cust_cols[2]:
        high_value = (customer_stats['lifetime_value'] >= customer_stats['lifetime_value'].quantile(0.8)).sum()
        st.metric("High-Value Customers", f"{high_value:,}")
    with cust_cols[3]:
        repeat_customers = (customer_stats['order_count'] > 1).sum()
        st.metric("Repeat Customers", f"{repeat_customers:,}")
except Exception as e:
    st.error(f"Customer analysis error: {e}")

# Data Explorer
st.markdown("---")
with st.expander("🔍 Data Explorer (Click to expand)"):
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        selected_category = st.multiselect(
            "Category",
            options=df['category'].unique(),
            default=df['category'].unique()[:3]
        )
    
    with filter_col2:
        selected_status = st.multiselect(
            "Order Status",
            options=df['orderstatus'].unique(),
            default=['Delivered']
        )
    
    # Apply filters
    filtered_df = df[
        (df['category'].isin(selected_category) if selected_category else True) &
        (df['orderstatus'].isin(selected_status) if selected_status else True)
    ]
    
    st.write(f"Showing {len(filtered_df):,} records")
    st.dataframe(filtered_df.head(100), use_container_width=True)
    
    # Download button
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name='filtered_data.csv',
        mime='text/csv'
    )

# Footer
st.markdown("---")
st.caption("*Dashboard created with Streamlit • Data: Amazon Sales Dataset*")
