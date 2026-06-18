# Railhead LangChain Release Checklist

Use this checklist before syncing or publishing `railhead-langchain`.

## Versioning

- Update `railhead_langchain/__init__.py#__version__`.
- Confirm `pyproject.toml` uses the dynamic version from `railhead_langchain.__version__`.
- Update `CHANGELOG.md` with notable changes.

## Safety Gates

- Do not commit private keys, tokens, or local credential files.
- Confirm current refs contain no 64-hex secret-shaped values.
- Confirm dependency points at the intended Railhead SDK source or published
  package.

## Local Verification

```bash
python -m compileall railhead_langchain
python -m pytest
python -m build
```

## Public Sync

- Push to `railheads/railhead-langchain` only after local tests pass.
- Confirm README install instructions match the current publication channel.
