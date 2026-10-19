# AI 与贡献者入口

先读 README、docs/PRINCIPLES.md、docs/VALIDATION.md 和 CONTRIBUTING.md。无需访问维护者的研究目录、记忆服务、私人备份或真实相机，即可分析与运行普通测试。

- `a6700_boot/records.py`：固定 RAM 窗口、记录编码／CRC／已验证载荷哈希，无 I/O。
- `a6700_boot/pico.py`：有限 Pico 命令和响应，不发送 reset、UART 或启用上拉。
- `a6700_boot/enter.py`：默认离线校验；显式 --arm 才启动载波；低基线失败不发记录，失败不自动重发。
- `a6700_boot/inspect.py`：只允许身份、版本、分区表；身份不符不继续，不读取设备序列号。
- `scripts/upstream.py`、`upstream.lock.json`：检查固定外部源码及输入哈希。
- `scripts/prepare_pico.py`、`build_read_payload.py`：只在本地生成／编译适配，不访问设备，产物不提交。

默认验证 `python3 -m unittest discover -s tests -v`。测试使用合成串口／USB，不因修复文档或主机代码而自行加载相机。需要硬件执行时，由维护者单独安排，不能把当前开源授权视为硬件写入授权。

不加入任意载荷／地址／命令执行接口、强制跳过哈希、自动重发、功能勾选或整盘备份模块。真实证据与模拟结果分别记录；Pico ACK 不证明相机执行成功，分区表下限不等于完整物理 eMMC。

自有代码 GPL-3.0-only 不覆盖上游。不要提交 vendor/build/、UF2、RAM 二进制、BootROM、密钥、相机固件、私人镜像或原始日志。未确认上游许可前，不把其代码复制进仓库。
