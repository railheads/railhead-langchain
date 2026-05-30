"""Offline smoke tests for LangChainAgent — no chain or network required.

Run directly:    python tests/test_wrapper.py
Run via pytest:  pytest tests/
"""
from types import SimpleNamespace

from langchain_core.runnables import RunnableLambda

from railhead_langchain import LangChainAgent, __version__


def _bare_agent() -> LangChainAgent:
    """Build a LangChainAgent with no chain connection — enough to test handler binding."""
    agent = LangChainAgent.__new__(LangChainAgent)
    agent._handlers = {}
    agent._last_block = 0
    agent._api_url = ""
    return agent


def test_version_string():
    assert isinstance(__version__, str) and __version__.count(".") >= 1


def test_serve_binds_handler():
    agent = _bare_agent()
    agent.serve("text_uppercase", RunnableLambda(str.upper), input_key="text")
    assert "text_uppercase" in agent._handlers


def test_input_key_extracts_scalar():
    agent = _bare_agent()
    agent.serve("text_uppercase", RunnableLambda(str.upper), input_key="text")
    result = agent._handlers["text_uppercase"](SimpleNamespace(input={"text": "hello"}))
    assert result == {"text": "HELLO"}


def test_no_input_key_passes_whole_dict():
    agent = _bare_agent()
    echo = RunnableLambda(lambda d: d.get("msg", "") + "!")
    agent.serve("echo", echo)
    result = agent._handlers["echo"](SimpleNamespace(input={"msg": "ping"}))
    assert result == {"text": "ping!"}


def test_input_mapper_overrides_input_key():
    agent = _bare_agent()
    runnable = RunnableLambda(lambda s: s.lower())
    agent.serve(
        "lower",
        runnable,
        input_key="ignored",
        input_mapper=lambda d: d["WORD"],
    )
    result = agent._handlers["lower"](SimpleNamespace(input={"WORD": "Yelling"}))
    assert result == {"text": "yelling"}


def test_output_mapper_overrides_default_coercion():
    agent = _bare_agent()
    multi = RunnableLambda(lambda s: s * 3)
    agent.serve(
        "multiply",
        multi,
        input_key="word",
        output_mapper=lambda raw: {"result": raw, "len": len(raw)},
    )
    result = agent._handlers["multiply"](SimpleNamespace(input={"word": "ab"}))
    assert result == {"result": "ababab", "len": 6}


def test_basemessage_content_unwrap():
    """A ChatModel-style return (object with .content) is unwrapped to the scalar."""
    class FakeMessage:
        def __init__(self, content):
            self.content = content

    agent = _bare_agent()
    chat = RunnableLambda(lambda s: FakeMessage(s + " (from chat)"))
    agent.serve("chat_cap", chat, input_key="prompt")
    result = agent._handlers["chat_cap"](SimpleNamespace(input={"prompt": "hi"}))
    assert result == {"text": "hi (from chat)"}


def test_dict_output_passes_through_unchanged():
    agent = _bare_agent()
    structured = RunnableLambda(lambda _: {"a": 1, "b": [2, 3]})
    agent.serve("structured", structured)
    result = agent._handlers["structured"](SimpleNamespace(input={}))
    assert result == {"a": 1, "b": [2, 3]}


def test_non_runnable_rejected_early():
    agent = _bare_agent()
    try:
        agent.serve("bad", lambda x: x)  # plain function, not a Runnable
    except TypeError as e:
        assert "Runnable" in str(e)
    else:
        raise AssertionError("serve() should reject a non-Runnable")


def test_output_mapper_must_return_dict():
    agent = _bare_agent()
    runnable = RunnableLambda(lambda s: s.upper())
    agent.serve(
        "wrong_mapper",
        runnable,
        input_key="text",
        output_mapper=lambda raw: raw,  # returns a string, not a dict
    )
    try:
        agent._handlers["wrong_mapper"](SimpleNamespace(input={"text": "x"}))
    except TypeError as e:
        assert "dict" in str(e).lower()
    else:
        raise AssertionError("handler should reject non-dict output_mapper result")


if __name__ == "__main__":
    import sys
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{len(tests)} tests passed")
    sys.exit(0 if passed == len(tests) else 1)
