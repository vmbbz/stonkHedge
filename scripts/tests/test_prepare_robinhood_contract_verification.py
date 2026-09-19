import importlib.util
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "prepare_robinhood_contract_verification.py"
)
SPEC = importlib.util.spec_from_file_location("contract_verifier", SCRIPT)
verifier = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(verifier)


class ContractVerificationPreparationTests(unittest.TestCase):
    def test_unverified_clone_payload_is_compact_and_classified(self):
        result = verifier.classify_explorer_payload(
            {
                "creation_status": "success",
                "deployed_bytecode": "0x1234",
                "proxy_type": "clone_with_immutable_arguments",
                "implementations": [
                    {"address_hash": "0x" + "11" * 20, "name": None}
                ],
            }
        )
        self.assertEqual(result["status"], "BYTECODE_ONLY")
        self.assertEqual(result["proxyType"], "clone_with_immutable_arguments")
        self.assertEqual(result["implementations"][0]["address"], "0x" + "11" * 20)
        self.assertNotIn("deployed_bytecode", result)

    def test_verified_payload_records_reproducibility_fields_only(self):
        result = verifier.classify_explorer_payload(
            {
                "source_code": "contract Example {}",
                "name": "Example",
                "file_path": "src/Example.sol",
                "compiler_version": "v0.8.28",
                "optimization_enabled": True,
                "optimization_runs": 200,
                "evm_version": "cancun",
                "verified_at": "2026-09-19T00:00:00Z",
                "creation_status": "success",
                "implementations": [],
            }
        )
        self.assertEqual(result["status"], "SOURCE_VERIFIED")
        self.assertEqual(result["contractName"], "Example")
        self.assertNotIn("source_code", result)

    def test_command_is_blockscout_specific_and_never_executes(self):
        config = {
            "env": {},
            "dataContracts": [],
            "logicContracts": {
                "Example": {
                    "path": "./contracts/Example.sol",
                    "deployment": {"address": "0x" + "22" * 20},
                    "optimizeRuns": 9999999,
                }
            },
        }
        original_inject = verifier._inject_metadata
        verifier._inject_metadata = lambda _config, _path: None
        try:
            command = verifier.build_verification_command(
                config, Path("unused.json"), "Example"
            )
        finally:
            verifier._inject_metadata = original_inject
        self.assertIn("blockscout", command)
        self.assertIn(verifier.DEFAULT_VERIFIER_URL, command)
        self.assertEqual(command[-1], "--watch")
        self.assertNotIn("cast wallet", " ".join(command))

    def test_committed_inventory_has_complete_separated_scope(self):
        inventory = verifier.load_json(verifier.DEFAULT_OUTPUT)
        self.assertEqual(inventory["summary"]["totalContracts"], 19)
        self.assertEqual(inventory["summary"]["metadataDataStores"], 7)
        self.assertEqual(inventory["summary"]["sourceImplementations"], 9)
        self.assertEqual(inventory["summary"]["immutableArgumentsClones"], 3)
        self.assertEqual(inventory["summary"]["runtimeIdentityFailures"], [])
        self.assertFalse(inventory["authorization"]["sourcePublicationAuthorized"])
        kinds = {record["kind"] for record in inventory["contracts"]}
        self.assertEqual(
            kinds,
            {
                "METADATA_DATA_STORE",
                "SOURCE_IMPLEMENTATION",
                "IMMUTABLE_ARGUMENTS_CLONE",
            },
        )


if __name__ == "__main__":
    unittest.main()
