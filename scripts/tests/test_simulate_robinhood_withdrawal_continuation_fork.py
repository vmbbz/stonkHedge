import copy
import importlib.util
import unittest
from pathlib import Path

from eth_abi import encode as abi_encode


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "simulate_robinhood_withdrawal_continuation_fork.py"
)
SPEC = importlib.util.spec_from_file_location("withdrawal_simulator", SCRIPT)
simulator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(simulator)


class WithdrawalSimulatorTests(unittest.TestCase):
    def setUp(self):
        self.withdrawal = simulator.load_json(simulator.DEFAULT_WITHDRAWAL_PLAN)
        self.lifecycle = simulator.load_json(simulator.DEFAULT_LIFECYCLE_PLAN)
        self.report = simulator.load_json(simulator.DEFAULT_LIFECYCLE_REPORT)

    def test_committed_plan_is_bound_and_ordered(self):
        simulator.validate_plan(
            self.withdrawal,
            self.lifecycle,
            simulator.DEFAULT_LIFECYCLE_PLAN,
            self.report,
            simulator.DEFAULT_LIFECYCLE_REPORT,
        )
        self.assertEqual(
            [transaction["ordinal"] for transaction in self.withdrawal["transactions"]],
            [0, 1, 2, 3],
        )
        self.assertTrue(
            all(transaction["nonce"] is None for transaction in self.withdrawal["transactions"])
        )

    def test_decodes_exact_tracker_withdraw_event(self):
        tracker = self.withdrawal["transactions"][0]["to"]
        topic0 = "0x" + simulator.qualifier.keccak(
            b"Withdraw(address,address,address,uint256,uint256)"
        ).hex()
        receipt = {
            "logs": [
                {
                    "address": tracker,
                    "topics": [topic0, "0x01", "0x02", "0x03"],
                    "data": "0x" + abi_encode(["uint256", "uint256"], [123, 456]).hex(),
                }
            ]
        }
        self.assertEqual(simulator.withdrawal_event(receipt, tracker), (123, 456))

        owner = self.withdrawal["transactions"][0]["sender"]
        transfer_topic = "0x" + simulator.qualifier.keccak(
            b"Transfer(address,address,uint256)"
        ).hex()
        owner_topic = "0x" + owner[2:].lower().rjust(64, "0")
        receipt["logs"].extend(
            [
                {
                    "address": tracker,
                    "topics": [transfer_topic, owner_topic, "0x" + "00" * 32],
                    "data": "0x" + abi_encode(["uint256"], [1]).hex(),
                },
                {
                    "address": tracker,
                    "topics": [transfer_topic, owner_topic, "0x" + "00" * 32],
                    "data": "0x" + abi_encode(["uint256"], [456]).hex(),
                },
            ]
        )
        self.assertEqual(simulator.receipt_burned_shares(receipt, tracker, owner), 457)

    def test_postcondition_uses_event_share_burn_not_pre_accrual_preview(self):
        transaction = self.withdrawal["transactions"][0]
        role = "buyer"
        assets = int(transaction["decodedIntent"]["assets"])
        before = {
            role: {
                "pltrBalance": "100",
                "tracker0Shares": "1000",
            }
        }
        after = {
            role: {
                "pltrBalance": str(100 + assets),
                "tracker0Shares": "599",
            }
        }
        result = simulator.assert_withdrawal_postconditions(
            self.lifecycle,
            transaction,
            before,
            after,
            pre_accrual_preview_shares=401,
            event_assets=assets,
            event_shares=400,
            receipt_burned_shares=401,
        )
        self.assertEqual(result["sharesBurned"], "401")
        self.assertEqual(result["interestAccrualSharesBurned"], "1")
        self.assertEqual(result["preAccrualPreviewWithdrawShares"], "401")
        self.assertEqual(
            result["status"],
            "PASS_EXACT_ASSETS_AND_RECEIPT_RECONCILED_SHARE_BURNS",
        )

        changed = copy.deepcopy(after)
        changed[role]["tracker0Shares"] = "598"
        with self.assertRaisesRegex(RuntimeError, "share burn drifted"):
            simulator.assert_withdrawal_postconditions(
                self.lifecycle,
                transaction,
                before,
                changed,
                pre_accrual_preview_shares=401,
                event_assets=assets,
                event_shares=400,
                receipt_burned_shares=400,
            )

    def test_source_has_loopback_guard_and_no_wallet_or_signing_primitive(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("validate_local_rpc_url", source)
        self.assertIn("anvil_impersonateAccount", source)
        self.assertNotIn("private_key", source.lower())
        self.assertNotIn("keystore", source.lower())
        self.assertNotIn("cast wallet", source.lower())
        self.assertNotIn("eth_sendRawTransaction", source)


if __name__ == "__main__":
    unittest.main()
