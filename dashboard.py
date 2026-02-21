"""
Amazon Sales Analytics Dashboard
Run with: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page config
st.set_page_config(
    page_title="Amazon Sales Analytics",
    page_icon="📊",
    layout="wide"
)

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('data/Amazon.csv')
    df.columns = df.columns.str.lower()
    df['orderdate'] = pd.to_datetime(df['orderdate'])
    return df

# Load
try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Title
st.title("📊 Amazon Sales Analytics Dashboard")
st.markdown("*Interactive analysis of 100,000 Amazon transactions (2020-2024)*")

# KPIs Row
st.markdown("---")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "💰 Total Revenue",
        f"${df['totalamount'].sum()/1e6:.1f}M",
        help="Total revenue across all transactions"
    )

with col2:
    st.metric(
        "📦 Total Orders",
        f"{len(df):,}",
        help="Total number of orders"
    )

with col3:
    st.metric(
        "💵 Avg Order Value",
        f"${df['totalamount'].mean():.0f}",
        help="Average value per order"
    )

with col4:
    st.metric(
        "👥 Unique Customers",
        f"{df['customerid'].nunique():,}",
        help="Number of unique customers"
    )

with col5:
    delivered_pct = (df['orderstatus'] == 'Delivered').mean() * 100
    st.metric(
        "✅ Delivery Rate",
        f"{delivered_pct:.1f}%",
        help="Percentage of successfully delivered orders"
    )

st.markdown("---")

# Charts Row 1
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("💰 Revenue by Category")
    cat_revenue = df.groupby('category')['totalamount'].sum().sort_values(ascending=True)
    fig1 = px.bar(
        x=cat_revenue.values,
        y=cat_revenue.index,
        orientation='h',
        color=cat_revenue.values,
        color_continuous_scale='Blues',
        labels={'x': 'Revenue ($)', 'y': 'Category'}
    )
    fig1.update_layout(height=350, coloraxis_showscale=False)
    st.plotly_chart(fig1, use_container_width=True)

with right_col:
    st.subheader("📋 Order Status Distribution")
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
    fig2.update_layout(height=350, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2))
    st.plotly_chart(fig2, use_container_width=True)

# Charts Row 2
left_col2, right_col2 = st.columns(2)

with left_col2:
    st.subheader("📈 Monthly Revenue Trend")
    df['month'] = df['orderdate'].dt.to_period('M').astype(str)
    monthly = df.groupby('month')['totalamount'].sum().reset_index()
    fig3 = px.line(
        monthly,
        x='month',
        y='totalamount',
        markers=True,
        labels={'month': 'Month', 'totalamount': 'Revenue ($)'}
    )
    fig3.update_layout(height=350, xaxis_tickangle=-45)
    st.plotly_chart(fig3, use_container_width=True)

with right_col2:
    st.subheader("💳 Payment Method Distribution")
    payment_counts = df['paymentmethod'].value_counts()
    fig4 = px.bar(
        x=payment_counts.index,
        y=payment_counts.values,
        color=payment_counts.values,
        color_continuous_scale='Viridis',
        labels={'x': 'Payment Method', 'y': 'Count'}
    )
    fig4.update_layout(height=350, xaxis_tickangle=-30, coloraxis_showscale=False)
    st.plotly_chart(fig4, use_container_width=True)

# Geographic Analysis
st.markdown("---")
st.subheader("🗺️ Geographic Analysis")

geo_col1, geo_col2 = st.columns(2)

with geo_col1:
    # Top states
    state_revenue = df.groupby('state')['totalamount'].sum().sort_values(ascending=False).head(10)
    fig5 = px.bar(
        x=state_revenue.index,
        y=state_revenue.values,
        color=state_revenue.values,
        color_continuous_scale='Greens',
        labels={'x': 'State', 'y': 'Revenue ($)'}
    )
    fig5.update_layout(height=300, coloraxis_showscale=False)
    st.plotly_chart(fig5, use_container_width=True)

with geo_col2:
    # Country distribution
    country_revenue = df.groupby('country')['totalamount'].sum().sort_values(ascending=False)
    fig6 = px.pie(
        values=country_revenue.values,
        names=country_revenue.index,
        hole=0.3
    )
    fig6.update_layout(height=300, showlegend=True)
    st.plotly_chart(fig6, use_container_width=True)

# Customer Analysis
st.markdown("---")
st.subheader("👥 Customer Insights")

customer_stats = df.groupby('customerid').agg({
    'totalamount': ['sum', 'mean', 'count']
}).round(2)
customer_stats.columns = ['lifetime_value', 'avg_order', 'order_count']

cust_col1, cust_col2, cust_col3 = st.columns(3)

with cust_col1:
    st.metric("Avg Customer LTV", f"${customer_stats['lifetime_value'].mean():,.0f}")
    
with cust_col2:
    st.metric("Avg Orders/Customer", f"{customer_stats['order_count'].mean():.1f}")
    
with cust_col3:
    top_20_pct = customer_stats['lifetime_value'].quantile(0.8)
    high_value_count = (customer_stats['lifetime_value'] >= top_20_pct).sum()
    st.metric("High-Value Customers", f"{high_value_count:,}")

# Filters
st.markdown("---")
st.subheader("🔍 Data Explorer")

filter_col1, filter_col2, filter_col3 = st.columns(3)

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

with filter_col3:
    date_range = st.date_input(
        "Date Range",
        value=[df['orderdate'].min(), df['orderdate'].max()],
        min_value=df['orderdate'].min(),
        max_value=df['orderdate'].max()
    )

# Apply filters
filtered_df = df[
    (df['category'].isin(selected_category) if selected_category else True) &
    (df['orderstatus'].isin(selected_status) if selected_status else True) &
    (df['orderdate'] >= pd.Timestamp(date_range[0])) &
    (df['orderdate'] <= pd.Timestamp(date_range[1]))
]

st.write(f"Showing {len(filtered_df):,} records")
st.dataframe(filtered_df.head(100), use_container_width=True)

# Download button
st.download_button(
    label="📥 Download Filtered Data as CSV",
    data=filtered_df.to_csv(index=False).encode('utf-8'),
    file_name='filtered_amazon_sales.csv',
    mime='text/csv'
)

# Footer
st.markdown("---")
st.markdown("*Dashboard created with Streamlit • Data: Amazon Sales Dataset (100K transactions)*")
