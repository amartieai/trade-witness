# AMARTIE Trade Witness

**A free, open-source, always-on witness for anyone who trades.**

It watches, it records, it links everything to a hash chain — and it never
judges. Screen capture, order timestamps, broker exports, and the public feed
are all folded into tamper-evident receipts. If the feed and your screen ever
disagree, you'll see exactly where.

Witness, not judge. Ruler, not strategy.

## What it does

- Automatically notices when your trading session starts (broker app opened or
  an export file landed) and starts recording the screen.
- Pulls your broker's execution log the instant it happens, and pulls the
  public feed again later — so a bar that existed and then vanished is caught.
- Folds every event into a SHA-256 hash chain. Edit or remove one and the whole
  chain breaks.
- Leaves everything local. The only thing that can leave your machine is
  anonymized pattern counts, and only when you run the submit yourself.

The triage on top of the recorder — "which anomalies should you look at?" — is
a pluggable layer. Ships with a zero-dependency local classifier; can point at
the JEV decision layer by flipping one config flag.

## Install (one command)

```bash
curl -fsSL https://github.com/amartieai/trade-witness/raw/main/install.sh | bash
```

(or clone and run `./install.sh`)

## Use

```bash
trade-witness status              # is it watching right now?
trade-witness record --duration 10  # capture 10s for a quick check
trade-witness report --session <id> # read a session's receipts + triage
```

## Try it in 30 seconds

Clone, then run the built-in demo — no broker, no account, no risk:

```bash
git clone https://github.com/amartieai/trade-witness.git
cd trade-witness
python3 demo.py
```

It simulates one trading session, then edits a receipt behind its back. This is
the actual output:

```
chain verifies: OK  (6 receipts)
  [session_start   ]  broker app opened — screen capture ON
  [screen_recording]  1920x1080 @ 30fps  sha=1f08aea043d5…
  [broker_export   ]  fill MBT #A8813 @ 61,442.00  qty=1
  [feed_pull_t0    ]  BTC 61,442.00  (moment of click)
  [feed_pull_t1    ]  BTC 61,378.00  ← pulled again later
  [session_seal    ]  triage: DISCREPANCY — the bar you bought the top of no longer shows that print
```

Now the "adversary" rewrites one price without fixing the hash:

```
before:  feed_pull_t0  price = 61,442.00
after:   feed_pull_t0  price = 61,402.00   (hash NOT updated)
chain verifies: CHAIN-BROKEN  (6 receipts)
```

The ledger noticed. That's the whole point: quiet edits don't stay quiet.

## How it protects you

1. **Early pull** — your exporter is read *immediately*, so the record of a fill
   exists before anyone could erase it.
2. **Late pull** — the same feed is read again later; a bar that existed and then
   disappeared is proof of a rewrite.
3. **Screen vs feed** — your recording is aligned against the public feed at the
   exact seconds you clicked, minute by minute.
4. **Hash chain** — every receipt links to the one before it. Tampering is
   visible, not hidden.

## Positioning

Trade Witness is a component of the [**AMARTIE**](https://github.com/amartieai/amartie) system — AMARTIE's whole use
case is to protect anyone at the kernel level of their entire machine, by
witnessing everything impartially. Trading is the first door in because that's
where the receipts already live; the same engine scales to files, processes,
and network calls at the OS level.

## Sibling tool

- **[Tape Witness](https://github.com/amartieai/tape-witness)** — the forensic
  grader: reconcile your own screen recording against the public record at the
  exact minutes you acted, and grade the anomalies that cluster only on your
  action minutes. Where Trade Witness records continuously, Tape Witness
  proves a specific session. Ruler, not trader; names no platforms.

## Contribute

MIT licensed. Pull requests welcome. See the `/witness` engine for the
reconciliation and grading rules that produce the receipts.