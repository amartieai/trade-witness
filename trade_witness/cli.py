#!/usr/bin/env python3
"""trade-witness CLI — status, record (one-shot), report, version."""
import argparse
import os
import sys

from . import __version__, __product__
from .config import Config
from .daemon import Daemon
from .detector import Detector
from .recorder import Recorder
from .receipts import Chain


def cmd_status(cfg):
    det = Detector(cfg.watch_processes, cfg.watch_export_dir)
    print(f"{__product__} v{__version__}")
    print(f"  broker:      {cfg.broker}")
    print(f"  capture:     {cfg.capture} @ {cfg.fps}fps")
    print(f"  session_dir: {cfg.session_dir}")
    print(f"  watching:    {'active' if det.active() else 'idle'}")
    print(f"  triggers:    {det.triggers()}")
    if os.path.isdir(cfg.session_dir):
        sessions = sorted(os.listdir(cfg.session_dir))
        print(f"  sessions:    {len(sessions)} recorded")
        for s in sessions[-5:]:
            chain = Chain(os.path.join(cfg.session_dir, s, "receipts.jsonl"))
            ok = "chain-OK" if chain.verify() else "CHAIN-BROKEN"
            print(f"    - {s}  ({ok}, {len(chain.receipts)} receipts)")


def cmd_record(cfg, duration):
    out = os.path.join(cfg.session_dir, "manual", "screen.mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    rec = Recorder(cfg.capture, cfg.fps, cfg.codec)
    print(f"recording {duration}s -> {out}")
    rec.start(out)
    import time
    time.sleep(duration)
    rec.stop()
    size = os.path.getsize(out) if os.path.exists(out) else 0
    print(f"done: {size} bytes -> {out}")
    return 0 if size > 0 else 1


def cmd_report(cfg, session_id):
    d = os.path.join(cfg.session_dir, session_id)
    chain = Chain(os.path.join(d, "receipts.jsonl"))
    print(f"session {session_id}  ({'CHAIN OK' if chain.verify() else 'CHAIN BROKEN'})")
    for r in chain.receipts:
        print(f"  [{r.event}] {r.timestamp}  {r.hash[:12]}")
        if r.event == "session_seal" and "triage" in r.payload:
            print(f"      triage: {r.payload['triage']}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="trade-witness")
    p.add_argument("--version", action="store_true")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("status")
    r = sub.add_parser("record")
    r.add_argument("--duration", type=float, default=5.0)
    rep = sub.add_parser("report")
    rep.add_argument("--session", required=True)

    args = p.parse_args(argv)
    if args.version:
        print(f"{__product__} v{__version__}")
        return 0
    cfg = Config.load()
    if args.cmd == "status":
        return cmd_status(cfg)
    if args.cmd == "record":
        return cmd_record(cfg, args.duration)
    if args.cmd == "report":
        return cmd_report(cfg, args.session)
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())