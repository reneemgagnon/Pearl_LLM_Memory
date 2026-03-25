import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "pearl_session.py"
SPEC = REPO_ROOT / "references" / "pearl-chat-spec.md"
SCHEMA = REPO_ROOT / "references" / "pearl-chat-schema.json"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
    )


class PearlSessionPhase1Tests(unittest.TestCase):
    def test_help_text_uses_clean_v02_description(self) -> None:
        result = run_cli("--help")
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("PEARL-CHAT v0.2", result.stdout)
        self.assertIn("Protected - Evolving - Annotation - Resistant - Layering", result.stdout)
        self.assertNotIn("\u00c3", result.stdout)
        self.assertNotIn("\u00e2", result.stdout)

    def test_file_flag_after_subcommand_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pearl_file = Path(tmp) / "cli-order.pearl"
            result = run_cli(
                "init",
                "--file",
                str(pearl_file),
                "--objective",
                "Parser compatibility smoke test",
                "--force",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertTrue(pearl_file.exists())

    def test_branch_updates_lineage_and_branch_head(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pearl_file = Path(tmp) / "branch-state.pearl"
            init_result = run_cli(
                "--file",
                str(pearl_file),
                "init",
                "--objective",
                "Branch bookkeeping test",
                "--force",
            )
            self.assertEqual(init_result.returncode, 0, msg=init_result.stderr or init_result.stdout)

            branch_result = run_cli(
                "branch",
                "--file",
                str(pearl_file),
                "--name",
                "candidate-a",
                "--switch",
            )
            self.assertEqual(branch_result.returncode, 0, msg=branch_result.stderr or branch_result.stdout)

            pearl = json.loads(pearl_file.read_text(encoding="utf-8"))
            latest_layer_id = pearl["layers"][-1]["layer_id"]
            candidate_branch = next(branch for branch in pearl["branches"] if branch["name"] == "candidate-a")

            self.assertEqual(pearl["lineage"]["current_layer_id"], latest_layer_id)
            self.assertEqual(pearl["lineage"]["depth"], len(pearl["layers"]) - 1)
            self.assertEqual(candidate_branch["head_layer_id"], latest_layer_id)
            self.assertEqual(candidate_branch["layer_ids"][-1], latest_layer_id)
            self.assertEqual(pearl["surface"]["active_branch_id"], candidate_branch["branch_id"])

    def test_verify_catches_branch_head_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pearl_file = Path(tmp) / "verify-mismatch.pearl"
            init_result = run_cli(
                "--file",
                str(pearl_file),
                "init",
                "--objective",
                "Verify mismatch test",
                "--force",
            )
            self.assertEqual(init_result.returncode, 0, msg=init_result.stderr or init_result.stdout)

            branch_result = run_cli(
                "--file",
                str(pearl_file),
                "branch",
                "--name",
                "candidate-b",
                "--switch",
            )
            self.assertEqual(branch_result.returncode, 0, msg=branch_result.stderr or branch_result.stdout)

            pearl = json.loads(pearl_file.read_text(encoding="utf-8"))
            candidate_branch = next(branch for branch in pearl["branches"] if branch["name"] == "candidate-b")
            candidate_branch["head_layer_id"] = "layer-does-not-exist"
            pearl_file.write_text(json.dumps(pearl, indent=2), encoding="utf-8")

            verify_result = run_cli("--file", str(pearl_file), "verify")
            self.assertNotEqual(verify_result.returncode, 0)
            self.assertIn("head_layer_id", verify_result.stdout)

    def test_reference_artifacts_are_v02(self) -> None:
        spec_text = SPEC.read_text(encoding="utf-8")
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

        self.assertIn("PEARL-CHAT v0.2", spec_text)
        self.assertEqual(schema["$id"], "https://nobot.ai/schemas/pearl/chat-context/0.2/pearl-chat.schema.json")
        self.assertEqual(schema["properties"]["pearl_version"]["pattern"], r"^0\.2(\.\d+)?$")
        self.assertIn("_core_hash", schema["required"])
        self.assertEqual(schema["properties"]["spec"]["properties"]["version"]["pattern"], r"^0\.2(\.\d+)?$")
        self.assertIn("current_understanding", schema["$defs"]["surfaceState"]["required"])
        self.assertIn("state_hash", schema["$defs"]["lineage"]["required"])
        self.assertIn("layer_ids", schema["$defs"]["branch"]["required"])
        self.assertIn("suspended", schema["$defs"]["branch"]["properties"]["status"]["enum"])
        self.assertIn("rejected", schema["$defs"]["branch"]["properties"]["status"]["enum"])
        self.assertIn("reopen_event", schema["$defs"]["layer"]["properties"]["kind"]["enum"])

    def test_surface_output_is_ascii_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pearl_file = Path(tmp) / "surface-output.pearl"
            init_result = run_cli(
                "--file",
                str(pearl_file),
                "init",
                "--objective",
                "Surface output test",
                "--force",
            )
            self.assertEqual(init_result.returncode, 0, msg=init_result.stderr or init_result.stdout)

            surface_result = run_cli("--file", str(pearl_file), "surface")
            self.assertEqual(surface_result.returncode, 0, msg=surface_result.stderr or surface_result.stdout)
            self.assertIn("Core Immutable    : OK enforced", surface_result.stdout)
            self.assertNotIn("\u00c3", surface_result.stdout)
            self.assertNotIn("\u00e2", surface_result.stdout)


if __name__ == "__main__":
    unittest.main()
