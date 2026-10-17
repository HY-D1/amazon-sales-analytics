"""Read-only, SQL-backed portfolio dashboard. Run: streamlit run dashboard.py."""

from datetime import date
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import connect_db, get_dashboard_data, query


PALETTE = ["#236B82", "#D88146", "#648A66", "#9A739A", "#C5AB65"]
STATUS_COLORS = dict(zip(["Delivered", "Returned", "Shipped", "Cancelled", "Pending"], PALETTE))
EXPORT_COLUMNS = [
    "orderid", "orderdate", "category", "quantity", "country", "orderstatus",
    "paymentmethod", "unitprice_cents", "discount", "merchandise_cents",
    "tax_cents", "shippingcost_cents", "totalamount_cents", "delivered_revenue_cents",
]


def money(cents):
    """Preserve undefined means instead of displaying a misleading zero."""
    return "—" if cents is None else f"${cents / 100:,.2f}"


def percentage(value):
    return "—" if value is None else f"{value:.1%}"


def style_chart(figure, height=310):
    figure.update_layout(
        height=height, font={"family": "Arial, sans-serif", "color": "#233B4B", "size": 12},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 0, "r": 10, "t": 10, "b": 10}, coloraxis_showscale=False,
        legend_title_text="",
    )
    figure.update_xaxes(showgrid=False)
    figure.update_yaxes(gridcolor="#E8EDEE", zeroline=False)
    return figure


def show_database_error(error):
    st.error("The analytics database is missing, outdated, or cannot be read.")
    st.info("Build the validated SQLite database from the project folder, then reload this page.")
    st.code("python -m src.data_loader", language="bash")
    st.caption(f"Database check: {error}")


def render_overview(data):
    kpis = data["kpis"]
    columns = st.columns(3)
    columns[0].metric(
        "Delivered revenue", money(kpis["delivered_revenue_cents"]),
        help="Delivered only: quantity × unit price × (1 − discount), rounded to cents per order. Excludes tax and shipping.",
    )
    columns[1].metric(
        "Orders", f'{int(kpis["total_orders"]):,}',
        help="Distinct canonical order IDs in the selected order-date cohort; all statuses.",
    )
    columns[2].metric(
        "Delivered AOV", money(kpis["delivered_aov_cents"]),
        help="Delivered merchandise revenue / delivered orders. Undefined if no delivered orders.",
    )
    secondary = st.columns(2)
    secondary[0].metric(
        "Returned order share", percentage(kpis["returned_share"]),
        help="Returned orders / all selected orders. Current status, not return events during the date range.",
    )
    secondary[1].metric(
        "All-order bookings", money(kpis["booked_total_cents"]),
        help="Supplied TotalAmount for all statuses, including tax and shipping. A descriptive measure, not realized revenue.",
    )
    st.caption(
        f'{int(kpis["delivered_orders"]):,} delivered · {int(kpis["returned_orders"]):,} returned · '
        f'{int(kpis["unique_customers"]):,} distinct customer IDs in this selection. '
        "USD is a demonstration assumption, not a verified source currency."
    )
    if kpis["total_orders"] == 0:
        st.info("No orders match these filters. Select at least one category and country, or widen the date range.")
        return

    st.divider()
    left, right = st.columns([1.4, 1])
    monthly = data["monthly"].copy()
    monthly["revenue_usd"] = monthly["delivered_revenue_cents"] / 100
    with left:
        st.subheader("Revenue over time")
        st.caption("Delivered merchandise revenue by order month")
        figure = px.line(monthly, x="month", y="revenue_usd", markers=True,
                         color_discrete_sequence=PALETTE, labels={"month": "Order month", "revenue_usd": "USD"})
        figure.update_traces(line={"width": 3}, marker={"size": 7})
        st.plotly_chart(style_chart(figure), use_container_width=True)

    category = data["category"].sort_values("delivered_revenue_cents").copy()
    category["revenue_usd"] = category["delivered_revenue_cents"] / 100
    with right:
        st.subheader("Category contribution")
        st.caption("Same revenue definition, grouped by selected category")
        figure = px.bar(category, x="revenue_usd", y="category", orientation="h",
                        color_discrete_sequence=PALETTE, labels={"category": "", "revenue_usd": "USD"})
        st.plotly_chart(style_chart(figure), use_container_width=True)

    left, right = st.columns([1, 1.4])
    with left:
        st.subheader("Order status mix")
        st.caption("Order counts, including statuses excluded from revenue")
        figure = px.bar(data["status"], x="orderstatus", y="orders", color="orderstatus",
                        color_discrete_map=STATUS_COLORS, labels={"orderstatus": "", "orders": "Orders"})
        figure.update_layout(showlegend=False)
        st.plotly_chart(style_chart(figure, 280), use_container_width=True)
    with right:
        st.subheader("What the selected cohort shows")
        top = category.iloc[-1]
        revenue = kpis["delivered_revenue_cents"]
        if revenue > 0:
            st.markdown(f'**{top["category"]}** contributes **{top["delivered_revenue_cents"] / revenue:.1%}** '
                        f'of delivered merchandise revenue ({money(top["delivered_revenue_cents"])}).')
        else:
            st.markdown("This selection has no positive delivered merchandise revenue.")
        st.markdown(f'**{percentage(kpis["returned_share"])}** of selected orders currently have Returned status. '
                    "Compare category-level counts before prioritizing a follow-up investigation.")
        st.caption("These observations are computed from the current filters. This cross-sectional order ledger "
                   "cannot establish causes, a return-event timeline, or the effect of any intervention.")
        st.markdown("**Next analysis question**")
        st.write("Which categories combine material delivered revenue with a high returned order share, "
                 "and is the order count large enough to justify investigating?")


