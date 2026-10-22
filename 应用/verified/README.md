# 历史代码与来源索引

本目录保留 USB 协议、macOS 接口接管和构造函数证明的历史归集原件，用于阅读原理和核对来源。**不作为当前设备操作入口**：旧脚本不具备当前应用完整的共享锁、设备约束及事务保护，不能与其他相机操作并行运行。

当前设备操作请用仓库根[USB root 教程](https://github.com/xyzhangxin/sony-a6700-powerful/blob/main/USB进入root教程.md)、[USB 功能刷写教程](https://github.com/xyzhangxin/sony-a6700-powerful/blob/main/USB功能刷写教程.md)及应用 `src/a6700_unlock/operations.py`。当前固定读写器在 `src/a6700_unlock/native/transaction.c`，历史载荷不能代替它。

| 历史内容 | 路径 |
|---|---|
| 认证、文件传输原实现 | `usb/usb_service_probe.py` |
| Jiritsu 报文 | `usb/packet_builder.py` |
| macOS 原接管实现 | `macos/mac_capture.m` |
| 自编写 root 构造函数证明 | `payloads/proof_ctor.c` |
| 上游 MIT 参考及许可 | `usb/reference/sony_pmca/` |

逐文件原始与归集哈希见 `SOURCES.json`，适配差异见[来源说明](../docs/PROVENANCE.md)。运行版本与历史原件分开维护，不改历史原件哈希来伪装与运行代码相同。

三份内嵌原厂扇区数组的历史 C 试验不公开分发，索引仅保留排除原因与原哈希，不含原厂数组。公开代码保留必要修改字段、校验元数据、自编原生代码与完整对应构建材料。完整固件／整机备份恢复尚未实现。
