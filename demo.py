#!/usr/bin/env python3
"""Trade Witness — live demo.

Simulates a short trading session and the receipts it leaves behind, then
shows what happens when someone tries to quietly edit one afterward.

Run:  python3 demo.py
"""
import json
import os
import tempfile

from trade_witness.receipts import Chain, sha256

LINE = "─" * 62


def show(chain):
    """Print the chain like the CLI does."""
    state = "OK" if chain.verify() else "CHAIN-BROKEN"
    print(f"chain verifies: {state}  ({len(chain.receipts)} receipts)")
    for r in chain.receipts:
        p = r.payload
        if r.event == "feed_pull_t0":
            detail = f"BTC {p['price']:,.2f}  (moment of click)"
        elif r.event == "feed_pull_t1":
            detail = f"BTC {p['price']:,.2f}  ← pulled again later"
        elif r.event == "broker_export":
            detail = f"fill {p['symbol']} #{p['order_id']} @ {p['price']:,.2f}  qty={p['qty']}"
        elif r.event == "screen_recording":
            detail = f"{p['res']} @ {p['fps']}fps  sha={p['frame_hash'][:12]}…"
        elif r.event == "session_seal":
            detail = f"triage: {p['triage']}"
        else:
            detail = p.get("note", "")
        print(f"  [{r.event:<16}] {r.timestamp[11:19]}Z  {detail}")
    return state


def main():
    print("Trade Witness — live demonstration")
    print(LINE)

    d = tempfile.mkdtemp(prefix="witdemo_")
    path = os.path.join(d, "receipts.jsonl")
    chain = Chain(path)

    print("\nSimulating a trading session — receipts are written as they happen…\n")

    chain.append("session_start", {"note": "broker app opened — screen capture ON"})
    chain.append("screen_recording", {
        "res": "1920x1080", "fps": 30,
        "frame_hash": sha256("demo-screen-frame"),
    })
    chain.append("broker_export", {
        "symbol": "MBT", "order_id": "A8813", "qty": 1, "price": 61442.00,
    })
    chain.append("feed_pull_t0", {"price": 61442.00})   # the feed at the moment you clicked
    chain.append("feed_pull_t1", {"price": 61378.00})   # the SAME bar, pulled again later
    chain.append("session_seal", {
        "triage": "DISCREPANCY — the bar you bought the top of no longer shows that print",
    })

    show(chain)
    print(LINE)

    print("\nNow the adversary edits one receipt afterward (price, no hash fix)…\n")
    lines = [json.loads(l) for l in open(path) if l.strip()]
    for rec in lines:
        if rec["event"] == "feed_pull_t0":
            print(f"  before:  feed_pull_t0  price = {rec['payload']['price']:,}")
            rec["payload"]["price"] = 61402.00     # rewrite the print
            print(f"  after:   feed_pull_t0  price = {rec['payload']['price']:,}   (hash NOT updated)")
    with open(path, "w") as f:
        for rec in lines:
            f.write(json.dumps(rec, sort_keys=True) + "\n")

    chain = Chain(path)
    print()
    state = show(chain)
    print(LINE)
    print(f"\nVerdict: the ledger saw the edit — {'tamper-proof as promised' if state == 'CHAIN-BROKEN' else 'something went wrong'}. Demo complete.")


if __name__ == "__main__":
    main()