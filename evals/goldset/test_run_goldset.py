from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "wiki-bridge"))

from run_goldset import run_all

HERE = Path(__file__).resolve().parent


def test_goldset_all_pass():
    summary = run_all(HERE / "cases")
    assert summary["failed"] == [], summary
    assert summary["passed"] >= 4
