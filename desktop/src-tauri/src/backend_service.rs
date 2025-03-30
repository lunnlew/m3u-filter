use std::process::{Child, Command};
use std::thread;
use std::time::Duration;
use reqwest::blocking::Client;
use sysinfo::{System, ProcessRefreshKind, RefreshKind};

const HEALTH_CHECK_URL: &str = "http://localhost:3232/api/health";
const MAX_RETRIES: u32 = 10;
const RETRY_DELAY: Duration = Duration::from_secs(1);

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

#[cfg(unix)]
use std::os::unix::process::CommandExt;

pub struct ServiceHandle {
    process: Child,
    exe_name: String,
}

impl ServiceHandle {
    pub fn stop(mut self) {
        // 先尝试优雅关闭
        let _ = self.process.kill();
        let _ = self.process.wait();
        
        // 确保清理所有相关进程
        thread::sleep(RETRY_DELAY);
        if let Ok(pids) = find_existing_service_process(&self.exe_name) {
            for pid in pids {
                terminate_process(pid);
                thread::sleep(RETRY_DELAY);
            }
        }
    }
}

fn check_service_health() -> bool {
    let client = Client::builder()
        .timeout(Duration::from_secs(5))
        .build()
        .unwrap_or_else(|_| Client::new());
        
    match client.get(HEALTH_CHECK_URL).send() {
        Ok(response) => response.status().is_success(),
        Err(_) => false,
    }
}

fn find_existing_service_process(exe_name: &str) -> Result<Vec<u32>, String> {
    let sys = System::new_with_specifics(
        RefreshKind::everything().with_processes(ProcessRefreshKind::everything())
    );
    
    Ok(sys.processes()
        .iter()
        .filter(|(_, process)| {
            let name = process.name().to_string_lossy();
            name.contains(exe_name)
        })
        .map(|(_, process)| process.pid().as_u32())
        .collect())
}

#[cfg(target_os = "windows")]
fn terminate_process(pid: u32) {
    use windows_sys::Win32::System::Threading::{OpenProcess, TerminateProcess};
    use windows_sys::Win32::Foundation::{HANDLE, CloseHandle};
    use windows_sys::Win32::System::Threading::PROCESS_TERMINATE;
    
    unsafe {
        let handle: HANDLE = OpenProcess(PROCESS_TERMINATE, 0, pid);
        if handle != 0 {
            let _ = TerminateProcess(handle, 0);
            let _ = CloseHandle(handle);
        }
    }
}

#[cfg(unix)]
fn terminate_process(pid: u32) {
    use nix::sys::signal::{kill, Signal};
    use nix::unistd::Pid;
    let _ = kill(Pid::from_raw(pid as i32), Signal::SIGTERM);
}

pub fn start_backend_service() -> Result<ServiceHandle, String> {
    let exe_name = if cfg!(target_os = "windows") {
        "m3u-filter-service.exe"
    } else {
        "m3u-filter-service"
    };

    // 确保清理已存在的进程
    if let Ok(pids) = find_existing_service_process(exe_name) {
        for pid in pids {
            terminate_process(pid);
            thread::sleep(RETRY_DELAY);
        }
    }

    let backend_path = std::env::current_exe()
        .map_err(|e| format!("Failed to get current exe path: {}", e))?
        .parent()
        .ok_or_else(|| "Failed to get parent directory".to_string())?
        .join(exe_name);

    #[cfg(target_os = "windows")]
    let mut command = {
        let mut cmd = Command::new(backend_path.as_os_str());
        cmd.creation_flags(0x08000000); // CREATE_NO_WINDOW
        cmd
    };

    #[cfg(unix)]
    let mut command = {
        let mut cmd = Command::new(backend_path.as_os_str());
        unsafe {
            cmd.pre_exec(|| {
                nix::unistd::setsid().expect("Failed to create new session");
                Ok(())
            });
        }
        cmd
    };

    let log_path = backend_path.parent()
        .ok_or_else(|| "Failed to get parent directory".to_string())?
        .join("backend.log");

    let log_file = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&log_path)
        .map_err(|e| format!("Failed to open log file: {}", e))?;

    let mut process = command // Added 'mut' here
        .stdout(log_file.try_clone().map_err(|e| format!("Failed to clone log file handle: {}", e))?)
        .stderr(log_file)
        .spawn()
        .map_err(|e| format!("Failed to start backend service: {}", e))?;

    // 等待服务启动并进行健康检查
    for _ in 0..MAX_RETRIES {
        thread::sleep(RETRY_DELAY);
        if check_service_health() {
            return Ok(ServiceHandle { 
                process,
                exe_name: exe_name.to_string()
            });
        }
    }

    // 启动失败时清理
    let _ = process.kill();
    let _ = process.wait();
    
    // 再次检查并清理可能的残留进程
    if let Ok(pids) = find_existing_service_process(exe_name) {
        for pid in pids {
            terminate_process(pid);
        }
    }
    
    Err("Backend service failed to start".to_string())
}