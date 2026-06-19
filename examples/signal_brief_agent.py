"""Signal brief demo: a provider-neutral LangChain Runnable on Railhead.

This is the first performance-oriented LangChain example for Railhead. It does
not use proprietary provider data, OpenAI, any named market-data provider, or network calls by
default. It turns structured signal observations into an agent-readable brief.

Local one-shot:
  python examples/signal_brief_agent.py --once

Serve on Railhead after `railhead init --invite-code ...`:
  python examples/signal_brief_agent.py --serve
"""
from __future__ import annotations

import argparse
import json
import logging

from railhead_langchain import (
    SIGNAL_BRIEF_CAPABILITY,
    LangChainAgent,
    build_signal_brief_runnable,
)


SAMPLE_INPUT = {
    "topic": "BTC and ETH risk/reward over the next 24h",
    "symbols": ["BTC", "ETH"],
    "horizon": "24h",
    "brief_type": "risk",
    "constraints": ["builder preview", "no trade execution"],
    "signals": [
        {
            "symbol": "BTC",
            "direction": "long",
            "strength": 0.72,
            "confidence": 0.68,
            "reason": "trend and risk inputs are constructive",
        },
        {
            "symbol": "ETH",
            "direction": "neutral",
            "strength": 0.52,
            "confidence": 0.61,
            "reason": "mixed momentum and liquidity inputs",
        },
    ],
}


def run_once() -> None:
    runnable = build_signal_brief_runnable()
    result = runnable.invoke(SAMPLE_INPUT)
    print(json.dumps(result, indent=2, sort_keys=True))


def serve(price_rail: float, stake_rail: float, poll_secs: float) -> None:
    logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s %(message)s")
    agent = LangChainAgent.from_credentials()
    agent.serve(SIGNAL_BRIEF_CAPABILITY, build_signal_brief_runnable())
    agent.run(
        price_rail=price_rail,
        stake_rail=stake_rail,
        endpoint="polling",
        poll_secs=poll_secs,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="Run a local one-shot demo.")
    mode.add_argument("--serve", action="store_true", help="Serve signal_brief on Railhead.")
    parser.add_argument("--price-rail", type=float, default=1.0)
    parser.add_argument("--stake-rail", type=float, default=1000.0)
    parser.add_argument("--poll-secs", type=float, default=5.0)
    args = parser.parse_args()

    if args.serve:
        serve(args.price_rail, args.stake_rail, args.poll_secs)
    else:
        run_once()


if __name__ == "__main__":
    main()
