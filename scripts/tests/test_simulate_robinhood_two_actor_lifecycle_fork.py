import copy
import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "simulate_robinhood_two_actor_lifecycle_fork.py"
)
SPEC = importlib.util.spec_from_file_location("lifecycle_simulator", SCRIPT)
simulator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(simulator)


class LifecycleForkSimulatorTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(simulator.DEFAULT_PLAN.read_text(encoding="utf-8"))

    def test_committed_plan_passes_strict_offline_validation(self):
        simulator.validate_plan(self.plan, simulator.DEFAULT_PLAN)

    def test_only_http_loopback_rpc_is_allowed(self):
        for allowed in (
            "http://127.0.0.1:8548",
            "http://localhost:8548",
            "http://[::1]:8548",
        ):
            simulator.validate_local_rpc_url(allowed)
        for rejected in (
            "https://rpc.testnet.chain.robinhood.com",
            "http://192.0.2.1:8548",
            "ws://127.0.0.1:8548",
            "http://user:pass@127.0.0.1:8548",
            "http://127.0.0.1",
            "http://127.0.0.1:8548/path",
        ):
            with self.assertRaises(ValueError):
                simulator.validate_local_rpc_url(rejected)

    def test_rejects_authority_nonce_and_target_expansion(self):
        authorized = copy.deepcopy(self.plan)
        authorized["authorization"]["signing"] = True
        with self.assertRaisesRegex(ValueError, "authorization"):
            simulator.validate_plan(authorized, simulator.DEFAULT_PLAN)

        nonce_bound = copy.deepcopy(self.plan)
        nonce_bound["transactions"][0]["nonce"] = 16
        with self.assertRaisesRegex(ValueError, "binds a nonce"):
            simulator.validate_plan(nonce_bound, simulator.DEFAULT_PLAN)

        admin_target = copy.deepcopy(self.plan)
        admin_target["transactions"][0]["to"] = admin_target["market"][
            "stockRegistry"
        ]
        with self.assertRaisesRegex(ValueError, "outside the user-call allowlist"):
            simulator.validate_plan(admin_target, simulator.DEFAULT_PLAN)

    def test_source_has_no_wallet_or_signing_import(self):
        source = SCRIPT.read_text(encoding="utf-8")
        tree = compile(source, str(SCRIPT), "exec", flags=0, dont_inherit=True)
        self.assertIsNotNone(tree)
        self.assertNotIn("eth_sendRawTransaction", source)
        self.assertNotIn("private_key", source.lower())
        self.assertNotIn("keystore", source.lower())
        self.assertNotIn("cast wallet", source.lower())
        self.assertEqual(simulator.DEFAULT_RPC_URL, "http://127.0.0.1:8548")

    def _external_state(self):
        runtime_names = (
            "stockRegistry",
            "pltr",
            "weth",
            "permit2",
            "universalRouter",
            "stateView",
            "panopticPool",
            "collateralTracker0",
            "collateralTracker1",
        )
        runtimes = {
            name: {
                "runtimeBytes": index + 1,
                "runtimeCodeHash": "0x" + f"{index + 1:02x}" * 32,
            }
            for index, name in enumerate(runtime_names)
        }
        wiring = {
            "pltrRegistry": self.plan["market"]["stockRegistry"].lower(),
            "panopticPoolCollateral0": self.plan["market"]["collateralTracker0"].lower(),
            "panopticPoolCollateral1": self.plan["market"]["collateralTracker1"].lower(),
            "panopticPoolManager": "0x" + "10" * 20,
            "panopticPoolRiskEngine": "0x" + "20" * 20,
            "panopticPoolSfpm": "0x" + "30" * 20,
            "panopticPoolNumericId": self.plan["market"]["sfpmPoolId"],
            "tracker0Pool": self.plan["market"]["panopticPool"].lower(),
            "tracker0Underlying": self.plan["market"]["pltr"].lower(),
            "tracker1Pool": self.plan["market"]["panopticPool"].lower(),
            "tracker1Underlying": self.plan["market"]["weth"].lower(),
        }
        controls = {
            "registryPaused": False,
            "tokenPaused": False,
            "uiMultiplier": "1000000000000000000",
            "newUIMultiplier": "1000000000000000000",
            "effectiveAt": "0",
            "writerBlocked": False,
            "buyerBlocked": False,
        }
        return {
            "chainId": 46630,
            "computedPoolId": self.plan["market"]["poolId"],
            "runtimes": copy.deepcopy(runtimes),
            "expectedRuntimes": copy.deepcopy(runtimes),
            "stockControls": copy.deepcopy(controls),
            "requiredStockState": copy.deepcopy(controls),
            "wiring": copy.deepcopy(wiring),
            "expectedWiring": copy.deepcopy(wiring),
        }

    def _initial_state(self):
        def actor(role):
            expected = self.plan["roles"][role]
            return {
                "nonce": expected["confirmedNonce"],
                "nativeBalanceWei": expected["nativeBalanceWei"],
                "pltrBalance": expected["pltrBalance"],
                "wethBalance": expected["wethBalance"],
                "tracker0Shares": expected["collateralTracker0Shares"],
                "tracker1Shares": expected["collateralTracker1Shares"],
                "openLegs": expected["openLegs"],
                "pltrToPermit2": "0",
                "wethToPermit2": "0",
                "pltrToTracker0": "0",
                "wethToTracker1": "0",
                "pltrPermit2ToRouter": [0, 0, 0],
                "wethPermit2ToRouter": [0, 0, 0],
            }

        return {
            "pool": {
                "tick": self.plan["market"]["referenceTick"],
                "activeLiquidity": self.plan["market"]["referenceActiveLiquidity"],
            },
            "writer": actor("writer"),
            "buyer": actor("buyer"),
        }

    def test_adverse_external_state_mutations_are_fail_closed(self):
        external = self._external_state()
        initial = self._initial_state()
        self.assertEqual(
            simulator._computed_pool_id(self.plan),
            "0xd600fd2ff936078114b72a01d3c6d31d449b7af12c24c82fb61efb7bf9c613ae",
        )
        simulator._assert_external_state(self.plan, external)
        simulator._assert_initial_state(self.plan, initial)

        results = simulator.rehearse_adverse_preflight_rejections(
            self.plan, external, initial
        )
        self.assertEqual(len(results), 8)
        self.assertTrue(
            all(
                result["status"] == "PASS_REJECTED_BY_FAIL_CLOSED_PREFLIGHT"
                for result in results
            )
        )
        self.assertEqual(
            {result["name"] for result in results},
            {
                "wrong PoolId",
                "runtime bytecode drift",
                "immutable wiring drift",
                "Stock registry paused",
                "writer blocked by Stock registry",
                "Stock Token UI multiplier drift",
                "writer balance below frozen PLTR snapshot",
                "elevated buyer tracker allowance",
            },
        )

    def test_swap_minimum_output_postcondition_rejects_shortfall(self):
        transaction = self.plan["transactions"][5]
        before = self._initial_state()
        after = copy.deepcopy(before)
        amount_in = int(transaction["decodedIntent"]["amountIn"])
        minimum_out = int(transaction["decodedIntent"]["amountOutMinimum"])
        after["writer"]["pltrBalance"] = str(
            int(before["writer"]["pltrBalance"]) - amount_in
        )
        after["writer"]["wethBalance"] = str(
            int(before["writer"]["wethBalance"]) + minimum_out - 1
        )

        with self.assertRaisesRegex(RuntimeError, "below committed minimum"):
            simulator.assert_swap_postconditions(
                self.plan, transaction, before, after
            )

        after["writer"]["wethBalance"] = str(
            int(before["writer"]["wethBalance"]) + minimum_out
        )
        result = simulator.assert_swap_postconditions(
            self.plan, transaction, before, after
        )
        self.assertEqual(result["status"], "PASS_EXACT_INPUT_AND_MINIMUM_OUTPUT")


if __name__ == "__main__":
    unittest.main()
