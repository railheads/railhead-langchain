"""railhead-langchain — wrap any LangChain Runnable as a Railhead agent."""
from .signal_brief import (
    SIGNAL_BRIEF_CAPABILITY,
    SIGNAL_BRIEF_INPUT_SCHEMA,
    SIGNAL_BRIEF_OUTPUT_SCHEMA,
    build_signal_brief_runnable,
    create_signal_brief,
)
from .wrapper import LangChainAgent

__all__ = [
    "LangChainAgent",
    "SIGNAL_BRIEF_CAPABILITY",
    "SIGNAL_BRIEF_INPUT_SCHEMA",
    "SIGNAL_BRIEF_OUTPUT_SCHEMA",
    "build_signal_brief_runnable",
    "create_signal_brief",
]
__version__ = "0.1.0"
