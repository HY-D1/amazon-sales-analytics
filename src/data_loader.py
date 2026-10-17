"""Validate an order-grain ledger and atomically publish the canonical SQLite store.

All relative paths resolve from the repository root. Readers never rebuild a DB.
Use ``python -m src.data_loader`` after generating the independent demo CSV.
"""
from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = '2'
FIELDS = 'orderid orderdate customerid customername productid productname category brand quantity unitprice discount tax shippingcost totalamount paymentmethod orderstatus city state country sellerid'.split()
CENT_COLUMNS = ['unitprice_cents', 'tax_cents', 'shippingcost_cents', 'totalamount_cents', 'merchandise_cents', 'delivered_revenue_cents']
STATUSES = {'Delivered', 'Returned', 'Cancelled', 'Pending', 'Shipped'}
MAX_INT = 2**63 - 1


def _root_path(path):
    path = Path(path).expanduser()
    return path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()


def resolve_paths(csv_path=None, db_path=None):
    """Explicit arguments override DATA_PATH / DB_PATH; relative means repo root."""
    return (_root_path(csv_path if csv_path is not None else os.getenv('DATA_PATH', 'data/demo_sales.csv')),
            _root_path(db_path if db_path is not None else os.getenv('DB_PATH', 'data/amazon_sales.db')))


def _decimal(value, field, row_number):
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f'Row {row_number}: {field} is not a decimal') from exc
    if not result.is_finite() or result < 0:
        raise ValueError(f'Row {row_number}: {field} must be finite and nonnegative')
    if result > Decimal(MAX_INT) / 100:
        raise ValueError(f'Row {row_number}: {field} exceeds supported integer range')
    return result


