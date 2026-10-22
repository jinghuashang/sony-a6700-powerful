import SwiftUI
import AppKit
import Foundation

struct CheckRow: Decodable, Identifiable {
    let id: String
    let name: String
    let ok: Bool
    let detail: String
    let remediation: String
}
struct EnvironmentState: Decodable { let ready: Bool; let checks: [CheckRow] }
struct NoticeSection: Decodable, Identifiable {
    let id: String; let title: String; let icon: String; let level: String
    let body: String; let source_url: String
}
struct NoticeContent: Decodable {
    let title: String; let introduction: String; let acknowledgement: String
    let sections: [NoticeSection]
}
struct MenuGuideRow: Decodable, Identifiable {
    let id: String; let title: String; let path: [String]; let target: String
    let choices: [String]; let source_url: String; let source_note: String
}
struct PreparationRow: Decodable, Identifiable {
    let id: String; let title: String; let instruction: String; let confirmed: Bool
    let confirmation_label: String; let skip_label: String; let menu_guides: [MenuGuideRow]
}
struct FeatureRow: Decodable, Identifiable {
    let id: String; let name: String; let state: String; let selected: Bool?
    let requires: [String]?
    let available: Bool?; let unavailable_reason: String?
    var isAvailable: Bool { available != false }
}
struct BackupRow: Decodable, Identifiable {
    let id: String; let name: String; let created_at: String; let size: Int
    let sector_count: Int; let total_bytes: Int; let bundle_state: String
    let features: [FeatureRow]
}
struct ScenarioRow: Decodable, Identifiable { let id: String; let name: String }
struct InspectSummary: Decodable {
    let compatible: Bool; let read_sectors: Int; let read_bytes: Int
    let features: [FeatureRow]
}
struct OperationResult: Decodable {
    let status: String; let title: String; let detail: String; let success: Bool; let error: String
    let backup_path: String?; let backup_sha256: String?; let backup_id: String?
}
struct Snapshot: Decodable {
    let revision: Int; let phase: String; let scenario: String; let scenarios: [ScenarioRow]
    let environment: EnvironmentState; let checked: Bool; let steps: [PreparationRow]
    let notice: NoticeContent; let notice_acknowledged: Bool
    let ready: Bool; let compatible: Bool; let connected: Bool; let busy: Bool
    let features: [FeatureRow]; let inspect_summary: InspectSummary?
    let backups: [BackupRow]; let backup_dir: String
    let action: String; let result: OperationResult?
    let simulation: Bool; let device_access: Bool; let write_attempted: Bool
}

/// The native view owns presentation only. The Python service owns preparation,
/// state transitions, planning and the in-memory transaction backend.
final class PreviewModel: ObservableObject {
    private static let operationInProgressMessage = "操作尚未结束，请保留窗口和 USB 连接。如需停止，请点击取消并等待明确结果。"
    @Published var state: Snapshot?
    @Published var progress: [String] = []
    @Published var error = ""
    @Published private(set) var pendingAction: String?
    var isBusy: Bool { pendingAction != nil || state?.busy == true }
    private var process: Process?
    private var input: FileHandle?
    private var buffer = Data()
    private let reader = DispatchQueue(label: "a6700.preview.json")
    private var physicalMode = false
    private var generation = UUID()

