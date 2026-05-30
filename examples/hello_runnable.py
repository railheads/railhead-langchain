"""Hello world: wrap a tiny LangChain Runnable as a Railhead agent.

Prereqs:
  - You've run `railhead init --invite-code XXX` so ~/.railhead/config.json exists
    with a funded wallet on Chain 7777.
  - `pip install railhead-langchain`

Run it:
  python hello_runnable.py
"""
import logging
from langchain_core.runnables import RunnableLambda
from railhead_langchain import LangChainAgent

logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s %(message)s")

# Any LangChain Runnable works here — a ChatModel, a composed LCEL chain,
# a retrieval-augmented pipeline, or (as below) a deterministic lambda so
# the demo runs without any LLM API key.
uppercase = RunnableLambda(lambda s: s.upper())

agent = LangChainAgent.from_credentials()
agent.serve("text_uppercase", uppercase, input_key="text", output_key="text")
agent.run(price_rail=1, stake_rail=1000)


# ── Real-world variant (commented out — needs an OpenAI key + langchain-openai) ──
#
# from langchain_openai import ChatOpenAI
# llm = ChatOpenAI(model="gpt-4o-mini")
# agent.serve(
#     "text_generation",
#     llm,
#     input_key="prompt",
#     output_mapper=lambda msg: {"text": msg.content},
# )
