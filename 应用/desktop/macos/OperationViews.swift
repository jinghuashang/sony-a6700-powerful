import SwiftUI
import AppKit

struct ResultReceipt: View {
    let result: OperationResult
    let physical: Bool
    let dismiss: () -> Void
    @State private var details = false
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .top, spacing: 11) {
                Image(systemName: "checkmark.circle.fill").font(.system(size: 19)).foregroundColor(UI.accent)
                VStack(alignment: .leading, spacing: 5) {
                    Text(result.title).font(.system(size: 12, weight: .semibold))
                    Text(result.detail).font(.system(size: 11)).foregroundColor(UI.muted)
                        .fixedSize(horizontal: false, vertical: true)
                }
                Spacer()
                if let path = result.backup_path, !path.isEmpty {
                    Button("在访达中显示") { NSWorkspace.shared.activateFileViewerSelecting([URL(fileURLWithPath: path)]) }
                        .buttonStyle(.plain).font(.system(size: 11)).foregroundColor(UI.accent)
                }
                Button { dismiss() } label: { Image(systemName: "xmark") }.buttonStyle(.plain)
                    .font(.system(size: 10)).foregroundColor(UI.muted).accessibilityLabel("收起操作结果")
            }
            if let digest = result.backup_sha256, !digest.isEmpty {
                DisclosureGroup("文件校验信息", isExpanded: $details) {
                    Text(digest).font(.system(size: 10, design: .monospaced)).textSelection(.enabled)
                }.font(.system(size: 10)).foregroundColor(UI.muted)
            }
        }.padding(15).frame(maxWidth: .infinity, alignment: .leading)
            .background(UI.accent.opacity(0.045)).cornerRadius(10)
    }
}

struct OperationProgressView: View {
    @ObservedObject var model: PreviewModel
    let physical: Bool
    @State private var started = Date()
    @State private var cancelled = false
    @State private var details = false
    private var title: String {
        switch model.state?.action {
        case "inspect": return "正在连接并检查"
        case "backup": return "正在保存功能状态"
        case "restore": return "正在恢复所选功能"
        case "close": return "正在关闭所选功能"
        default: return "正在解锁所选功能"
        }
    }
    var body: some View {
        VStack(alignment: .leading, spacing: 22) {
            PageTitle(title: title, subtitle: physical ? "请保持相机开机和 USB 连接，等待明确结果。" : "正在运行演示流程，不会访问真实相机。")
            Panel {
                HStack(alignment: .center, spacing: 18) {
                    ProgressView().controlSize(.regular).frame(width: 32)
                    VStack(alignment: .leading, spacing: 8) {
                        Text(cancelled ? "正在请求结束，请稍候…" : currentStep)
                            .font(.system(size: 16, weight: .semibold))
                            .fixedSize(horizontal: false, vertical: true)
                        TimelineView(.periodic(from: started, by: 1)) { context in
                            Text("已用 \(max(0, Int(context.date.timeIntervalSince(started)))) 秒 · " + (physical ? "请勿拔线或关机" : "演示步骤会短暂停留"))
                                .font(.system(size: 11)).foregroundColor(UI.muted)
                        }
                    }
                    Spacer()
                }.padding(.vertical, 18)
                if !model.progress.isEmpty {
                    Divider().padding(.vertical, 14)
                    DisclosureGroup("查看处理过程", isExpanded: $details) {
                        VStack(alignment: .leading, spacing: 9) {
                            ForEach(Array(model.progress.enumerated()), id: \.offset) { index, line in
                                Label(line, systemImage: index == model.progress.count - 1 ? "ellipsis.circle" : "checkmark.circle")
                                    .font(.system(size: 11)).foregroundColor(UI.muted)
                                    .fixedSize(horizontal: false, vertical: true)
                            }
                        }.padding(.top, 12)
                    }.font(.system(size: 11)).foregroundColor(UI.muted)
                }
            }
            HStack(spacing: 14) {
                Button(cancelled ? "正在等待结果…" : "请求取消") {
                    cancelled = true; model.send("cancel")
                }.buttonStyle(PrimaryStyle(secondary: true)).disabled(cancelled)
                Text("取消不会强制中断已发送的写入，请等待核验结果。")
                    .font(.system(size: 11)).foregroundColor(UI.muted)
            }
        }
    }
    private var currentStep: String {
        if let last = model.progress.last { return last }
        return physical ? "正在准备连接相机…" : "正在准备演示数据…"
    }
}