    func start(physical: Bool = false) {
        do {
            physicalMode = physical
            let session = UUID()
            generation = session
            reader.sync { buffer = Data() }
            state = nil
            progress = []
            error = ""
            pendingAction = nil
            guard let resources = Bundle.main.resourceURL else { throw bridgeError("预览资源缺失。") }
            let config = try JSONSerialization.jsonObject(with: Data(contentsOf: resources.appendingPathComponent("runtime.json"))) as? [String: String]
            guard let configuredPython = config?["python"] else {
                throw bridgeError("应用运行配置缺失。")
            }
            let bundled = config?["kind"] == "bundled"
            let python = bundled ? resources.appendingPathComponent(configuredPython).standardizedFileURL.path : configuredPython
            guard (!bundled || python.hasPrefix(resources.standardizedFileURL.path + "/")),
                  FileManager.default.isExecutableFile(atPath: python) else {
                throw bridgeError("本机开发运行环境已移动。请重新构建桌面预览。")
            }
            let worker = Process()
            worker.executableURL = URL(fileURLWithPath: python)
            worker.arguments = bundled
                ? ["-I", "-S", "-B", "-u", resources.appendingPathComponent("worker.py").path] + (physical ? ["--physical"] : [])
                : ["-u", "-m", physical ? "a6700_unlock.desktop.physical_bridge" : "a6700_unlock.desktop.bridge"]
            var environment = ProcessInfo.processInfo.environment
            environment["PYTHONPATH"] = resources.appendingPathComponent("python").path
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            worker.environment = environment
            let source = Pipe(), output = Pipe(), diagnostics = Pipe()
            worker.standardInput = source; worker.standardOutput = output; worker.standardError = diagnostics
            input = source.fileHandleForWriting
            output.fileHandleForReading.readabilityHandler = { [weak self] handle in
                let data = handle.availableData
                guard !data.isEmpty else { return }
                self?.reader.async { [weak self] in
                    guard self?.generation == session else { return }
                    self?.read(data, session: session)
                }
            }
            // Drain stderr so a failed dependency cannot fill a pipe and freeze
            // the interface. Raw diagnostics/paths are not shown in user pages.
            diagnostics.fileHandleForReading.readabilityHandler = { handle in _ = handle.availableData }
            worker.terminationHandler = { [weak self] job in
                guard job.terminationStatus != 0 else { return }
                DispatchQueue.main.async {
                    guard self?.generation == session else { return }
                    self?.error = (self?.physicalMode ?? false)
                        ? "真实设备服务已退出。请检查 USB 连接后重新打开应用。"
                        : "模拟服务已退出。请关闭窗口后重新打开预览。"
                }
            }
            try worker.run()
            process = worker
            if physical { send("environment") } else { send("reset", extra: ["scenario": "enabled"]) }
        } catch { self.error = error.localizedDescription }
    }
    func setMode(_ physical: Bool) {
        guard physical != physicalMode, !isBusy else { return }
        shutdown()
        start(physical: physical)
    }
    private func bridgeError(_ text: String) -> NSError {
        NSError(domain: "A6700Preview", code: 1, userInfo: [NSLocalizedDescriptionKey: text])
    }
    private func read(_ data: Data, session: UUID) {
        buffer.append(data)
        while let end = buffer.firstIndex(of: 10) {
            let line = buffer.prefix(upTo: end)
            buffer.removeSubrange(...end)
            guard let message = try? JSONSerialization.jsonObject(with: line) as? [String: Any],
                  let kind = message["type"] as? String else { continue }
            if kind == "state" {
                guard let raw = message["state"],
                      let encoded = try? JSONSerialization.data(withJSONObject: raw),
                      let snapshot = try? JSONDecoder().decode(Snapshot.self, from: encoded) else {
                    DispatchQueue.main.async { [weak self] in
                        guard self?.generation == session else { return }
                        self?.error = "本地服务状态格式不兼容，请重新获取同一版本的完整应用。"
                    }
                    continue
                }
                DispatchQueue.main.async { [weak self] in
                    guard let self = self else { return }
                    guard self.generation == session else { return }
                    if let current = self.state, snapshot.revision < current.revision { return }
                    let valid = self.physicalMode
                        ? !snapshot.simulation
                        : snapshot.simulation && !snapshot.device_access && !snapshot.write_attempted
                    guard valid else {
                        self.error = self.physicalMode
                            ? "真实设备服务返回了模拟状态，已停止更新。"
                            : "预览收到不支持的设备模式，已停止更新。"
                        return
                    }
                    self.state = snapshot
                    if !snapshot.busy && self.error == Self.operationInProgressMessage {
                        self.error = ""
                    }
                    if snapshot.busy && snapshot.action == self.pendingAction {
                        self.pendingAction = nil
                    }
                }
            } else if kind == "progress", let text = message["message"] as? String {
                DispatchQueue.main.async { [weak self] in
                    guard self?.generation == session else { return }
                    self?.progress.append(text)
                }
            } else if kind == "error" {
                DispatchQueue.main.async { [weak self] in
                    guard self?.generation == session else { return }
                    self?.error = message["message"] as? String ?? "预览操作失败。"
                    self?.pendingAction = nil
                }
            }
        }
    }
    func send(_ command: String, extra: [String: Any] = [:]) {
        if ["inspect", "unlock", "close", "backup", "restore"].contains(command) {
            guard !isBusy else { return }
            pendingAction = command
        }
        error = ""
        if ["inspect", "unlock", "close", "backup", "restore", "reset", "environment"].contains(command) { progress = [] }
        var request = extra; request["command"] = command
        guard let bytes = try? JSONSerialization.data(withJSONObject: request), let input = input else {
            pendingAction = nil
            error = "本地服务尚未就绪，请重新打开应用。"
            return
        }
        do { try input.write(contentsOf: bytes + Data([10])) }
        catch {
            pendingAction = nil
            self.error = "无法连接本地服务。请重新打开应用；如操作已开始，先核实相机状态。"
        }
    }
    func shutdown() {
        generation = UUID()
        if let input = input, let process = process, process.isRunning {
            if let bytes = try? JSONSerialization.data(withJSONObject: ["command": "shutdown"]) {
                try? input.write(contentsOf: bytes + Data([10]))
            }
            try? input.close()
            let deadline = Date().addingTimeInterval(1.5)
            while process.isRunning && Date() < deadline {
                Thread.sleep(forTimeInterval: 0.05)
            }
            if process.isRunning { process.terminate() }
        } else {
            try? input?.close()
            if process?.isRunning == true { process?.terminate() }
        }
        process = nil
        input = nil
    }

    func allowWindowExit() -> Bool {
        guard isBusy else { return true }
        error = Self.operationInProgressMessage
        NSSound.beep()
        return false
    }
}
