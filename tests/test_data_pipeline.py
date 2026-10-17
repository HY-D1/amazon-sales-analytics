"""Business-contract tests using a tiny independently constructed order ledger."""
import csv
import hashlib
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from src import data_loader

FIELDS = 'OrderID OrderDate CustomerID CustomerName ProductID ProductName Category Brand Quantity UnitPrice Discount Tax ShippingCost TotalAmount PaymentMethod OrderStatus City State Country SellerID'.split()


def order(order_id='ORD1', status='Delivered', **changes):
    row = dict(zip(FIELDS, [order_id, '2025-01-15', 'DEMO-C1', 'Demo customer 1', 'P1', 'Demo lamp', 'Home', 'Demo brand', '2', '10.00', '0.1', '1.00', '2.00', '21.00', 'Credit Card', status, 'Demo city', 'Demo state', 'Demo country', 'DEMO-S1']))
    row.update(changes)
    return row


class DataPipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.csv = self.root / 'orders.csv'
        self.db = self.root / 'sales.db'

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rows, fields=FIELDS):
        with self.csv.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def load(self, rows):
        self.write(rows)
        return data_loader.load_data(self.csv, self.db)

    def test_delivered_revenue_excludes_other_statuses_tax_shipping(self):
        _, conn = self.load([order(), order('ORD2', 'Returned'), order('ORD3', 'Cancelled'), order('ORD4', 'Pending'), order('ORD5', 'Shipped')])
        with conn:
            kpi = data_loader.get_dashboard_data(conn)['kpis']
            self.assertEqual(kpi['total_orders'], 5)
            self.assertEqual(kpi['delivered_revenue_cents'], 1800)
            self.assertEqual(kpi['booked_total_cents'], 10500)
            self.assertEqual(kpi['delivered_aov_cents'], 1800)
            self.assertEqual(kpi['returned_share'], 0.2)
            self.assertEqual(kpi['completed_return_rate'], 0.5)
        conn.close()

    def test_exact_duplicates_do_not_inflate_orders(self):
        _, conn = self.load([order(), order()])
        data = data_loader.get_dashboard_data(conn)
        self.assertEqual(data['kpis']['total_orders'], 1)
        self.assertEqual(data['quality']['exact_duplicates_removed'], 1)
        conn.close()

    def test_conflicting_order_id_fails_without_replacing_last_good(self):
        _, conn = self.load([order()])
        conn.close()
        old = self.db.read_bytes()
        self.write([order(), order(Quantity='3', TotalAmount='30.00')])
        with self.assertRaisesRegex(ValueError, 'orderid'):
            data_loader.load_data(self.csv, self.db)
        self.assertEqual(self.db.read_bytes(), old)

    def test_money_rounds_half_up_and_accepts_one_cent_source_tolerance(self):
        _, conn = self.load([order(Quantity='1', UnitPrice='0.05', Discount='0.5', Tax='0', ShippingCost='0', TotalAmount='0.03')])
        self.assertEqual(data_loader.get_dashboard_data(conn)['kpis']['delivered_revenue_cents'], 3)
        conn.close()
        _, conn = self.load([order(TotalAmount='21.01')])
        self.assertEqual(data_loader.get_dashboard_data(conn)['kpis']['booked_total_cents'], 2101)
        conn.close()

    def test_integer_cents_above_float_exact_range_remain_exact(self):
        rows = [order(f'ORD{i}', Quantity='1', UnitPrice='30000000000000.01', Discount='0',
                      Tax='0', ShippingCost='0', TotalAmount='30000000000000.01') for i in range(4)]
        _, conn = self.load(rows)
        kpis = data_loader.get_dashboard_data(conn)['kpis']
        self.assertIsInstance(kpis['delivered_revenue_cents'], int)
        self.assertEqual(kpis['delivered_revenue_cents'], 12000000000000004)
        conn.close()

    def test_sql_views_api_and_combined_filters_reconcile(self):
        _, conn = self.load([order(), order('ORD2', 'Returned'), order('ORD3', OrderDate='2025-02-01')])
        full = data_loader.get_dashboard_data(conn)
        self.assertEqual(dict(zip([c[0] for c in conn.execute('SELECT * FROM kpi_summary').description],
                                  conn.execute('SELECT * FROM kpi_summary').fetchone())), full['kpis'])
        self.assertEqual(int(full['category']['delivered_revenue_cents'].sum()), full['kpis']['delivered_revenue_cents'])
        self.assertEqual(int(full['monthly']['delivered_revenue_cents'].sum()), full['kpis']['delivered_revenue_cents'])
        filtered = data_loader.get_dashboard_data(conn, start_date='2025-01-15', end_date='2025-01-15',
                                                  categories=['Home'], countries=['Demo country'])
        self.assertEqual(filtered['kpis']['total_orders'], 2)
        self.assertEqual(filtered['kpis']['delivered_revenue_cents'], 1800)
        conn.close()

    def test_empty_dataset_and_filter_have_defined_zero_counts(self):
        _, conn = self.load([])
        kpi = data_loader.get_dashboard_data(conn)['kpis']
        self.assertEqual(kpi['total_orders'], 0)
        self.assertEqual(kpi['delivered_revenue_cents'], 0)
        self.assertIsNone(kpi['delivered_aov_cents'])
        self.assertIsNone(kpi['returned_share'])
        conn.close()
        _, conn = self.load([order()])
        self.assertEqual(data_loader.get_dashboard_data(conn, categories=[])['kpis']['total_orders'], 0)
        self.assertEqual(data_loader.get_dashboard_data(conn, countries=[])['kpis']['total_orders'], 0)
        self.assertEqual(data_loader.get_dashboard_data(conn, categories=["Home' OR 1=1 --"])['kpis']['total_orders'], 0)
        conn.close()

    def test_malformed_values_are_rejected_before_writing(self):
        cases = [dict(OrderDate='2025-02-30'), dict(OrderDate='1/2/2025'), dict(OrderStatus='Lost'), dict(Quantity='1.5'), dict(Quantity='0'), dict(UnitPrice='NaN'), dict(UnitPrice='Infinity'), dict(UnitPrice='-1'), dict(Discount='1.1'), dict(TotalAmount='9'), dict(CustomerID=' '), dict(Tax='-1'),
                 dict(UnitPrice='92233720368547758.08'), dict(Discount='1e999999'),
                 dict(Quantity='10000000000000000', UnitPrice='10000000000000000.00')]
        for changes in cases:
            with self.subTest(changes=changes):
                self.write([order(**changes)])
                with self.assertRaises(ValueError):
                    data_loader.load_data(self.csv, self.db)
                self.assertFalse(self.db.exists())

    def test_dimension_conflicts_and_missing_columns_are_rejected(self):
        for changes in [dict(CustomerName='Another customer'), dict(ProductName='Another product'), dict(Category='Wrong category')]:
            with self.subTest(changes=changes):
                self.write([order(), order('ORD2', **changes)])
                with self.assertRaises(ValueError):
                    data_loader.load_data(self.csv, self.db)
        self.write([], FIELDS[:-1])
        with self.assertRaisesRegex(ValueError, 'sellerid'):
            data_loader.load_data(self.csv, self.db)

    def test_relative_environment_paths_resolve_from_repository(self):
        with patch.dict(os.environ, {'DATA_PATH': 'data/custom.csv', 'DB_PATH': 'data/custom.db'}):
            csv_path, db_path = data_loader.resolve_paths()
        self.assertEqual(csv_path, data_loader.PROJECT_ROOT / 'data/custom.csv')
        self.assertEqual(db_path, data_loader.PROJECT_ROOT / 'data/custom.db')

    def test_read_connection_cannot_write_or_create_missing_database(self):
        with self.assertRaises(FileNotFoundError):
            data_loader.connect_db(self.db)
        self.assertFalse(self.db.exists())
        _, conn = self.load([order()])
        with self.assertRaises(sqlite3.OperationalError):
            conn.execute('DELETE FROM sales')
        conn.close()

    def test_failed_database_build_preserves_last_good(self):
        _, conn = self.load([order()])
        conn.close()
        old = self.db.read_bytes()
        self.write([order('ORD2')])
        with patch.object(data_loader, '_create_views', side_effect=sqlite3.OperationalError('simulated SQL build failure')):
            with self.assertRaises(sqlite3.OperationalError):
                data_loader.load_data(self.csv, self.db)
        self.assertEqual(self.db.read_bytes(), old)
        self.assertFalse(list(self.root.glob('*.tmp')))


