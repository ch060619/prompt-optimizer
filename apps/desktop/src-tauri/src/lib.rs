use std::path::PathBuf;

#[tauri::command]
fn open_window() -> Result<(), String> {
    Ok(())
}

#[tauri::command]
fn start_sidecar() -> Result<PathBuf, String> {
    Err("sidecar launch is owned by the packaged host process".to_string())
}

#[tauri::command]
fn store_secret() -> Result<(), String> {
    Err("secret storage requires the platform keychain bridge".to_string())
}

#[tauri::command]
fn pick_file() -> Result<(), String> {
    Err("file picker is available in the packaged desktop host".to_string())
}

pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            open_window,
            start_sidecar,
            store_secret,
            pick_file
        ])
        .run(tauri::generate_context!())
        .expect("error while running Rabbit Code desktop shell");
}
