mod backend_service;
use tauri::Manager;

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // 注册全局清理处理程序
    ctrlc::set_handler(move || {
        backend_service::stop_backend_service();
        std::process::exit(0);
    }).expect("Error setting Ctrl-C handler");

    // 启动后端服务
    if let Err(e) = backend_service::start_backend_service() {
        eprintln!("Failed to start backend service: {}", e);
        std::process::exit(1);
    }

    tauri::Builder::default()
        .setup(|app| {
            let _window = app.get_webview_window("main").unwrap(); // Add underscore
            Ok(())
        })
        .on_window_event(|_window, event| {  // Add underscore
            if let tauri::WindowEvent::Destroyed = event {
                // 当窗口关闭时停止后端服务
                backend_service::stop_backend_service();
            }
        })
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![greet])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