class ReproducibleDemoTests(unittest.TestCase):
    def test_source_hash_describes_validated_snapshot_during_concurrent_change(self):
        from scripts.generate_demo_data import generate
        with tempfile.TemporaryDirectory() as directory:
            source = generate(Path(directory) / 'orders.csv', rows=2, seed=42)
            validated_bytes = source.read_bytes()
            original_validate = data_loader._validate

            def validate_then_simulate_external_change(*args, **kwargs):
                result = original_validate(*args, **kwargs)
                # Another process replaces both CSV and sidecar between validation
                # and metadata creation; the DB must describe the validated bytes.
                generate(source, rows=3, seed=42)
                return result

            with patch.object(data_loader, '_validate', side_effect=validate_then_simulate_external_change):
                frame, conn = data_loader.load_data(source, Path(directory) / 'sales.db')
            try:
                metadata = data_loader.get_dashboard_data(conn)['metadata']
                self.assertEqual(len(frame), 2)
                self.assertNotEqual(source.read_bytes(), validated_bytes)
                self.assertEqual(metadata['source_sha256'], hashlib.sha256(validated_bytes).hexdigest())
                self.assertEqual(metadata['data_kind'], 'user-supplied CSV; source and license unverified')
            finally:
                conn.close()

    def test_generator_is_byte_reproducible_and_does_not_use_real_identities(self):
        from scripts.generate_demo_data import generate
        with tempfile.TemporaryDirectory() as directory:
            first = generate(Path(directory) / 'one.csv', rows=50, seed=42)
            second = generate(Path(directory) / 'two.csv', rows=50, seed=42)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(first.with_suffix('.csv.metadata.json').read_bytes(), second.with_suffix('.csv.metadata.json').read_bytes())
            frame, conn = data_loader.load_data(first, Path(directory) / 'demo.db')
            self.assertTrue(frame['customername'].str.startswith('Demo Customer ').all())
            self.assertEqual(data_loader.get_dashboard_data(conn)['metadata']['data_kind'], 'independently generated synthetic demo')
            conn.close()

    def test_calendar_spine_window_sql_handles_missing_month(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'orders.csv'
            with source.open('w', newline='', encoding='utf-8') as handle:
                writer = csv.DictWriter(handle, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows([order(), order('ORD2', OrderDate='2025-03-15')])
            _, conn = data_loader.load_data(source, Path(directory) / 'demo.db')
            statements = (data_loader.PROJECT_ROOT / 'sql/analyst_queries.sql').read_text().split(';')
            results = [conn.execute(statement).fetchall() for statement in statements if statement.strip()]
            self.assertEqual([row[0] for row in results[0]], ['2025-01', '2025-02', '2025-03'])
            self.assertEqual(results[0][1][1], 0)
            self.assertIsNone(results[0][2][-1])  # no division by zero for March vs February
            self.assertEqual(results[2], [(3600, 3600, 3600)])
            conn.close()


if __name__ == '__main__':
    unittest.main()
