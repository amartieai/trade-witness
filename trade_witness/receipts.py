"""Hash-chained session receipts for Trade Witness.

Append-only. Every session event (start, seal) is a receipt that links to the
previous by SHA-256. Editing or removing one breaks the chain — tampering is
visible, not trust-hidden.
"""
import hashlib
import json
import os
import time
from datetime import datetime, timezone


def sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Receipt:
    def __init__(self, event: str, payload: dict, previous_hash: str = "GENESIS"):
        self.event = event
        self.payload = payload
        self.previous_hash = previous_hash
        self.timestamp = now_iso()
        self.hash = self._compute()

    def _compute(self) -> str:
        content = json.dumps({
            "event": self.event,
            "payload": self.payload,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
        }, sort_keys=True)
        return sha256(content)

    def verify(self) -> bool:
        return self.hash == self._compute()

    def to_dict(self) -> dict:
        return {
            "event": self.event,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
        }


class Chain:
    """Append-only receipt chain written as JSONL."""

    def __init__(self, path: str):
        self.path = path
        self.receipts = []
        if os.path.exists(path):
            for line in open(path):
                line = line.strip()
                if line:
                    r = json.loads(line)
                    self.receipts.append(self._from_dict(r))

    @staticmethod
    def _from_dict(d: dict) -> Receipt:
        r = Receipt(d["event"], d["payload"], d["previous_hash"])
        r.timestamp = d["timestamp"]
        r.hash = d["hash"]
        return r

    def append(self, event: str, payload: dict) -> Receipt:
        prev = self.receipts[-1].hash if self.receipts else "GENESIS"
        r = Receipt(event, payload, prev)
        self.receipts.append(r)
        with open(self.path, "a") as f:
            f.write(json.dumps(r.to_dict(), sort_keys=True) + "\n")
        return r

    def verify(self) -> bool:
        for i, r in enumerate(self.receipts):
            if not r.verify():
                return False
            if i > 0 and r.previous_hash != self.receipts[i - 1].hash:
                return False
        return True

    @property
    def latest_hash(self) -> str:
        return self.receipts[-1].hash if self.receipts else "GENESIS"