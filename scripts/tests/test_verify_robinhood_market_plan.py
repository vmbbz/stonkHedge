import copy
import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "verify_robinhood_market_plan.py"
REPOSITORY = Path(__file__).resolve().parents[2]
PLAN_PATH = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-offline-plan-2026-09-09.json"
)

SPEC = importlib.util.spec_from_file_location("market_verifier", SCRIPT)
verifier = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(verifier)


def sample_qualification(plan):
    return {
        "status": "READ_ONLY_QUALIFICATION_PASS_PLTR_RECOMMENDED_OWNER_ACCEPTANCE_REQUIRED",
        "qualificationMode": "READ_ONLY_NO_KEYS_NO_SIGNING_NO_BROADCAST",
        "snapshot": {
            "blockNumber": 123,
            "blockHash": "0x" + "44" * 32,
            "blockTimestamp": "2026-09-09T20:00:00Z",
        },
        "configuration": {
            "fee": 3000,
            "tickSpacing": 60,
            "hooks": verifier.ZERO_ADDRESS,
            "riskEngine": plan["contracts"]["riskEngine"],
            "poolManager": plan["contracts"]["poolManager"],
            "positionManager": plan["contracts"]["positionManager"],
            "stateView": plan["contracts"]["stateView"],
            "weth": plan["contracts"]["weth"],
            "panopticFactoryV4": plan["contracts"]["panopticFactoryV4"],
        },
        "accounts": {
            "secondActor": {
                "address": plan["actor"]["address"],
                "nativeBalanceWei": "10000000000000000",
                "confirmedNonce": 0,
                "wethBalance": "0",
                "stockBalances": {"PLTR": "5000000000000000000"},
                "blockedByStockRegistry": False,
            }
        },
        "candidates": [
            {
                "symbol": "PLTR",
                "stockToken": plan["contracts"]["pltr"],
                "poolKey": plan["market"]["poolKey"],
                "poolId": plan["market"]["poolId"],
                "poolInitialized": False,
                "slot0": {"sqrtPriceX96": "0", "tick": 0},
                "existingPanopticPool": verifier.ZERO_ADDRESS,
                "eligible": True,
                "blockers": [],
                "actorBalance": "5000000000000000000",
            }
        ],
        "checks": {"passed": 79, "failed": 0, "results": []},
    }


class FakeRpc:
    def __init__(self, plan, *, erc_allowance=0, permit_amount=0, active_liquidity=0):
        self.plan = plan
        self.erc_allowance = erc_allowance
        self.permit_amount = permit_amount
        self.active_liquidity = active_liquidity

    def call(self, method, params):
        if method == "eth_getTransactionCount":
            return "0x0"
        if method == "eth_getCode":
            return "0x"
        if method != "eth_call":
            raise AssertionError(f"unexpected method {method}")
        target = params[0]["to"].lower()
        selector = params[0]["data"][:10]
        if selector == verifier.function_selector_hex("allowance(address,address)"):
            return verifier.encode_return(["uint256"], [self.erc_allowance])
        if selector == verifier.function_selector_hex(
            "allowance(address,address,address)"
        ):
            return verifier.encode_return(
                ["uint160", "uint48", "uint48"], [self.permit_amount, 0, 0]
            )
        if target == self.plan["contracts"]["positionManager"].lower():
            return verifier.encode_return(["uint256"], [3732])
        if target == self.plan["contracts"]["stateView"].lower():
            return verifier.encode_return(["uint128"], [self.active_liquidity])
        raise AssertionError(f"unexpected call target {target} selector {selector}")


class MarketVerifierTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))

    def test_committed_plan_passes_static_integrity(self):
        verifier.validate_offline_plan(self.plan, PLAN_PATH)

    def test_static_integrity_rejects_calldata_or_authorization_mutation(self):
        changed = copy.deepcopy(self.plan)
        changed["transactions"][0]["calldata"] = "0x00"
        with self.assertRaisesRegex(ValueError, "calldata"):
            verifier.validate_offline_plan(changed, PLAN_PATH)
        changed = copy.deepcopy(self.plan)
        changed["authorization"]["wrapping"] = True
        with self.assertRaisesRegex(ValueError, "authorization"):
            verifier.validate_offline_plan(changed, PLAN_PATH)

    def test_static_integrity_rejects_rehashed_non_generator_plan(self):
        changed = copy.deepcopy(self.plan)
        changed["priceAndLiquidity"]["liquidity"] = "1"
        body = {field: changed[field] for field in verifier.PLAN_BODY_FIELDS}
        changed["planBodySha256"] = verifier.planner.canonical_sha256(body)
        with self.assertRaisesRegex(ValueError, "exact output"):
            verifier.validate_offline_plan(changed, PLAN_PATH)

    def test_initial_preflight_passes_only_fully_empty_market_state(self):
        report = verifier.verify_initial_prestate(
            FakeRpc(self.plan), self.plan, sample_qualification(self.plan)
        )
        self.assertEqual(report["status"], "PASS_INITIAL_MARKET_PREFLIGHT")
        self.assertEqual(report["checks"]["failed"], 0)
        self.assertEqual(report["observations"]["positionManagerNextTokenId"], "3732")
        self.assertEqual(report["observations"]["actorPendingNonce"], 0)

    def test_nonzero_allowance_or_active_liquidity_blocks(self):
        allowance = verifier.verify_initial_prestate(
            FakeRpc(self.plan, erc_allowance=1),
            self.plan,
            sample_qualification(self.plan),
        )
        self.assertTrue(allowance["status"].startswith("BLOCKED"))
        self.assertGreater(allowance["checks"]["failed"], 0)
        liquidity = verifier.verify_initial_prestate(
            FakeRpc(self.plan, active_liquidity=1),
            self.plan,
            sample_qualification(self.plan),
        )
        self.assertTrue(liquidity["status"].startswith("BLOCKED"))

    def test_qualification_failure_or_wrong_pool_blocks(self):
        qualification = sample_qualification(self.plan)
        qualification["checks"]["failed"] = 1
        qualification["status"] = "BLOCKED_READ_ONLY_QUALIFICATION_FAILED"
        report = verifier.verify_initial_prestate(
            FakeRpc(self.plan), self.plan, qualification
        )
        self.assertTrue(report["status"].startswith("BLOCKED"))

        qualification = sample_qualification(self.plan)
        qualification["candidates"][0]["poolId"] = "0x" + "11" * 32
        report = verifier.verify_initial_prestate(
            FakeRpc(self.plan), self.plan, qualification
        )
        self.assertTrue(report["status"].startswith("BLOCKED"))

    def test_verifier_rpc_surface_is_read_only(self):
        self.assertTrue(
            verifier.RPC_METHODS.issubset(
                {
                    "eth_chainId",
                    "eth_blockNumber",
                    "eth_getBlockByNumber",
                    "eth_getCode",
                    "eth_call",
                    "eth_getBalance",
                    "eth_getTransactionCount",
                }
            )
        )
        self.assertNotIn("eth_sendRawTransaction", SCRIPT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