struct OperationFailureView: View {
    @ObservedObject var model: PreviewModel
    let physical: Bool
    @State private var details = false
    private var status: String { model.state?.result?.status ?? "error" }
    private var uncertain: Bool { ["uncertain", "verification-failed", "recovery-required"].contains(status) }
    var body: some View {
        VStack(alignment: .leading, spacing: 22) {
            PageTitle(title: model.state?.result?.title ?? "操作未完成",
                      subtitle: uncertain ? "先核实当前状态，再决定下一步。" : "处理下面的问题后，可以重新连接并检查。")
            Panel {
                HStack(alignment: .top, spacing: 16) {
                    Image(systemName: uncertain ? "questionmark.circle.fill" : "exclamationmark.circle.fill")
                        .font(.system(size: 31)).foregroundColor(UI.amber)
                    VStack(alignment: .leading, spacing: 10) {
                        Text(model.state?.result?.detail ?? "当前状态无法确认，请重新检查。")
                            .font(.system(size: 14, weight: .medium)).fixedSize(horizontal: false, vertical: true)
                        Text(nextStep).font(.system(size: 12)).foregroundColor(UI.muted).lineSpacing(4)
                            .fixedSize(horizontal: false, vertical: true)
                        if !physical {
                            Text("这是演示场景，真实相机没有被访问或修改。")
                                .font(.system(size: 11)).foregroundColor(UI.accent)
                        }
                    }
                }.padding(.bottom, 18)
                Divider()
                DisclosureGroup("查看诊断详情", isExpanded: $details) {
                    VStack(alignment: .leading, spacing: 9) {
                        if let error = model.state?.result?.error, !error.isEmpty {
                            Text(error).textSelection(.enabled)
                        }
                        Text("状态：" + status)
                        Text(physical ? "功能写入器：" + (model.state?.write_attempted == true ? "已发送或尝试发送" : "未发送") : "真实设备访问：无")
                        ForEach(Array(model.progress.enumerated()), id: \.offset) { _, line in Text(line) }
                    }.font(.system(size: 11)).foregroundColor(UI.muted)
                        .fixedSize(horizontal: false, vertical: true).padding(.top, 12)
                }.font(.system(size: 11)).foregroundColor(UI.muted).padding(.top, 15)
            }
            HStack {
                Button("重新准备并检查") { model.send("restart_preparation") }.buttonStyle(PrimaryStyle())
                if !physical { Text("也可在右上角“演示设置”切换场景。").font(.system(size: 11)).foregroundColor(UI.muted) }
                Spacer()
            }
        }
    }
    private var nextStep: String {
        if !physical {
            switch status {
            case "uncertain", "verification-failed", "recovery-required":
                return "保留本次演示结果，重新准备并检查以核实演示状态。"
            case "blocked":
                return "当前演示内容不兼容。可在演示设置中切换场景，再重新准备。"
            case "cancelled":
                return "本次演示已结束。重新准备后可以再次检查。"
            case "rolled-back":
                return "演示状态已回退。重新准备并检查后，可以继续体验。"
            default:
                return "在右上角“演示设置”重新连接演示设备，再返回准备页检查。"
            }
        }
        switch status {
        case "blocked": return "请核对机型、固件和已有修改。不要跳过兼容检查或重复尝试写入。"
        case "uncertain", "verification-failed", "recovery-required": return "请保留本次记录，检查相机状态，必要时拔线并重启相机。"
        case "cancelled": return "本次操作已结束。重新确认相机准备状态后，可以再次检查。"
        case "rolled-back": return "已确认回退结果。重新连接并检查后，再决定是否继续。"
        default: return "确认相机为 MSC 模式、保持唤醒；如有 FTP 菜单，请先关闭传输。"
        }
    }
}
