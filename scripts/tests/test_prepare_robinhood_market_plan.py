import ast
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "prepare_robinhood_market_plan.py"
REPOSITORY = Path(__file__).resolve().parents[2]
ACCEPTANCE = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-offline-acceptance-2026-09-09.json"
)
SELECTION = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-market-selection-2026-09-09.json"
)
CHAIN = REPOSITORY / "manifests" / "chains" / "robinhood-testnet-46630.json"
DEPLOYMENT = (
    REPOSITORY
    / "manifests"
    / "deployments"
    / "robinhood-testnet-direct-public-progress-2026-09-09.json"
)
PLAN = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-offline-plan-2026-09-09.json"
)

SPEC = importlib.util.spec_from_file_location("market_planner", SCRIPT)
planner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(planner)


class MarketMathTests(unittest.TestCase):
    def test_tick_math_matches_canonical_boundary_vectors(self):
        self.assertEqual(planner.get_sqrt_price_at_tick(0), 2**96)
        self.assertEqual(planner.get_sqrt_price_at_tick(-887272), 4295128739)
        self.assertEqual(
            planner.get_sqrt_price_at_tick(887272),
            1461446703485210103287273052203988822378723970342,
        )

    def test_tick_inverse_is_consistent_around_synthetic_price(self):
        sqrt_price = planner.sqrt_price_x96_for_ratio(1, 1000)
        tick = planner.get_tick_at_sqrt_price(sqrt_price)
        self.assertLessEqual(planner.get_sqrt_price_at_tick(tick), sqrt_price)
        self.assertGreater(planner.get_sqrt_price_at_tick(tick + 1), sqrt_price)
        self.assertEqual(tick, -69082)

    def test_liquidity_never_exceeds_rounded_up_token_budgets(self):
        sqrt_price = planner.sqrt_price_x96_for_ratio(1, 1000)
        tick = planner.get_tick_at_sqrt_price(sqrt_price)
        lower = planner.floor_to_spacing(tick - 12000, 60)
        upper = planner.ceil_to_spacing(tick + 12000, 60)
        sqrt_lower = planner.get_sqrt_price_at_tick(lower)
        sqrt_upper = planner.get_sqrt_price_at_tick(upper)
        liquidity = planner.fit_liquidity_within_budgets(
            sqrt_price,
            sqrt_lower,
            sqrt_upper,
            2 * 10**18,
            2 * 10**15,
        )
        amount0, amount1 = planner.amounts_for_liquidity_rounding_up(
            sqrt_price, sqrt_lower, sqrt_upper, liquidity
        )
        self.assertGreater(liquidity, 0)
        self.assertLessEqual(amount0, 2 * 10**18)
        self.assertLessEqual(amount1, 2 * 10**15)
        next0, next1 = planner.amounts_for_liquidity_rounding_up(
            sqrt_price, sqrt_lower, sqrt_upper, liquidity + 1
        )
        self.assertTrue(next0 > 2 * 10**18 or next1 > 2 * 10**15)


