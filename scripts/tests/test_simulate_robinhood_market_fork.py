import copy
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "simulate_robinhood_market_fork.py"
REPOSITORY = Path(__file__).resolve().parents[2]
PLAN_PATH = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-fork-plan-2026-09-09.json"
)

SPEC = importlib.util.spec_from_file_location("market_fork_simulator", SCRIPT)
simulator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(simulator)


class FakeRpc:
    def __init__(self, responses):
        self.responses = {key: list(values) for key, values in responses.items()}
        self.calls = []

    def call(self, method, params):
        self.calls.append((method, params))
        values = self.responses.get(method)
        if not values:
            raise AssertionError(f"unexpected RPC call: {method}")
        return values.pop(0)


class MarketForkSimulatorTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))

    def test_rejects_non_loopback_rpc(self):
        with self.assertRaisesRegex(ValueError, "loopback"):
            simulator.validate_local_rpc_url(
                "https://rpc.testnet.chain.robinhood.com"
            )
        with self.assertRaisesRegex(ValueError, "credentials"):
            simulator.validate_local_rpc_url("http://user:pass@127.0.0.1:8547")

    def test_committed_plan_is_exact_and_unauthorized(self):
        simulator.validate_fork_plan(self.plan, PLAN_PATH)
        changed = copy.deepcopy(self.plan)
        changed["transactions"][0]["authorizedForBroadcast"] = True
        with self.assertRaisesRegex(ValueError, "unauthorized"):
            simulator.validate_fork_plan(changed, PLAN_PATH)

        changed = copy.deepcopy(self.plan)
        changed["predictedMarketContracts"]["create3Proxy"] = "0x" + "11" * 20
        changed["forkPlanBodySha256"] = simulator.fork_planner.fork_plan_body_sha256(
            changed
        )
        with self.assertRaisesRegex(ValueError, "CREATE3 proxy"):
            simulator.validate_fork_plan(changed, PLAN_PATH)

    def test_rejects_non_anvil_before_any_mutation(self):
        rpc = FakeRpc({"web3_clientVersion": ["reth/v1.0"]})
        with self.assertRaisesRegex(RuntimeError, "non-Anvil"):
            simulator.assert_exact_fork(self.plan, rpc)
        self.assertEqual(rpc.calls, [("web3_clientVersion", [])])

    def test_rejects_wrong_chain_before_any_mutation(self):
        rpc = FakeRpc(
            {"web3_clientVersion": ["anvil/v1.8.1"], "eth_chainId": ["0x1"]}
        )
        with self.assertRaisesRegex(RuntimeError, "chain ID"):
            simulator.assert_exact_fork(self.plan, rpc)
        self.assertEqual(
            rpc.calls,
            [("web3_clientVersion", []), ("eth_chainId", [])],
        )

    def test_pool_deployed_event_decoder_rejects_wrong_topic(self):
        with self.assertRaisesRegex(ValueError, "PoolDeployed"):
            simulator.decode_pool_deployed_event(
                [{"topics": ["0x" + "00" * 32], "data": "0x"}]
            )

    def test_transaction_result_does_not_retain_calldata(self):
        transaction = {
            "ordinal": 0,
            "label": "test",
            "to": "0x" + "11" * 20,
            "valueWei": "0",
            "calldata": "0x1234",
            "calldataKeccak256": "0x" + "22" * 32,
        }
        receipt = {
            "transactionHash": "0x" + "33" * 32,
            "blockNumber": "0x2",
            "gasUsed": "0x5208",
            "status": "0x1",
        }
        result = simulator.transaction_result(transaction, receipt)
        self.assertNotIn("calldata", result)
        self.assertEqual(result["gasUsed"], 21000)

    def test_negative_case_does_not_treat_rpc_failure_as_pass(self):
        rpc = FakeRpc({"evm_snapshot": ["0x1"], "evm_revert": [True]})
        with patch.object(
            simulator, "_send", side_effect=RuntimeError("RPC request failed")
        ):
            with self.assertRaisesRegex(RuntimeError, "RPC request failed"):
                simulator._expect_revert_in_snapshot(
                    rpc,
                    self.plan,
                    5,
                    "test negative",
                    "0xff0000",
                    attempts=1,
                    interval_seconds=0,
                    sleep=lambda _: None,
                )
        self.assertEqual(
            rpc.calls,
            [("evm_snapshot", []), ("evm_revert", ["0x1"])],
        )


if __name__ == "__main__":
    unittest.main()
