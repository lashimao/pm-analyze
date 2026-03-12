from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "polymarket_strategy_snapshot.py"
SPEC = importlib.util.spec_from_file_location("polymarket_strategy_snapshot", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PublicSnapshotTests(unittest.TestCase):
    def test_mask_address_redacts_evm_wallet(self) -> None:
        wallet = "0x1111111111111111111111111111111111111111"
        self.assertEqual(MODULE.mask_address(wallet), "0x1111...1111")

    def test_redact_query_url_masks_user_parameter(self) -> None:
        url = (
            "https://data-api.polymarket.com/activity"
            "?user=0x1111111111111111111111111111111111111111&limit=10"
        )
        self.assertEqual(
            MODULE.redact_query_url(url),
            "https://data-api.polymarket.com/activity?user=0x1111...1111&limit=10",
        )

    def test_sanitize_endpoint_can_be_disabled(self) -> None:
        MODULE.REDACT_IDENTIFIERS = False
        url = (
            "https://data-api.polymarket.com/activity"
            "?user=0x1111111111111111111111111111111111111111&limit=10"
        )
        self.assertEqual(MODULE.sanitize_endpoint(url), url)


if __name__ == "__main__":
    unittest.main()
