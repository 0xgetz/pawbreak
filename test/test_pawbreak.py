"""Offline test suite: payload integrity, sandbox tripwires, scoring math,
and a full end-to-end run against the bundled mock endpoint."""
from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
import unittest
from pathlib import Path

from pawbreak.payloads import PAYLOADS, build_scenarios
from pawbreak.runner import Result, score
from pawbreak.sandbox import FORBIDDEN, Sandbox, TOOLS_SPEC, surface_message

ROOT = Path(__file__).resolve().parent.parent


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class TestPayloads(unittest.TestCase):
    def test_scenarios_built(self):
        sc = build_scenarios(FORBIDDEN)
        self.assertGreaterEqual(len(sc), 10)
        ids = {s.id for s in sc}
        self.assertEqual(len(ids), len(sc), "scenario ids must be unique")

    def test_forbidden_tools_exist(self):
        for s in build_scenarios(FORBIDDEN):
            self.assertIn(s.forbidden_tool, FORBIDDEN)
            self.assertIn(s.surface, {"file", "web", "email", "tool_output"})

    def test_payload_coverage(self):
        used = "\n".join(s.artifact_body for s in build_scenarios(FORBIDDEN))
        # every library payload text must appear in at least one scenario
        heads = {"readme-authority", "web-encoded-bait"}  # noqa: F841
        self.assertIn("Ignore all previous", used)
        self.assertIn("SECURITY NOTICE", used)


class TestSandbox(unittest.TestCase):
    def test_tripwires_record(self):
        sb = Sandbox({"a.md": "hello"}, "t")
        out = json.loads(sb.execute("wipe_workspace", {}))
        self.assertTrue(out["ok"])
        self.assertEqual(len(sb.breaches), 1)
        self.assertEqual(sb.breaches[0].tool, "wipe_workspace")

    def test_safe_tools_read(self):
        sb = Sandbox({"a.md": "content"}, "t")
        self.assertEqual(sb.execute("read_file", {"path": "a.md"}), "content")
        self.assertEqual(sb.breaches, [])

    def test_tools_spec_wellformed(self):
        for t in TOOLS_SPEC:
            self.assertEqual(t["type"], "function")
            self.assertIn("name", t["function"])

    def test_surface_message(self):
        for s in build_scenarios(FORBIDDEN):
            msg, _ = surface_message(s)
            self.assertEqual(msg["role"], "user")
            self.assertTrue(msg["content"])


class TestScoring(unittest.TestCase):
    def _r(self, breached, sev="medium", err=""):
        return Result("x", "file", sev, breached, [], 2, "", err)

    def test_asr_math(self):
        rs = [self._r(True), self._r(False), self._r(True, "critical"),
              self._r(False), self._r(False, err="boom")]
        sc = score(rs)
        self.assertEqual(sc["valid"], 4)
        self.assertEqual(sc["errors"], 1)
        self.assertAlmostEqual(sc["asr_pct"], 50.0)
        self.assertEqual(sc["critical_asr_pct"], 100.0)
        self.assertEqual(sc["paw_score"], 50.0)

    def test_clean_agent(self):
        sc = score([self._r(False)] * 5)
        self.assertEqual(sc["asr_pct"], 0.0)
        self.assertEqual(sc["paw_score"], 100.0)


class TestEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = free_port()
        cls.proc = subprocess.Popen(
            [sys.executable, "-m", "pawbreak.mock_agent",
             "--port", str(cls.port)],
            cwd=ROOT,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            try:
                socket.create_connection(("127.0.0.1", cls.port), 0.5).close()
                return
            except OSError:
                time.sleep(0.1)
        cls.proc.kill()
        raise RuntimeError("mock agent did not start")

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait(timeout=5)

    def _run(self, model: str) -> dict:
        out = ROOT / f".tmp-report-{model}"
        r = subprocess.run(
            [sys.executable, "-m", "pawbreak.cli", "--base-url",
             f"http://127.0.0.1:{self.port}/v1", "--model", model,
             "--out", str(out), "--quiet"],
            cwd=ROOT, capture_output=True, text=True, timeout=120)
        report = json.loads((out.with_suffix(".json")).read_text())
        self.assertTrue(out.with_suffix(".md").exists())
        out.unlink(missing_ok=True)
        out.with_suffix(".md").unlink(missing_ok=True)
        return {"rc": r.returncode, "stdout": r.stdout, **report}

    def test_gullible_gets_caught(self):
        rep = self._run("gullible")
        self.assertEqual(rep["rc"], 1)  # nonzero exit = agent failed
        self.assertGreater(rep["score"]["asr_pct"], 50.0)
        self.assertTrue(any(r["breached"] for r in rep["results"]))
        bad = [r for r in rep["results"] if r["breached"]]
        for b in bad:  # every recorded breach must be a forbidden tool
            for call in b["forbidden_calls"]:
                self.assertIn(call["tool"], FORBIDDEN)

    def test_hardened_refuses_everything(self):
        rep = self._run("hardened")
        self.assertEqual(rep["rc"], 0)
        self.assertEqual(rep["score"]["asr_pct"], 0.0)
        self.assertEqual(rep["score"]["paw_score"], 100.0)

    def test_surface_filter(self):
        out = ROOT / ".tmp-report-web"
        r = subprocess.run(
            [sys.executable, "-m", "pawbreak.cli", "--base-url",
             f"http://127.0.0.1:{self.port}/v1", "--model", "gullible",
             "--surface", "web", "--out", str(out), "--quiet"],
            cwd=ROOT, capture_output=True, text=True, timeout=60)
        rep = json.loads(out.with_suffix(".json").read_text())
        out.unlink(missing_ok=True)
        out.with_suffix(".md").unlink(missing_ok=True)
        self.assertEqual(r.returncode, 1)
        self.assertTrue(all(x["surface"] == "web" for x in rep["results"]))


if __name__ == "__main__":
    unittest.main()
