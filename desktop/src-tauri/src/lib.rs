mod backend_service;
use tauri::Manager;
use std::sync::{Arc, Mutex};

struct AppState {
    service_handle: Mutex<Option<backend_service::ServiceHandle>>, // Removed Arc wrapper
}

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let state = Arc::new(AppState {
        service_handle: Mutex::new(None),
    });

    let state_clone = state.clone(); // Clone state for the second closure

    tauri::Builder::default()
        .manage(state.clone())
        .setup(move |app| {
            let _window = app.get_webview_window("main").unwrap();
            
            let handle = backend_service::start_backend_service()?;
            *state.service_handle.lock().unwrap() = Some(handle);

            #[cfg(debug_assertions)]
            {
                _window.open_devtools();
                _window.close_devtools();
            }
            Ok(())
        })
        .on_window_event(move |_window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                if let Some(handle) = state_clone.service_handle.lock().unwrap().take() {
                    handle.stop();
                }
            }
        })
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![greet])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
