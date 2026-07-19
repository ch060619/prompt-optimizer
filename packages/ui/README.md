# UI Boundary

`packages/ui` owns shared React presentation primitives and design tokens. Product routes remain
in the current frontend until the shared protocol and shell boundaries are stable.

## Design Tokens

- Source: `tokens.json`
- Generated CSS variables: `tokens.css`
- Generated TypeScript values and names: `tokens.ts`
- Generated light/dark snapshot: `token-snapshot.md`
- Generator/check: `scripts/generate_design_tokens.py`

The source separates light/dark theme values from static semantic colors and dimensions. Frontend
CSS imports the generated variables and must not add raw main-interface colors, font stacks, spacing,
shadow, icon-size, or motion values. Run `python scripts/generate_design_tokens.py --write` after
changing the source; `python scripts/generate_design_tokens.py --check` is a workspace gate.
