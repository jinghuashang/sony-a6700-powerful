# 构建、注入与 Fastboot 查询

以下命令从仓库根目录运行。Python 3.10+；本轮仅核对 macOS 路线，Linux 主机尚未实机验收，Windows 不作为支持平台。**本批未分发可直接使用的 UF2 或 RAM 二进制**，需先完成本地构建。使用默认 Arduino 上游固件代替 v2、或者原版 A7 IV Fastboot 代替只读适配版，都不能通过本工具校验。

## 1. 安装主机依赖

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

USB 查询还需要系统 libusb；macOS 使用 Homebrew 时可安装 `libusb`，构建 RAM 程序需要 clang 和 AArch64 GNU binutils（`aarch64-elf-ld`、`aarch64-elf-objcopy`、`aarch64-elf-nm`）。工具路径可通过构建参数指定，不要求使用维护者的目录。

若 PyUSB 无法自动发现已安装的库，查询命令可加 `--libusb /opt/homebrew/lib/libusb-1.0.dylib`（Apple Silicon Homebrew）或自己的实际库路径；该参数不改变设备命令范围。

## 2. 单独取得固定上游

上游来源与许可状态见 [PROVENANCE.md](PROVENANCE.md)。仓库不包含该上游的副本，也不会自动下载代码：

```sh
git clone https://github.com/DavidBuchanan314/ILCE-7M4-RE.git vendor/ILCE-7M4-RE
git -C vendor/ILCE-7M4-RE checkout --detach 2328d18ce640e6c8cd9341efcf0043ce9042a135
```

两个适配器都会检查 HEAD 和 33 个输入文件的 SHA-256。版本不符、文件被修改或输出目录已存在时停止，不覆盖既有构建。

## 3. 准备 Pico v2

```sh
python scripts/prepare_pico.py --upstream vendor/ILCE-7M4-RE
```

生成 `build/uart_boot_upstream_pio/`。与历史实机源码核对的改动为：版本应答 `a6700_pio_od 2`、强制 `OPEN_DRAIN`、启动时关闭 GP28 内部上拉、增加仅空闲时设置上拉的命令 `0x07`、增加不改变方向的 2 ms 采样命令 `0x08`。PIO 源码／生成头不变；本仓库主机只用 `0x07` **关闭**上拉，不提供相机连接状态下的上拉测试。

使用 [Arduino-Pico](https://github.com/earlephilhower/arduino-pico) 的 RP2040 core 编译本地 sketch，**必须传 `-DOPEN_DRAIN`，不要启用 `UART_TX`**。依据实际 RP2040 板型选择 FQBN；维护者历史使用 core 6.3.0，但没有保留足以保证 UF2 逐字节复现的完整板型／工具链构建配置，因此不冒称这一步已经复现历史 UF2。

```sh
# 先安装 Arduino CLI 和对应 core；FQBN 按自己实际板型填写
arduino-cli compile --fqbn YOUR_BOARD_FQBN \
  --build-property 'compiler.cpp.extra_flags=-DOPEN_DRAIN' \
  --build-path build/pico-output build/uart_boot_upstream_pio
```

刷入 Pico 时先与相机完全断开，按板子的 BOOTSEL／UF2 流程操作。历史已验证 UF2 的 SHA-256 为 `8a8bb5c1c962b3a174c7f7715d24e0620b9c20367e75538bda27645c19115d3e`，这里只记录证据，不提供下载。本轮验证了生成的源码与历史源码逐字节一致，没有重刷 Pico。

连接 Pico 数据线后查看串口列表，再只做 PING：

```sh
python -m serial.tools.list_ports
python -m a6700_boot.enter --ping --port /dev/cu.usbmodemXXXX
```

预期 `PING a6700_pio_od 2; carrier not started.`；必须指定实际端口，不自动选择其他串口设备。

## 4. 构建固定只读 RAM 程序

```sh
python scripts/build_read_payload.py --upstream vendor/ILCE-7M4-RE
# clang/binutils 不在 PATH 时：使用 --cc、--ld、--objcopy、--nm 指定
```

输出 `build/read/fastboot-read.bin`，20,992 字节，预期 SHA-256：

```text
8d8b968940a868116bb3cd77c0f040795c1aae28d2a5d96d119d992498473fcb
```

构建适配器对本地上游生成 A6700 AP-only 源码和链接程序，包含 USB2 路由设置与只读命令限制。会检查禁止的存储写入／执行符号未链接。编译器版本可能改变二进制；如果哈希不同，构建与注入均保持拒绝，不提供强制发送开关。提交工具链信息供维护者复核，不自行修改允许哈希。

## 5. 离线校验，再冷启动注入

```sh
python -m a6700_boot.enter --payload build/read/fastboot-read.bin
```

应输出 45 条记录且没有串口／USB 访问。接下来严格按 [WIRING.md](WIRING.md) 布线，测试板先不插相机：

```sh
python -m a6700_boot.enter --payload build/read/fastboot-read.bin \
  --port /dev/cu.usbmodemXXXX --arm --activation-timeout 900
```

确认准备后按回车；程序先停止载波、关闭内部上拉，再启动载波并确认 GP28 低基线。看到 `ARMED` 后才插板、装电池、拨 ON。检测到 HIGH 后等待 0.5 秒，再顺序发送全部记录，记录间隔 0.0144 秒；发送一次，不自动重发，不发送 reset 命令。失败／Ctrl-C 时尝试停止载波并关闭上拉；Pico 另有 1200 ms 饥饿保护。ACK 仅表示 Pico 完成发送，不能证明相机接收成功。

完整发送后保留电池及 ON，**先拔整个测试板，再移动 Pico 数据线到相机**。

## 6. 身份与分区表

```sh
python -m a6700_boot.inspect
python -m a6700_boot.inspect --partitions
```

首次只查固定 product 与版本。加 `--partitions` 后仍先核对 `A6700-AP-read-candidate`，再发 `oem partition`，后者会初始化 eMMC 并读取分区表。命令白名单没有 `flash`、`erase`、`download`、`poke`、`exec`、dump 或备份入口；身份不符时不继续。

若自行使用兼容的 fastboot CLI，同等查询为：

```sh
fastboot devices
fastboot getvar product
fastboot getvar version
# 仅当上面的 product 明确匹配 A6700-AP-read-candidate 后：
fastboot oem partition
```

通用 fastboot CLI 的不同版本未在本轮逐一验证，本项目的 Python 查询实现有模拟测试。不要照搬手机解锁或通用刷机命令。表查询成功不代表已备份全部物理 eMMC，也不证明全盘恢复可用。
