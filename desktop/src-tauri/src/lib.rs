mod backend_service;
use tauri::{
    Manager, 
    SystemTray, 
    SystemTrayMenu, 
    SystemTrayEvent,
    SystemTrayMenuItem
};

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // 解析命令行参数
    let args: Vec<String> = std::env::args().collect();
    let service_mode = args.iter().any(|arg| arg == "--service");
    
    // 设置服务模式
    backend_service::set_service_mode(service_mode);

    // 注册全局清理处理程序
    if !service_mode {
        ctrlc::set_handler(move || {
            backend_service::stop_backend_service();
            std::process::exit(0);
        }).expect("Error setting Ctrl-C handler");
    }

    // 启动后端服务
    if let Err(e) = backend_service::start_backend_service() {
        eprintln!("Failed to start backend service: {}", e);
        std::process::exit(1);
    }

    tauri::Builder::default()
        .system_tray(
            SystemTray::new().with_menu(
                SystemTrayMenu::new()
                    .add_item("显示", "显示窗口")
                    .add_native_item(SystemTrayMenuItem::Separator)
                    .add_item("退出", "退出程序")
            )
        )
        .on_system_tray_event(|app, event| {
            let window = app.get_webview_window("main").unwrap();
            match event {
                tauri::SystemTrayEvent::MenuItemClick { id, .. } => match id.as_str() {
                    "显示" => {
                        window.show().unwrap();
                        window.set_focus().unwrap();
                    }
                    "退出" => {
                        backend_service::stop_backend_service();
                        std::process::exit(0);
                    }
                    _ => {}
                },
                _ => {}
            }
        })
        .setup(|app| {
            let _window = app.get_webview_window("main").unwrap();
            Ok(())
        })
        .on_window_event(move |_window, event| {  // Added move keyword here
            if let tauri::WindowEvent::Destroyed = event {
                if !service_mode {
                    backend_service::stop_backend_service();
                }
            }
        })
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![greet])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
