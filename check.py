#!/usr/bin/env python3
"""Check the built artifact, not port availability. Fail with a nonzero exit code."""
import json
import sys
from pathlib import Path

from src.data_loader import connect_db, get_dashboard_data


def main():
    if sys.version_info < (3, 11):
        print('FAIL: Python 3.11+ required', file=sys.stderr)
        return 1
    try:
        conn = connect_db()
        try:
            if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('SQLite integrity check failed')
            data = get_dashboard_data(conn)
            csv_path = Path(data['metadata']['source_path'])
            import hashlib
            if not csv_path.is_file() or hashlib.sha256(csv_path.read_bytes()).hexdigest() != data['metadata']['source_sha256']:
                raise ValueError('Source changed or missing; rebuild the database')
            if data['kpis']['total_orders'] == 0:
                raise ValueError('No canonical orders; cannot demonstrate the dashboard')
            print(json.dumps({'result': 'PASS', 'quality': data['quality'], 'kpis': data['kpis']}, indent=2))
        finally:
            conn.close()
        return 0
    except Exception as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
