import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "qualify_robinhood_market.py"
REPOSITORY = Path(__file__).resolve().parents[2]
SELECTION_MANIFEST = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-market-selection-2026-09-09.json"
)
SPEC = importlib.util.spec_from_file_location("market_qualifier", SCRIPT)
qualifier = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(qualifier)


WETH = "0x33e4191705c386532ba27cBF171Db86919200B94"
STOCKS = {
    "AMZN": (
        "0x5884aD2f920c162CFBbACc88C9C51AA75eC09E02",
        "0xe9f5eb0ccbf0dcf8feb022afd0ffc5688af4cc55e8ca7e644fe5e9b7c50887b8",
    ),
    "AMD": (
        "0x71178BAc73cBeb415514eB542a8995b82669778d",
        "0x5164b26ecf3d2c0c769f56a800376a365f99e8dae41f4969952d20cbad32fe8a",
    ),
    "TSLA": (
        "0xC9f9c86933092BbbfFF3CCb4b105A4A94bf3Bd4E",
        "0x199971df12db0d0e0630d753780bd7d4e4bd21f3727b1a4d3873c49f88cbfa8e",
    ),
    "PLTR": (
        "0x1FBE1a0e43594b3455993B5dE5Fd0A7A266298d0",
        "0xd600fd2ff936078114b72a01d3c6d31d449b7af12c24c82fb61efb7bf9c613ae",
    ),
    "NFLX": (
        "0x3b8262A63d25f0477c4DDE23F83cfe22Cb768C93",
        "0x0d5f0b76d3e4c767eda91346e4a84725f4532188ba6b5d35ff4acc227988095f",
    ),
}


def healthy_candidate(symbol="PLTR", stock_is_currency0=True):
    stock, pool_id = STOCKS[symbol]
    key = qualifier.pool_key_for(stock, WETH)
    key["stockIsCurrency0"] = stock_is_currency0
    return {
        "symbol": symbol,
        "stockToken": stock,
        "poolId": pool_id,
        "poolKey": key,
        "runtimeIdentityMatches": True,
        "paused": False,
        "tokenPaused": False,
        "multiplierStateMatches": True,
        "registryWiringMatches": True,
        "deployerBalance": "5000000000000000000",
        "actorBalance": "5000000000000000000",
        "deployerBlocked": False,
        "actorBlocked": False,
        "poolInitialized": False,
        "existingPanopticPool": qualifier.ZERO_ADDRESS,
        "eligible": True,
    }


class MarketQualifierTests(unittest.TestCase):
    def test_all_golden_pool_ids_match_solidity_abi_encoding(self):
        for symbol, (stock, expected_pool_id) in STOCKS.items():
            with self.subTest(symbol=symbol):
                key = qualifier.pool_key_for(stock, WETH)
                self.assertEqual(qualifier.pool_id_for(key), expected_pool_id)
                self.assertEqual(len(qualifier.encode_pool_key(key)), 160)

    def test_pool_key_sorts_addresses_and_pltr_is_currency_zero(self):
        pltr = qualifier.pool_key_for(STOCKS["PLTR"][0], WETH)
        amzn = qualifier.pool_key_for(STOCKS["AMZN"][0], WETH)
        self.assertTrue(pltr["stockIsCurrency0"])
        self.assertFalse(amzn["stockIsCurrency0"])
        self.assertLess(int(pltr["currency0"], 16), int(pltr["currency1"], 16))
        self.assertLess(int(amzn["currency0"], 16), int(amzn["currency1"], 16))

    def test_pool_key_rejects_invalid_parameters(self):
        with self.assertRaisesRegex(ValueError, "different currencies"):
            qualifier.pool_key_for(WETH, WETH)
        with self.assertRaisesRegex(ValueError, "uint24"):
            qualifier.pool_key_for(STOCKS["PLTR"][0], WETH, fee=2**24)
        with self.assertRaisesRegex(ValueError, "non-zero int24"):
            qualifier.pool_key_for(STOCKS["PLTR"][0], WETH, tick_spacing=0)

    def test_rpc_rejects_every_non_allowlisted_method_before_network_use(self):
        transports = (
            qualifier.ReadOnlyRpc("http://127.0.0.1:1", attempts=1),
            qualifier.CastReadOnlyRpc("http://127.0.0.1:1", attempts=1),
        )
        for rpc in transports:
            for method in (
                "eth_sendRawTransaction",
                "eth_sendTransaction",
                "personal_sign",
            ):
                with (
                    self.subTest(transport=type(rpc).__name__, method=method),
                    self.assertRaisesRegex(ValueError, "not read-only"),
                ):
                    rpc.call(method, [])

    def test_healthy_candidate_has_no_blockers(self):
        self.assertEqual(qualifier.assess_candidate(healthy_candidate()), [])

    def test_initialized_pool_is_blocked(self):
        candidate = healthy_candidate()
        candidate["poolInitialized"] = True
        self.assertIn(
            "V4_POOL_ALREADY_INITIALIZED_OR_UNREADABLE",
            qualifier.assess_candidate(candidate),
        )

    def test_zero_second_actor_balance_is_blocked(self):
        candidate = healthy_candidate()
        candidate["actorBalance"] = "0"
        self.assertIn(
            "SECOND_ACTOR_HAS_NO_STOCK_BALANCE", qualifier.assess_candidate(candidate)
        )

    def test_unhealthy_or_registered_stock_is_blocked(self):
        candidate = healthy_candidate()
        candidate["tokenPaused"] = True
        candidate["existingPanopticPool"] = "0x1111111111111111111111111111111111111111"
        blockers = qualifier.assess_candidate(candidate)
        self.assertIn("STOCK_TOKEN_PAUSED_OR_UNREADABLE", blockers)
        self.assertIn("PANOPTIC_MARKET_ALREADY_REGISTERED", blockers)

    def test_recommendation_prefers_stock_as_currency_zero_not_popularity(self):
        popular = healthy_candidate("TSLA", stock_is_currency0=False)
        popular["popularity"] = 1_000_000
        pltr = healthy_candidate("PLTR", stock_is_currency0=True)
        pltr["popularity"] = 1
        recommendation = qualifier.recommend_candidate([popular, pltr])
        self.assertEqual(recommendation["symbol"], "PLTR")
        self.assertFalse(recommendation["accepted"])
        self.assertIn("popularity", recommendation["excludedBasis"].lower())

    def test_no_eligible_candidate_has_no_recommendation(self):
        candidate = healthy_candidate()
        candidate["eligible"] = False
        self.assertIsNone(qualifier.recommend_candidate([candidate]))

    def test_committed_selection_manifest_is_bound_to_qualifier_and_pool_math(self):
        manifest = json.loads(SELECTION_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(
            manifest["sourceBindings"]["qualifierSha256"], qualifier.file_sha256(SCRIPT)
        )
        self.assertEqual(manifest["verification"]["passedChecks"], 79)
        self.assertEqual(manifest["verification"]["failedChecks"], 0)
        for candidate in manifest["candidates"]:
            with self.subTest(symbol=candidate["symbol"]):
                key = dict(candidate["poolKey"])
                key["stockIsCurrency0"] = candidate["stockIsCurrency0"]
                self.assertEqual(qualifier.pool_id_for(key), candidate["poolId"])
        self.assertEqual(manifest["recommendation"]["symbol"], "PLTR")
        self.assertFalse(manifest["recommendation"]["accepted"])
        self.assertTrue(
            all(value is False for value in manifest["authorization"].values())
        )


if __name__ == "__main__":
    unittest.main()
