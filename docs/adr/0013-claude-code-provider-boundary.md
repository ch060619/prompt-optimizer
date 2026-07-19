# ADR-0013: Claude Code Format Boundary

RC IDs: RC-164

## Status

Accepted.

## Decision

Rabbit Code treats the user phrase “Claude Code format” as an ambiguous label,
not as permission to import a Claude Code subscription session. The supported
public mappings are Anthropic Messages API and, only after separate approval,
the official Anthropic Agent SDK.

Provider credentials are limited to an official Anthropic API key or a provider-
approved OAuth flow. Cookie import, subscription tokens, internal tokens,
reverse-engineered login, and bundled Claude Code CLI distribution are rejected.

## Verification

The local boundary parser and tests reject forbidden credential kinds and unknown
protocol labels. The existing RC-019/020/029 research registers remain the source
of rights and authorization restrictions; no private Claude Code protocol is
implemented.
