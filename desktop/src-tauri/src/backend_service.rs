use std::process::{Child, Command};
use std::sync::Mutex;
use std::thread;
use std::time::Duration;
use reqwest::blocking::Client;

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

#[cfg(any(target_os = "linux", target_os = "macos"))]
use std::os::unix::process::CommandExt;

static BACKEND_PROCESS: Mutex<Option<Child>> = Mutex::new(None);
const MAX_RETRIES: u32 = 3;
const HEALTH_CHECK_URL: &str = "http://localhost:3232/api/health";
static SERVICE_MODE: Mutex<bool> = Mutex::new(false);  // 添加服务模式标志

pub fn set_service_mode(enabled: bool) {
    if let Ok(mut mode) = SERVICE_MODE.lock() {
        *mode = enabled;
    }
}

fn check_service_health() -> bool {
    let client = Client::new();
    match client.get(HEALTH_CHECK_URL).send() {
        Ok(response) => response.status().is_success(),
        Err(_) => false,
    }
}

pub fn start_backend_service() -> Result<(), String> {
    let exe_name = if cfg!(target_os = "windows") {
        "m3u-filter-service.exe"
    } else {
        "m3u-filter-service"
    };

    let backend_path = std::env::current_exe()
        .map_err(|e| format!("Failed to get current exe path: {}", e))?
        .parent()
        .ok_or_else(|| "Failed to get parent directory".to_string())?
        .join(exe_name);

    // 创建日志文件路径
    let log_path = backend_path.parent()
        .ok_or_else(|| "Failed to get parent directory".to_string())?
        .join("backend.log");

    for attempt in 1..=MAX_RETRIES {
        let log_file = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&log_path)
            .map_err(|e| format!("Failed to open log file: {}", e))?;

        #[cfg(target_os = "windows")]
        let mut command = {
            let mut cmd = Command::new(backend_path.as_os_str());
            cmd.creation_flags(0x08000000); // CREATE_NO_WINDOW
            cmd
        };

        #[cfg(any(target_os = "linux", target_os = "macos"))]
        let mut command = {
            let mut cmd = Command::new(backend_path.as_os_str());
            unsafe {
                cmd.pre_exec(|| {
                    Ok(())
                });
            }
            cmd
        };

        let mut process = command
            .stdout(log_file.try_clone().map_err(|e| format!("Failed to clone log file handle: {}", e))?)
            .stderr(log_file)
            .spawn()
            .map_err(|e| format!("Failed to start backend service: {}", e))?;

        // 等待服务启动并进行健康检查
        for _ in 0..10 {
            thread::sleep(Duration::from_secs(1));
            if check_service_health() {
                let mut guard = BACKEND_PROCESS.lock().unwrap();
                *guard = Some(process);
                return Ok(());
            }
        }

        // 如果健康检查失败，终止进程并重试
        let _ = process.kill();
        if attempt == MAX_RETRIES {
            return Err(format!("Backend service failed to start after {} attempts", MAX_RETRIES));
        }
        thread::sleep(Duration::from_secs(2));
    }

    Err("Backend service failed to start".to_string())
}

pub fn stop_backend_service() {
    // 如果是服务模式，不终止后台进程
    if let Ok(mode) = SERVICE_MODE.lock() {
        if *mode {
            return;
        }
    }

    if let Ok(mut guard) = BACKEND_PROCESS.lock() {
        if let Some(mut process) = guard.take() {
            // 先尝试正常终止进程
            let _ = process.kill();
            
            // 等待进程完全退出，设置超时时间
            let timeout = Duration::from_secs(5);
            let start = std::time::Instant::now();
            
            while start.elapsed() < timeout {
                match process.try_wait() {
                    Ok(Some(_)) => return, // 进程已退出
                    Ok(None) => thread::sleep(Duration::from_millis(100)), // 继续等待
                    Err(_) => break, // 出错时退出循环
                }
            }
            
            // 如果超时，强制终止进程
            #[cfg(target_os = "windows")]
            {
                use std::os::windows::process::CommandExt;
                let _ = Command::new("taskkill")
                    .args(&["/F", "/PID"])
                    .arg(process.id().to_string())
                    .creation_flags(0x08000000)
                    .output();
            }
            
            #[cfg(not(target_os = "windows"))]
            {
                use std::os::unix::prelude::*;
                let _ = Command::new("kill")
                    .args(&["-9", &process.id().to_string()])
                    .output();
            }
        }
    }
}