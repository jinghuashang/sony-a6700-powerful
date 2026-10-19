# 来源、许可与发布边界

## 自有内容

本仓库文档、自有 Python 主机实现与本地构建适配代码按 GPL-3.0-only 提供。协议编码器依据协议字段事实重新实现；原理和来源参考不省略。GPL 文本复制自本项目已有发布工程，其原文来源为 SPDX license-list-data 的 GPL-3.0-only 文本。

## 上游

参考项目：[DavidBuchanan314/ILCE-7M4-RE](https://github.com/DavidBuchanan314/ILCE-7M4-RE)，固定提交 [`2328d18ce640e6c8cd9341efcf0043ce9042a135`](https://github.com/DavidBuchanan314/ILCE-7M4-RE/tree/2328d18ce640e6c8cd9341efcf0043ce9042a135)。该项目建立了 Pico PIO/DMA 引导与 Mira AP RAM Fastboot 的基础。本项目增加 A6700 接线／GPIO 路由、只读限制、上电检测与相应主机流程；不能将整个基础机制归功于本项目。

2026-10-19 检查本地固定提交的 Git 文件树，未找到 LICENSE 文件。**不能把 GitHub 可见等同于已获开源再分发许可**。因此本仓库不转载上游原件、不提交其派生 UF2／RAM 程序，也不将其重新标为 GPL。只提供固定提交引用、自有适配脚本与输入哈希；使用者在单独取得的本地副本上生成并研究。该安排不授予上游作品的新权利，公开分发构建结果仍待上游许可明确。

`upstream.lock.json` 记录仓库、提交与 33 个构建输入的哈希，不包含输入本体。`scripts/upstream.py` 在每次生成前检查这些数据；不会自动下载源码或执行上游脚本。生成的源码与二进制只落在被忽略的 `build/`，不会纳入本仓库的 Git 提交。

Arduino-Pico／Pico SDK、编译器、PySerial、PyUSB 和系统 libusb 是独立依赖，遵循各自许可，本仓库不捆绑它们。Pico PIO 程序及原始 RAM Fastboot 来源仍为上述上游。

## 保留的公开技术证据

| 对象 | 值／SHA-256 | 说明 |
|---|---|---|
| Pico 版本 | `a6700_pio_od 2` | 主机必须精确匹配 |
| 历史 Pico UF2 | `8a8bb5c1c962b3a174c7f7715d24e0620b9c20367e75538bda27645c19115d3e` | 不随仓库分发，未在本轮重新编译 UF2 |
| Pico v2 sketch | `acc13bfc67e78534ffcb1ec5164a1e45b43ce572a51f71d89b9bb489cee2cfd7` | 适配后文本与历史实机版本核对 |
| RAM 只读程序 | `8d8b968940a868116bb3cd77c0f040795c1aae28d2a5d96d119d992498473fcb` | 20,992 字节；主机发送前检查 |
| RAM 地址／入口 | `0xfe020000` | 固定窗口，不提供任意目标地址参数 |

## 不公开的资料

不上传厂商完整固件、BootROM 镜像、相机用户区／引导区备份、ProductInfo、校准数据、设备唯一信息、照片、网络配置、原始 USB 抓包或带私人路径的内部报告。公开证据写成去标识摘要，不将整个研究目录直接推送到 GitHub。锁文件中的哈希只针对代码输入和通用工具产物，不针对私人备份。

本批没有发布功能解锁或关闭器；后续按模块补充来源、许可和验证，不把本批硬件入口等同于整个产品已验收。
