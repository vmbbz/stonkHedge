import copy
import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "operate_robinhood_direct_deployment.py"
)
SPEC = importlib.util.spec_from_file_location("direct_operator", SCRIPT)
operator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(operator)


SENDER = "0x1111111111111111111111111111111111111111"
FIRST = "0x2222222222222222222222222222222222222222"
SECOND = "0x3333333333333333333333333333333333333333"
PLAN_HASH = "ab" * 32


def sample_plan():
    return {
        "schemaVersion": 1,
        "status": "SIMULATION_REQUIRED",
        "deploymentMethod": "EOA_CREATE",
        "chainId": 46630,
        "sender": SENDER,
        "startNonce": 0,
        "nextNonce": 2,
        "transactionCount": 2,
        "transactions": [
            {
                "ordinal": 0,
                "label": "first",
                "from": SENDER,
                "to": None,
                "nonce": 0,
                "valueWei": "0",
                "expectedCreatedAddress": FIRST,
                "initcodeBytes": 5,
                "initcodeHash": "0x" + "01" * 32,
                "initcode": "0x60006000f3",
            },
            {
                "ordinal": 1,
                "label": "second",
                "from": SENDER,
                "to": None,
                "nonce": 1,
                "valueWei": "0",
                "expectedCreatedAddress": SECOND,
                "initcodeBytes": 5,
                "initcodeHash": "0x" + "02" * 32,
                "initcode": "0x60006000f3",
            },
        ],
    }


def sample_report():
    return {
        "status": "PASS",
        "mode": "LOCAL_ANVIL_ONLY",
        "chainId": 46630,
        "sender": SENDER,
        "startNonce": 0,
        "nextNonce": 2,
        "planSha256": PLAN_HASH,
        "deployments": [
            {
                "label": "first",
                "nonce": 0,
                "expectedCreatedAddress": FIRST,
                "initcodeHash": "0x" + "01" * 32,
                "runtimeBytes": 2,
            },
            {
                "label": "second",
                "nonce": 1,
                "expectedCreatedAddress": SECOND,
                "initcodeHash": "0x" + "02" * 32,
                "runtimeBytes": 2,
            },
        ],
    }


def sample_operator_manifest():
    return {
        "status": "OPERATOR_RUNTIME_HASH_REPLAY_PASS_AUTHORIZATION_REQUIRED",
        "network": {"chainId": 46630},
        "artifactBindings": {
            "transactionPlanSha256": PLAN_HASH,
            "simulationReportSha256": "cd" * 32,
        },
        "expectedDeployments": [
            {
                "ordinal": 0,
                "label": "first",
                "address": FIRST,
                "runtimeBytes": 2,
                "runtimeCodeHash": "0x07ad118d6cc8642c86c03827f276d8b791a65e5c99a3845faf186be720a1455d",
            },
            {
                "ordinal": 1,
                "label": "second",
                "address": SECOND,
                "runtimeBytes": 2,
                "runtimeCodeHash": "0x07ad118d6cc8642c86c03827f276d8b791a65e5c99a3845faf186be720a1455d",
            },
        ],
    }


class FakeRpc:
    def __init__(self, *, nonce=0, codes=None, estimate=50_000, balance=10**18):
        self.nonce = nonce
        self.codes = {key.lower(): value for key, value in (codes or {}).items()}
        self.estimate = estimate
        self.balance = balance

    def call(self, method, params):
        if method == "eth_chainId":
            return hex(46630)
        if method == "eth_getBlockByNumber":
            return {
                "number": hex(123),
                "hash": "0x" + "44" * 32,
                "timestamp": hex(1_788_929_606),
            }
        if method == "eth_getTransactionCount":
            return hex(self.nonce)
        if method == "eth_getCode":
            return self.codes.get(params[0].lower(), "0x")
        if method == "eth_getBalance":
            return hex(self.balance)
        if method == "eth_gasPrice":
            return hex(10_000_000)
        if method == "eth_estimateGas":
            return hex(self.estimate)
        raise AssertionError(f"unexpected RPC method {method}")


