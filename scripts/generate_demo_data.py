"""Generate independent, deterministic mock retail orders; no external source or PII.

Each row is exactly one order for one product. USD is an explicit demo assumption.
The data is a practice scenario and cannot establish real Amazon performance.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import random

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIELDS = 'OrderID OrderDate CustomerID CustomerName ProductID ProductName Category Brand Quantity UnitPrice Discount Tax ShippingCost TotalAmount PaymentMethod OrderStatus City State Country SellerID'.split()
PRODUCTS = [
    ('P001', 'Demo Wireless Headset', 'Electronics', 'Demo Circuit', '59.99'),
    ('P002', 'Demo Keyboard', 'Electronics', 'Demo Circuit', '49.50'),
    ('P003', 'Demo USB Hub', 'Electronics', 'Demo Circuit', '24.99'),
    ('P004', 'Demo Desk Lamp', 'Home & Office', 'Demo Habitat', '29.95'),
    ('P005', 'Demo Desk Organizer', 'Home & Office', 'Demo Habitat', '18.50'),
    ('P006', 'Demo Insulated Mug', 'Home & Office', 'Demo Habitat', '22.00'),
    ('P007', 'Demo Running Socks', 'Sports', 'Demo Trail', '12.99'),
    ('P008', 'Demo Yoga Mat', 'Sports', 'Demo Trail', '35.00'),
    ('P009', 'Demo Water Bottle', 'Sports', 'Demo Trail', '19.99'),
]
GEOGRAPHIES = [
    ('Demo City A', 'Demo Region A', 'Demo Market A'),
    ('Demo City B', 'Demo Region B', 'Demo Market B'),
    ('Demo City C', 'Demo Region C', 'Demo Market C'),
]


def money(value):
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def generate(output=None, rows=2400, seed=42):
    """Return output path; identical arguments produce byte-identical CSV/manifest."""
    if rows < 0:
        raise ValueError('rows must be nonnegative')
    output = Path(output) if output else PROJECT_ROOT / 'data/demo_sales.csv'
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    start = date(2024, 1, 1)
    days = (date(2025, 12, 31) - start).days + 1
    with output.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator='\n')
        writer.writeheader()
        for index in range(rows):
            customer = rng.randrange(1, 181)
            product_id, product, category, brand, unit_price = rng.choice(PRODUCTS)
            city, state, country = GEOGRAPHIES[(customer - 1) % len(GEOGRAPHIES)]
            quantity = rng.randrange(1, 5)
            discount = rng.choice(['0', '0', '0.05', '0.10', '0.15'])
            merchandise = money(Decimal(unit_price) * quantity * (1 - Decimal(discount)))
            tax = money(merchandise * Decimal('0.05'))
            shipping = Decimal('0.00') if merchandise >= 75 else Decimal('4.99')
            status = rng.choices(['Delivered', 'Returned', 'Cancelled', 'Pending', 'Shipped'], weights=[70, 9, 7, 6, 8])[0]
            values = [f'DEMO-ORD{index + 1:06d}', str(start + timedelta(days=rng.randrange(days))),
                      f'DEMO-C{customer:04d}', f'Demo Customer {customer:04d}', product_id, product, category, brand,
                      quantity, unit_price, discount, str(tax), str(shipping), str(merchandise + tax + shipping),
                      rng.choice(['Credit Card', 'Debit Card', 'Digital Wallet']), status,
                      city, state, country, 'DEMO-SELLER01']
            writer.writerow(dict(zip(FIELDS, values)))
    manifest = {'generator': 'scripts/generate_demo_data.py', 'generator_version': 1,
                'seed': seed, 'rows': rows, 'currency': 'USD',
                'data_kind': 'independently generated synthetic demo',
                'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}
    output.with_suffix(output.suffix + '.metadata.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', help='Relative paths resolve from the repository root')
    parser.add_argument('--rows', type=int, default=2400)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    output = generate(args.output, args.rows, args.seed)
    print(f'Generated {args.rows:,} independent synthetic orders: {output}')
    print(f'SHA-256: {hashlib.sha256(output.read_bytes()).hexdigest()}')


if __name__ == '__main__':
    main()
