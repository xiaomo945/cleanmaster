# -*- coding: utf-8 -*-
"""生成「下载 → 解压 → 双击就能用」的绿色版分发 zip。

用法:
    py -3 _make_release.py

输出:
    release/CleanMaster_v<版本>_win64.zip

版本号自动从 clean_master.py 首行 docstring 读取，SHA256 自动从 dist 里的
EXE 计算，写进压缩包内的《使用说明.txt》，别人下载后可以直接核对完整性。
"""
import hashlib
import os
import re
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "clean_master.py")
EXE = os.path.join(ROOT, "dist", "电脑清理大师.exe")
OUT_DIR = os.path.join(ROOT, "release")


def read_version():
    with open(SRC, "r", encoding="utf-8") as f:
        m = re.search(r"PC Cleanup Master\)\s+v(\d+\.\d+\.\d+)", f.read())
    if not m:
        raise RuntimeError("没在 clean_master.py 里找到版本号")
    return m.group(1)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def usage_text(version, digest, exe_size):
    # UTF-8 BOM 由 writestr 时用 utf-8-sig 编码写入，Windows 记事本不会乱码。
    return r"""电脑清理大师 v{ver} · 绿色版（免安装）
作者：xiaomo945      https://github.com/xiaomo945/cleanmaster

==========================================================
一、怎么开始（30 秒）
==========================================================
1. 先把整个文件夹【解压出来】再用。不要直接在压缩包里双击 exe，
   Windows 自带解压：右键 zip → 全部提取 → 选个文件夹（桌面就行）。
2. 双击「电脑清理大师.exe」。
   不用装 Python，不用装运行库，不用安装，不会写注册表。
3. 第一次运行若弹出蓝色窗口「Windows 已保护你的电脑」：
   点「更多信息」→「仍要运行」。这是没有代码签名证书的程序都会有的提示，
   不是病毒。若杀毒软件拦截，请添加信任（PyInstaller 打包程序常被误报）。

==========================================================
二、怎么用
==========================================================
· 选盘符 → 点「扫描此盘」。一次只扫这一块盘，一般十几秒。
· 点「一键清理」：全程只弹一次「是否开始」确认，点「是」之后
  不再弹任何窗口，也不会闪黑色命令行窗口。
  清理结果直接显示在窗口顶部的绿色结果条上（实际释放了多少空间）。
· 想自己挑：点方框或点名称 = 勾选；点左边箭头 / 双击 = 展开下一层。
  大文件夹可以逐层展开，挑里面的子项单独删。
  「清理影响」那一列写明了删掉会影响什么功能，请看清再勾。
· 顶部「已勾选可释放」会随勾选实时变化。

==========================================================
三、安全须知（请务必看一眼）
==========================================================
· 默认一个项目都不勾。「一键清理」只处理系统临时文件、缓存、回收站
  这类删了会自动再生的东西，不碰文档、照片、聊天记录、游戏本体。
· 系统路径（C:\Windows、Program Files、AppData 整体、用户主目录等）
  已硬锁，界面显示 ×，点了也勾不上，防止手滑删掉整个用户目录。
· 手动勾选的删除是【永久删除，不进回收站，不可恢复】，
  确认窗口会逐条列出完整路径，请核对后再点「是」。
· 想清得更彻底，可以右键 exe →「以管理员身份运行」（不强制，
  普通权限也能用，只是个别系统项会跳过并写进日志）。
· 适用系统：Windows 10 / 11（64 位）。

==========================================================
四、文件校验
==========================================================
电脑清理大师.exe
  大小：{size} 字节
  SHA256：{digest}

在 exe 所在文件夹按住 Shift + 右键 →「在此处打开 PowerShell 窗口」，执行：
  Get-FileHash .\电脑清理大师.exe -Algorithm SHA256
比对上面的值，一致说明下载过程没有损坏或被篡改。

==========================================================
有问题 / 想看源码：https://github.com/xiaomo945/cleanmaster
""".format(ver=version, digest=digest, size=format(exe_size, ","))


def main():
    version = read_version()
    if not os.path.isfile(EXE):
        raise RuntimeError("找不到 EXE，请先打包：" + EXE)
    digest = sha256(EXE)
    size = os.path.getsize(EXE)
    os.makedirs(OUT_DIR, exist_ok=True)
    zip_path = os.path.join(OUT_DIR,
                            "CleanMaster_v%s_win64.zip" % version)
    folder = "电脑清理大师_v%s" % version
    text = usage_text(version, digest, size).encode("utf-8-sig")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED,
                         compresslevel=9) as z:
        z.write(EXE, arcname=folder + "/电脑清理大师.exe")
        info = zipfile.ZipInfo(folder + "/使用说明.txt")
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        z.writestr(info, text)

    # 自校验：读回压缩包，确认中文名、内容与 EXE 逐字节一致
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        assert len(names) == 2, names
        assert names[1].endswith("使用说明.txt"), names
        with open(EXE, "rb") as f:
            assert z.read(names[0]) == f.read(), "EXE 不一致"
        assert "绿色版" in z.read(names[1]).decode("utf-8-sig")
        bad = z.testzip()
        assert bad is None, "压缩包损坏: " + str(bad)

    print("版本: v%s" % version)
    print("输出: %s" % zip_path)
    print("压缩包大小: %.2f MB" % (os.path.getsize(zip_path) / 1024 ** 2))
    print("内文件:")
    for n in names:
        print("   ", n)
    print("EXE SHA256: %s" % digest)
    print("自校验: PASS（含中文文件名、说明编码、EXE 逐字节一致）")


if __name__ == "__main__":
    main()
