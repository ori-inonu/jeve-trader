#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use std::{io::{BufRead, BufReader, Write}, process::{Child, ChildStdin, Command, Stdio}, sync::{Mutex, atomic::{AtomicUsize, Ordering}}, time::{Duration, Instant}};
use tauri::{Emitter, Manager};

struct Engine { child: Mutex<Child>, input: Mutex<Option<ChildStdin>>, job: AtomicUsize }
impl Engine {
    fn stop(&self) {
        // EOF gives SQLite and the Excel worker time to close normally.
        if let Ok(mut input) = self.input.lock() { input.take(); }
        if let Ok(mut child) = self.child.lock() {
            let deadline = Instant::now() + Duration::from_secs(2);
            while matches!(child.try_wait(), Ok(None)) && Instant::now() < deadline {std::thread::sleep(Duration::from_millis(25));}
            if matches!(child.try_wait(), Ok(None)) {let _ = child.kill();}
            let _ = child.wait();
        }
        #[cfg(windows)] unsafe {
            let job = self.job.swap(0, Ordering::SeqCst);
            if job != 0 {windows_sys::Win32::Foundation::CloseHandle(job as _);}
        }
    }
}
impl Drop for Engine {
    fn drop(&mut self) {
        self.stop();
    }
}

#[tauri::command]
fn engine_send(message: String, engine: tauri::State<Engine>) -> Result<(), String> {
    if message.len() > 65536 { return Err("Mensagem excede o limite".into()); }
    let value: serde_json::Value = serde_json::from_str(&message).map_err(|_| "JSON inválido")?;
    if value["schema_version"] != 1 || !value["id"].is_string() || !value["method"].is_string() {return Err("Contrato inválido".into());}
    let mut guard = engine.input.lock().map_err(|_| "Motor indisponível")?;
    let input = guard.as_mut().ok_or("Motor encerrado")?;
    writeln!(input, "{}", value).map_err(|_| "Motor Python encerrou")?;
    input.flush().map_err(|_| "Motor Python encerrou".into())
}

fn start_engine(app: &tauri::App) -> Result<Engine, Box<dyn std::error::Error>> {
    #[cfg(debug_assertions)]
    let mut command = {
        let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
        let mut cmd = Command::new(root.join(".venv/Scripts/python.exe"));
        cmd.arg("-u").arg(root.join("app/desktop_service.py"));
        if let Ok(directory) = std::env::var("JEV_TRADER_DATA_DIR") {cmd.arg("--data-dir").arg(directory);}
        cmd
    };
    #[cfg(not(debug_assertions))]
    let mut command = {
        let mut cmd = Command::new(std::env::current_exe()?.parent().ok_or("Diretório não encontrado")?.join("jeve-engine.exe"));
        if let Ok(directory) = std::env::var("JEV_TRADER_DATA_DIR") {cmd.arg("--data-dir").arg(directory);}
        cmd
    };
    command.stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::null());
    #[cfg(windows)] {
        use std::os::windows::process::CommandExt;
        command.creation_flags(0x08000000); // CREATE_NO_WINDOW
    }
    let mut child = command.spawn()?;
    #[cfg(not(windows))] let job = 0usize;
    #[cfg(windows)] let job = unsafe {
        use std::os::windows::io::AsRawHandle;
        use windows_sys::Win32::{Foundation::CloseHandle, System::JobObjects::*};
        let handle = CreateJobObjectW(std::ptr::null(), std::ptr::null());
        let mut limits: JOBOBJECT_EXTENDED_LIMIT_INFORMATION = std::mem::zeroed();
        limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        if handle.is_null() || SetInformationJobObject(handle, JobObjectExtendedLimitInformation, &limits as *const _ as _, std::mem::size_of_val(&limits) as u32) == 0 || AssignProcessToJobObject(handle, child.as_raw_handle() as _) == 0 {
            if !handle.is_null() {CloseHandle(handle);}
            let _ = child.kill(); let _ = child.wait();
            return Err("Não foi possível supervisionar o processo Python".into());
        }
        handle as usize
    };
    let input = child.stdin.take().ok_or("stdin não disponível")?;
    let output = child.stdout.take().ok_or("stdout não disponível")?;
    let app_handle = app.handle().clone();
    std::thread::spawn(move || {
        for line in BufReader::new(output).lines().map_while(Result::ok) {
            if line.len() > 2_000_000 {continue;}
            if let Ok(value) = serde_json::from_str::<serde_json::Value>(&line) {let _ = app_handle.emit("engine", value);}
        }
    });
    Ok(Engine {child: Mutex::new(child), input: Mutex::new(Some(input)), job: AtomicUsize::new(job)})
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {let engine = start_engine(app)?; app.manage(engine); Ok(())})
        .invoke_handler(tauri::generate_handler![engine_send])
        .on_window_event(|window, event| { if matches!(event, tauri::WindowEvent::Destroyed) {window.state::<Engine>().stop();} })
        .run(tauri::generate_context!()).expect("Falha ao iniciar Jeve Trader");
}
