import ast
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "prepare_robinhood_market_fork_plan.py"
)
REPOSITORY = Path(__file__).resolve().parents[2]
BASE_PLAN = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-offline-plan-2026-09-09.json"
)
PREFLIGHT = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-initial-preflight-2026-09-09.json"
)

SPEC = importlib.util.spec_from_file_location("market_fork_planner", SCRIPT)
fork_planner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(fork_planner)


class MarketForkPlanTests(unittest.TestCase):
    def build(self):
        return fork_planner.build_fork_plan(BASE_PLAN, PREFLIGHT, SCRIPT)

    def test_builds_fork_only_plan_at_exact_preflight_head(self):
        plan = self.build()
        preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
        reference_timestamp = fork_planner._unix_timestamp(
            preflight["network"]["blockTimestamp"]
        )
        self.assertEqual(plan["status"], "FORK_REHEARSAL_ONLY_NO_PUBLIC_BROADCAST")
        self.assertEqual(
            plan["network"]["forkBlock"], preflight["network"]["blockNumber"]
        )
        self.assertEqual(
            plan["network"]["forkBlockHash"],
            preflight["network"]["blockHash"],
        )
        self.assertEqual(
            plan["forkClock"]["referenceTimestampUnix"], reference_timestamp
        )
        self.assertEqual(
            plan["forkClock"]["localCompatibilityTimestampUnix"],
            reference_timestamp + 1,
        )
        self.assertEqual(
            plan["forkClock"]["liquidityDeadlineUnix"], reference_timestamp + 3600
        )
        self.assertEqual(
            plan["forkClock"]["permit2ExpirationUnix"], reference_timestamp + 7200
        )
        self.assertFalse(plan["publicExecution"]["ready"])
        self.assertTrue(all(value is False for value in plan["authorization"].values()))
        self.assertEqual(
            plan["predictedMarketContracts"]["create3Proxy"],
            "0xa7b2ac1231363a675d987c9bc326417d9fc50409",
        )

    def test_only_deadline_bound_transactions_change(self):
        base = json.loads(BASE_PLAN.read_text(encoding="utf-8"))
        plan = self.build()
        changed = [
            index
            for index, transaction in enumerate(plan["transactions"])
            if transaction["calldata"] != base["transactions"][index]["calldata"]
        ]
        self.assertEqual(changed, [3, 4, 6])
        self.assertEqual(
            plan["transactions"][3]["decodedIntent"]["expiration"],
            plan["forkClock"]["permit2ExpirationUnix"],
        )
        decoded = fork_planner.planner.decode_liquidity_calldata(
            plan["transactions"][6]["calldata"]
        )
        self.assertEqual(decoded["deadline"], plan["forkClock"]["liquidityDeadlineUnix"])
        self.assertEqual(decoded["liquidity"], plan["priceAndLiquidity"]["liquidity"])

    def test_is_deterministic_and_keeps_nonces_unset(self):
        first = self.build()
        self.assertEqual(first, self.build())
        self.assertEqual(
            first["forkPlanBodySha256"], fork_planner.fork_plan_body_sha256(first)
        )
        for transaction in first["transactions"]:
            self.assertIsNone(transaction["nonce"])
            self.assertFalse(transaction["authorizedForBroadcast"])

    def test_rejects_preflight_or_source_substitution(self):
        preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preflight.json"
            changed = copy.deepcopy(preflight)
            changed["publicExecution"]["ready"] = True
            path.write_text(json.dumps(changed), encoding="utf-8", newline="\n")
            with self.assertRaisesRegex(ValueError, "public execution"):
                fork_planner.build_fork_plan(BASE_PLAN, path, SCRIPT)

            changed = copy.deepcopy(preflight)
            changed["plan"]["planBodySha256"] = "00" * 32
            path.write_text(json.dumps(changed), encoding="utf-8", newline="\n")
            with self.assertRaisesRegex(ValueError, "plan body"):
                fork_planner.build_fork_plan(BASE_PLAN, path, SCRIPT)

    def test_generator_has_no_network_key_signing_or_broadcast_capability(self):
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

    def test_create3_proxy_prediction_rejects_malformed_salt(self):
        with self.assertRaisesRegex(ValueError, "CREATE3 salt"):
            fork_planner.predict_create3_proxy("0x" + "11" * 20, "0x1234")


if __name__ == "__main__":
    unittest.main()
