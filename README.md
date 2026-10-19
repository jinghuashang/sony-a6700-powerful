# Sony A6700 Powerful

Sony A6700 / ILCE-6700 的独立社区项目，逐步公开硬件引导、功能管理及恢复方面的基础原理与自有代码。首批发布聚焦 **Pico → BootROM 串行加载 → RAM Fastboot** 路线。

Independent community project for the Sony A6700. This first publication documents the tested Pico boot path and provides host-side code and local build adapters. Only A6700 firmware 2.00 has been tested; this is an early developer release.

**仅在一台 A6700、2.00 固件与 RP2040 Pico 接线上验证过硬件路线。** 进入 Fastboot 是临时 RAM 引导，不会自动解锁功能，也不是 Sony 官方恢复模式。接线、时序或载荷错误可能造成设备故障，相关改动也可能影响保修或维修支持。完整备份、全盘恢复和可直接分发的救砖包尚未完成验证。

## 首批内容

| 内容 | 入口 |
|---|---|
| BootROM、Pico 与 RAM Fastboot 的关系 | [基础原理](docs/PRINCIPLES.md) |
| 材料、接线、上电与换线顺序 | [接线与操作](docs/WIRING.md) |
| 构建、注入命令、身份与分区表查询 | [Fastboot 操作](docs/FASTBOOT.md) |
| 自有代码、上游依赖、哈希与许可边界 | [来源与许可](docs/PROVENANCE.md) |
| 哪些是实机记录，哪些只是本轮离线测试 | [验证状态](docs/VALIDATION.md) |
| AI 分析和协作提交 | [AGENTS.md](AGENTS.md)、[CONTRIBUTING.md](CONTRIBUTING.md) |

本批包含记录编码器、固定载荷注入主机、Pico v2 本地源码适配器、AP-only 只读 RAM 程序构建适配器，以及身份／分区表查询客户端。没有功能刷写、固件、BootROM 镜像、个人备份、机身密钥或第三方预编译程序。

## 快速开始

只检查代码，不需要相机或第三方依赖：

```sh
python3 -m unittest discover -s tests -v
python3 -m a6700_boot.enter --help
```

要复现硬件流程，先完整阅读[接线](docs/WIRING.md)和[构建／注入步骤](docs/FASTBOOT.md)。准备好本地构建的、哈希匹配的只读 RAM 载荷后：

```sh
# 默认仅离线验证，不打开串口或 USB
python3 -m a6700_boot.enter --payload build/read/fastboot-read.bin

# 只检查 Pico 固件版本；端口须替换为自己设备的实际端口
python3 -m a6700_boot.enter --ping --port /dev/cu.usbmodemXXXX

# 冷启动注入：先阅读接线页，运行后按提示操作
python3 -m a6700_boot.enter --payload build/read/fastboot-read.bin \
  --port /dev/cu.usbmodemXXXX --arm

# 完成换线后，查询固定 RAM 程序身份；匹配后才初始化 eMMC 并查表
python3 -m a6700_boot.inspect --partitions
```

完整发送通常为 **45 条记录**。必须等程序提示换线；黑屏、闪灯或 Pico 的 ACK 都不能单独证明相机已运行 Fastboot。成功标准是后续 USB 身份匹配并查询到分区表。

## 许可与后续

本仓库自有代码采用 **GPL-3.0-only**，见 [LICENSE](LICENSE) 与 [NOTICE](NOTICE)。固定版本的上游工程没有附许可证；因此本仓库只提供引用和自有适配脚本，不转载其源码／UF2／RAM 二进制，也不宣称 GPL 覆盖上游内容。详见[来源说明](docs/PROVENANCE.md)。

后续会在同一项目逐步整理整套功能解锁／关闭、普通 USB 管理和桌面应用。当前尚未发布这些模块；完整备份／恢复继续留待后续。无需为使用本批代码购买逻辑分析仪，也无需全盘备份才能运行离线测试。
