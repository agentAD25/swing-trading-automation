import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from swingtrade.config import RuntimeConfig
from swingtrade.wdc import FixtureError, load_wdc_fixture

FIXTURE = Path(__file__).parents[1] / "fixtures" / "wdc-reference"


def test_missing_mode_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SWINGTRADE_MODE", raising=False)
    with pytest.raises(ValidationError):
        RuntimeConfig(_env_file=None)  # type: ignore[call-arg]


def test_corrupt_fixture_stops_before_evaluation(tmp_path: Path) -> None:
    root = tmp_path / "wdc-reference"
    shutil.copytree(FIXTURE, root)
    (root / "bars.csv").write_bytes((root / "bars.csv").read_bytes() + b"\n")
    with pytest.raises(FixtureError, match="digest"):
        load_wdc_fixture(root)


def test_runtime_package_has_no_network_or_live_order_client() -> None:
    source_root = Path(__file__).parents[2] / "src" / "swingtrade"
    source = "\n".join(path.read_text() for path in source_root.glob("*.py"))
    forbidden = ("requests.", "httpx.", "socket.", "tradestation", "place_order", "cancel_order")
    assert all(token not in source.lower() for token in forbidden)
