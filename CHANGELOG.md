# Changelog

All notable changes to Railhead LangChain are tracked here.

## 0.1.0 - Builder Preview

Release status: prepared for GitHub source install. PyPI publication is not yet
confirmed.

### Added

- Initial wrapper package for serving LangChain Runnables as Railhead-paid agent capabilities.
- GitHub-based dependency on the Railhead Python SDK while the SDK is not yet on
  PyPI.
- Example and README guidance for invite-code onboarding via `railhead init`.
- Provider-neutral `signal_brief` demo Runnable for a Railhead-native LangChain
  showcase capability with structured output, latency metadata, and no external
  model/provider dependency.
- `examples/signal_brief_agent.py` with safe local `--once` mode and wallet-backed
  `--serve` mode.

### Changed

- Agent run examples default to `endpoint="polling"` to match Railhead alpha job
  delivery.
- README status and license wording now use Builder Preview language and GitHub
  Issues instead of unconfirmed public email routing.
