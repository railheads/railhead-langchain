"""LangChainAgent — bind LangChain Runnables to Railhead capabilities."""
from __future__ import annotations
import logging
from typing import Any, Callable

from langchain_core.runnables import Runnable
from railhead import RailheadAgent

log = logging.getLogger("railhead_langchain")


def _coerce_output(raw: Any, output_key: str) -> dict:
    """Turn a Runnable's output into a result dict that Railhead can hash and submit.

    Handles the common shapes you get back from LangChain pieces:
      - dict                          → returned unchanged
      - BaseMessage (ChatModel reply) → {output_key: msg.content}
      - str / int / float / bool      → {output_key: value}
      - list                          → {output_key: list}
      - anything else                 → {output_key: str(value)}
    """
    if isinstance(raw, dict):
        return raw
    content = getattr(raw, "content", None)
    if content is not None and isinstance(content, (str, int, float)):
        return {output_key: content}
    if isinstance(raw, (str, int, float, bool, list)):
        return {output_key: raw}
    return {output_key: str(raw)}


class LangChainAgent(RailheadAgent):
    """
    A Railhead agent backed by LangChain Runnables.

    Quick start::

        from langchain_core.runnables import RunnableLambda
        from railhead_langchain import LangChainAgent

        agent = LangChainAgent.from_credentials()
        agent.serve("text_uppercase", RunnableLambda(str.upper), input_key="text")
        agent.run(price_rail=1, stake_rail=1000, endpoint="polling")

    Inherits every method on RailheadAgent — you can still mix in custom
    handlers via ``@agent.on(capability)`` for non-LangChain logic alongside
    Runnable-backed ones.
    """

    def serve(
        self,
        capability: str,
        runnable: Runnable,
        *,
        input_key: str | None = None,
        input_mapper: Callable[[dict], Any] | None = None,
        output_key: str = "text",
        output_mapper: Callable[[Any], dict] | None = None,
    ) -> None:
        """Bind a LangChain Runnable to a Railhead capability.

        :param capability:    Capability tag this Runnable will fulfil.
        :param runnable:      Any LangChain ``Runnable`` (ChatModel, chain, custom).
        :param input_key:     If set, ``runnable.invoke(job.input[input_key])`` is called.
                              Otherwise the entire ``job.input`` dict is passed in.
        :param input_mapper:  Full control — receives ``job.input``, returns Runnable input.
                              Wins over ``input_key`` when both are provided.
        :param output_key:    When the Runnable returns a scalar / message, the result
                              dict becomes ``{output_key: value}``.
        :param output_mapper: Full control — receives the raw Runnable output, returns a dict.
                              Wins over the default coercion when provided.
        """
        if not isinstance(runnable, Runnable):
            raise TypeError(
                f"serve() expected a LangChain Runnable, got {type(runnable).__name__}. "
                "If you have a plain function, wrap it: RunnableLambda(my_func)."
            )

        def handler(job):
            if input_mapper is not None:
                payload = input_mapper(job.input)
            elif input_key is not None:
                payload = job.input.get(input_key, "")
            else:
                payload = job.input

            raw = runnable.invoke(payload)

            if output_mapper is not None:
                result = output_mapper(raw)
                if not isinstance(result, dict):
                    raise TypeError(
                        f"output_mapper for '{capability}' must return dict, got {type(result).__name__}"
                    )
                return result
            return _coerce_output(raw, output_key)

        handler.__name__ = f"{capability}_handler"
        self._handlers[capability] = handler
        log.info(
            "Bound LangChain Runnable to capability '%s' (input_key=%r, output_key=%r)",
            capability, input_key, output_key,
        )

    def run(
        self,
        price_rail: float | None = None,
        stake_rail: float = 1000.0,
        endpoint: str = "polling",
        poll_secs: float = 5.0,
    ) -> None:
        """Start the agent's poll loop.

        If ``price_rail`` is provided, every capability you've bound via ``.serve()``
        is registered on-chain first (a no-op if the agent is already registered).
        Otherwise this just polls — useful if you registered elsewhere.
        """
        if price_rail is not None:
            caps = list(self._handlers.keys())
            if not caps:
                raise RuntimeError(
                    "No capabilities bound. Call .serve(capability, runnable, ...) before .run()."
                )
            self.register(
                capabilities=caps,
                price_rail=price_rail,
                stake_rail=stake_rail,
                endpoint=endpoint,
            )
        super().run(poll_secs=poll_secs)