class MarketPlanTests(unittest.TestCase):
    def build(self):
        return planner.build_plan(ACCEPTANCE, SELECTION, CHAIN, DEPLOYMENT, SCRIPT)

    def test_committed_inputs_build_exact_accepted_pool_and_actor(self):
        plan = self.build()
        self.assertEqual(plan["status"], "OFFLINE_REHEARSAL_ONLY_NO_BROADCAST")
        self.assertEqual(plan["network"]["chainId"], 46630)
        self.assertEqual(plan["market"]["symbol"], "PLTR")
        self.assertEqual(
            plan["market"]["poolId"],
            "0xd600fd2ff936078114b72a01d3c6d31d449b7af12c24c82fb61efb7bf9c613ae",
        )
        self.assertEqual(
            plan["actor"]["address"].lower(),
            "0x04d5a0f57cb2e110fac9703024888cd4562b6d6f",
        )
        self.assertTrue(all(value is False for value in plan["authorization"].values()))

    def test_generator_has_no_network_wallet_signing_or_broadcast_import(self):
        source = SCRIPT.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_roots = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertTrue(
            imported_roots.isdisjoint(
                {"requests", "socket", "subprocess", "urllib", "web3"}
            )
        )
        self.assertNotIn("eth_sendRawTransaction", source)
        self.assertNotIn("eth_sendTransaction", source)

    def test_plan_is_deterministic_and_all_intents_are_hash_bound(self):
        first = self.build()
        second = self.build()
        self.assertEqual(first, second)
        self.assertEqual(first["transactionCount"], len(first["transactions"]))
        self.assertEqual(
            [tx["ordinal"] for tx in first["transactions"]], list(range(12))
        )
        for transaction in first["transactions"]:
            self.assertIsNone(transaction["nonce"])
            self.assertRegex(transaction["calldata"], r"^0x[0-9a-f]+$")
            self.assertEqual(
                transaction["calldataKeccak256"],
                "0x" + planner.keccak(bytes.fromhex(transaction["calldata"][2:])).hex(),
            )

    def test_committed_plan_is_exact_generator_output(self):
        self.assertEqual(json.loads(PLAN.read_text(encoding="utf-8")), self.build())
        self.assertNotIn(b"\r\n", PLAN.read_bytes())
        self.assertTrue(PLAN.read_bytes().endswith(b"\n"))

    def test_transaction_order_uses_direct_pool_initialization_and_cleans_allowances(
        self,
    ):
        plan = self.build()
        labels = [transaction["label"] for transaction in plan["transactions"]]
        self.assertEqual(
            labels,
            [
                "wrap bounded native ETH into WETH",
                "approve bounded PLTR to Permit2",
                "approve bounded WETH to Permit2",
                "approve bounded PLTR from Permit2 to PositionManager",
                "approve bounded WETH from Permit2 to PositionManager",
                "initialize exact PLTR/WETH pool directly through PoolManager",
                "mint bounded two-sided V4 liquidity position",
                "revoke PLTR Permit2-to-PositionManager allowance",
                "revoke WETH Permit2-to-PositionManager allowance",
                "revoke PLTR ERC20-to-Permit2 allowance",
                "revoke WETH ERC20-to-Permit2 allowance",
                "deploy and register Panoptic market; mint factory NFT to actor",
            ],
        )
        self.assertEqual(
            plan["transactions"][5]["to"].lower(),
            plan["contracts"]["poolManager"].lower(),
        )
        self.assertEqual(
            plan["transactions"][6]["to"].lower(),
            plan["contracts"]["positionManager"].lower(),
        )
        self.assertEqual(
            plan["transactions"][11]["to"].lower(),
            plan["contracts"]["panopticFactoryV4"].lower(),
        )

    def test_calldata_decodes_back_to_exact_liquidity_intent(self):
        plan = self.build()
        decoded = planner.decode_liquidity_calldata(plan["transactions"][6]["calldata"])
        self.assertEqual(decoded["actions"], "0x021212")
        self.assertEqual(decoded["poolKey"], plan["market"]["poolKey"])
        self.assertEqual(decoded["tickLower"], plan["priceAndLiquidity"]["tickLower"])
        self.assertEqual(decoded["tickUpper"], plan["priceAndLiquidity"]["tickUpper"])
        self.assertEqual(decoded["liquidity"], plan["priceAndLiquidity"]["liquidity"])
        self.assertEqual(decoded["owner"].lower(), plan["actor"]["address"].lower())

    def test_rejects_any_authorization_or_selection_substitution(self):
        acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
        selection = json.loads(SELECTION.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            acceptance_path = Path(directory) / "acceptance.json"
            changed = copy.deepcopy(acceptance)
            changed["authorization"]["wrapping"] = True
            acceptance_path.write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "authorization"):
                planner.build_plan(
                    acceptance_path, SELECTION, CHAIN, DEPLOYMENT, SCRIPT
                )

            selection_path = Path(directory) / "selection.json"
            changed_selection = copy.deepcopy(selection)
            changed_selection["candidates"][3]["poolId"] = "0x" + "11" * 32
            selection_path.write_text(json.dumps(changed_selection), encoding="utf-8")
            changed = copy.deepcopy(acceptance)
            changed["selectionBinding"]["sha256"] = planner.file_sha256(selection_path)
            acceptance_path.write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "PoolId"):
                planner.build_plan(
                    acceptance_path, selection_path, CHAIN, DEPLOYMENT, SCRIPT
                )


if __name__ == "__main__":
    unittest.main()