class DirectOperatorTests(unittest.TestCase):
    def test_rlp_encode_known_values(self):
        self.assertEqual(operator.rlp_encode(b"dog").hex(), "83646f67")
        self.assertEqual(
            operator.rlp_encode([b"cat", b"dog"]).hex(),
            "c88363617483646f67",
        )
        self.assertEqual(operator.rlp_encode(0).hex(), "80")
        self.assertEqual(operator.rlp_encode(15).hex(), "0f")

    def test_parse_signature_accepts_recovery_byte(self):
        signature = "0x" + ("11" * 32) + ("22" * 32) + "1b"
        r, s, parity = operator.parse_signature(signature)
        self.assertEqual(r, int("11" * 32, 16))
        self.assertEqual(s, int("22" * 32, 16))
        self.assertEqual(parity, 0)

    def test_parse_signature_rejects_invalid_recovery_byte(self):
        signature = "0x" + ("11" * 32) + ("22" * 32) + "05"
        with self.assertRaisesRegex(ValueError, "recovery"):
            operator.parse_signature(signature)

    def test_signed_legacy_transaction_uses_eip155_v(self):
        raw = operator.build_signed_legacy_transaction(
            nonce=1,
            gas_price=10,
            gas_limit=100_000,
            data=bytes.fromhex("60006000f3"),
            chain_id=46630,
            r=1,
            s=2,
            parity=1,
        )
        self.assertTrue(raw.startswith("0x"))
        self.assertGreater(len(raw), 20)
        self.assertIn(operator.rlp_encode(2 * 46630 + 35 + 1).hex(), raw)

    def test_validate_plan_rejects_sender_substitution(self):
        plan = sample_plan()
        plan["transactions"][1]["from"] = FIRST
        with self.assertRaisesRegex(ValueError, "sender"):
            operator.validate_plan(
                plan,
                lambda _: plan["transactions"][0]["initcodeHash"],
                lambda _, nonce: FIRST if nonce == 0 else SECOND,
            )

    def test_validate_plan_rejects_nonconsecutive_nonce(self):
        plan = sample_plan()
        plan["transactions"][1]["nonce"] = 4
        with self.assertRaisesRegex(ValueError, "nonce"):
            operator.validate_plan(
                plan,
                lambda _: plan["transactions"][0]["initcodeHash"],
                lambda _, nonce: FIRST if nonce == 0 else SECOND,
            )

    def test_validate_report_binds_plan_and_runtime(self):
        operator.validate_simulation_report(sample_report(), sample_plan(), PLAN_HASH)
        report = sample_report()
        report["deployments"][1]["expectedCreatedAddress"] = FIRST
        with self.assertRaisesRegex(ValueError, "address"):
            operator.validate_simulation_report(report, sample_plan(), PLAN_HASH)

    def test_preflight_index_zero_requires_all_addresses_empty(self):
        rpc = FakeRpc(codes={SECOND: "0x6000"})
        with self.assertRaisesRegex(RuntimeError, "future.*not empty"):
            operator.validate_public_state(
                rpc,
                sample_plan(),
                sample_report(),
                sample_operator_manifest(),
                index=0,
                gas_limit=100_000,
                max_gas_price=100_000_000,
            )

    def test_preflight_continuation_requires_prior_runtime_size(self):
        rpc = FakeRpc(nonce=1, codes={FIRST: "0x60"})
        with self.assertRaisesRegex(RuntimeError, "runtime bytes"):
            operator.validate_public_state(
                rpc,
                sample_plan(),
                sample_report(),
                sample_operator_manifest(),
                index=1,
                gas_limit=100_000,
                max_gas_price=100_000_000,
            )

    def test_preflight_accepts_exact_continuation_state(self):
        rpc = FakeRpc(nonce=1, codes={FIRST: "0x6000"})
        result = operator.validate_public_state(
            rpc,
            sample_plan(),
            sample_report(),
            sample_operator_manifest(),
            index=1,
            gas_limit=100_000,
            max_gas_price=100_000_000,
        )
        self.assertEqual(result["nonce"], 1)
        self.assertEqual(result["gasPriceWei"], 10_000_000)

    def test_authorization_is_exact_and_not_reusable_for_other_plan(self):
        authorization = {
            "status": "AUTHORIZED_ONE_TRANSACTION_AT_A_TIME",
            "chainId": 46630,
            "sender": SENDER,
            "planSha256": PLAN_HASH,
            "maximumTransactionIndex": 1,
            "executionPolicy": "ONE_TRANSACTION_WAIT_VERIFY_STOP_ON_MISMATCH",
            "testnetOnly": True,
            "approvedBy": "owner",
            "approvedAt": "2026-09-09T00:00:00Z",
        }
        operator.validate_authorization(authorization, sample_plan(), PLAN_HASH, 1)
        changed = copy.deepcopy(authorization)
        changed["planSha256"] = "cd" * 32
        with self.assertRaisesRegex(ValueError, "plan"):
            operator.validate_authorization(changed, sample_plan(), PLAN_HASH, 1)

    def test_confirmation_phrase_binds_chain_plan_and_nonce(self):
        self.assertEqual(
            operator.confirmation_phrase(PLAN_HASH, 1),
            "BROADCAST_ROBINHOOD_46630_PLAN_abababab_NONCE_1",
        )


if __name__ == "__main__":
    unittest.main()