def render_explorer(data):
    st.subheader("Explore the selected orders")
    st.caption("One canonical row per order. Every chart, KPI and download uses the same filters. "
               "Customer names and identifiers are omitted from this export. Amounts use integer cents.")
    orders = data["orders"][EXPORT_COLUMNS].copy()
    st.dataframe(orders.head(200), use_container_width=True, hide_index=True)
    st.caption(f"Preview: up to 200 of {len(orders):,} selected orders. Download includes every selected order.")
    st.download_button("Download selected orders (CSV)", data=orders.to_csv(index=False).encode("utf-8"),
                       file_name="retail_selected_orders.csv", mime="text/csv")


def render_definitions(data):
    st.subheader("A small metric contract")
    st.markdown("""
| Measure | Definition |
| --- | --- |
| Delivered merchandise revenue | Discounted merchandise amounts for **Delivered** orders; excludes tax and shipping. |
| Orders | Distinct canonical order IDs across all selected statuses. |
| Delivered average order value | Delivered merchandise revenue divided by delivered order count. |
| Returned order share | Returned orders divided by **all orders** in the selected cohort. |
| All-order bookings | Supplied `TotalAmount` summed across **all statuses**, including tax and shipping; distinct from revenue. |

Filters define a cohort by **order date**, category and country. Returned is a current status; it does not supply a return date. An empty category or country selection means **no orders**. A rate or mean with a zero denominator is displayed as **—**.

The supported input grain is **one row per order**, not order lines. Exact duplicate source rows are removed during ingestion; conflicting duplicate order IDs are rejected. The dashboard opens the validated database in read-only mode and never rebuilds it.
""")
    with st.expander("Source and validation notes"):
        st.write("No real company performance or individual customer behavior is inferred. "
                 "The metadata below describes the imported source, not only the selected cohort.")
        st.markdown("[Repository README and reproducible setup](https://github.com/HY-D1/amazon-sales-analytics/blob/portfolio-v2/README.md) "
                    "· [Metric contract](https://github.com/HY-D1/amazon-sales-analytics/blob/portfolio-v2/docs/METRICS.md) "
                    "· [Processing trace](https://github.com/HY-D1/amazon-sales-analytics/blob/portfolio-v2/docs/PROCESSING_TRACE.md) "
                    "· [Source and license audit](https://github.com/HY-D1/amazon-sales-analytics/blob/portfolio-v2/docs/DATA_AUDIT.md)")
        st.json({"metadata": data["metadata"], "quality": data["quality"]})