def _cents(value):
    if not value.is_finite() or value < 0 or value > Decimal(MAX_INT) / 100:
        raise ValueError('Money amount exceeds supported SQLite integer cents range')
    return int((value * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def _validate(csv_path, source_bytes=None):
    # A single immutable snapshot must feed both parsing and the provenance hash.
    # Keep the path-only helper for audits, without reopening during load_data.
    if source_bytes is None:
        source_bytes = Path(csv_path).read_bytes()
    frame = pd.read_csv(BytesIO(source_bytes), dtype=str, keep_default_na=False, skip_blank_lines=False)
    frame.columns = frame.columns.str.strip().str.lower()
    missing = sorted(set(FIELDS) - set(frame.columns))
    if missing:
        raise ValueError('Missing required columns: ' + ', '.join(missing))
    if len(set(frame.columns)) != len(frame.columns) or any(c.endswith('.1') for c in frame.columns):
        raise ValueError('Duplicate CSV columns are not supported')
    # Ignore no columns silently: extra fields may represent an incompatible grain.
    if set(frame.columns) != set(FIELDS):
        raise ValueError('Unexpected columns: ' + ', '.join(sorted(set(frame.columns) - set(FIELDS))))
    frame = frame[FIELDS].apply(lambda series: series.str.strip())
    if frame.eq('').any().any() or frame.isna().any().any():
        raise ValueError('All required fields must be nonempty')
    input_rows = len(frame)
    frame = frame.drop_duplicates().reset_index(drop=True)
    if frame['orderid'].duplicated().any():
        raise ValueError('Conflicting orderid: source has no line ID; do not guess or sum order lines')
    for key, attributes in [('customerid', ['customername', 'city', 'state', 'country']),
                            ('productid', ['productname', 'category', 'brand'])]:
        if not frame.empty and frame.groupby(key)[attributes].nunique().gt(1).any().any():
            raise ValueError(f'Conflicting {key} dimension attributes')
    records = []
    for index, row in frame.iterrows():
        row_number = index + 2
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', row['orderdate']):
            raise ValueError(f'Row {row_number}: orderdate must be YYYY-MM-DD')
        try:
            date.fromisoformat(row['orderdate'])
        except ValueError as exc:
            raise ValueError(f'Row {row_number}: invalid orderdate') from exc
        if row['orderstatus'] not in STATUSES:
            raise ValueError(f'Row {row_number}: unsupported orderstatus {row["orderstatus"]!r}')
        quantity = _decimal(row['quantity'], 'quantity', row_number)
        if quantity <= 0 or quantity != quantity.to_integral_value():
            raise ValueError(f'Row {row_number}: quantity must be a positive integer')
        discount = _decimal(row['discount'], 'discount', row_number)
        if discount > 1:
            raise ValueError(f'Row {row_number}: discount must be between 0 and 1')
        money = {key: _decimal(row[key], key, row_number) for key in ['unitprice', 'tax', 'shippingcost', 'totalamount']}
        if any(value * 100 != (value * 100).to_integral_value() for value in money.values()):
            raise ValueError(f'Row {row_number}: input money must have at most two decimal places')
        merchandise = _cents(quantity * money['unitprice'] * (1 - discount))
        cent_values = {f'{key}_cents': _cents(value) for key, value in money.items()}
        expected_total = merchandise + cent_values['tax_cents'] + cent_values['shippingcost_cents']
        if abs(expected_total - cent_values['totalamount_cents']) > 1:
            raise ValueError(f'Row {row_number}: totalamount differs from discounted merchandise + tax + shipping by more than one cent')
        if merchandise > MAX_INT:
            raise ValueError(f'Row {row_number}: merchandise exceeds SQLite integer range')
        record = row.to_dict()
        record.update({key: float(value) for key, value in money.items()})
        record.update(quantity=int(quantity), discount=float(discount), **cent_values,
                      merchandise_cents=merchandise,
                      delivered_revenue_cents=merchandise if row['orderstatus'] == 'Delivered' else 0,
                      currency='USD')
        records.append(record)
    result = pd.DataFrame(records, columns=FIELDS + CENT_COLUMNS + ['currency'])
    for column in CENT_COLUMNS + ['quantity']:
        if sum(int(value) for value in result[column]) > MAX_INT:
            raise ValueError(f'{column} total exceeds SQLite integer range')
        result[column] = result[column].astype('int64')
    quality = {'input_rows': input_rows, 'exact_duplicates_removed': input_rows - len(result),
               'valid_orders': len(result), 'rejected_rows': 0}
    return result, quality


def _create_views(conn):
    conn.executescript((PROJECT_ROOT / 'sql/views.sql').read_text(encoding='utf-8'))


def _source_metadata(csv_path, frame, quality, source_bytes):
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    data_kind = 'user-supplied CSV; source and license unverified'
    manifest_path = csv_path.with_suffix(csv_path.suffix + '.metadata.json')
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if manifest.get('sha256') == source_hash and manifest.get('generator') == 'scripts/generate_demo_data.py':
            data_kind = 'independently generated synthetic demo'
    return {'schema_version': SCHEMA_VERSION, 'source_path': str(csv_path),
            'source_sha256': source_hash, 'data_kind': data_kind,
            'currency': 'USD (demo assumption)', 'grain': 'one order, one product per row',
            'date_min': None if frame.empty else frame['orderdate'].min(),
            'date_max': None if frame.empty else frame['orderdate'].max(), **quality}


def load_data(csv_path=None, db_path=None):
    """Validate first, build beside the destination, then replace atomically.

    A failed validation/build leaves the last successfully published DB intact.
    Returns the canonical DataFrame and a read-only connection for compatibility.
    """
    csv_path, db_path = resolve_paths(csv_path, db_path)
    if csv_path == db_path:
        raise ValueError('CSV and database paths must differ')
    source_bytes = csv_path.read_bytes()
    frame, quality = _validate(csv_path, source_bytes)
    metadata = _source_metadata(csv_path, frame, quality, source_bytes)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=db_path.name + '.', suffix='.tmp', dir=db_path.parent)
    os.close(fd)
    temporary_path = Path(temporary_name)
    try:
        conn = sqlite3.connect(temporary_path)
        try:
            frame.to_sql('sales', conn, index=False, if_exists='fail')
            conn.execute('CREATE UNIQUE INDEX sales_orderid ON sales(orderid)')
            conn.execute('CREATE INDEX sales_orderdate ON sales(orderdate)')
            conn.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
            conn.executemany('INSERT INTO metadata VALUES (?, ?)', [(key, json.dumps(value)) for key, value in metadata.items()])
            _create_views(conn)
            conn.commit()
            if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('SQLite integrity check failed')
        finally:
            conn.close()
        os.replace(temporary_path, db_path)
    finally:
        temporary_path.unlink(missing_ok=True)
    return frame, connect_db(db_path)


def connect_db(db_path=None):
    """Open an existing schema-v2 DB in SQLite read-only mode; never create files."""
    path = resolve_paths(db_path=db_path)[1]
    if not path.is_file():
        raise FileNotFoundError(f'Database not found: {path}. Run python -m src.data_loader first.')
    conn = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    try:
        row = conn.execute("SELECT value FROM metadata WHERE key = 'schema_version'").fetchone()
        if row is None or json.loads(row[0]) != SCHEMA_VERSION:
            raise ValueError('Unsupported database schema; run python -m src.data_loader')
    except Exception:
        conn.close()
        raise
    return conn


def query(sql, conn, params=None):
    """Execute a SQL read and return a DataFrame; canonical connections are read-only."""
    return pd.read_sql_query(sql, conn, params=params)


def get_dashboard_data(conn, start_date=None, end_date=None, categories=None, countries=None):
    """Compute all dashboard metrics from one parameterized SQL order selection.

    None means unrestricted; an empty category/country selection means zero orders.
    Source quality/metadata describe the entire imported file, never the filter.
    """
    clauses, params = [], []
    for name, value, operation in [('orderdate', start_date, '>='), ('orderdate', end_date, '<=')]:
        if value is not None:
            value = str(value)
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
                raise ValueError('Filters require ISO dates')
            date.fromisoformat(value)
            clauses.append(f'{name} {operation} ?')
            params.append(value)
    for name, values in [('category', categories), ('country', countries)]:
        if values is not None:
            values = list(values)
            clauses.append(f'{name} IN ({",".join("?" for _ in values)})' if values else '0')
            params.extend(values)
    selected = 'SELECT * FROM sales' + (' WHERE ' + ' AND '.join(clauses) if clauses else '')
    cte = 'WITH selected AS (' + selected + ') '
    aggregate = '''COUNT(*) AS orders,
        COALESCE(SUM(orderstatus = 'Delivered'), 0) AS delivered_orders,
        COALESCE(SUM(CASE WHEN orderstatus = 'Delivered' THEN quantity ELSE 0 END), 0) AS items_sold,
        COALESCE(SUM(delivered_revenue_cents), 0) AS delivered_revenue_cents,
        COALESCE(SUM(totalamount_cents), 0) AS booked_total_cents,
        1.0 * SUM(delivered_revenue_cents) / NULLIF(SUM(orderstatus = 'Delivered'), 0) AS delivered_aov_cents'''
    def read(statement):
        return query(cte + statement, conn, params)
    kpi_sql = '''SELECT COUNT(*) AS total_orders,
        COALESCE(SUM(orderstatus = 'Delivered'), 0) AS delivered_orders,
        COALESCE(SUM(orderstatus = 'Returned'), 0) AS returned_orders,
        COUNT(DISTINCT customerid) AS unique_customers,
        COALESCE(SUM(delivered_revenue_cents), 0) AS delivered_revenue_cents,
        COALESCE(SUM(totalamount_cents), 0) AS booked_total_cents,
        1.0 * SUM(delivered_revenue_cents) / NULLIF(SUM(orderstatus = 'Delivered'), 0) AS delivered_aov_cents,
        1.0 * SUM(orderstatus = 'Returned') / NULLIF(COUNT(*), 0) AS returned_share,
        1.0 * SUM(orderstatus = 'Returned') / NULLIF(SUM(orderstatus IN ('Returned', 'Delivered')), 0) AS completed_return_rate,
        1.0 * SUM(orderstatus = 'Delivered') / NULLIF(COUNT(*), 0) AS delivered_share
        FROM selected'''
    cursor = conn.execute(cte + kpi_sql, params)
    # pandas coerces mixed numeric rows to float; keep exact SQLite int cents.
    kpis = dict(zip([column[0] for column in cursor.description], cursor.fetchone()))
    metadata = {key: json.loads(value) for key, value in conn.execute('SELECT key, value FROM metadata')}
    return {'kpis': kpis,
            'category': read(f'SELECT category, {aggregate} FROM selected GROUP BY category ORDER BY delivered_revenue_cents DESC, category'),
            'monthly': read(f"SELECT substr(orderdate, 1, 7) AS month, {aggregate} FROM selected GROUP BY month ORDER BY month"),
            'status': read('SELECT orderstatus, COUNT(*) AS orders FROM selected GROUP BY orderstatus ORDER BY orderstatus'),
            'payment': read('SELECT paymentmethod, COUNT(*) AS orders FROM selected GROUP BY paymentmethod ORDER BY orders DESC, paymentmethod'),
            'customers': read('''SELECT customerid, customername, COUNT(*) AS orders,
                SUM(orderstatus = 'Delivered') AS delivered_orders,
                SUM(delivered_revenue_cents) AS observed_spend_cents,
                MIN(orderdate) AS first_order, MAX(orderdate) AS last_order
                FROM selected GROUP BY customerid, customername ORDER BY observed_spend_cents DESC, customerid'''),
            'orders': read('SELECT * FROM selected ORDER BY orderdate, orderid'),
            'quality': {key: metadata[key] for key in ['input_rows', 'exact_duplicates_removed', 'valid_orders', 'rejected_rows']},
            'metadata': metadata}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', help='CSV input; default DATA_PATH or data/demo_sales.csv')
    parser.add_argument('--db', help='SQLite output; default DB_PATH or data/amazon_sales.db')
    args = parser.parse_args()
    _, conn = load_data(args.csv, args.db)
    try:
        result = get_dashboard_data(conn)
        print(json.dumps({'database': str(resolve_paths(args.csv, args.db)[1]), 'quality': result['quality'],
                          'kpis': result['kpis'], 'metadata': result['metadata']}, indent=2))
    finally:
        conn.close()


if __name__ == '__main__':
    main()
