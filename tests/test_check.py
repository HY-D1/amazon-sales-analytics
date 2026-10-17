"""CLI health check must inspect the imported source and signal failures to CI."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from scripts.generate_demo_data import generate
from src.data_loader import load_data

ROOT = Path(__file__).resolve().parents[1]


def test_health_check_uses_recorded_custom_source_and_rejects_changed_input():
    with tempfile.TemporaryDirectory() as directory:
        source = generate(Path(directory) / 'custom.csv', rows=6)
        db = Path(directory) / 'custom.db'
        _, conn = load_data(source, db)
        conn.close()
        env = os.environ.copy()
        env['DB_PATH'] = str(db)
        # Even an unrelated DATA_PATH must not replace the imported source identity.
        env['DATA_PATH'] = str(Path(directory) / 'not-the-imported-input.csv')
        result = subprocess.run([sys.executable, str(ROOT / 'check.py')], cwd=directory,
                                env=env, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        generate(source, rows=7)
        result = subprocess.run([sys.executable, str(ROOT / 'check.py')], cwd=directory,
                                env=env, capture_output=True, text=True)
        assert result.returncode == 1
        assert 'Source changed or missing' in result.stderr
        source.unlink()
        result = subprocess.run([sys.executable, str(ROOT / 'check.py')], cwd=directory,
                                env=env, capture_output=True, text=True)
        assert result.returncode == 1
