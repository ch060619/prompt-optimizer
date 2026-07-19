# RC-171 Evidence

<!-- RC ID: RC-171. -->

## Delivered

- Added exponential backoff with bounded jitter for retryable Provider
  failures, honoring numeric and HTTP-date `Retry-After` values.
- Retry waits poll the existing cancellation event, so cancellation interrupts
  the wait and prevents the next request.
- Added Provider network configuration for HTTP(S) proxy, `NO_PROXY` host
  matching, custom CA bundle, IPv4/IPv6 preference, and environment loading
  through `RABBIT_CODE_<PROVIDER>_*` variables.
- Proxy URLs reject embedded plaintext credentials. Authenticated proxies use
  an opaque `proxy_credential_ref` and an injected runtime resolver, keeping
  secrets out of configuration and logs.
- Preserved injected `httpx.Client` support for Mock-first tests and existing
  adapter contracts.

## Validation

- RC-160 through RC-171 Provider/API regression: 90 passed, 6 existing data
  directory migration warnings.
- RC-171 contract: 6 passed for `Retry-After`, exponential backoff, cancelable
  waits, proxy/CA/IP family/`NO_PROXY`, opaque proxy credentials, and env
  configuration.
- Provider Ruff, targeted Provider Mypy with the repository `PYTHONPATH`, and
  Python compilation passed.

## Limits

- No real Provider request was made and no external service charge was
  incurred.
- Proxy credentials require the future/host SecretStore boundary to provide
  the resolver; plaintext credentials are intentionally rejected.
- Existing jsdom navigation and data-directory migration warnings remain.