def main():
    st.set_page_config(page_title="Amazon Sales Analytics V2 | Portfolio", page_icon="📊",
                       layout="wide", initial_sidebar_state="expanded")
    st.markdown("""<style>
    .stApp {background: #FAFBF8; color: #193549;}
    section[data-testid="stSidebar"] {background: #EDF2F1;}
    [data-testid="stMetric"] {background: #FFFFFF; padding: 16px 14px; border-radius: 10px; border: 1px solid #E1E8E6;}
    [data-testid="stMetricLabel"] {font-size: 0.82rem; color: #526675;}
    [data-testid="stMetricValue"] {font-size: 1.65rem; color: #193549;}
    @media (max-width: 900px) {
      [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {flex-wrap: wrap;}
      [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > div {
        flex: 1 1 100% !important; width: 100% !important; min-width: 0 !important;
      }
      [data-testid="stMetricValue"] {font-size: 1.5rem;}
    }
    .eyebrow {font-size: 0.72rem; font-weight: 700; letter-spacing: 0.15em; color: #236B82; margin-bottom: 0.4rem;}
    h1 {letter-spacing: -0.04em; padding-top: 0;}
    h3 {font-size: 1.2rem; letter-spacing: -0.02em;}
    </style>""", unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">SQL · PYTHON · RETAIL ANALYTICS</div>', unsafe_allow_html=True)
    st.title("Amazon Sales Analytics V2")
    st.markdown("An auditable retail analytics portfolio: from validated orders to business questions.")
    source_note = st.empty()

    try:
        connection = connect_db()
    except (OSError, ValueError, sqlite3.Error) as error:
        show_database_error(error)
        return
    try:
        limits = query("SELECT MIN(orderdate) AS first_date, MAX(orderdate) AS last_date FROM sales", connection).iloc[0]
        if pd.isna(limits["first_date"]):
            st.error("The database contains no canonical orders. Rebuild it with a non-empty, validated source.")
            return
        first_date, last_date = date.fromisoformat(limits["first_date"]), date.fromisoformat(limits["last_date"])
        categories = query("SELECT DISTINCT category FROM sales ORDER BY category", connection)["category"].tolist()
        countries = query("SELECT DISTINCT country FROM sales ORDER BY country", connection)["country"].tolist()
        with st.sidebar:
            st.markdown("### Your analysis cohort")
            st.caption("Filters apply to every metric, chart and exported row.")
            dates = st.date_input("Order date range", value=(first_date, last_date),
                                  min_value=first_date, max_value=last_date, key="date_range")
            selected_categories = st.multiselect("Categories", categories, default=categories, key="categories")
            selected_countries = st.multiselect("Countries", countries, default=countries, key="countries")
            st.caption("Clearing a category or country selection returns no orders.")
            st.divider()
            st.markdown("**Built to be checked**")
            st.caption("SQLite is the single metric source. Explicit ingestion validates order grain and integer-cents amounts.")
            st.caption("This is an imported database snapshot. After editing a source CSV, explicitly rebuild the database to refresh it.")
        if len(dates) != 2:
            st.info("Choose both a start date and an end date to define the order cohort.")
            return
        start_date, end_date = dates
        data = get_dashboard_data(connection, start_date=start_date.isoformat(), end_date=end_date.isoformat(),
                                  categories=selected_categories, countries=selected_countries)
    except (OSError, ValueError, KeyError, sqlite3.Error, pd.errors.DatabaseError) as error:
        show_database_error(error)
        return
    finally:
        connection.close()

    if data["metadata"].get("data_kind") == "independently generated synthetic demo":
        source_note.caption("SYNTHETIC RETAIL DEMO · Not Amazon operational data · USD demonstration assumption")
    else:
        source_note.warning("USER-SUPPLIED DATA · Source and redistribution license unverified. "
                            "USD is a demonstration assumption. Do not treat these figures as verified Amazon operational data.")
    st.markdown(f"**Selected order cohort** · {start_date:%b %d, %Y} – {end_date:%b %d, %Y}")
    overview, explorer, definitions = st.tabs(["Business overview", "Order explorer", "Metric definitions"])
    with overview:
        render_overview(data)
    with explorer:
        render_explorer(data)
    with definitions:
        render_definitions(data)
    st.divider()
    st.caption("PORTFOLIO PROJECT · Reproducible SQL metrics, validated Python ingestion and a read-only Streamlit interface.")


if __name__ == "__main__":
    main()
