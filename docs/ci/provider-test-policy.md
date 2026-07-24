# Provider Test Policy

RC ID: RC-241

Ordinary push and pull-request CI runs deterministic Provider and runner mocks. The backend
job sets `RABBIT_CODE_REAL_PROVIDER_TESTS=0`, and the contract suite uses
`httpx.MockTransport`; no project API key, scheduled real request, or model weight is used.

Real Provider/model checks are a protected manual matrix only. They require the user's own
credentials or local hardware, explicit confirmation, a cost/token limit, and a separate
workflow or local invocation. They are not a merge requirement for ordinary CI.
