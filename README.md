个人对 Sony A6700 固件与 USB 维护协议的学习记录，分享已走通的教程和 **Powerful6700** 实验工具，与 Sony 官方无关。

目前仅针对 **A6700、2.00 固件**。操作可能影响保修，存在无法启动及数据丢失风险；请先阅读[声明与使用边界](声明与使用边界.md)。

## Windows 移植

本项目希望将已验证的主机流程逐步移植到 **Windows 10/11 x64**。当前已完成的适配：

- 只读 Pico 引导、Fastboot 查询与区间备份脚本可在原生 Windows 运行，依赖自动提供 libusb DLL；
- 应用 CLI 的设备锁、状态目录、目录同步与 libusb 加载已支持 Windows，`应用/start.cmd` 可直接启动；
- 仓库统一 LF 检出，固定源码与原生载荷哈希在 Windows 不再因 CRLF 失效；
- 离线检查覆盖 Windows：`源码` 脚本、`应用` 156 项测试（含原生 ELF 仿真）均在本机通过。

**Windows 的真实相机通信尚未验收**：Pico 串口、相机 RAM Fastboot 的 WinUSB 接入、应用 USB 维护会话仍需实机验证。macOS 内置环境版安装包保持不变；Windows 暂不提供安装包，源码运行见[操作手册](操作手册.md)和[应用说明](应用/README.md)。

## 从这里开始

| 想做什么 | 入口 |
|---|---|
| 使用一键解锁应用 | [下载测试版](https://github.com/xyzhangxin/sony-a6700-powerful/releases) · [使用说明](Powerful6700使用说明.md) |
| 理解普通 USB 如何取得临时 root 执行能力 | [USB 进入 root 教程](USB进入root教程.md) |
| 从源码执行功能解锁／关闭 | [USB 功能刷写教程](USB功能刷写教程.md) |
| 用 Pico 进入 Fastboot 并读取备份 | [硬件说明](硬件说明.md) · [操作手册](操作手册.md) |

**Powerful6700 0.2.0** 继续面向更多用户测试，安装包仅支持 Apple Silicon、macOS 13+，内置运行环境，保留演示模式。开放 FTP、关机快门帘、灵活曝光和电子快门声音，可逐项解锁／关闭。位移多帧合成、动态增强防抖暂禁用。

<img width="1100" height="798" alt="1792660874815000_F84B856F-BAF4-4711-8F70-52066802C66B" src="https://github.com/user-attachments/assets/4ebb305d-47a4-4b22-a701-74a275fe5532" />


0.2 主要修复 USB 连接／重连问题，优化操作结果、断电重启和继续操作的引导。完整备份恢复尚未提供；软件路线仅修改清单内功能字段，不提供任意固件刷入。更新详情见[变更记录](应用/CHANGELOG.md)。

## 开发计划与进展

- **功能开发**：先完善现有四项功能的兼容性与测试，再推进动态增强防抖、FL2／FL3 等研究；未验证项不作为可用能力。
- **开源与工具**：公开教程、应用及对应源码，逐步改善跨机身适配和连接体验；完整备份／恢复、更多平台及功能包更新后续推进。

详见[开发计划与进展](开发计划与进展.md)。应用源码在[应用/](应用/)，Pico 源码在[源码/](源码/)；参与改进见[参与开发](参与开发.md)和 [AGENTS.md](AGENTS.md)。

## 支持项目

如果这个项目对你有帮助，欢迎自愿支持一点 AI Token 费用，帮助加快开发与验证。

<p align="center">
  <img src="图片/支持项目.png" alt="支持项目：微信支付与支付宝收款码" width="760">
</p>

## 参考项目

- [ILCE-7M4-RE](https://github.com/DavidBuchanan314/ILCE-7M4-RE)：BootROM、Pico 引导与 RAM Fastboot 参考。
- [Arduino-Pico](https://github.com/earlephilhower/arduino-pico)：RP2040 编译环境。
- [Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE)：USB 维护协议与认证参考。

自有代码与文档采用 GPL-3.0-only；第三方来源及许可状态见 [NOTICE](NOTICE) 与[应用第三方归属](应用/THIRD_PARTY_NOTICES.md)。请勿上传固件、私人备份、机身数据或凭据。
