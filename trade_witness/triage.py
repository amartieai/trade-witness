"""Triage layer — the optional smart reader sitting ON TOP of the witness.

The witness itself is dumb: it records, regardless. This layer answers the one
bounded question the user cares about afterward:

    "of the anomalies found this session, which should I actually look at?"

Backends:
  - "local": deterministic heuristic (zero dependencies, always works).
  - "jev":   the JEV system-one decision layer (optional; same interface).

JEV-ready, not JEV-dependent: the core runs with `local` out of the box; a user
who wants JEV flips one config flag and the SAME `classify()` call routes to it.
"""
import sys

# severity weight per anomaly pattern (higher = more worth a human's eye)
_SEVERITY = {
    "removal_proof": 1.0,          # a bar existed, then vanished — strongest
    "screen_price_divergence": 1.0,
    "inverted_classification": 0.8,
    "volume_inflation": 0.8,
    "volume_spike": 0.6,
    "spike_unclassified": 0.6,
    "minute_absent": 0.8,
    "reclick_signature": 0.4,
    "export_behavior_anomaly": 0.6,
}


def _local_classify(patterns: dict) -> dict:
    score = 0.0
    for name, count in (patterns or {}).items():
        score += _SEVERITY.get(name, 0.5) * count
    if score >= 3.0:
        severity, action = "high", "escalate"
        confidence = min(0.95, 0.5 + score * 0.06)
    elif score >= 1.0:
        severity, action = "medium", "review"
        confidence = 0.5 + score * 0.08
    else:
        severity, action = "low", "archive"
        confidence = 0.9
    return {"severity": severity, "action": action,
            "confidence": round(confidence, 3), "score": round(score, 2)}


def classify(patterns: dict, backend: str = "local") -> dict:
    """Classify a session's anomaly counts into an escalation decision.

    Returns: {"severity", "action", "confidence", "score", "backend"}.
    """
    if backend == "jev":
        try:
            from trade_witness import jev_backend  # optional integration
            return jev_backend.classify(patterns)
        except Exception:
            # JEV configured but unavailable -> fail safe to local, never break the witness
            backend = "local"
    out = _local_classify(patterns)
    out["backend"] = backend
    return out