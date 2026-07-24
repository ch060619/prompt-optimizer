# Desktop App Boundary

`apps/desktop` is the desktop shell boundary. The Tauri project under `src-tauri` owns only
window lifecycle and OS bridge commands from `command-allowlist.toml`; Agent, Provider, Prompt,
Session, and storage business logic remains in the backend/App Server.

Build the shell after generating the frontend bundle:

```powershell
npm --prefix frontend run build
$env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
cargo check --manifest-path apps/desktop/src-tauri/Cargo.toml
```
