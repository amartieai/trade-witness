import json
import os
import tempfile
import time
import unittest

from trade_witness.config import Config
from trade_witness.detector import Detector
from trade_witness.receipts import Chain
from trade_witness.triage import classify


class ConfigTests(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "config.json")
            import trade_witness.config as C
            old = C.CONFIG_PATH
            C.CONFIG_PATH = p
            try:
                cfg = Config()
                cfg.broker = "tradovate"
                cfg.save()
                loaded = Config.load()
                self.assertEqual(loaded.broker, "tradovate")
            finally:
                C.CONFIG_PATH = old


class ReceiptTests(unittest.TestCase):
    def test_chain_verify(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.jsonl")
            c = Chain(p)
            c.append("a", {"x": 1})
            c.append("b", {"x": 2})
            self.assertTrue(c.verify())
            self.assertEqual(len(c.receipts), 2)

    def test_tamper_detected(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.jsonl")
            c = Chain(p)
            c.append("a", {"x": 1})
            # edit a line on disk -> chain must break
            with open(p) as f:
                line = f.read()
            with open(p, "w") as f:
                f.write(line.replace('"x": 1', '"x": 9'))
            c2 = Chain(p)
            self.assertFalse(c2.verify())

    def test_reload_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.jsonl")
            c = Chain(p)
            c.append("start", {"s": "id"})
            h1 = c.latest_hash
            c2 = Chain(p)  # reload from disk
            self.assertEqual(c2.latest_hash, h1)
            self.assertTrue(c2.verify())


class TriageTests(unittest.TestCase):
    def test_local_low(self):
        out = classify({}, "local")
        self.assertEqual(out["action"], "archive")
        self.assertEqual(out["backend"], "local")

    def test_local_high(self):
        out = classify({"removal_proof": 3, "volume_spike": 2}, "local")
        self.assertEqual(out["action"], "escalate")

    def test_jev_fails_safe_to_local(self):
        # JEV not installed -> must fall back to local, never raise
        out = classify({"removal_proof": 1}, "jev")
        self.assertEqual(out["backend"], "local")


class DetectorTests(unittest.TestCase):
    def test_process_detected(self):
        # 'python3' is running this very test
        d = Detector(["python3"], "", window_seconds=1)
        self.assertTrue(d.active())

    def test_export_dir_fresh(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "export.csv")
            open(p, "w").write("t,o,h,l,c\n")
            det = Detector([], d, window_seconds=60)
            self.assertTrue(det.active())
            # stale beyond window -> idle
            os.utime(p, (time.time() - 500, time.time() - 500))
            det2 = Detector([], d, window_seconds=30)
            self.assertFalse(det2.active())


if __name__ == "__main__":
    unittest.main()