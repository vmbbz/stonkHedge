import ast
import copy
import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "operate_robinhood_market_genesis.py"
REPOSITORY = Path(__file__).resolve().parents[2]
PLAN_PATH = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-execution-candidate-2026-09-10.json"
)

SPEC = importlib.util.spec_from_file_location("market_operator", SCRIPT)
operator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(operator)


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


class MarketOperatorTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))

    def test_committed_execution_candidate_is_exact_and_unauthorized(self):
        operator.validate_execution_plan(self.plan, PLAN_PATH)
        changed = copy.deepcopy(self.plan)
        changed["authorization"]["signing"] = True
        changed["executionPlanBodySha256"] = (
            operator.execution_planner.execution_plan_body_sha256(changed)
        )
        with self.assertRaisesRegex(ValueError, "authorization"):
            operator.validate_execution_plan(changed, PLAN_PATH)

    def test_rejects_public_or_credentialed_rpc(self):
        with self.assertRaisesRegex(ValueError, "loopback"):
            operator.validate_local_rpc_url("https://rpc.testnet.chain.robinhood.com")
        with self.assertRaisesRegex(ValueError, "credentials"):
            operator.validate_local_rpc_url("http://user:pass@127.0.0.1:8547")

    def test_rejects_non_anvil_before_mutation(self):
        rpc = FakeRpc({"web3_clientVersion": ["reth/v1.0"]})
        with self.assertRaisesRegex(RuntimeError, "non-Anvil"):
            operator.ensure_anvil_lineage(self.plan, rpc)
        self.assertEqual(rpc.calls, [("web3_clientVersion", [])])

    def test_allowance_state_windows_match_twelve_step_sequence(self):
        maximum_pltr = int(self.plan["maximumExposure"]["maximumPltrTransfer"])
        maximum_weth = int(self.plan["maximumExposure"]["maximumWethTransfer"])
        self.assertEqual(operator.expected_allowances(self.plan, 0), (0, 0, 0, 0))
        self.assertEqual(
            operator.expected_allowances(self.plan, 5),
            (maximum_pltr, maximum_weth, maximum_pltr, maximum_weth),
        )
        self.assertEqual(
            operator.expected_allowances(self.plan, 8),
            (
                maximum_pltr
                - int(
                    self.plan["priceAndLiquidity"][
                        "expectedAmount0AtSyntheticPriceRoundedUp"
                    ]
                ),
                maximum_weth
                - int(
                    self.plan["priceAndLiquidity"][
                        "expectedAmount1AtSyntheticPriceRoundedUp"
                    ]
                ),
                0,
                maximum_weth
                - int(
                    self.plan["priceAndLiquidity"][
                        "expectedAmount1AtSyntheticPriceRoundedUp"
                    ]
                ),
            ),
        )
        self.assertEqual(
            operator.expected_allowances(self.plan, 12), (0, 0, 0, 0)
        )

    def test_step_result_is_sanitized(self):
        receipt = {
            "transactionHash": "0x" + "11" * 32,
            "blockNumber": "0x10",
            "gasUsed": "0x5208",
            "effectiveGasPrice": "0x1",
            "status": "0x1",
        }
        result = operator.step_result(self.plan["transactions"][0], receipt)
        self.assertNotIn("calldata", result)
        self.assertEqual(result["nonce"], self.plan["startNonce"])
        self.assertEqual(result["gasUsed"], 21000)

    def test_authorization_must_bind_plan_operator_simulation_and_index(self):
        authorization = {
            "status": "AUTHORIZED_MARKET_GENESIS_ONE_TRANSACTION_AT_A_TIME",
            "chainId": 46630,
            "actor": self.plan["actor"]["address"],
            "executionPlanBodySha256": self.plan["executionPlanBodySha256"],
            "executionPlanFileSha256": "11" * 32,
            "operatorSha256": "22" * 32,
            "operatorSimulationReportSha256": "33" * 32,
            "maximumTransactionIndex": 4,
            "executionPolicy": "ONE_TRANSACTION_WAIT_VERIFY_STOP_ON_MISMATCH",
            "testnetOnly": True,
            "approvedBy": "owner",
            "approvedAt": "2026-09-10T00:00:00Z",
        }
        operator.validate_authorization(
            authorization,
            self.plan,
            index=4,
            plan_file_hash="11" * 32,
            operator_hash="22" * 32,
            simulation_report_hash="33" * 32,
        )
        changed = copy.deepcopy(authorization)
        changed["maximumTransactionIndex"] = 3
        with self.assertRaisesRegex(ValueError, "index"):
            operator.validate_authorization(
                changed,
                self.plan,
                index=4,
                plan_file_hash="11" * 32,
                operator_hash="22" * 32,
                simulation_report_hash="33" * 32,
            )
        changed = copy.deepcopy(authorization)
        changed["maximumTransactionIndex"] = 12
        with self.assertRaisesRegex(ValueError, "maximum transaction index"):
            operator.validate_authorization(
                changed,
                self.plan,
                index=4,
                plan_file_hash="11" * 32,
                operator_hash="22" * 32,
                simulation_report_hash="33" * 32,
            )

    def test_confirmation_binds_plan_index_and_nonce(self):
        phrase = operator.confirmation_phrase("11" * 32, 3, 3)
        self.assertEqual(
            phrase,
            "BROADCAST_ROBINHOOD_46630_MARKET_PLAN_11111111_INDEX_3_NONCE_3",
        )

    def test_legacy_encoding_commits_recipient_value_and_chain(self):
        unsigned = operator.unsigned_legacy_transaction(
            nonce=0,
            gas_price=1,
            gas_limit=21000,
            to="0x" + "11" * 20,
            value=2,
            data=bytes.fromhex("1234"),
            chain_id=46630,
        )
        self.assertEqual(
            unsigned.hex(),
            "e380018252089411111111111111111111111111111111111111110282123482b6268080",
        )
        signed = operator.build_signed_legacy_transaction(
            nonce=0,
            gas_price=1,
            gas_limit=21000,
            to="0x" + "11" * 20,
            value=2,
            data=bytes.fromhex("1234"),
            chain_id=46630,
            r=3,
            s=4,
            parity=1,
        )
        self.assertEqual(
            signed,
            "0xe480018252089411111111111111111111111111111111111111110282123483016c700304",
        )

    def test_mined_transaction_must_match_every_signed_intent_field(self):
        transaction = self.plan["transactions"][0]
        transaction_hash = "0x" + "11" * 32
        block_hash = "0x" + "22" * 32
        receipt = {
            "transactionHash": transaction_hash,
            "blockNumber": "0x10",
            "blockHash": block_hash,
            "transactionIndex": "0x0",
            "gasUsed": "0x5208",
            "effectiveGasPrice": "0x1",
        }
        rpc = FakeRpc(
            {
                "eth_getTransactionByHash": [
                    {
                        "from": self.plan["actor"]["address"],
                        "to": transaction["to"],
                        "nonce": hex(transaction["nonce"]),
                        "value": hex(int(transaction["valueWei"])),
                        "input": transaction["calldata"],
                        "blockHash": block_hash,
                    }
                ]
            }
        )
        mined = operator.verify_mined_transaction(
            rpc,
            self.plan,
            0,
            transaction_hash,
            transaction_hash,
            receipt,
            100_000,
        )
        self.assertEqual(mined["nonce"], 0)
        self.assertEqual(mined["calldataKeccak256"], transaction["calldataKeccak256"])

        changed = copy.deepcopy(receipt)
        changed["transactionHash"] = "0x" + "33" * 32
        rpc = FakeRpc(
            {
                "eth_getTransactionByHash": [
                    {
                        "from": self.plan["actor"]["address"],
                        "to": transaction["to"],
                        "nonce": hex(transaction["nonce"]),
                        "value": hex(int(transaction["valueWei"])),
                        "input": transaction["calldata"],
                        "blockHash": block_hash,
                    }
                ]
            }
        )
        with self.assertRaisesRegex(RuntimeError, "receipt transaction hash"):
            operator.verify_mined_transaction(
                rpc,
                self.plan,
                0,
                transaction_hash,
                transaction_hash,
                changed,
                100_000,
            )

    def test_simulation_report_must_bind_current_operator(self):
        report_path = (
            REPOSITORY
            / "manifests"
            / "markets"
            / "robinhood-testnet-pltr-weth-execution-operator-simulation-2026-09-10.json"
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        changed = copy.deepcopy(report)
        changed["sourceBindings"]["operatorSha256"] = "ff" * 32
        with self.assertRaisesRegex(ValueError, "operatorSha256"):
            operator.validate_simulation_report(
                changed,
                self.plan,
                plan_file_hash=operator.file_sha256(PLAN_PATH),
                operator_hash=operator.file_sha256(SCRIPT),
            )

    def test_market_aware_qualification_allows_only_planned_initialization(self):
        preflight_path = (
            REPOSITORY
            / "manifests"
            / "markets"
            / "robinhood-testnet-pltr-weth-execution-preflight-2026-09-10.json"
        )
        preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
        qualification = {
            "status": preflight["qualificationChecks"].get(
                "status", "READ_ONLY_QUALIFICATION_PASS_PLTR"
            ),
            "checks": copy.deepcopy(preflight["qualificationChecks"]),
        }
        operator.validate_market_aware_qualification(qualification, self.plan, 5)

        initialized = copy.deepcopy(qualification)
        initialized["status"] = "BLOCKED_READ_ONLY_QUALIFICATION_FAILED"
        target = next(
            check
            for check in initialized["checks"]["results"]
            if check["name"] == "PLTR V4 PoolId is uninitialized"
        )
        target["status"] = "FAIL"
        target["actual"] = {
            "poolId": self.plan["market"]["poolId"],
            "sqrtPriceX96": self.plan["priceAndLiquidity"]["sqrtPriceX96"],
        }
        operator.validate_market_aware_qualification(initialized, self.plan, 6)
        target["actual"]["sqrtPriceX96"] = "1"
        with self.assertRaisesRegex(RuntimeError, "differs"):
            operator.validate_market_aware_qualification(initialized, self.plan, 6)

    def test_operator_source_has_explicit_live_gates(self):
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
        self.assertNotIn("subprocess", imported_roots)
        self.assertIn("eth_sendRawTransaction", source)
        self.assertIn("--authorization-manifest", source)
        self.assertIn("--confirmation", source)
        self.assertIn("--keystore", source)


if __name__ == "__main__":
    unittest.main()
