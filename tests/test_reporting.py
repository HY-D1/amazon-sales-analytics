"""Independent BI export checks against a deliberately small, known order ledger."""
import csv
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from src import data_loader, reporting
from scripts.generate_demo_data import generate


FIELDS = 'OrderID OrderDate CustomerID CustomerName ProductID ProductName Category Brand Quantity UnitPrice Discount Tax ShippingCost TotalAmount PaymentMethod OrderStatus City State Country SellerID'.split()


def fixture_order(order_id, status, order_date, **changes):
    row = dict(zip(FIELDS, [
        order_id, order_date, 'DEMO-C1', 'Demo customer 1', 'P1', 'Demo lamp',
        'Home', 'Demo brand', '2', '10.00', '0.1', '1.00', '2.00', '21.00',
        'Credit Card', status, 'Demo city', 'Demo state', 'Demo country', 'DEMO-S1',
    ]))
    row.update(changes)
    return row


def ledger():
    # Delivered merchandise is 18.00 + 2.50 = 20.50; booked value is 108.00.
    # One return / six orders; the second delivered order shares a customer.
    return [
        fixture_order('ORD1', 'Delivered', '2025-01-01'),
        fixture_order('ORD2', 'Delivered', '2025-01-03',
                      ProductID='P2', ProductName='Demo book', Category='Books',
                      Quantity='1', UnitPrice='5.00', Discount='0.5',
                      Tax='0.50', ShippingCost='0.00', TotalAmount='3.00'),
        fixture_order('ORD3', 'Returned', '2025-01-03'),
        fixture_order('ORD4', 'Cancelled', '2025-01-05'),
        fixture_order('ORD5', 'Pending', '2025-01-07'),
        fixture_order('ORD6', 'Shipped', '2025-01-07'),
    ]


class ReportingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.csv_path = self.root / 'private-input' / 'orders.csv'
        self.db_path = self.root / 'private-db' / 'sales.db'
        self.exports = self.root / 'public' / 'exports'
        self.reports = self.root / 'public' / 'reports'

    def tearDown(self):
        self.temporary.cleanup()

    def load(self, rows):
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_path.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        frame, conn = data_loader.load_data(self.csv_path, self.db_path)
        conn.close()
        return frame

    def export(self):
        return reporting.export(self.db_path, self.exports, self.reports)

    def public_bytes(self):
        return {str(path.relative_to(self.root / 'public')): path.read_bytes()
                for path in (self.root / 'public').rglob('*') if path.is_file()}

    def test_exported_fact_and_sql_match_independent_business_totals(self):
        self.load(ledger())
        manifest = self.export()
        fact = pd.read_csv(self.exports / 'FactOrders.csv')
        delivered = fact[fact.orderstatus == 'Delivered']
        returned = fact[fact.orderstatus == 'Returned']
        self.assertEqual(len(fact), 6)
        self.assertEqual(fact.orderid.nunique(), 6)
        self.assertEqual(int(fact.totalamount_cents.sum()), 10800)
        self.assertEqual(int(fact.delivered_revenue_cents.sum()), 2050)
        self.assertEqual(len(delivered), 2)
        self.assertEqual(len(returned), 1)
        self.assertEqual(delivered.merchandise_cents.sum() / len(delivered), 1025)
        with data_loader.connect_db(self.db_path) as conn:
            sql = conn.execute('''SELECT COUNT(DISTINCT orderid),
                SUM(totalamount_cents),
                SUM(CASE WHEN orderstatus = 'Delivered' THEN merchandise_cents ELSE 0 END),
                COUNT(DISTINCT CASE WHEN orderstatus = 'Delivered' THEN orderid END),
                COUNT(DISTINCT CASE WHEN orderstatus = 'Returned' THEN orderid END)
                FROM sales''').fetchone()
        self.assertEqual(sql, (6, 10800, 2050, 2, 1))
        expected = manifest['expected_metrics']
        self.assertEqual(expected['total_orders'], 6)
        self.assertEqual(expected['booked_total_cents'], 10800)
        self.assertEqual(expected['delivered_revenue_cents'], 2050)
        self.assertEqual(expected['delivered_aov_cents'], 1025)
        self.assertAlmostEqual(expected['returned_share'], 1 / 6)
        self.assertAlmostEqual(expected['completed_return_rate'], 1 / 3)
        self.assertEqual(expected['unique_customers'], 1)
        published = json.loads((self.reports / 'metrics.json').read_text())
        self.assertEqual(published['kpis'], expected)
        report = (self.reports / 'business_insights.md').read_text()
        self.assertIn('USD 20.50', report)
        self.assertIn('USD 108.00', report)
        self.assertIn('USD 10.25', report)
        self.assertIn('16.67%', report)

    def test_dimension_joins_preserve_grain_and_amounts(self):
        self.load(ledger())
        self.export()
        fact = pd.read_csv(self.exports / 'FactOrders.csv', dtype={'orderid': str})
        joined = fact.copy()
        for table, key in [('DimCustomer', 'customerid'), ('DimProduct', 'productid'),
                           ('DimGeography', 'geography_key'), ('DimDate', 'orderdate')]:
            dimension = pd.read_csv(self.exports / f'{table}.csv')
            self.assertFalse(dimension[key].isna().any(), table)
            self.assertEqual(dimension[key].nunique(), len(dimension), table)
            joined = joined.merge(dimension, on=key, how='left',
                                  validate='many_to_one', indicator=True)
            self.assertTrue(joined['_merge'].eq('both').all(), table)
            joined = joined.drop(columns='_merge')
            self.assertEqual(len(joined), 6, table)
            self.assertEqual(joined.orderid.nunique(), 6, table)
            self.assertEqual(int(joined.totalamount_cents.sum()), 10800, table)
            self.assertEqual(int(joined.delivered_revenue_cents.sum()), 2050, table)
        dates = pd.read_csv(self.exports / 'DimDate.csv')
        self.assertEqual(dates.orderdate.tolist(),
                         pd.date_range('2025-01-01', '2025-01-07').strftime('%Y-%m-%d').tolist())
        self.assertIn('2025-01-02', dates.orderdate.tolist())

    def test_same_input_produces_identical_published_bytes_and_valid_hashes(self):
        self.load(ledger())
        manifest = self.export()
        first = self.public_bytes()
        self.export()
        self.assertEqual(self.public_bytes(), first)
        for name, description in manifest['files'].items():
            raw = (self.exports / name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), description['sha256'], name)
            with (self.exports / name).open(newline='') as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), description['rows'], name)

    def test_dimension_key_assignment_is_independent_of_input_order(self):
        rows = ledger()
        rows[3].update(CustomerID='DEMO-C2', CustomerName='Demo customer 2',
                       City='Another city', State='Another state', Country='Another country')
        frame = self.load(rows)
        first = reporting.build_star(frame)
        second = reporting.build_star(frame.iloc[::-1])
        for name in first:
            self.assertEqual(first[name].to_csv(index=False), second[name].to_csv(index=False), name)

    def test_empty_input_exports_header_only_tables_and_na_rates(self):
        self.load([])
        manifest = self.export()
        self.assertEqual(len(manifest['files']), 5)
        for name, description in manifest['files'].items():
            self.assertEqual(description['rows'], 0, name)
            self.assertTrue(pd.read_csv(self.exports / name).empty, name)
        metrics = manifest['expected_metrics']
        self.assertEqual(metrics['total_orders'], 0)
        self.assertEqual(metrics['delivered_revenue_cents'], 0)
        self.assertEqual(metrics['booked_total_cents'], 0)
        self.assertIsNone(metrics['delivered_aov_cents'])
        self.assertIsNone(metrics['returned_share'])
        self.assertIsNone(metrics['completed_return_rate'])
        report = (self.reports / 'business_insights.md').read_text()
        self.assertIn('**N/A**', report)
        self.assertNotRegex(report.lower(), r'\bnan\b')

    def test_no_delivered_orders_cannot_create_revenue_or_aov(self):
        rows = [fixture_order('RET1', 'Returned', '2025-01-01'),
                fixture_order('CAN1', 'Cancelled', '2025-01-01')]
        self.load(rows)
        metrics = self.export()['expected_metrics']
        self.assertEqual(metrics['delivered_orders'], 0)
        self.assertEqual(metrics['delivered_revenue_cents'], 0)
        self.assertEqual(metrics['booked_total_cents'], 4200)
        self.assertIsNone(metrics['delivered_aov_cents'])
        self.assertEqual(metrics['returned_share'], 0.5)
        self.assertEqual(metrics['completed_return_rate'], 1)

    def test_export_rejects_conflicting_dimension_ids_and_duplicate_orders(self):
        frame = self.load(ledger())
        for field, value, expected in [('orderid', 'ORD1', 'orderid'),
                                       ('customername', 'Conflicting name', 'DimCustomer'),
                                       ('productname', 'Conflicting product', 'DimProduct')]:
            with self.subTest(field=field):
                bad = frame.copy()
                # Rows 0 and 2 already share customer/product keys.
                bad.loc[2, field] = value
                with self.assertRaisesRegex(ValueError, expected):
                    reporting.build_star(bad)
        self.assertFalse(self.exports.exists())

    def test_private_paths_are_not_in_published_manifest_or_reports(self):
        self.load(ledger())
        manifest = self.export()
        self.assertNotIn('source_path', manifest['metadata'])
        self.assertEqual(manifest['metadata']['source_sha256'],
                         hashlib.sha256(self.csv_path.read_bytes()).hexdigest())
        for name, raw in self.public_bytes().items():
            text = raw.decode('utf-8')
            self.assertNotIn(str(self.root), text, name)
            self.assertNotIn(str(data_loader.PROJECT_ROOT), text, name)
            self.assertNotIn('source_path', text, name)

    def test_custom_csv_report_does_not_claim_verified_synthetic_provenance(self):
        self.load(ledger())
        manifest = self.export()
        self.assertIn('unverified', manifest['metadata']['data_kind'])
        report = (self.reports / 'business_insights.md').read_text()
        self.assertNotIn('Independently generated synthetic demonstration', report)
        self.assertIn('unverified', report.lower())

    def test_export_refuses_to_overwrite_source_csv_before_any_output_write(self):
        self.csv_path = self.exports / 'FactOrders.csv'
        self.load(ledger())
        source_before = self.csv_path.read_bytes()
        database_before = self.db_path.read_bytes()
        with self.assertRaises(ValueError):
            self.export()
        self.assertEqual(self.csv_path.read_bytes(), source_before)
        self.assertEqual(self.db_path.read_bytes(), database_before)
        self.assertEqual(set(self.exports.iterdir()), {self.csv_path})
        self.assertFalse(self.reports.exists())

    def test_export_refuses_to_overwrite_database_before_any_output_write(self):
        self.db_path = self.exports / 'FactOrders.csv'
        self.load(ledger())
        database_before = self.db_path.read_bytes()
        source_before = self.csv_path.read_bytes()
        with self.assertRaises(ValueError):
            self.export()
        self.assertEqual(self.db_path.read_bytes(), database_before)
        self.assertEqual(self.csv_path.read_bytes(), source_before)
        with data_loader.connect_db(self.db_path) as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM sales').fetchone()[0], 6)
        self.assertEqual(set(self.exports.iterdir()), {self.db_path})
        self.assertFalse(self.reports.exists())

    def test_export_resolves_output_symlinks_to_protect_sidecar_and_report_inputs(self):
        self.load(ledger())
        sidecar = self.csv_path.with_suffix('.csv.metadata.json')
        sidecar.write_text('{"provenance": "preserve this input metadata"}\n')
        self.exports.mkdir(parents=True)
        self.reports.mkdir(parents=True)
        for destination, protected in [(self.exports / 'manifest.json', sidecar),
                                       (self.reports / 'metrics.json', self.csv_path),
                                       (self.reports / 'business_insights.md', self.db_path)]:
            with self.subTest(destination=destination.name, protected=protected.name):
                protected_before = protected.read_bytes()
                destination.symlink_to(protected)
                try:
                    with self.assertRaises(ValueError):
                        self.export()
                    self.assertEqual(protected.read_bytes(), protected_before)
                    self.assertEqual(set(self.exports.iterdir()),
                                     {destination} if destination.parent == self.exports else set())
                    self.assertEqual(set(self.reports.iterdir()),
                                     {destination} if destination.parent == self.reports else set())
                finally:
                    for directory in (self.exports, self.reports):
                        for artifact in directory.iterdir():
                            artifact.unlink()
                    protected.write_bytes(protected_before)

    def test_generated_demo_end_to_end_reconciles_to_independent_csv_arithmetic(self):
        generate(self.csv_path, rows=64, seed=17)
        raw = self.csv_path.read_bytes()
        source_metadata = self.csv_path.with_suffix('.csv.metadata.json').read_bytes()
        generate(self.csv_path, rows=64, seed=17)
        self.assertEqual(self.csv_path.read_bytes(), raw)
        self.assertEqual(self.csv_path.with_suffix('.csv.metadata.json').read_bytes(), source_metadata)
        with self.csv_path.open(newline='') as handle:
            rows = list(csv.DictReader(handle))
        booked = sum(Decimal(row['TotalAmount']) for row in rows)
        delivered = [row for row in rows if row['OrderStatus'] == 'Delivered']
        revenue = sum((Decimal(row['Quantity']) * Decimal(row['UnitPrice']) *
                       (1 - Decimal(row['Discount']))).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
                      for row in delivered)
        _, conn = data_loader.load_data(self.csv_path, self.db_path)
        conn.close()
        manifest = self.export()
        self.assertEqual(manifest['metadata']['data_kind'],
                         'independently generated synthetic demo')
        metrics = manifest['expected_metrics']
        self.assertEqual(metrics['total_orders'], 64)
        self.assertEqual(metrics['booked_total_cents'], int(booked * 100))
        self.assertEqual(metrics['delivered_revenue_cents'], int(revenue * 100))
        self.assertEqual(metrics['delivered_orders'], len(delivered))
        self.assertAlmostEqual(metrics['delivered_aov_cents'], int(revenue * 100) / len(delivered))
        self.assertEqual(manifest['files']['FactOrders.csv']['rows'], 64)
        self.assertIn('Independently generated synthetic demonstration',
                      (self.reports / 'business_insights.md').read_text())


if __name__ == '__main__':
    unittest.main()
