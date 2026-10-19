"""将本地 RAM 工程改为原始扇区读写实验版；不引入密钥或自动恢复。"""

PRODUCT = 'A6700-AP-raw-maintenance'

NO_CRYPTO = '''#include "spacc.h"
u32 spacc_last_status;
void spacc_init(void) {}
int spacc_xts_sector(void *dst, const void *src, u32 sector, int encrypt) {
    (void)dst; (void)src; (void)sector; (void)encrypt;
    return -1; /* 本版只处理原始密文；没有解密密钥。 */
}
'''


def adapt(text, replace_fn):
    text = text.replace('A6700-AP-read-candidate', PRODUCT)
    text = replace_fn(text, 'cmd_help', '''static void cmd_help(void)
{
    fb_result("A6700 raw-only maintenance: getvar, upload, download, flash");
    fb_result("targets: nflasha, nflashaB0, nflashaB1; no plaintext slots");
}''')
    text = replace_fn(text, 'cmd_oem', '''static void cmd_oem(const char *args)
{
    const char *rest;
    if (str_eq(args, "help")) { cmd_help(); return; }
    if (str_eq(args, "partition")) { cmd_partition(); return; }
    rest = str_after(args, "partition dump ");
    if (rest && (str_eq(rest,"nflasha") || str_after(rest,"nflasha ") ||
                 str_eq(rest,"nflashaB0") || str_after(rest,"nflashaB0 ") ||
                 str_eq(rest,"nflashaB1") || str_after(rest,"nflashaB1 "))) {
        cmd_partition_dump(rest); return;
    }
    fb_fail("raw maintenance: command unavailable");
}''')
    text = replace_fn(text, 'fastboot_command', '''static void fastboot_command(const char *cmd)
{
    const char *rest;
    if ((rest = str_after(cmd, "getvar:")) != 0) cmd_getvar(rest);
    else if ((rest = str_after(cmd, "oem ")) != 0) cmd_oem(rest);
    else if (str_eq(cmd, "upload")) cmd_upload();
    else if ((rest = str_after(cmd, "download:")) != 0) cmd_download(rest);
    else if ((rest = str_after(cmd, "flash:")) != 0) {
        if (str_eq(rest,"nflasha") || str_eq(rest,"nflashaB0") || str_eq(rest,"nflashaB1"))
            cmd_flash(rest);
        else fb_fail("raw targets only; plaintext slots are unavailable");
    }
    else fb_fail("raw maintenance: command unavailable");
}''')
    # 原始别名不会进入加解密路径。拒绝未对齐镜像，避免末扇区被补零。
    marker = '    if (!mmc_ready)\n        mmc_init();'
    start = text.index('static void cmd_flash(')
    before, flash = text[:start], text[start:]
    if marker not in flash:
        raise ValueError('上游 flash 初始化结构变化')
    flash = flash.replace(marker, '''    if ((download_len < 4 || le32(download_buf) != SPARSE_MAGIC) &&
        (download_len % SECTOR_SIZE)) {
        fb_fail("raw image length must be a multiple of 512"); return;
    }
''' + marker, 1)
    return before + flash
