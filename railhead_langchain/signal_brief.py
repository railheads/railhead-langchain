"""Provider-neutral signal brief Runnable for Railhead LangChain demos.

The default implementation is deterministic and local-only. It is intentionally
not tied to any proprietary signal provider, model, prompt, or dataset.
"""
from __future__ import annotations

from time import perf_counter
from typing import Any

from langchain_core.runnables import Runnable, RunnableLambda


SIGNAL_BRIEF_CAPABILITY = "signal_brief"

SIGNAL_BRIEF_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "topic": {"type": "string"},
        "symbols": {"type": "array", "items": {"type": "string"}},
        "horizon": {"type": "string", "default": "24h"},
        "brief_type": {"type": "string", "default": "risk"},
        "signals": {
            "type": "array",
            "description": "Optional provider-neutral signal observations.",
            "items": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "direction": {
                        "type": "string",
                        "enum": ["long", "short", "neutral"],
                    },
                    "strength": {"type": "number"},
                    "confidence": {"type": "number"},
                    "reason": {"type": "string"},
                },
            },
        },
        "constraints": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["topic"],
}

SIGNAL_BRIEF_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "capability": {"type": "string", "const": SIGNAL_BRIEF_CAPABILITY},
        "headline": {"type": "string"},
        "stance": {
            "type": "string",
            "enum": ["constructive", "neutral", "defensive"],
        },
        "confidence": {"type": "number"},
        "supporting_signals": {"type": "array"},
        "risk_flags": {"type": "array"},
        "next_agent_actions": {"type": "array"},
        "limitations": {"type": "array"},
        "performance": {"type": "object"},
    },
    "required": [
        "capability",
        "headline",
        "stance",
        "confidence",
        "supporting_signals",
        "risk_flags",
        "next_agent_actions",
        "limitations",
        "performance",
    ],
}


def build_signal_brief_runnable() -> Runnable:
    """Return a provider-neutral Runnable that emits structured brief output."""
    return RunnableLambda(create_signal_brief)


def create_signal_brief(payload: dict[str, Any]) -> dict[str, Any]:
    """Create a deterministic structured signal brief from provider-neutral input."""
    started = perf_counter()
    if not isinstance(payload, dict):
        payload = {"topic": str(payload)}

    topic = str(payload.get("topic") or "market context").strip()
    horizon = str(payload.get("horizon") or "24h").strip()
    symbols = _normalize_symbols(payload.get("symbols"), topic)
    signals = _normalize_signals(payload.get("signals"), symbols)
    constraints = [str(item) for item in payload.get("constraints") or [] if str(item).strip()]

    aggregate = _aggregate_signal_score(signals)
    stance = _stance_from_score(aggregate)
    confidence = _confidence_from_signals(signals)
    risk_flags = _risk_flags(signals, constraints, confidence)

    elapsed_ms = round((perf_counter() - started) * 1000, 3)
    return {
        "capability": SIGNAL_BRIEF_CAPABILITY,
        "version": "0.1.0",
        "headline": _headline(topic, horizon, stance, confidence),
        "stance": stance,
        "confidence": confidence,
        "supporting_signals": signals,
        "risk_flags": risk_flags,
        "next_agent_actions": _next_actions(symbols, horizon, stance),
        "limitations": [
            "Builder Preview output; use as agent-readable context, not investment advice.",
            "No trade execution is performed by this capability.",
            "Brief quality depends on caller-supplied or marketplace-provided signal inputs.",
        ],
        "performance": {
            "latency_ms": elapsed_ms,
            "engine": "railhead-langchain-signal-brief-local-v0",
            "external_calls": 0,
        },
    }


def _normalize_symbols(value: Any, topic: str) -> list[str]:
    if isinstance(value, str):
        raw = [value]
    elif isinstance(value, list):
        raw = value
    else:
        raw = []
    symbols = [str(item).strip().upper() for item in raw if str(item).strip()]
    if symbols:
        return symbols[:8]
    guessed = [token.strip(".,:;()[]").upper() for token in topic.split()]
    guessed = [token for token in guessed if token.isalnum() and 2 <= len(token) <= 8]
    return guessed[:3] or ["MARKET"]


def _normalize_signals(value: Any, symbols: list[str]) -> list[dict[str, Any]]:
    if isinstance(value, list) and value:
        normalized = []
        for item in value[:12]:
            if not isinstance(item, dict):
                continue
            normalized.append(
                {
                    "symbol": str(item.get("symbol") or symbols[0]).upper(),
                    "direction": _direction(item.get("direction")),
                    "strength": _clamp_float(item.get("strength"), 0.5),
                    "confidence": _clamp_float(item.get("confidence"), 0.5),
                    "reason": str(item.get("reason") or "caller supplied signal"),
                }
            )
        if normalized:
            return normalized

    return [
        {
            "symbol": symbol,
            "direction": "neutral",
            "strength": 0.5,
            "confidence": 0.45,
            "reason": "no external signal supplied; default neutral prior",
        }
        for symbol in symbols[:4]
    ]


def _direction(value: Any) -> str:
    text = str(value or "neutral").lower()
    if text in {"long", "short", "neutral"}:
        return text
    if text in {"bullish", "up", "positive"}:
        return "long"
    if text in {"bearish", "down", "negative"}:
        return "short"
    return "neutral"


def _clamp_float(value: Any, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return round(max(0.0, min(1.0, number)), 3)


def _aggregate_signal_score(signals: list[dict[str, Any]]) -> float:
    if not signals:
        return 0.0
    total = 0.0
    weight = 0.0
    for signal in signals:
        direction = signal["direction"]
        signed = 1.0 if direction == "long" else -1.0 if direction == "short" else 0.0
        signal_weight = float(signal["confidence"])
        total += signed * float(signal["strength"]) * signal_weight
        weight += signal_weight
    return 0.0 if weight == 0 else total / weight


def _stance_from_score(score: float) -> str:
    if score >= 0.18:
        return "constructive"
    if score <= -0.18:
        return "defensive"
    return "neutral"


def _confidence_from_signals(signals: list[dict[str, Any]]) -> float:
    if not signals:
        return 0.35
    avg_conf = sum(float(signal["confidence"]) for signal in signals) / len(signals)
    avg_strength = sum(float(signal["strength"]) for signal in signals) / len(signals)
    return round(max(0.1, min(0.95, (avg_conf * 0.7) + (avg_strength * 0.3))), 3)


def _risk_flags(
    signals: list[dict[str, Any]], constraints: list[str], confidence: float
) -> list[str]:
    flags: list[str] = []
    directions = {signal["direction"] for signal in signals}
    if "long" in directions and "short" in directions:
        flags.append("mixed directional inputs")
    if confidence < 0.55:
        flags.append("low confidence")
    if any("no trade" in item.lower() or "preview" in item.lower() for item in constraints):
        flags.append("execution disabled by caller constraints")
    return flags or ["no major risk flag from supplied inputs"]


def _headline(topic: str, horizon: str, stance: str, confidence: float) -> str:
    return f"{topic}: {stance} {horizon} read with {confidence:.2f} confidence"


def _next_actions(symbols: list[str], horizon: str, stance: str) -> list[str]:
    first = symbols[0] if symbols else "target"
    return [
        f"request fresh signal inputs for {first} before the next {horizon} decision",
        f"compare another provider's {SIGNAL_BRIEF_CAPABILITY} output for stance drift",
        f"avoid autonomous execution while stance is {stance} in Builder Preview",
    ]
