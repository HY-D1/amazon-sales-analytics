"""Exercise the real Streamlit app against a tiny, isolated canonical database."""

import csv
from datetime import date
import json
from pathlib import Path
import sqlite3

import pytest
from streamlit.testing.v1 import AppTest

from src.data_loader import FIELDS, load_data


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def dashboard_db(tmp_path, monkeypatch):
    rows = []
    # Order-grain hand calculations: revenue 180 + 80; bookings 203 + 44 + 85 + 50.
    specs = [
        ("1", "Electronics", "Canada", "Delivered", "2", "100", "0.1", "18", "5", "203"),
        ("2", "Books", "Canada", "Returned", "1", "40", "0", "4", "0", "44"),
        ("3", "Books", "United States", "Delivered", "1", "80", "0", "0", "5", "85"),
        ("4", "Electronics", "Canada", "Pending", "1", "50", "0", "0", "0", "50"),
    ]
    for ident, category, country, status, qty, price, discount, tax, ship, total in specs:
        rows.append(dict(zip(FIELDS, [
            f"ORD-{ident}", f"2024-01-0{ident}", f"DEMO-C-{ident}", f"Demo customer {ident}",
            f"DEMO-P-{ident}", f"Demo item {ident}", category, "Demo brand", qty, price,
            discount, tax, ship, total, "Credit Card", status, "Demo city", "Demo state", country, "DEMO-S-1",
        ])))
    source = tmp_path / "orders.csv"
    with source.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    database = tmp_path / "dashboard.db"
    _, connection = load_data(source, database)
    connection.close()
    monkeypatch.setenv("DB_PATH", str(database))
    return database


def app():
    return AppTest.from_file(str(ROOT / "dashboard.py"), default_timeout=20).run()


def metrics(test_app):
    return {metric.label: metric.value for metric in test_app.metric}


def assert_healthy(test_app):
    assert not test_app.exception
    assert not test_app.error


def test_startup_uses_verified_sql_metrics_without_mutating_db(dashboard_db):
    before = dashboard_db.read_bytes()
    test_app = app()
    assert_healthy(test_app)
    assert metrics(test_app) == {
        "Delivered revenue": "$260.00",
        "Orders": "4",
        "Delivered AOV": "$130.00",
        "Returned order share": "25.0%",
        "All-order bookings": "$382.00",
    }
    assert len(test_app.dataframe[0].value) == 4
    assert "customername" not in test_app.dataframe[0].value.columns
    assert "customerid" not in test_app.dataframe[0].value.columns
    assert any("Source and redistribution license unverified" in item.value for item in test_app.warning)
    assert dashboard_db.read_bytes() == before


def test_category_filter_updates_kpis_chart_and_explorer(dashboard_db):
    test_app = app()
    test_app.multiselect(key="categories").set_value(["Books"]).run()
    assert_healthy(test_app)
    actual = metrics(test_app)
    assert actual["Delivered revenue"] == "$80.00"
    assert actual["Orders"] == "2"
    assert actual["Returned order share"] == "50.0%"
    assert actual["All-order bookings"] == "$129.00"
    assert set(test_app.dataframe[0].value["category"]) == {"Books"}
    assert len(test_app.dataframe[0].value) == 2
    monthly, category, status = [json.loads(item.proto.figure.spec)["data"] for item in test_app.get("plotly_chart")]
    assert monthly[0]["y"] == [80.0]
    assert category[0]["x"] == [80.0]
    assert category[0]["y"] == ["Books"]
    assert sum(trace["y"][0] for trace in status) == 2
    # The computed business observation also follows the same SQL selection.
    assert any("**Books** contributes **100.0%**" in item.value for item in test_app.markdown)


def test_country_and_date_filters_apply_to_whole_cohort(dashboard_db):
    test_app = app()
    test_app.multiselect(key="countries").set_value(["Canada"])
    test_app.date_input(key="date_range").set_value((date(2024, 1, 1), date(2024, 1, 2))).run()
    assert_healthy(test_app)
    assert metrics(test_app)["Delivered revenue"] == "$180.00"
    assert metrics(test_app)["Orders"] == "2"
    assert metrics(test_app)["All-order bookings"] == "$247.00"
    selected = test_app.dataframe[0].value
    assert set(selected["country"]) == {"Canada"}
    assert selected["orderdate"].max() == "2024-01-02"


@pytest.mark.parametrize("filter_key", ["categories", "countries"])
def test_empty_selection_means_no_orders_and_undefined_rates(dashboard_db, filter_key):
    test_app = app()
    test_app.multiselect(key=filter_key).set_value([]).run()
    assert_healthy(test_app)
    assert metrics(test_app)["Orders"] == "0"
    assert metrics(test_app)["Delivered revenue"] == "$0.00"
    assert metrics(test_app)["Returned order share"] == "—"
    assert metrics(test_app)["Delivered AOV"] == "—"
    assert test_app.dataframe[0].value.empty
    assert any("No orders match" in item.value for item in test_app.info)


def test_incomplete_date_range_requests_end_date_without_metrics(dashboard_db):
    test_app = app()
    test_app.date_input(key="date_range").set_value((date(2024, 1, 1),)).run()
    assert_healthy(test_app)
    assert any("Choose both a start date and an end date" in item.value for item in test_app.info)
    assert not test_app.metric


def test_missing_database_has_actionable_rebuild_message(tmp_path, monkeypatch):
    database = tmp_path / "missing.db"
    monkeypatch.setenv("DB_PATH", str(database))
    test_app = app()
    assert not test_app.exception
    assert "missing, outdated" in test_app.error[0].value
    assert test_app.code[0].value == "python -m src.data_loader"
    assert not database.exists()
    assert not test_app.metric


def test_stale_database_is_reported_without_overwriting_it(tmp_path, monkeypatch):
    database = tmp_path / "old.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE sales (orderid TEXT)")
    before = database.read_bytes()
    monkeypatch.setenv("DB_PATH", str(database))
    test_app = app()
    assert not test_app.exception
    assert "missing, outdated" in test_app.error[0].value
    assert test_app.code[0].value == "python -m src.data_loader"
    assert database.read_bytes() == before
    assert not test_app.metric
