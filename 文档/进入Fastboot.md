# 进入 Fastboot：从源码到注入

从仓库根运行。当前实机路线为 macOS、A6700 2.00、RP2040 Pico；Pico 2、其他机型／固件、Linux／Windows 实机连接未验收。这里是 RAM 临时引导，不要求先在相机菜单设置 MSC／FTP。实际接线先读[接线与操作](接线与操作.md)。

## 1. 准备 Python

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r 依赖列表.txt
```

查询／读取还需要系统 libusb。Apple Silicon Homebrew 常见库路径是 `/opt/homebrew/lib/libusb-1.0.dylib`；自动发现失败时，在查询或备份命令后加 `--USB库` 和自己的实际路径。主机代码不会携带维护者的私人运行环境。

## 2. 编译 Pico 固件

完整板端代码已在 `硬件/Pico注入/pico_boot/`，释义见[源码说明](../硬件/Pico注入/源码说明.md)。可直接用 Arduino IDE 打开 `pico_boot.ino`，也可先复制到构建区：

```sh
python 脚本/准备Pico源码.py
```

安装 Arduino CLI 和 Arduino-Pico 的 RP2040 core；历史使用 core 6.3.0。以普通 Raspberry Pi Pico 为例，命令如下；其他兼容板须按自己的板型替换 FQBN，不应把 Pico 2 当作 RP2040：

```sh
arduino-cli core update-index --additional-urls https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json
arduino-cli core install rp2040:rp2040@6.3.0 --additional-urls https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json
arduino-cli compile --fqbn rp2040:rp2040:rpipico \
  --build-property 'compiler.cpp.extra_flags=-DOPEN_DRAIN' \
  --build-path 构建产物/Pico编译输出 构建产物/pico_boot
```

必须启用 `-DOPEN_DRAIN`，不要启用 `UART_TX`。Pico 与相机分离时，按开发板 BOOTSEL／UF2 流程刷入编译得到的 UF2，再重新连接 Pico 数据线。仓库没有上传历史 UF2；完整源码已提供，不依赖下载该二进制。`pico_boot.ino` 与 sketch 目录同名，保留 ASCII 是为了 Arduino 工具兼容。

检查端口并核对版本：

```sh
python -m serial.tools.list_ports
python 脚本/进入Fastboot.py --检查Pico --串口 /dev/cu.usbmodemXXXX
```

预期版本 `a6700_pio_od 2`，且不会启动载波。端口必须换为本机实际值。

## 3. 构建相机 RAM 程序

Pico 程序只负责发送，尚需相机 AP 运行的 RAM 程序。固定上游仍由使用者单独取得：

```sh
git clone https://github.com/DavidBuchanan314/ILCE-7M4-RE.git 外部源码/ILCE-7M4-RE
git -C 外部源码/ILCE-7M4-RE checkout --detach 2328d18ce640e6c8cd9341efcf0043ce9042a135
```

准备 clang 和 AArch64 GNU binutils（ld、objcopy、nm），确保命令在 PATH；也可用 `--cc`、`--ld`、`--objcopy`、`--nm` 指定工具。构建不访问设备、不同名输出不覆盖：

```sh
# 默认只读模式；与历史实机程序保持一致
python 脚本/构建相机引导.py --上游目录 外部源码/ILCE-7M4-RE

# 仅有明确刷写需求时另构建原始读写实验版
python 脚本/构建相机引导.py --上游目录 外部源码/ILCE-7M4-RE --模式 原始读写
```

| 模式 | 本地产物 | 身份 | 记录数 |
|---|---|---|---:|
| 只读 | `构建产物/只读/相机只读引导.bin` | `A6700-AP-read-candidate` | 45 |
| 原始读写 | `构建产物/原始读写/相机原始读写引导.bin` | `A6700-AP-raw-maintenance` | 59 |

本轮RAM构建使用 Apple clang 21.0.0（clang-2100.1.1.101）和 GNU Binutils 2.47.20260726；其他工具链尚未核对逐字节复现。构建器核对固定提交和输入哈希；产物再匹配 `核心/载荷清单.json`。工具链差异导致哈希不同时停止，不能修改清单来强行发送。原始读写版用无密钥占位替换上游 SPACC；只接受原始别名，实际用途与限制见[备份与刷写](备份与刷写.md)。

## 4. 默认离线检查

```sh
python 脚本/进入Fastboot.py --载荷 构建产物/只读/相机只读引导.bin
```

应显示45条记录、没有访问串口／USB。检查原始读写载荷时必须加 `--模式 原始读写`；模式或哈希不符不会发送。

## 5. 冷启动注入

先核对[接线](接线与操作.md)：相机 OFF、普通 USB 已断开、取电池至少5秒、测试板与相机分离。Pico 数据线和 USB-A 供电接电脑，然后运行：

```sh
python 脚本/进入Fastboot.py --载荷 构建产物/只读/相机只读引导.bin \
  --串口 /dev/cu.usbmodemXXXX --开始注入 --等待秒数 900
```

按回车后主机核对版本、关闭内部上拉、启动载波并测低基线。**看到 ARMED 才插测试板、装电池、拨 ON**。检测相机释放高电平后等待0.5秒，发送一次有序记录，记录间隔0.0144秒。等待完整发送提示；不从半条流继续，不自动重发，不发送 reset。

Pico 的 ACK 仅确认发送过程，不证明相机接收或执行。失败／Ctrl-C 后主机尝试释放GP28，Pico还有1200ms饥饿保护；需重新操作时应完整冷启动。

## 6. 先拔板，再换线，再查身份

保持相机电池和 ON，先拔整个测试板，再把数据线从 Pico 端移到相机；USB-A供电可保持，测试板不再接相机。运行：

```sh
python 脚本/查询Fastboot.py --分区表
```

只有固定 product 匹配，才继续初始化 eMMC／读取表。若注入的是原始读写实验版，查询也要加 `--模式 原始读写`。黑屏、闪灯、USB VID/PID 或单纯 Pico ACK 不能代替身份／分区表核验。

当前原始读写入口的显式注入命令是：

```sh
python 脚本/进入Fastboot.py --模式 原始读写 \
  --载荷 构建产物/原始读写/相机原始读写引导.bin \
  --串口 /dev/cu.usbmodemXXXX --开始注入
```

它仍只把程序装入 RAM；只有后续另发 `flash` 才会改非易失存储。该新载荷没有完成本轮实机刷写验收，不能把“编译成功”写成“刷写／救砖已验证”。
