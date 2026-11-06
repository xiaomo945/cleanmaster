#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电脑清理大师 (PC Cleanup Master)  v3.0.2
作者: xiaomo945  https://github.com/xiaomo945

纯 Python、零依赖（仅用标准库 + Tkinter）的 Windows 电脑清理工具。

v3.0 —— 修交互 + 大目录逐层浏览：
  【勾选框点不动】选择列的列号写死成 #2，实测 Tkinter 中它是 #1
    （#2 是「大小」列），于是点方框永远没反应。改成按列名动态算。
  【下一层的减号只能展开不能收回】_maybe_expand 在 ButtonRelease 时
    无条件把节点设回 open=True，把 Tk 刚做好的折叠又改回去了。
    现在只有点展开箭头 / 双击才管展开，且不再覆写折叠状态。
  【几万 MB 的大目录不能展开、不能挑着删】只读的「根目录用途说明」
    现在可以逐层展开（复用全盘扫描时算好的目录体积，零额外读盘），
    里面的子文件夹 / 文件可以手动勾选后删除：
      · 顶层目录本身永远不可整体删除（防手滑删掉 47.9GB 用户数据）
      · 系统路径（Windows / Program Files / 回收站 / 页面文件…）硬锁
      · 默认全不勾，一键清理绝不碰，删除前逐条列完整路径二次确认
  【描述写错盘】Users 在 C 盘就是系统自带的用户目录，
    不再写「从 C 盘迁移来的」；迁移说法只在非系统盘上出现。

v2.9 —— E/F 数据盘优化：软件缓存知识库、四级清理影响分级、只读保护
v2.8 —— 按商业清理软件（360 安全卫士 / 腾讯电脑管家）的思路重做，
        解决两个老毛病：「报了很大的数却没效果」+「几万个文件刷屏」：

  【根因】旧版把「最大的文件夹排行」里的 C:\\Users\\windos（46.8GB）
          这类【用户真实数据】也算进了「可释放空间」。
          用户勾上后这些文件大量被占用删不掉，
          结果就是「预计释放 89.8GB，实际只释放 600MB」—— 数字虚高 + 没效果。
  【现在】
  - 空间分析类目全部改为【只读】：只告诉你空间被谁占了，绝不计入可释放
  - 顶部三个数字分开摆：已勾选可释放 / 一键可清理 / 需你确认
  - 新增「⚡ 一键清理」：只清安全类垃圾，点一下就有确定效果
  - 新增「安装包 / 更新残留 / 未完成下载」扫描：
    认出 updater\\installer.exe、app_shell_cache、*.part 这类真垃圾
    （实测本机就找出 1.4GB，纯属白扔的空间）

  【不再显示几万个文件】
  - 逐文件清单改为【按目录聚合】：15828 个垃圾文件 → 800 个目录组
    （g_old 11610 → 800），每个目录组还能展开看具体是哪些文件
  - 每个类目默认只渲染 30 条，剩下的折成「还有 N 项」按需加载
  - 新增「应用维度归并」：不再列 C:\\Users 这种大而无当的路径，
    而是像商业软件那样列出「Chrome 5.6GB / 微信 1.7GB / Ollama 3.1GB」

  【清理更靠谱】
  - 缓存目录改成【清空内容但保留目录本身】（dirclean）：
    旧版整个删掉 C:\\Users\\xx\\AppData\\Local\\Temp，
    很多程序约定要往那儿写，目录没了会直接报错
  - 批量删除按【字符长度】分批（Windows 命令行上限 8191 字符），
    旧版按个数分批，路径一长整条命令静默失败 —— 一个都没删掉
  - 删除加超时保护 + rd /s /q 兜底，单个锁死的文件不再卡住整个清理
  - 清理后报【实际删掉了多少字节】，不再只看磁盘剩余空间差值
    （清理时后台还在写盘，差值经常是 0，看着像没干活）

v2.7.1 —— 修掉「双击没反应 / 闪退」+ 交互提速：
  - 去掉打包时的强制 UAC 提权（--uac-admin）。以前每次双击都弹提权窗，
    被安全软件拦掉或用户点「否」时就表现为「双击没反应」，
    其实程序本身完全正常。现在双击立刻出界面，零弹窗
  - 改成【按需提权】：顶部有「以管理员身份重启」按钮；
    清理时若勾到了注册表(HKLM)或系统目录里的项目，
    会提示「要不要以管理员身份重启后继续」，选「否」就跳过这些项，
    其余照常清理，不再是「删了没反应」
  - 未提权时顶部明确说明：用户目录能清，注册表与系统目录会被跳过
  - 结果区新增工具栏：全部展开 / 全部收起 / 只看已勾选 / 全选全不选
  - 扫描期间关闭 Python GC —— 一盘会造几十万个小对象，
    GC 的 full collection 会让界面卡顿

v2.7 —— 性能与体验大改（针对「太卡、显示太多、扫太久」）：
  - 结果区改为分层树（分组 → 类别 → 文件），点开一个类别不再卡：
    旧版每条文件要建 4 个 ttk 控件，展开就是几千个控件 → 直接卡死；
    新版用单个 Treeview，展开 2 万条也只要几毫秒
  - 扫描提速 4.4 倍（C 盘 78 秒 → 18 秒）：
    · 用途说明改为按需计算并缓存（原来每个文件跑 91 条规则，
      光这一项就吃掉 24.8 秒）
    · 重复文件的 md5 哈希移出主流程，改为展开该类目时才按需检测
    · 线程池 8 → 16，并消除队列锁空转
  - 默认只扫「当前选中的盘」，不再一上来就扫整个电脑；
    需要全扫可点「扫描全部盘」
  - 精简模式：默认只显示高价值类别，其余折进「⋯ 更多类别」
  - 每一类都支持展开后逐项勾选；清理只删用户勾选的那几项

特点:
  - 图形界面，全程点击操作，无需命令行知识
  - 一次扫描所有固定盘（C/D/E/F/G/H…），按盘分组，一个盘一个盘地清理
  - 除 Windows 系统核心文件（DLL/驱动/系统目录）外，能识别的文件都扫出来：
    缓存、临时文件、回收站、各类应用缓存、安装包残留、内存转储、注册表残留，
    以及「通用文件扫描」：垃圾扩展名文件 / 大文件 / 长期未使用文件 / 重复文件 /
    空文件夹 —— 并按目录聚合，不刷屏
  - 「磁盘空间分析」：按应用归并（Chrome / 微信 / Ollama 各占多少），
    并列出「最大的文件排行」，只读，不计入可释放
  - 安全项自动清理；不确定项默认不勾，用户可选；风险项清理前必须确认
  - 注册表同样清理（仅系统盘，无风险自动，有风险提示）
  - 实时进度条 + 日志框，清理前后显示已删除 / 已释放空间
"""

import os
import sys
import time
import gc
import heapq
import hashlib
import re
import shutil
import ctypes
import queue
import threading
import concurrent.futures as _futures
import collections as _collections
import subprocess
import winreg
import traceback
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox
    MISSING_TK = False
except Exception:  # 某些精简 Python 环境没有 tkinter
    MISSING_TK = True
    tk = ttk = scrolledtext = messagebox = None

# ----------------------------------------------------------------------------
# 工具函数
# ----------------------------------------------------------------------------

def _hidden_window_kwargs():
    """GUI 程序调用 cmd / powershell 时，绝不能弹出黑色控制台窗口。

    PyInstaller --windowed 打出来的程序没有控制台，但 subprocess.run
    默认会为子进程新建一个控制台 —— 清理时分批调用 del / rd / powershell
    就会「刷刷刷」闪出一串黑框，用户以为程序坏了。
    两个都加：CREATE_NO_WINDOW（不创建控制台）+ STARTUPINFO 的 SW_HIDE
    （某些调用链仍会显示窗口，双保险）。
    """
    if os.name != 'nt':
        return {}
    kw = {'creationflags': getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)}
    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0                  # SW_HIDE
        kw['startupinfo'] = si
    except Exception:
        pass
    return kw


_NO_WINDOW_KW = _hidden_window_kwargs()

def _dedup_size(pairs):
    """按路径去重后累加大小。

    同一份空间可能被多个类目同时命中（例如「最大的文件夹」和「大文件」
    都包含同一个文件），或父子目录同时被勾选。这里做两件事：
      1. 完全相同的路径只算一次；
      2. 若某路径位于另一个已计入的目录之下，则不再重复累加。

    性能：第 2 步原实现是「遍历全部已计入前缀做 startswith」= O(n²)。
    几万个条目时是十几亿次字符串比较 —— 点开一个类别就卡住的主因之一。
    改成沿路径向上逐级查集合 = O(路径深度)，快两个数量级。
    """
    items = [(p, s) for p, s in pairs if p and s > 0]
    if not items:
        return 0
    # 归一化分隔符（统一成 \），避免 \ 与 / 混用导致去重失效
    items = [(p.replace('/', '\\'), s) for p, s in items]
    # 同一路径可能被多个类目命中，取最大值即可
    best = {}
    for path, size in items:
        low = path.lower()
        cur = best.get(low)
        if cur is None or size > cur:
            best[low] = size
    # 短路径优先（父目录先于子项进入），这样父子同时被勾选时只算父目录一次
    ordered = sorted(best.items(), key=lambda kv: (len(kv[0]), kv[0]))
    total = 0
    covered = set()   # 已计入的目录（小写）
    for low, size in ordered:
        # 若某个祖先目录已计入，则跳过（父目录已包含它）
        idx = low.rfind('\\')
        skip = False
        while idx > 0:
            anc = low[:idx]
            if anc in covered:
                skip = True
                break
            idx = anc.rfind('\\')
        if skip:
            continue
        total += size
        covered.add(low)
    return total
# ----------------------------------------------------------------------------
# 聚合层：把「几十万个文件」压成「几十个能执行的动作」
#
# 商业清理软件（360 安全卫士 / 腾讯电脑管家 / CCleaner）都不逐文件列清单：
#   · 垃圾    → 按「所在目录」聚合成一条（临时文件 47MB / 33 个）
#   · 占用    → 按「应用」归并成一条（Chrome 5.6GB、微信 4.3GB）
#   · 大文件  → 只列 Top N
# 好处有两个：
#   1) 界面永远只有几十行，不是几万个文件名；
#   2) 一次操作删一整个目录里的那批垃圾，比逐文件删快几十倍，
#      也更容易「清理前就说清楚要删什么」。
# ----------------------------------------------------------------------------

DISPLAY_PAGE = 30          # 展开类目时默认显示多少条子项
DISPLAY_PAGE_MAX = 300     # 单个类目最多加载多少条（防止误点撑爆界面）
AGG_DIR_CAP = 800          # 单个类目最多聚合出多少个目录组

# 这些是「厂商目录」，下面往往还套着具体应用名，
# 统计占用时要往下一层取（Google\Chrome 而不是笼统的 Google）。
_VENDOR_DEEP = {
    "google", "microsoft", "tencent", "programs", "baidu", "bytedance",
    "adobe", "kingsoft", "jetbrains", "netease", "alibaba", "aliyun",
    "quark", "sogou", "deepin", "xiaomi", "huawei", "douyin", "tiktok",
    "kuaishou", "bilibili", "jd", "meituan", "weibo", "xiaohongshu",
}


def _app_root(path):
    """把一个路径归到「应用根目录」。

    返回 (应用名, 应用根目录全路径, 类别)，无法归类返回 (None, None, None)。
    规则模仿商业清理软件的「按程序统计占用」：
        AppData\\Local\\Google\\Chrome  → Google\\Chrome
        AppData\\Local\\Programs\\Ollama → Programs\\Ollama
        C:\\Program Files\\Adobe         → Adobe
        C:\\Users\\xx\\.workbuddy        → .workbuddy
    """
    p = (path or "").replace("/", "\\")
    drive = ""
    if len(p) > 1 and p[1] == ":":
        drive, p = p[:2], p[2:]
    segs = [s for s in p.split("\\") if s]
    if not segs:
        return None, None, None
    sl = [s.lower() for s in segs]
    for i, s in enumerate(sl):
        if s == "appdata" and i + 2 < len(segs):
            vendor = segs[i + 2]
            if sl[i + 2] in _VENDOR_DEEP and i + 3 < len(segs):
                name = segs[i + 3]
                root = segs[:i + 4]
            else:
                name = vendor
                root = segs[:i + 3]
            return name, (drive + "\\" + "\\".join(root)).rstrip("\\"), "app"
        if s in ("program files", "program files (x86)") and i + 1 < len(segs):
            return segs[i + 1], drive + "\\" + "\\".join(segs[:i + 2]), "app"
        if s == "programdata" and i + 1 < len(segs):
            return segs[i + 1], drive + "\\" + "\\".join(segs[:i + 2]), "app"
        if s == "windows" and i == 0:
            return "Windows 系统", drive + "\\Windows", "system"
        if s == "users" and i + 1 < len(segs):
            if i + 2 < len(segs):
                if sl[i + 2] == "appdata":
                    continue        # 交给上面的 appdata 分支
                tool = segs[i + 2]
                return tool, drive + "\\" + "\\".join(segs[:i + 3]), "user"
            return segs[i + 1], drive + "\\" + "\\".join(segs[:i + 2]), "user"
    return segs[0], drive + "\\" + segs[0], "other"


def app_groups_from_dir_own(dir_own):
    """把每个目录的体积按「应用根」归并，得到「谁占了多少空间」。

    输入是 {目录: 子树体积}，输出按体积降序的应用列表。
    父子重复会在这里消掉：C:\\Users 与 C:\\Users\\windos 只留后者。
    """
    if not dir_own:
        return []
    lower = {d.lower(): d for d in dir_own}
    cands = {}
    for d in dir_own:
        name, root, kind = _app_root(d)
        if not root:
            continue
        cands.setdefault(root.lower(), (name, root, kind))

    # 最深的优先；某个根下面还有更深的根时，浅的那个整体丢掉（否则重复统计）
    roots = sorted(cands.keys(), key=lambda r: (-len(r), r))
    keep = []
    for r in roots:
        if any(k.startswith(r + "\\") for k in keep):
            continue
        keep.append(r)

    out = []
    for r in keep:
        name, root, kind = cands[r]
        size = dir_own.get(lower.get(r, ""), 0)
        if not size:
            # 根目录本身没被扫描到（少见）→ 直接子目录的体积之和
            pref = r + "\\"
            for dk, dv in dir_own.items():
                if dk.lower().startswith(pref) and "\\" not in dk[len(r) + 1:]:
                    size += dv
        if size <= 0:
            continue
        out.append({"path": root, "size": size, "kind": "appgroup",
                    "label": name + "（" + root + "）",
                    "desc": describe_path(root, True) +
                            f" · 该程序在本盘占用 {human_size(size)}",
                    "level": kind})
    out.sort(key=lambda x: -x["size"])
    return out


def group_items_by_dir(items, cap=AGG_DIR_CAP, noun="个文件"):
    """把逐文件条目按「所在目录」聚合成「目录组」条目。

    聚合后每个条目代表「这个目录里那 N 个符合条件的文件」，
    删除时精确到组内那几个文件 —— 同目录里的其它内容不会被动。
    """
    groups = {}
    for it in items:
        path = it.get("path", "")
        if not path:
            continue
        parent = os.path.dirname(path)
        g = groups.get(parent)
        if g is None:
            g = groups[parent] = {"paths": [], "size": 0, "is_dir":
                                  it.get("kind") == "edir"}
        g["paths"].append(path)
        g["size"] += it.get("size", 0)
    out = []
    for parent, g in groups.items():
        n = len(g["paths"])
        if not n:
            continue
        out.append({
            "path": parent,
            "size": g["size"],
            "kind": "files",
            "paths": g["paths"],
            "count": n,
            "label": f"{parent}（{n} {noun}）",
            "desc": (describe_path(parent, True) +
                     f" · 目录内 {n} {noun}，共 {human_size(g['size'])}"),
        })
    out.sort(key=lambda x: -x["size"])
    return out[:cap]


def human_size(n):
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "0 B"
    if n < 0:
        n = 0
    units = ["B", "KB", "MB", "GB", "TB"]
    for u in units:
        if n < 1024 or u == "TB":
            if u == "B":
                return f"{int(n)} {u}"
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} PB"


def get_drive_space(letter):
    try:
        free = ctypes.c_ulonglong(0)
        total = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            f"{letter}:\\", ctypes.byref(free), ctypes.byref(total), None)
        return free.value, total.value
    except Exception:
        return 0, 0


def get_fixed_drives():
    out = []
    for d in "CDEFGHIJKLMNOPQRSTUVWXYZ":
        try:
            if os.path.isdir(f"{d}:\\"):
                out.append(d)
        except Exception:
            pass
    return out


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def relaunch_as_admin():
    """以管理员身份重新启动本程序，返回 True 表示新实例已拉起。

    之所以不用 PyInstaller 的 --uac-admin：那样每次双击都强制弹 UAC，
    在被安全软件拦截、或用户直接点「否」的环境里，
    表现就是「双击没反应 / 闪退」—— 其实程序本身完全正常。
    改成按需提权：界面立刻出来，只有真要动系统项时才弹一次 UAC。
    """
    try:
        if is_admin():
            return False
        if getattr(sys, "frozen", False):
            exe = sys.executable
            args = list(sys.argv[1:])
        else:
            exe = sys.executable
            args = [os.path.abspath(sys.argv[0])] + list(sys.argv[1:])
        # ShellExecuteW(..., "runas", ...) → 触发 UAC 提权
        rc = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", exe, subprocess.list2cmdline(args), None, 1)
        return int(rc) > 32
    except Exception:
        return False


def safe_size(p):
    try:
        return os.path.getsize(p)
    except OSError:
        return 0


def dir_size(path, cap=50 * 1024 ** 3):
    total = 0
    try:
        for root, dirs, files in os.walk(path):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
                if total > cap:
                    return total
    except OSError:
        pass
    return total


def force_rmtree(path, timeout=60):
    """返回 True 表示目录确实已被删除；False 表示删除失败/部分失败。

    带超时保护：Windows 上遇到被系统占用的文件时，rmtree 可能反复重试
    卡住整个清理流程。所以超时后改用系统的 rd /s /q 强制删除，
    还是不行就如实返回 False（这一项没清掉，UI 上会显示为失败）。
    """
    if not (os.path.exists(path) or os.path.islink(path)):
        return False

    def _onerror(func, p, exc):
        try:
            os.chmod(p, 0o777)
            func(p)
        except Exception:
            pass

    result = {}

    def _worker():
        try:
            shutil.rmtree(path, onerror=_onerror)
        except Exception:
            pass
        result['done'] = True

    th = threading.Thread(target=_worker, daemon=True)
    th.start()
    th.join(timeout)
    if th.is_alive():
        # rmtree 卡住了（多半是文件被占用）→ 用系统命令强删
        try:
            subprocess.run(['cmd', '/c', 'rd', '/s', '/q', os.path.abspath(path)],
                           capture_output=True, timeout=timeout,
                           **_NO_WINDOW_KW)
        except Exception:
            pass
        th.join(5)
    return not (os.path.exists(path) or os.path.islink(path))


def force_remove_file(path):
    """返回 True 表示文件确实已被删除；False 表示被占用/无权限等删除失败。"""
    if not (os.path.exists(path) or os.path.islink(path)):
        return False
    try:
        try:
            os.chmod(path, 0o777)
        except Exception:
            pass
        os.remove(path)
        return not (os.path.exists(path) or os.path.islink(path))
    except Exception:
        pass
    # 回退：用系统命令强制删除（仍可能被系统锁定而失败，会如实返回 False）
    try:
        r = subprocess.run(
            ['cmd', '/c', 'del', '/f', '/q', os.path.abspath(path)],
            capture_output=True, timeout=60, **_NO_WINDOW_KW)
        if r.returncode == 0:
            return not (os.path.exists(path) or os.path.islink(path))
    except Exception:
        pass
    return False


def clear_dir_contents(path, timeout=180):
    """清空目录里的内容，但【保留目录本身】。

    为什么不能直接 rmtree 整个目录：
      · C:\\Users\\xx\\AppData\\Local\\Temp 是很多程序约定的位置，
        把目录本身删了会导致后续程序写不进去（报错、行为异常）
      · 目录里可能有几万个子项，一次性 rmtree 又慢又容易卡住

    所以改成：分批删文件 → 逐个删子目录 → 目录本身留着。
    返回 True 表示内容基本清空。
    """
    if not os.path.isdir(path):
        return False
    try:
        entries = list(os.scandir(path))
    except OSError:
        return False

    files, dirs = [], []
    for e in entries:
        try:
            if e.is_dir(follow_symlinks=False):
                dirs.append(e.path)
            else:
                files.append(e.path)
        except OSError:
            pass

    ok = True
    if files:
        ok = _delete_files_batch(files, timeout=timeout) and ok
    for d in dirs:
        ok = force_rmtree(d) and ok
    return ok


def _delete_files_batch(paths, timeout=120):
    """用系统命令批量删除同目录下的多个文件。

    逐个 os.remove 删 1 万个小文件要几十秒；
    cmd 的 del /f /q 一次能删几百个，快一个数量级。

    注意：Windows 命令行总长上限 8191 字符，
    路径一长就会超限导致整条命令失败（而且不报错，只是啥也没删）。
    所以这里按【字符长度】分批，而不是按个数。
    """
    if not paths:
        return True
    ok = True
    LIMIT = 7000          # 留出 cmd /c del /f /q 的开销余量
    batch = []
    batch_len = 0
    batches = []
    for p in paths:
        add = len(p) + 3      # 加上引号和分隔
        if batch and batch_len + add > LIMIT:
            batches.append(batch)
            batch, batch_len = [], 0
        batch.append(p)
        batch_len += add
    if batch:
        batches.append(batch)

    for group in batches:
        if len(group) == 1:
            ok = force_remove_file(group[0]) and ok
            continue
        try:
            subprocess.run(
                ["cmd", "/c", "del", "/f", "/q"] + group,
                capture_output=True, timeout=timeout, **_NO_WINDOW_KW)
        except Exception:
            ok = False
        # 逐个核对是否真删掉了 —— cmd 对被占用的文件会静默跳过
        for p in group:
            if os.path.exists(p):
                ok = False
    return ok


def run_powershell(script, timeout=180):
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True, text=True, timeout=timeout,
            **_NO_WINDOW_KW,
        )
        return r.stdout.strip()
    except Exception:
        return ""


def expand_env(s):
    if not s:
        return s
    try:
        return os.path.expandvars(s)
    except Exception:
        return s


def extract_exe_path(s):
    if not s:
        return None
    s = s.strip()
    if s.startswith('"'):
        end = s.find('"', 1)
        if end != -1:
            return s[1:end]
    if s.lower().startswith("msiexec"):
        return None
    parts = s.split()
    return parts[0] if parts else None


# ----------------------------------------------------------------------------
# 注册表辅助
# ----------------------------------------------------------------------------

HIVES = {
    "HKLM": winreg.HKEY_LOCAL_MACHINE,
    "HKCU": winreg.HKEY_CURRENT_USER,
}
READ = winreg.KEY_READ | winreg.KEY_WOW64_64KEY
WRITE = winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY
ALL = winreg.KEY_ALL_ACCESS | winreg.KEY_WOW64_64KEY


def reg_open(hive, subkey, access):
    try:
        return winreg.OpenKey(HIVES[hive], subkey, 0, access)
    except OSError:
        return None


def reg_subkeys(key):
    out = []
    i = 0
    while True:
        try:
            out.append(winreg.EnumKey(key, i))
        except OSError:
            break
        i += 1
    return out


def reg_values(key):
    out = []
    i = 0
    while True:
        try:
            out.append(winreg.EnumValue(key, i))
        except OSError:
            break
        i += 1
    return out


def reg_item(hive, subkey, valuename, risk, label):
    return {
        "path": f"{hive}\\{subkey}" + (f"\\{valuename}" if valuename else ""),
        "size": 0,
        "kind": "reg",
        "risk": risk,
        "label": label,
        "reg": {"hive": hive, "subkey": subkey, "valuename": valuename},
    }


def delete_subkey_tree(hive, key_path):
    key = reg_open(hive, key_path, ALL)
    if key is None:
        return
    for sk in reg_subkeys(key):
        delete_subkey_tree(hive, key_path + "\\" + sk)
    try:
        winreg.CloseKey(key)
    except Exception:
        pass
    try:
        winreg.DeleteKey(HIVES[hive], key_path)
    except OSError:
        pass


def clean_reg(item):
    r = item.get("reg")
    if not r:
        return
    hive, subkey, valuename = r["hive"], r["subkey"], r["valuename"]
    if valuename:
        key = reg_open(hive, subkey, WRITE)
        if key is None:
            return
        try:
            winreg.DeleteValue(key, valuename)
        except OSError:
            pass
        try:
            winreg.CloseKey(key)
        except Exception:
            pass
    else:
        delete_subkey_tree(hive, subkey)


# ----------------------------------------------------------------------------
# 扫描函数
# ----------------------------------------------------------------------------

def scan_temp(drive='C'):
    items = []
    for base in [os.environ.get("TEMP"), r"C:\Windows\Temp"]:
        if base and os.path.isdir(base):
            # 用 dirclean：只清空里面的内容，保留 Temp 目录本身
            # （很多程序约定要往这里写，目录没了会导致程序报错）
            items.append({
                "path": base, "size": dir_size(base), "kind": "dirclean",
                "label": "临时文件夹 " + base,
                "desc": "清空里面的临时文件，保留 Temp 目录本身",
            })
    return items


def scan_windows_update(drive='C'):
    p = r"C:\Windows\SoftwareDistribution\Download"
    if os.path.isdir(p):
        return [{"path": p, "size": dir_size(p), "kind": "dirclean",
                 "label": "Windows 更新下载缓存"}]
    return []


def scan_delivery_opt(drive='C'):
    p = r"C:\Windows\SoftwareDistribution\DeliveryOptimization"
    if os.path.isdir(p):
        return [{"path": p, "size": dir_size(p), "kind": "dirclean",
                 "label": "传递优化缓存（系统更新分发残留）"}]
    return []


def scan_wer(drive='C'):
    items = []
    for p in [r"C:\ProgramData\Microsoft\Windows\WER",
              r"C:\ProgramData\Microsoft\Windows\WER\ReportQueue",
              r"C:\ProgramData\Microsoft\Windows\WER\ReportArchive"]:
        if os.path.isdir(p):
            items.append({"path": p, "size": dir_size(p), "kind": "dirclean",
                          "label": "Windows 错误报告 " + p})
    return items


def scan_windows_old(drive='C'):
    p = r"C:\Windows.old"
    if os.path.isdir(p):
        return [{"path": p, "size": dir_size(p), "kind": "dir",
                 "label": "Windows.old 旧系统备份（升级残留，删除后无法回退系统）"}]
    return []


def scan_mem_dumps(drive='C'):
    items = []
    mini = r"C:\Windows\Minidump"
    if os.path.isdir(mini):
        items.append({"path": mini, "size": dir_size(mini), "kind": "dirclean",
                      "label": "内存转储 Minidump"})
    mem = r"C:\Windows\MEMORY.DMP"
    if os.path.isfile(mem):
        items.append({"path": mem, "size": safe_size(mem), "kind": "file",
                      "label": "系统内存转储 MEMORY.DMP（通常很大）"})
    return items


def scan_font_cache(drive='C'):
    p = r"C:\Windows\ServiceProfiles\LocalService\AppData\Local\FontCache"
    if os.path.isdir(p):
        return [{"path": p, "size": dir_size(p), "kind": "dirclean",
                 "label": "字体缓存 FontCache"}]
    return []


def scan_icon_cache(drive='C'):
    items = []
    local = os.environ.get("LOCALAPPDATA", "")
    for f in ["IconCache.db", "ImageCache.db"]:
        fp = os.path.join(local, f)
        if os.path.isfile(fp):
            items.append({"path": fp, "size": safe_size(fp), "kind": "file",
                          "label": "图标缓存 " + f})
    return items


def scan_inet_cache(drive='C'):
    items = []
    local = os.environ.get("LOCALAPPDATA", "")
    for name, p in [
        ("IE/Edge 临时文件", os.path.join(local, "Microsoft", "Windows", "INetCache")),
        ("WebCache", os.path.join(local, "Microsoft", "Windows", "WebCache")),
        ("Edge 临时文件", os.path.join(local, "Microsoft", "Edge", "User Data",
                                      "Default", "Cache")),
    ]:
        if os.path.isdir(p):
            items.append({"path": p, "size": dir_size(p), "kind": "dirclean",
                          "label": name})
    return items


def scan_thumbnails(drive='C'):
    items = []
    exp = os.path.join(os.environ.get("LOCALAPPDATA", ""),
                       "Microsoft", "Windows", "Explorer")
    if os.path.isdir(exp):
        for f in os.listdir(exp):
            if f.lower().startswith("thumbcache") and f.lower().endswith(".db"):
                fp = os.path.join(exp, f)
                items.append({"path": fp, "size": safe_size(fp), "kind": "file",
                              "label": "缩略图缓存 " + f})
    return items


def scan_browser_cache(drive='C'):
    items = []
    local = os.environ.get("LOCALAPPDATA", "")
    appdata = os.environ.get("APPDATA", "")
    targets = {
        "Chrome 缓存": os.path.join(local, "Google", "Chrome", "User Data",
                                    "Default", "Cache"),
        "Chrome 媒体缓存": os.path.join(local, "Google", "Chrome", "User Data",
                                        "Default", "Media Cache"),
        "Chrome 代码缓存": os.path.join(local, "Google", "Chrome", "User Data",
                                        "Default", "Code Cache"),
        "Chrome ServiceWorker": os.path.join(local, "Google", "Chrome",
                                             "User Data", "Default",
                                             "Service Worker", "CacheStorage"),
        "Chrome GPU缓存": os.path.join(local, "Google", "Chrome", "User Data",
                                       "Default", "GPUCache"),
        "Edge 缓存": os.path.join(local, "Microsoft", "Edge", "User Data",
                                  "Default", "Cache"),
        "Edge 媒体缓存": os.path.join(local, "Microsoft", "Edge", "User Data",
                                      "Default", "Media Cache"),
        "Edge 代码缓存": os.path.join(local, "Microsoft", "Edge", "User Data",
                                      "Default", "Code Cache"),
        "Edge ServiceWorker": os.path.join(local, "Microsoft", "Edge",
                                           "User Data", "Default",
                                           "Service Worker", "CacheStorage"),
        "Edge GPU缓存": os.path.join(local, "Microsoft", "Edge", "User Data",
                                     "Default", "GPUCache"),
    }
    for name, p in targets.items():
        if os.path.isdir(p):
            items.append({"path": p, "size": dir_size(p), "kind": "dirclean",
                          "label": name})
    ff = os.path.join(appdata, "Mozilla", "Firefox", "Profiles")
    if os.path.isdir(ff):
        for prof in os.listdir(ff):
            cp = os.path.join(ff, prof, "cache2")
            if os.path.isdir(cp):
                items.append({"path": cp, "size": dir_size(cp), "kind": "dirclean",
                              "label": "Firefox 缓存 (" + prof + ")"})
    return items


def scan_gpu_shader_cache(drive='C'):
    items = []
    local = os.environ.get("LOCALAPPDATA", "")
    for name, base in [
        ("NVIDIA 着色器缓存", os.path.join(local, "NVIDIA", "DXCache")),
        ("NVIDIA OpenGL缓存", os.path.join(local, "NVIDIA", "GLCache")),
        ("AMD 着色器缓存", os.path.join(local, "AMD", "DxcCache")),
        ("AMD 链接缓存", os.path.join(local, "AMD", "GLCache")),
    ]:
        if os.path.isdir(base):
            items.append({"path": base, "size": dir_size(base), "kind": "dirclean",
                          "label": name})
    return items


def scan_app_caches(drive='C'):
    items = []
    local = os.environ.get("LOCALAPPDATA", "")
    appdata = os.environ.get("APPDATA", "")
    cands = {
        "OneDrive 缓存": os.path.join(local, "Microsoft", "OneDrive", "cache"),
        "Teams 缓存": os.path.join(local, "Microsoft", "Teams", "Cache"),
        "Teams 媒体缓存": os.path.join(local, "Microsoft", "Teams",
                                       "media-stack", "Cache"),
        "微信缓存": os.path.join(local, "Tencent", "WeChat"),
        "QQ 缓存": os.path.join(local, "Tencent", "QQ", "Temp"),
        "Spotify 缓存": os.path.join(local, "Spotify", "Data"),
        "Discord 缓存": os.path.join(local, "Discord", "Cache"),
        "pip 缓存": os.path.join(local, "pip", "Cache"),
        "npm 缓存": os.path.join(appdata, "npm-cache"),
        "Adobe 缓存": os.path.join(local, "Adobe", "Common", "Media Cache Files"),
    }
    for name, p in cands.items():
        if os.path.isdir(p):
            items.append({"path": p, "size": dir_size(p), "kind": "dirclean",
                          "label": name})
    return items


def scan_store_cache(drive='C'):
    items = []
    local = os.environ.get("LOCALAPPDATA", "")
    pkgs = os.path.join(local, "Packages")
    if os.path.isdir(pkgs):
        for sub in os.listdir(pkgs):
            base = os.path.join(pkgs, sub)
            for cand in ["AC\\Temp", "TempState", "Cache", "LocalCache"]:
                p = os.path.join(base, cand)
                if os.path.isdir(p):
                    items.append({"path": p, "size": dir_size(p), "kind": "dirclean",
                                  "label": "应用商店缓存 " + sub})
    return items


def scan_workbuddy_logs(drive='C'):
    p = os.path.join(os.environ.get("USERPROFILE", ""), ".workbuddy", "logs")
    if os.path.isdir(p):
        return [{"path": p, "size": dir_size(p), "kind": "dirclean",
                 "label": "WorkBuddy 运行日志"}]
    return []


def scan_windows_logs(drive='C'):
    items = []
    for p in [r"C:\Windows\Logs\CBS", r"C:\Windows\Logs\DISM",
              r"C:\Windows\Logs\WindowsUpdate"]:
        if os.path.isdir(p):
            items.append({"path": p, "size": dir_size(p), "kind": "dirclean",
                          "label": "系统日志 " + p})
    return items


def scan_prefetch(drive='C'):
    p = r"C:\Windows\Prefetch"
    if os.path.isdir(p):
        return [{"path": p, "size": dir_size(p), "kind": "dirclean",
                 "label": "预读取文件（可加快启动，清理后首次启动略慢）"}]
    return []


def scan_downloads_old(drive='C', days=60):
    if drive.upper() == 'C':
        dlf = os.path.join(os.environ.get("USERPROFILE", ""), "Downloads")
    else:
        dlf = f"{drive}:\\Downloads"
    if not os.path.isdir(dlf):
        return []
    exts = ('.exe', '.msi', '.tmp', '.log', '.old', '.bak', '.zip',
            '.rar', '.7z', '.iso', '.dmg', '.tar', '.gz')
    cutoff = time.time() - days * 86400
    paths = []
    try:
        for f in os.listdir(dlf):
            fp = os.path.join(dlf, f)
            if os.path.isfile(fp) and f.lower().endswith(exts):
                try:
                    if os.path.getmtime(fp) < cutoff:
                        paths.append(fp)
                except OSError:
                    pass
    except OSError:
        pass
    if paths:
        sz = sum(safe_size(p) for p in paths)
        return [{"path": dlf, "size": sz, "kind": "files", "paths": paths,
                 "label": f"下载文件夹旧文件/安装包（{len(paths)} 个，>{days}天）"}]
    return []


# ------------------------- 回收站（按盘） -------------------------
def scan_recycle(drive='C'):
    drives = [drive] if drive else get_fixed_drives()
    out = []
    for d in drives:
        s = run_powershell(
            f"(Get-ChildItem '{d}:\\$Recycle.Bin' -Recurse -Force "
            f"-ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum"
        )
        try:
            sz = float(s) if s else 0.0
        except ValueError:
            sz = 0.0
        if sz > 0:
            out.append({"path": f"{d}:\\$Recycle.Bin", "size": sz,
                        "kind": "recycle", "drive": d,
                        "label": f"回收站（{d}: 盘）"})
    return out


# ------------------------- 其他盘的扫描 -------------------------
def scan_drive_temp(drive):
    items = []
    for base in [f"{drive}:\\Temp", f"{drive}:\\tmp", f"{drive}:\\Windows\\Temp"]:
        if os.path.isdir(base):
            items.append({"path": base, "size": dir_size(base), "kind": "dirclean",
                          "label": f"临时文件夹 {base}"})
    return items


def scan_drive_tmp_files(drive):
    roots = [f"{drive}:\\Temp", f"{drive}:\\tmp"]
    paths = []
    for r in roots:
        if not os.path.isdir(r):
            continue
        for root, dirs, files in os.walk(r):
            for f in files:
                if f.lower().endswith(".tmp"):
                    paths.append(os.path.join(root, f))
    if paths:
        sz = sum(safe_size(p) for p in paths)
        return [{"path": f"{drive}:\\", "size": sz, "kind": "files",
                 "paths": paths, "label": f"{drive}: 盘 .tmp 临时文件（{len(paths)} 个）"}]
    return []


def scan_drive_app_caches(drive):
    items = []
    cands = {
        f"Steam 下载缓存": os.path.join(f"{drive}:\\Steam", "steamapps", "downloading"),
        f"Steam  depotcache": os.path.join(f"{drive}:\\Steam", "depotcache"),
        f"Steam 日志": os.path.join(f"{drive}:\\Steam", "logs"),
        f"NVIDIA 缓存": os.path.join(f"{drive}:\\NVIDIA"),
        f"Unity 缓存": os.path.join(f"{drive}:\\Unity", "cache"),
        f"Epic 缓存": os.path.join(f"{drive}:\\EpicGames"),
    }
    for name, p in cands.items():
        if os.path.isdir(p):
            items.append({"path": p, "size": dir_size(p), "kind": "dir",
                          "label": name + "（" + p + "）"})
    return items


# ----------------------------------------------------------------------------
# 通用「全盘文件」扫描：识别可删除文件，逐文件交给用户决定
# ----------------------------------------------------------------------------

# 跳过系统核心目录，避免列出无数系统 DLL / 驱动（这些不是垃圾，也不该动）
EXCLUDE_DIRS = {
    '$recycle.bin', 'system volume information', 'windows',
    'program files', 'program files (x86)', 'programdata', 'recovery',
    'perflogs', '$windows.~bt', '$sysreset', '$getcurrent', '$winreagent',
    'documents and settings',
}

# 典型「垃圾扩展名」——这些通常是临时/残留文件，删除一般安全，但仍交用户决定
JUNK_EXTS = (
    '.tmp', '.temp', '.log', '.bak', '.old', '.dmp', '.cache', '.part',
    '.download', '.gid', '.chk', '.wbk', '.fts', '.ftg', '.$$$', '.prv',
    '.sav', '.~mp', '.err', '.swap',
)
JUNK_NAME_EXACT = ('thumbs.db', 'ehthumbs.db', 'picasa.ini')
JUNK_NAME_PREFIX = ('~$',)

# 系统自管理的关键文件：虚拟内存/休眠/启动引导文件——既不该删、也删不掉
# （普通删除会被系统锁定而失败，或删后立刻重建，列出来只会虚报可释放空间）
SYSTEM_FILES = {
    'pagefile.sys', 'hiberfil.sys', 'swapfile.sys', 'dumpfile.sys',
    'bootmgr', 'bootnxt', 'bootsect.bak', 'bootstat.dat',
}


def _is_system_file(name):
    return name.lower() in SYSTEM_FILES


def _is_junk_name(name):
    low = name.lower()
    if low in JUNK_NAME_EXACT:
        return True
    for pre in JUNK_NAME_PREFIX:
        if low.startswith(pre):
            return True
    if low.endswith(JUNK_EXTS):
        return True
    return False


def _hash_file(p, chunk=1 << 20):
    try:
        h = hashlib.md5()
        with open(p, 'rb') as f:
            while True:
                b = f.read(chunk)
                if not b:
                    break
                h.update(b)
        return h.hexdigest()
    except OSError:
        return None


def _walk_user_files(drive, max_files=80000):
    """生成 (path, size, mtime)，跳过系统核心目录。"""
    top = f"{drive}:\\"
    try:
        for root, dirs, files in os.walk(top):
            dl = [d.lower() for d in dirs]
            keep = [d for d, dlow in zip(dirs, dl) if dlow not in EXCLUDE_DIRS]
            dirs[:] = keep
            for f in files:
                if _is_system_file(f):
                    continue
                fp = os.path.join(root, f)
                try:
                    st = os.stat(fp)
                    yield fp, st.st_size, st.st_mtime
                except OSError:
                    continue
                # 通过外部计数控制总量，这里不 yield 控制，调用方计数
    except OSError:
        pass


# ----------------------------------------------------------------------------
# 单次全盘遍历引擎
#   一次遍历同时产出：
#     · 通用垃圾清单（垃圾扩展名 / 大文件 / 旧文件 / 重复文件 / 零字节 / 空文件夹）
#     · 文件类型归类（图片/视频/音乐/文档/压缩包/安装包/其他）
#     · 最大的文件夹排行 / 最大的文件排行
#     · 系统与程序占用（只读统计）
#   支持实时进度回调 progress_cb(files, bytes, cur_dir) 与随时中断 should_stop()。
# ----------------------------------------------------------------------------

_FULL_CACHE = {}


def scan_full_disk(drive, progress_cb=None, should_stop=None):
    """遍历整个盘一次，产出所有清单。同一次扫描内结果缓存复用。"""
    if drive in _FULL_CACHE:
        return _FULL_CACHE[drive]
    result = _do_full_scan(drive, progress_cb, should_stop)
    _FULL_CACHE[drive] = result
    return result


class _FakeEntry:
    """把普通路径包装成类似 os.DirEntry 的对象（供根目录文件复用 add_file）。"""

    __slots__ = ('path', 'name')

    def __init__(self, path):
        self.path = path
        self.name = path.replace('/', '\\').rsplit('\\', 1)[-1]


# FILE_ATTRIBUTE_REPARSE_POINT：联接点(junction)/符号链接/云端占位符的标记。
# 跟着这些目录递归 = 无限循环 + 体积重复统计，必须跳过。
_REPARSE_POINT = 0x400

# AI / 开发缓存特征索引：按路径首段建字典，避免对每个目录做 24 次全路径匹配。
# 索引延迟到首次使用时构建 —— AI_CACHE_PATTERNS 定义在本函数之后。
_AI_INDEX = None


def _seg_soft_eq(seg, pat):
    """目录段宽松比较：'comfyui' 能匹配 'comfyui-shared' / 'comfyui_pt' 等。

    Windows 上同一个工具的目录常带后缀（ComfyUI-Shared、.cache-huggingface、
    node_modules_backup 等），硬相等会大量漏判。
    """
    if seg == pat:
        return True
    if seg.startswith(pat) and len(seg) > len(pat):
        return seg[len(pat)] in '-_. '
    return False


def _match_ai_fast(path):
    """_match_ai_cache 的快速版：命中返回 (说明, 级别)，否则 None。"""
    global _AI_INDEX
    if _AI_INDEX is None:
        idx = {}
        for _segs, _desc, _lvl in AI_CACHE_PATTERNS:
            idx.setdefault(_segs[0].lower(), []).append((list(_segs), _desc, _lvl))
        _AI_INDEX = idx
    parts = [p.lower() for p in (path or '').replace('/', '\\').split('\\') if p]
    n = len(parts)
    if not n:
        return None
    for i in range(n):
        # 先用首段精确命中做快筛，再退回宽松匹配
        cand = _AI_INDEX.get(parts[i])
        if not cand:
            cand = []
            for key, lst in _AI_INDEX.items():
                if _seg_soft_eq(parts[i], key):
                    cand.extend(lst)
        if not cand:
            continue
        for segs, desc, level in cand:
            m = len(segs)
            if i + m > n:
                continue
            if all(_seg_soft_eq(parts[i + k], segs[k]) for k in range(m)):
                return desc, level
    return None


def _do_full_scan(drive, progress_cb=None, should_stop=None):
    """全盘扫描：一次遍历产出垃圾/类型归类/最大文件夹/最大文件/AI缓存/系统占用。

    返回结构与 v2.5 保持一致，下游（类目渲染、清理）无需改动。
    """
    t_start = time.time()
    root = f"{drive}:\\"

    try:
        with os.scandir(root) as it:
            top_entries = list(it)
    except OSError:
        top_entries = []

    sys_dirs, scan_dirs, root_files = [], [], []
    for e in top_entries:
        try:
            st = e.stat(follow_symlinks=False)
        except OSError:
            continue
        if getattr(st, 'st_file_attributes', 0) & _REPARSE_POINT:
            continue                       # 盘根下的联接点：不进去
        try:
            if e.is_dir(follow_symlinks=False):
                if e.name.lower() in SYSTEM_INVENTORY_DIRS:
                    sys_dirs.append(e.path)
                else:
                    scan_dirs.append(e.path)
            elif e.is_file(follow_symlinks=False):
                root_files.append(e.path)
        except OSError:
            continue

    # 任务队列用 queue.Queue：只在取/放任务时短暂持锁，
    # 不会出现 cond.notify_all 把 16 个线程同时唤醒再睡回去的空转。
    task_q = queue.Queue()
    for p in scan_dirs:
        task_q.put((p, False, False))   # (路径, 是否系统目录, 是否已在 AI 缓存目录内)
    for p in sys_dirs:
        task_q.put((p, True, False))
    stop_flag = {'stop': False}
    # pending = 还没处理完的任务数（含正在处理的）。
    # 队列空且 pending==0 → 全部处理完，可以收工。
    pending = [len(scan_dirs) + len(sys_dirs)]
    stats = {'n': 0, 'bytes': 0, 'dir': '', 'last': 0.0}

    def is_stopped():
        if stop_flag['stop']:
            return True
        if should_stop and should_stop():
            stop_flag['stop'] = True
            return True
        return False

    stats_lock = threading.Lock()

    def report(force=False):
        t = time.time()
        with stats_lock:
            if not force and t - stats['last'] < 1.0:
                return
            stats['last'] = t
            n, b, d = stats['n'], stats['bytes'], stats['dir']
        if progress_cb:
            try:
                progress_cb(n, b, d)
            except Exception:
                pass

    def worker():
        """线程主体：所有中间结果都是本线程私有，最后统一合并（无跨线程冲突）。"""
        LARGE_TH = 500 * 1024 ** 2
        OLD_DAYS = 365
        old_cut = time.time() - OLD_DAYS * 86400
        CAP_JUNK, CAP_LARGE, CAP_OLD, CAP_ZERO = 20000, 5000, 20000, 5000
        TOPN = 300
        MAX_BUCKETS = 200000
        DUP_MIN = 256 * 1024

        dir_own = {}        # 目录 → 该目录「直接包含」的文件字节
        cats = {k: {'total': 0, 'heap': []} for k in INV_CAT_META}
        cats['inv_other'] = {'total': 0, 'heap': []}
        junk, large, old, zero = [], [], [], []
        top_files = []
        empties = []
        size_groups = {}     # 文件大小 → 路径列表（只留前 5 个，用于查重复）
        ai_dirs = {}        # AI/开发缓存目录 → (说明, 级别)
        nf = 0              # 本线程待上报的文件数
        nb = 0              # 本线程待上报的字节数
        tf = 0              # 本线程累计文件数
        tb = 0              # 本线程累计字节数

        def push(heap, size, path, topn=TOPN):
            if len(heap) < topn:
                heapq.heappush(heap, (size, path))
            elif size > heap[0][0]:
                heapq.heapreplace(heap, (size, path))

        while True:
            if stop_flag['stop']:
                break
            try:
                path, sys_only, in_ai = task_q.get_nowait()
            except queue.Empty:
                # 队列空了：如果 pending 也归零，说明没有任何任务了 → 收工
                with stats_lock:
                    if pending[0] <= 0:
                        break
                try:
                    path, sys_only, in_ai = task_q.get(timeout=0.5)
                except queue.Empty:
                    continue

            if not in_ai:
                hit = _match_ai_fast(path)
                if hit:
                    ai_dirs[path] = hit
                    in_ai = True

            try:
                with os.scandir(path) as it:
                    entries = list(it)
            except OSError:
                entries = []

            own = 0
            subdirs = []
            for e in entries:
                try:
                    st = e.stat(follow_symlinks=False)
                except OSError:
                    continue
                if getattr(st, 'st_file_attributes', 0) & _REPARSE_POINT:
                    continue               # 联接点/占位符：不递归、不计大小
                try:
                    is_dir = e.is_dir(follow_symlinks=False)
                except OSError:
                    continue
                if is_dir:
                    subdirs.append(e.path)
                    continue

                sz = st.st_size
                own += sz
                nf += 1
                nb += sz
                tf += 1
                tb += sz
                if sys_only:
                    continue               # 系统目录只统计体积

                if sz == 0:
                    if len(zero) < CAP_ZERO:
                        zero.append((e.path, 0))
                    continue
                if _is_junk_name(e.name) and len(junk) < CAP_JUNK:
                    junk.append((e.path, sz))
                if sz >= LARGE_TH and len(large) < CAP_LARGE:
                    large.append((e.path, sz))
                if st.st_mtime < old_cut and len(old) < CAP_OLD:
                    old.append((e.path, sz))
                if sz >= DUP_MIN:
                    bucket = size_groups.get(sz)
                    if bucket is None:
                        if len(size_groups) < MAX_BUCKETS:
                            size_groups[sz] = [e.path]
                    elif len(bucket) < 5:
                        bucket.append(e.path)
                cat = _inv_classify(e.name)
                cats[cat]['total'] += sz
                push(cats[cat]['heap'], sz, e.path)
                push(top_files, sz, e.path)

            dir_own[path] = dir_own.get(path, 0) + own

            for s in subdirs:
                task_q.put((s, sys_only, in_ai))
            if not subdirs and own == 0 and not sys_only:
                if len(empties) < 500:
                    empties.append(path)
            # 当前任务处理完（-1），并新增了 len(subdirs) 个子任务
            with stats_lock:
                pending[0] += len(subdirs) - 1

            if (nf & 0xFFF) == 0:
                with stats_lock:
                    stats['n'] += nf
                    stats['bytes'] += nb
                    stats['dir'] = path
                    nf = 0
                    nb = 0
                report()
                if is_stopped():
                    break

        with stats_lock:
            stats['n'] += nf
            stats['bytes'] += nb
        return {
            'dir_own': dir_own,
            'cats': cats,
            'junk': junk, 'large': large, 'old': old, 'zero': zero,
            'top_files': top_files, 'empties': empties,
            'size_groups': size_groups, 'ai_dirs': ai_dirs,
            'nfiles': tf, 'nbytes': tb,
        }

    # 基准：8 线程 83.6k 文件/s，16 线程 135.2k 文件/s（快 1.6 倍）
    nworkers = min(16, max(4, (os.cpu_count() or 4) * 2))
    parts = []
    try:
        with _futures.ThreadPoolExecutor(max_workers=nworkers) as pool:
            futs = [pool.submit(worker) for _ in range(nworkers)]
            for f in _futures.as_completed(futs):
                try:
                    parts.append(f.result())
                except Exception:
                    pass
    except Exception:
        pass
    report(force=True)

    # ---------------- 合并各线程结果 ----------------
    dir_own = {}
    cats = {k: {'total': 0, 'heap': []} for k in INV_CAT_META}
    cats['inv_other'] = {'total': 0, 'heap': []}
    junk, large, old, zero = [], [], [], []
    top_files = []
    empties = []
    size_groups = {}
    ai_dirs = {}
    total_files = 0
    total_bytes = 0

    def push(heap, size, path, topn=_INV_TOPN):
        if len(heap) < topn:
            heapq.heappush(heap, (size, path))
        elif size > heap[0][0]:
            heapq.heapreplace(heap, (size, path))

    for part in parts:
        for d, b in part['dir_own'].items():
            dir_own[d] = dir_own.get(d, 0) + b
        for k, c in part['cats'].items():
            if k in cats:
                cats[k]['total'] += c['total']
                for s, p in c['heap']:
                    push(cats[k]['heap'], s, p)
        junk.extend(part['junk'])
        large.extend(part['large'])
        old.extend(part['old'])
        zero.extend(part['zero'])
        empties.extend(part['empties'])
        for s, p in part['top_files']:
            push(top_files, s, p)
        for sz, ps in part['size_groups'].items():
            bucket = size_groups.get(sz)
            if bucket is None:
                size_groups[sz] = list(ps)
            else:
                for p in ps:
                    if len(bucket) >= 5:
                        break
                    bucket.append(p)
        for p, hit in part['ai_dirs'].items():
            ai_dirs.setdefault(p, hit)
        total_files += part['nfiles']
        total_bytes += part['nbytes']

    # ---------------- 自底向上汇总目录体积 ----------------
    # 路径倒序遍历时，子目录一定排在父目录前面（父路径是子路径的前缀）
    for d in sorted(dir_own, reverse=True):
        parent = os.path.dirname(d)
        if parent and parent in dir_own:
            dir_own[parent] += dir_own[d]

    # ---------------- 系统 / 程序占用（只读） ----------------
    sys_total = 0
    sys_prefixes = []
    sys_dirs_low = set()
    for p in sys_dirs:
        t = dir_own.get(p, 0)
        sys_total += t
        lowp = p.lower().rstrip('\\')
        sys_dirs_low.add(lowp)
        sys_prefixes.append(lowp + '\\')

    # 盘根下的零散文件（pagefile.sys 等）算作系统占用，不列进可删除清单
    for p in root_files:
        try:
            st = os.stat(p, follow_symlinks=False)
        except OSError:
            continue
        sys_total += st.st_size
        total_files += 1
        total_bytes += st.st_size

    # ---------------- 最大文件夹排行 ----------------
    folders = []
    for d, s in dir_own.items():
        if s <= 0:
            continue
        low = d.lower()
        if any(low.startswith(pre) for pre in sys_prefixes):
            continue                      # 系统目录不列入「可删」清单
        if low in sys_dirs_low:
            continue
        folders.append((s, d))
    folders.sort(key=lambda x: -x[0])
    folders = folders[:_INV_TOPN]

    # ---------------- AI / 开发缓存清单 ----------------
    ai_cache = []
    for path, (desc, level) in ai_dirs.items():
        ai_cache.append({'path': path, 'size': dir_own.get(path, 0),
                         'kind': 'dir', 'label': path, 'desc': desc,
                         'level': level})
    ai_cache.sort(key=lambda x: -x['size'])
    ai_cache = ai_cache[:400]

    # ---------------- 重复文件（同大小 + 内容哈希一致） ----------------
    # 只保留「同大小且体积够大」的分组 —— 小文件的重复没有清理价值。
    # 注意：这里【不做】md5 哈希。哈希是整个扫描里最贵的一步
    # （cProfile 实测 3121 次 HASH.update 吃掉 6.3 秒），
    # 而「重复文件」是低频需求 —— 真正的哈希推迟到用户展开该类目时
    # 由 _scan_dups_on_demand() 按需触发，扫描速度因此不受影响。
    dup_groups = [(sz, ps) for sz, ps in size_groups.items()
                  if sz >= 1024 * 1024 and len(ps) >= 2]
    dup_groups.sort(key=lambda x: -x[0])
    dup = []

    # 全局收敛：多线程合并后条目数会放大，这里统一裁到全局上限
    junk = junk[:20000]
    large = sorted(large, key=lambda x: -x[1])[:1000]
    old = old[:20000]
    zero = zero[:5000]
    empties = empties[:5000]

    def mk(lst, kind):
        return [{"path": p, "size": s, "kind": kind, "label": p,
                 "desc": describe_path(p)} for p, s in lst]

    result = {
        "g_junk": mk(junk, "file"),
        "g_large": mk(large, "file"),
        "g_old": mk(old, "file"),
        "g_dup": [{"path": p, "size": s, "kind": "file",
                   "label": p + "（重复）",
                   "desc": describe_path(p) + " · 与另一处内容完全相同的副本"}
                  for p, s in dup],
        "_dup_groups": dup_groups[:400],
        "g_zero": [{"path": p, "size": 0, "kind": "file", "label": p,
                    "desc": describe_path(p)} for p, _ in zero],
        "g_empty": [{"path": p, "size": 0, "kind": "edir",
                     "label": p + "（空文件夹）",
                     "desc": describe_path(p, True)} for p in empties],
        "inv_system_total": sys_total,
        "ai_cache": ai_cache,
        # v3.0：把「自底向上汇总后的目录体积表」留给大目录逐层浏览用。
        # 它是同一个 dict 的引用，不额外占内存；展开 47.9GB 的 Users
        # 时直接查表就能给出每个子目录的体积，不用重新遍历几十万文件。
        "dir_sizes": dir_own,
        # v2.9：软件缓存识别复用本次遍历的 dir_own，不额外读盘
        "software_caches": classify_software_dirs(drive, dir_own),
        "top_dirs": classify_top_dirs(drive, dir_own),
        "_file_count": total_files,
        "_scan_bytes": total_bytes,
        "_scan_seconds": round(time.time() - t_start, 1),
    }
    for key in INV_CAT_META:
        heap = sorted(cats[key]['heap'], reverse=True)
        result[key] = [{"path": p, "size": s, "kind": "file", "label": p,
                        "desc": describe_path(p)}
                       for s, p in heap]
    oheap = sorted(cats['inv_other']['heap'], reverse=True)
    result['inv_other'] = [{'path': p, 'size': s, 'kind': 'file', 'label': p,
                            'desc': describe_path(p)} for s, p in oheap]
    result['inv_bigfolders'] = [
        {'path': p, 'size': s, 'kind': 'dir', 'label': p + '（文件夹）',
         'desc': describe_path(p, True)}
        for s, p in folders]
    result['inv_bigfiles'] = [
        {'path': p, 'size': s, 'kind': 'file', 'label': p,
         'desc': describe_path(p)}
        for s, p in sorted(top_files, key=lambda x: -x[0])]

    # ---- 应用维度归并：谁占了这个盘 ----
    # 「最大的文件夹排行」有父子重复（C:\Users 与 C:\Users\windos），
    # 用户看到会觉得数字乱。商业清理软件按「应用」归并后才直观。
    result['inv_apps'] = app_groups_from_dir_own(dir_own)
    report(force=True)
    return result


def _scan_dups_on_demand(drive, budget=400, time_limit=25):
    """按需检测重复文件：只对「同大小」的候选做 md5 比对。

    故意放在扫描之后单独触发 —— 它是整个扫描里最贵的一步，
    不该拖慢用户等结果的时间。
    """
    r = scan_full_disk(drive)
    groups = r.get("_dup_groups", [])
    dup = []
    used = 0
    t0 = time.time()
    for sz, paths in groups:
        if used >= budget or (time.time() - t0) > time_limit:
            break
        seen = {}
        for p in paths[:4]:
            if used >= budget or (time.time() - t0) > time_limit:
                break
            h = _hash_file(p)
            used += 1
            if h is None:
                continue
            if h in seen:
                dup.append((p, sz))
            else:
                seen[h] = p
            if len(dup) >= 200:
                break
    return [{"path": p, "size": s, "kind": "file",
             "label": p + "（重复）",
             "desc": describe_path(p) + " · 与另一处内容完全相同的副本"}
            for p, s in dup]


def scan_all_files(drive, progress_cb=None, should_stop=None):
    """通用垃圾清单（垃圾扩展名/大文件/旧文件/重复文件/零字节）。"""
    r = scan_full_disk(drive, progress_cb, should_stop)
    return {k: r.get(k, []) for k in
            ("g_junk", "g_large", "g_old", "g_dup", "g_zero")}


def scan_empty_dirs(drive):
    """空文件夹（复用同一次全盘遍历的结果，不再额外遍历）。"""
    return scan_full_disk(drive).get("g_empty", [])


# ----------------------------------------------------------------------------
# 磁盘文件分析（全盘归类，让用户自己决定删不删）
# 覆盖「已知垃圾」之外的真实文件：图片/视频/音乐/文档/压缩包/安装包/其他，
# 以及「最大的文件夹排行」「最大的文件排行」，并单独统计系统/程序占用（只读）。
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# 知识库：告诉用户「这个文件/文件夹到底是干什么的」
# 命中目录规则 → 该目录的用途说明；命中扩展名规则 → 该文件类型的用途说明
# 两者都命中时组合成一句；都不命中就写「未知用途」
# ----------------------------------------------------------------------------

# 目录特征 → 用途说明
# 规则用「路径段序列」匹配（精确，不会把 comfyui-notes 误判成 comfyui）
DIR_KNOWLEDGE = [
    # ---- AI / 大模型 / 出图 ----
    (('comfyui', 'models'), 'ComfyUI 模型权重：SD / Flux 的 checkpoint、LoRA、VAE 等'),
    (('comfyui',), 'ComfyUI AI 出图工作目录（含模型、自定义节点与输出图片）'),
    (('stable-diffusion-webui',), 'Stable Diffusion WebUI 出图目录'),
    (('automatic1111',), 'AUTOMATIC1111 Stable Diffusion 出图目录'),
    (('sd-webui',), 'Stable Diffusion WebUI 出图目录'),
    (('fooocus',), 'Fooocus 出图目录'),
    (('invokeai',), 'InvokeAI 出图目录'),
    (('.ollama', 'models'), 'Ollama 本地大模型权重（删掉后本地 LLM 就没了，需重新 pull）'),
    (('.ollama',), 'Ollama 大模型运行目录（模型权重与配置）'),
    (('huggingface', 'hub'), 'Hugging Face 模型缓存：Transformers 等库下载的模型权重'),
    (('huggingface',), 'Hugging Face 缓存与数据集'),
    (('.cache', 'torch'), 'PyTorch 预训练权重缓存（torch hub 下载）'),
    (('torch', 'hub'), 'PyTorch Hub 下载的模型缓存'),
    (('checkpoints',), 'AI 模型检查点目录（训练或推理用的模型权重）'),
    (('loras',), 'LoRA 低秩适配模型目录（AI 出图微调模型）'),
    (('vae',), 'VAE 变分自编码器模型目录（AI 出图用）'),
    (('embeddings',), 'Embedding 嵌入模型目录（文本向量化模型）'),
    (('whisper',), 'Whisper 语音识别模型文件'),
    (('sana',), 'Sana 图像生成模型目录'),
    (('sd-models',), 'Stable Diffusion 模型目录'),
    (('models',), '模型文件目录（多为 AI 模型权重，具体看所在应用）'),
    (('node_modules',), 'Node 依赖包目录：可用 npm / pnpm install 重新生成'),
    (('site-packages',), 'Python 第三方库目录：可用 pip install 重新生成'),
    (('__pycache__',), 'Python 字节码缓存（可安全删除，会自动重建）'),
    (('.venv',), 'Python 虚拟环境（可重建，但依赖要重新安装）'),
    (('venv',), 'Python 虚拟环境（可重建，但依赖要重新安装）'),
    (('.git',), 'Git 仓库元数据（含提交历史，删除会丢失版本记录）'),
    (('.gradle',), 'Gradle 构建缓存与依赖缓存'),
    (('.m2',), 'Maven 本地依赖仓库（可删除，会重新下载）'),
    (('.cargo',), 'Rust 工具链与 crates 缓存'),
    (('.nuget',), 'NuGet 包缓存'),
    (('.cache',), '通用缓存目录（多数内容可安全删除，会自动重建）'),
    (('pnpm', 'store'), 'pnpm 全局包仓库：Node 依赖包缓存，删后重新 install 会再下载'),
    (('pnpm',), 'pnpm 包管理器数据（全局 store 与元数据缓存）'),
    (('npm-cache',), 'npm 下载缓存（已下载的 tarball，可删除）'),
    (('pip', 'cache'), 'pip 下载缓存（已下载的 wheel 安装包，可删除）'),
    (('uv', 'cache'), 'uv 包管理器缓存（可删除）'),
    (('pip',), 'pip 包管理器数据（含下载缓存）'),
    (('uv',), 'uv 包管理器数据（含缓存）'),
    # ---- Windows 系统 ----
    (('windows', 'system32'), 'Windows 64 位系统核心文件（不可删除）'),
    (('windows', 'syswow64'), 'Windows 32 位兼容系统文件（不可删除）'),
    (('windows', 'winsxs'), 'Windows 组件存储（系统更新回滚用，勿手工删）'),
    (('windows', 'installer'), 'Windows 安装程序缓存（卸载软件要用）'),
    (('windows',), 'Windows 系统目录（不要手工删除）'),
    (('program files', 'common files'), '程序共享组件库（删除会影响多个软件）'),
    (('program files (x86)',), '已安装的 32 位程序（删除相当于卸载，慎用）'),
    (('program files',), '已安装的程序（删除相当于卸载，慎用）'),
    (('programdata',), '所有用户共享的程序数据（删除会破坏软件）'),
    (('$recycle.bin',), '回收站（清空即彻底删除）'),
    (('system volume information',), '系统还原点与卷影副本（建议用系统清理释放）'),
    (('recovery',), 'Windows 恢复环境（不可删除）'),
    # ---- 用户数据 ----
    (('appdata', 'local', 'packages'), 'UWP / 商店应用的沙盒数据'),
    (('appdata', 'local', 'temp'), '系统与程序的临时文件（可安全删除）'),
    (('appdata', 'local', 'microsoft', 'windows', 'inetcache'),
     'IE / Edge 临时上网文件'),
    (('appdata', 'local', 'microsoft', 'windows', 'webcache'),
     'IE / Edge 网页缓存'),
    (('appdata', 'local', 'microsoft', 'edge', 'user data'),
     'Edge 浏览器用户数据（书签 / 密码 / 缓存，勿整目录删）'),
    (('appdata', 'local', 'google', 'chrome', 'user data'),
     'Chrome 浏览器用户数据（书签 / 密码 / 缓存，勿整目录删）'),
    (('appdata', 'local', 'nvidia'), 'NVIDIA 显卡驱动数据与着色器缓存'),
    (('appdata', 'local', 'discord'), 'Discord 缓存与登录数据'),
    (('appdata', 'local', 'docker'), 'Docker 镜像与容器数据（删除会丢容器）'),
    (('appdata', 'local', 'wsl'), 'WSL Linux 发行版数据（删发行版即丢数据）'),
    (('appdata', 'local', 'android'), 'Android SDK（模拟器与系统镜像）'),
    (('appdata', 'roaming', 'code'), 'VS Code 编辑器数据与扩展'),
    (('appdata', 'roaming', 'obs-studio'), 'OBS 推流软件录制与配置'),
    (('appdata', 'roaming', 'unity'), 'Unity 编辑器缓存与资产'),
    (('appdata', 'roaming', 'unity3d'), 'Unity 编辑器缓存与资产'),
    (('appdata', 'roaming', 'tencent'), '腾讯软件数据（QQ / 微信缓存）'),
    (('appdata', 'roaming', 'adobe'), 'Adobe 软件缓存与临时文件'),
    (('appdata', 'roaming', 'spotify'), 'Spotify 音乐缓存'),
    (('appdata', 'roaming', 'zoom'), 'Zoom 会议缓存与录制'),
    (('appdata', 'roaming', 'wechat'), '微信数据目录（聊天记录与缓存）'),
    (('appdata', 'roaming', 'codeium'), 'Codeium / Copilot 扩展数据与索引缓存'),
    (('appdata', 'local'), '当前用户的本地程序数据（缓存、程序本体、日志）'),
    (('appdata', 'roaming'), '漫游配置：跨设备同步的用户设置（勿整目录删）'),
    (('appdata',), '应用程序配置与缓存数据目录'),
    (('onedrive',), 'OneDrive 云盘同步目录（删除可能丢云端副本）'),
    (('downloads',), '下载文件夹'),
    (('desktop',), '桌面'),
    (('documents',), '文档'),
    (('pictures',), '图片库'),
    (('videos',), '视频库'),
    (('music',), '音乐库'),
    (('steamapps',), 'Steam 游戏本体（删除即卸载游戏）'),
    (('steam',), 'Steam 客户端数据'),
    (('.vscode',), 'VS Code 编辑器配置与扩展'),
    (('.cursor',), 'Cursor 编辑器数据与扩展'),
    (('.claude',), 'Claude Code / Claude 桌面端数据'),
    (('.workbuddy',), 'WorkBuddy AI 工作台的数据与日志'),
    (('.conda',), 'conda 环境目录'),
    (('miniconda',), 'Miniconda 环境目录'),
    (('anaconda',), 'Anaconda 环境目录'),
]

# 文件扩展名 → 用途说明
EXT_KNOWLEDGE = {
    'safetensors': 'AI 模型权重文件（safetensors 格式）',
    'gguf': '大模型量化权重（GGUF，Ollama / LM Studio 用）',
    'ckpt': 'AI 模型检查点（PyTorch checkpoint）',
    'pth': 'PyTorch 模型权重',
    'pt': 'PyTorch 模型权重',
    'onnx': 'ONNX 推理模型',
    'bin': '二进制文件（模型权重常见）',
    'pkl': 'Python 数据序列化文件（模型/数据集）',
    'npy': 'NumPy 数值数组文件',
    'npz': 'NumPy 压缩数组文件',
    'parquet': '列式数据文件（数据集）',
    'log': '日志文件（程序运行记录）',
    'tmp': '临时文件（可删）',
    'temp': '临时文件（可删）',
    'bak': '备份文件（可删）',
    'old': '旧版本遗留文件（可删）',
    'dmp': '崩溃转储文件（可删）',
    'etl': 'Windows 事件日志',
    'evtx': 'Windows 事件日志',
    'db': '数据库文件',
    'sqlite': 'SQLite 数据库文件',
    'exe': '可执行程序',
    'msi': 'Windows 安装包',
    'apk': 'Android 安装包',
    'iso': '光盘 / 系统镜像文件',
    'img': '磁盘镜像文件',
    'zip': '压缩包',
    'rar': 'RAR 压缩包',
    '7z': '7-Zip 压缩包',
    'tar': 'tar 归档包',
    'gz': 'gzip 压缩包',
    'mp4': '视频文件',
    'mkv': '视频文件',
    'avi': '视频文件',
    'mov': '视频文件（QuickTime）',
    'flv': '视频文件',
    'webm': '视频文件',
    'wmv': '视频文件',
    'm4v': '视频文件',
    'jpg': '图片文件',
    'jpeg': '图片文件',
    'png': '图片文件',
    'gif': '图片文件',
    'bmp': '图片文件',
    'webp': '图片文件',
    'heic': '图片文件（苹果 HEIC）',
    'raw': '相机 RAW 原图',
    'cr2': '相机 RAW 原图',
    'nef': '相机 RAW 原图',
    'arw': '相机 RAW 原图',
    'psd': 'Photoshop 工程文件',
    'mp3': '音频文件',
    'flac': '无损音频文件',
    'wav': '音频文件',
    'aac': '音频文件',
    'ogg': '音频文件',
    'm4a': '音频文件',
    'wma': '音频文件',
    'pdf': 'PDF 文档',
    'doc': 'Word 文档',
    'docx': 'Word 文档',
    'xls': 'Excel 表格',
    'xlsx': 'Excel 表格',
    'ppt': 'PowerPoint 演示文稿',
    'pptx': 'PowerPoint 演示文稿',
    'txt': '纯文本文件',
    'md': 'Markdown 文档',
    'csv': 'CSV 表格文件',
    'rtf': '富文本文档',
    'epub': '电子书',
    'py': 'Python 源代码',
    'ipynb': 'Jupyter Notebook（AI / 数据分析笔记本）',
    'js': 'JavaScript 源代码',
    'ts': 'TypeScript 源代码',
    'jsx': 'React 源代码',
    'tsx': 'React TypeScript 源代码',
    'java': 'Java 源代码',
    'cs': 'C# 源代码',
    'cpp': 'C++ 源代码',
    'go': 'Go 源代码',
    'rs': 'Rust 源代码',
    'php': 'PHP 源代码',
    'html': '网页文件',
    'htm': '网页文件',
    'css': '样式表',
    'json': 'JSON 数据 / 配置文件',
    'xml': 'XML 配置文件',
    'yml': 'YAML 配置文件',
    'yaml': 'YAML 配置文件',
    'ini': 'INI 配置文件',
    'cfg': '配置文件',
    'conf': '配置文件',
    'dll': '程序动态链接库（系统 / 软件依赖，不要删）',
    'sys': '系统驱动文件（不可删）',
    'bat': '批处理脚本',
    'cmd': '命令行脚本',
    'ps1': 'PowerShell 脚本',
    'lnk': '快捷方式（删了只是少个图标）',
    'desktop': '桌面快捷方式',
    'url': '网址快捷方式',
    'reg': '注册表导出文件',
    'cab': 'Windows 压缩包（系统安装缓存）',
    'pf': '预读取文件（加速启动用）',
}


def _seg_match(path, segs):
    """路径的目录段序列里是否连续包含 segs（大小写不敏感）。"""
    parts = [p for p in (path or '').replace('/', '\\').split('\\') if p]
    low = [p.lower() for p in parts]
    n = len(segs)
    if n == 0 or n > len(low):
        return False
    for i in range(len(low) - n + 1):
        if low[i:i + n] == list(segs):
            return True
    return False


# DIR_KNOWLEDGE 的首段索引：91 条规则里，只有首段能对上的才需要逐段比对。
# 原来每条规则都要把整条路径 split + lower 一遍，扫描几十万文件时
# 这就是几千万次字符串操作（cProfile 实测吃掉 24.8 秒）。
_DIR_KW_INDEX = None
_DIR_KW_BY_LEN = None


def _build_dir_kw_index():
    """构建 DIR_KNOWLEDGE 索引：首段 -> 规则列表，以及按规则长度分组。"""
    global _DIR_KW_INDEX, _DIR_KW_BY_LEN
    if _DIR_KW_INDEX is not None:
        return
    idx = {}
    for segs, desc in DIR_KNOWLEDGE:
        key = segs[0].lower()
        idx.setdefault(key, []).append((tuple(s.lower() for s in segs), desc))
    _DIR_KW_INDEX = idx
    # 多段规则（长度 > 1）单独放一张表，遍历时先查短规则再查长规则
    by_len = {}
    for segs, desc in DIR_KNOWLEDGE:
        by_len.setdefault(len(segs), []).append(
            (tuple(s.lower() for s in segs), desc))
    _DIR_KW_BY_LEN = by_len


_DESC_CACHE = {}


def describe_path(path, is_dir=False):
    """给一个文件 / 文件夹生成中文用途说明；识别不出就明说「未知用途」。

    结果按路径缓存 —— 同一个目录下的成千上万个文件会命中同一条目录规则。
    """
    ck = (path, is_dir)
    hit = _DESC_CACHE.get(ck)
    if hit is not None:
        return hit
    r = _describe_path_uncached(path, is_dir)
    if len(_DESC_CACHE) < 200000:
        _DESC_CACHE[ck] = r
    return r


def _describe_path_uncached(path, is_dir=False):
    """给一个文件 / 文件夹生成中文用途说明；识别不出就明说「未知用途」。"""
    _build_dir_kw_index()
    # 路径只切一次段，后面所有规则都复用这份分段
    raw = [p for p in (path or '').replace('/', '\\').split('\\') if p]
    low = [p.lower() for p in raw]
    n = len(low)

    dir_desc = None
    # 先用首段索引快筛：只有首段能对上的规则才值得逐段比对
    cands = []
    for i in range(n):
        lst = _DIR_KW_INDEX.get(low[i])
        if lst:
            cands.append((i, lst))
    if cands:
        for segs, desc in _DIR_KW_BY_LEN.get(1, ()):
            if segs[0] in low:
                dir_desc = desc
                break
        if dir_desc is None:
            # 多段规则：按首段索引命中后逐段比对
            for i, lst in cands:
                for segs, desc in lst:
                    m = len(segs)
                    if m == 1:
                        continue
                    if i + m <= n and low[i:i + m] == segs:
                        dir_desc = desc
                        break
                if dir_desc:
                    break

    base = low[-1] if low else ''
    ext = base.rsplit('.', 1)[-1] if '.' in base else ''
    ext_desc = EXT_KNOWLEDGE.get(ext)
    if is_dir:
        if dir_desc:
            return dir_desc
        if ext_desc:
            return ext_desc + '（以该类型命名的文件夹）'
        return '未知用途的文件夹'
    parts = []
    if dir_desc:
        parts.append(dir_desc)
    if ext_desc:
        parts.append(ext_desc)
    elif ext:
        # 有扩展名但知识库里没有 → 明确写「未知用途」
        parts.append(f'未知用途（.{ext} 格式，无法自动识别）')
    else:
        parts.append('未知用途（无扩展名，无法自动识别）')
    return ' · '.join(parts)

# AI / 开发工具目录特征（用于单独识别「AI 缓存」）
AI_CACHE_PATTERNS = [
    (('comfyui', 'models'), 'ComfyUI 模型权重（SD / Flux checkpoint、LoRA、VAE）', 'ai-model'),
    (('comfyui',), 'ComfyUI 出图工作目录（模型 + 自定义节点 + 输出图）', 'ai-work'),
    (('stable-diffusion-webui',), 'Stable Diffusion WebUI 出图目录', 'ai-work'),
    (('automatic1111',), 'AUTOMATIC1111 Stable Diffusion 出图目录', 'ai-work'),
    (('sd-webui',), 'Stable Diffusion WebUI 出图目录', 'ai-work'),
    (('fooocus',), 'Fooocus 出图目录', 'ai-work'),
    (('invokeai',), 'InvokeAI 出图目录', 'ai-work'),
    (('.ollama', 'models'), 'Ollama 本地大模型权重（删了要重新 pull）', 'ai-model'),
    (('.ollama',), 'Ollama 大模型运行目录', 'ai-model'),
    (('huggingface', 'hub'), 'Hugging Face 模型缓存（Transformers 下载的权重）', 'ai-model'),
    (('.cache', 'torch'), 'PyTorch 预训练权重缓存', 'ai-model'),
    (('torch', 'hub'), 'PyTorch Hub 模型缓存', 'ai-model'),
    (('.cache', 'huggingface'), 'Hugging Face 缓存', 'ai-model'),
    (('.cache', 'transformers'), 'Transformers 模型缓存', 'ai-model'),
    (('pnpm', 'store'), 'pnpm 全局包仓库（Node 依赖缓存，可重新下载）', 'dev-cache'),
    (('npm-cache',), 'npm 下载缓存（可删，会重下）', 'dev-cache'),
    (('pip', 'cache'), 'pip 下载缓存（可删，会重下）', 'dev-cache'),
    (('uv', 'cache'), 'uv 包缓存（可删，会重下）', 'dev-cache'),
    (('node_modules',), 'Node 依赖包目录（npm / pnpm install 可重建）', 'dev-cache'),
    (('site-packages',), 'Python 第三方库目录（pip install 可重建）', 'dev-cache'),
    (('__pycache__',), 'Python 字节码缓存（可安全删除）', 'dev-cache'),
    (('.venv',), 'Python 虚拟环境（可重建，依赖需重装）', 'dev-env'),
    (('.cache',), '通用缓存目录（多数可安全删除）', 'dev-cache'),
    (('.git',), 'Git 仓库元数据（含提交历史，删了丢版本记录）', 'dev-repo'),
]


def _match_ai_cache(path):
    """路径命中 AI / 开发缓存特征时返回 (说明, 级别)，否则返回 None。"""
    for segs, desc, level in AI_CACHE_PATTERNS:
        if _seg_match(path, segs):
            return desc, level
    return None


INV_EXT = {
    'image':     {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tif', 'tiff', 'webp',
                  'heic', 'heif', 'raw', 'cr2', 'nef', 'arw', 'svg', 'psd', 'ai'},
    'video':     {'mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'm4v', 'webm',
                  'mpg', 'mpeg', '3gp', 'rmvb'},
    'audio':     {'mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma', 'ape'},
    'doc':       {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt',
                  'rtf', 'epub', 'mobi', 'csv', 'md', 'odt', 'ods', 'odp'},
    'archive':   {'zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'tgz'},
    'installer': {'exe', 'msi', 'dmg', 'bin', 'cab', 'apk', 'iso', 'img'},
}

INV_CAT_META = {
    'inv_image':     ('图片', 'optional'),
    'inv_video':     ('视频', 'optional'),
    'inv_audio':     ('音乐', 'optional'),
    'inv_doc':       ('文档', 'optional'),
    'inv_archive':   ('压缩包', 'optional'),
    'inv_installer': ('安装包 / 光盘镜像', 'optional'),
}

# 这些目录是 Windows 系统与已装软件，单独统计为「系统 / 程序占用（只读）」，
# 不逐项列出（数量巨大且删除会破坏系统），只告诉用户它们占了多少空间。
SYSTEM_INVENTORY_DIRS = {
    'windows', 'program files', 'program files (x86)', 'programdata',
    '$recycle.bin', 'system volume information', 'recovery', 'perflogs',
    'boot', 'documents and settings', 'msocache',
}

INV_CAT_DESC = {
    'inv_image': '图片文件（照片/截图/素材）',
    'inv_video': '视频文件（录屏/影片）',
    'inv_audio': '音频文件（音乐/录音）',
    'inv_doc': '文档文件（Office/PDF/文本）',
    'inv_archive': '压缩包（zip/rar/7z 等）',
    'inv_installer': '安装包与光盘镜像（exe/msi/iso）',
}

_INV_TOPN = 300        # 每类最多列出体积最大的 N 项
_INV_FILE_CAP = 2000000  # 单盘最多统计的文件数（防极端超大盘卡死；堆有上限，内存不受文件数影响）


def _inv_classify(name):
    if '.' not in name:
        return 'inv_other'
    ext = name.rsplit('.', 1)[-1].lower()
    for cat, exts in INV_EXT.items():
        if ext in exts:
            return 'inv_' + cat
    return 'inv_other'


def _dir_size_capped(path, cap):
    """带计数上限地累加目录大小（仅用于系统目录只读统计）。"""
    total = 0
    try:
        with os.scandir(path) as it:
            entries = list(it)
    except OSError:
        return 0
    files = [e for e in entries if not e.is_dir(follow_symlinks=False)]
    dirs = [e for e in entries if e.is_dir(follow_symlinks=False)]
    for e in files:
        if cap['n'] > _INV_FILE_CAP:
            return total
        try:
            total += e.stat(follow_symlinks=False).st_size
            cap['n'] += 1
        except OSError:
            pass
    for e in dirs:
        if cap['n'] > _INV_FILE_CAP:
            break
        total += _dir_size_capped(e.path, cap)
    return total


def scan_inventory(drive, log_cb=None, progress_cb=None, should_stop=None):
    """文件类型归类 / 最大文件夹 / 最大文件 / 系统占用（复用同一次全盘遍历）。"""
    r = scan_full_disk(drive, progress_cb, should_stop)
    out = {k: v for k, v in r.items() if k.startswith('inv_')}
    if log_cb:
        log_cb(f"  （{drive}: 盘共统计 {r.get('_file_count', 0)} 个文件，"
               f"系统/程序占用 {human_size(out.get('inv_system_total', 0))}）")
    return out


def _inv_slice(drive, key):
    return scan_full_disk(drive).get(key, [])

def inventory_categories(drive):
    cats = [{
        'key': 'inv_system', 'name': '系统 / 程序占用（只读·不可清理）',
        'risk': 'safe', 'per_file': False, 'readonly': True,
        'desc': 'Windows 与已安装软件占用的空间，只能看不能删',
        'scan': lambda d: [],
    }]
    cats.append({
        'key': 'ai_cache', 'name': '🤖 AI / 开发工具缓存与模型（可重建）',
        'risk': 'optional', 'per_file': True,
        'desc': 'AI 模型权重、npm/pnpm/pip 包缓存、node_modules 等；'
                '删掉不会丢数据，但需要时会重新下载',
        'scan': lambda d: _inv_slice(d, 'ai_cache')})
    # ---- 以下是「空间分析」，只读：让用户看清空间被谁占了 ----
    # 它们列的是用户的真实数据（照片、微信记录、Chrome 模型…），
    # 不是垃圾。之前把它们算进「可释放空间」，
    # 结果就是「预计释放 89GB、实际只释放 600MB」—— 数字虚高 + 勾了也删不掉。
    cats.append({
        'key': 'inv_bigfolders', 'name': '📁 空间占用：应用 / 文件夹排行（只读）',
        'risk': 'safe', 'per_file': False, 'readonly': True,
        'desc': '按程序归并后的占用排行，看清空间被谁占了；'
                '这里只做分析，不计入可释放空间',
        'scan': lambda d: _inv_slice(d, 'inv_apps')})
    cats.append({
        'key': 'inv_bigfiles', 'name': '📄 空间占用：最大的文件排行（只读）',
        'risk': 'safe', 'per_file': False, 'readonly': True,
        'desc': '按体积排序的大文件，用来定位空间黑洞；'
                '真要删请到「大文件」类目里逐个确认',
        'scan': lambda d: _inv_slice(d, 'inv_bigfiles')})
    for key, (nm, risk) in INV_CAT_META.items():
        cats.append({
            'key': key, 'name': nm, 'risk': risk, 'per_file': True,
            'readonly': True,
            'desc': INV_CAT_DESC.get(key, '') + '（只读分析，不计入可释放空间）',
            'scan': (lambda k: (lambda d: _inv_slice(d, k)))(key)})
    cats.append({
        'key': 'inv_other', 'name': '其他文件', 'risk': 'optional',
        'per_file': True, 'readonly': True,
        'desc': '未归类的其它文件（只读分析）',
        'scan': lambda d: _inv_slice(d, 'inv_other')})
    return cats


# ----------------------------------------------------------------------------
# 注册表扫描（仅系统盘）
# ----------------------------------------------------------------------------

def scan_reg_broken_uninstall(drive=None):
    items = []
    roots = [
        ("HKLM", r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        ("HKLM", r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        ("HKCU", r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    for hive, sub in roots:
        key = reg_open(hive, sub, READ)
        if not key:
            continue
        for sk in reg_subkeys(key):
            full = sub + "\\" + sk
            sub_key = reg_open(hive, full, READ)
            if sub_key is None:
                continue
            name = None
            try:
                name = winreg.QueryValueEx(sub_key, "DisplayName")[0]
            except OSError:
                pass
            ustr = None
            try:
                ustr = winreg.QueryValueEx(sub_key, "UninstallString")[0]
            except OSError:
                pass
            loc = None
            try:
                loc = winreg.QueryValueEx(sub_key, "InstallLocation")[0]
            except OSError:
                pass
            try:
                winreg.CloseKey(sub_key)
            except Exception:
                pass
            if not name:
                items.append(reg_item(hive, full, None, "risky",
                                      "孤立卸载项: " + sk))
                continue
            target = extract_exe_path(ustr) or (loc if loc else None)
            if target:
                expanded = expand_env(target)
                if not (os.path.exists(expanded) or
                        os.path.exists(os.path.dirname(expanded) or expanded)):
                    items.append(reg_item(hive, full, None, "risky",
                                          "无效卸载项: " + name))
        try:
            winreg.CloseKey(key)
        except Exception:
            pass
    return items


def scan_reg_startup(drive=None):
    items = []
    roots = [
        ("HKLM", r"Software\Microsoft\Windows\CurrentVersion\Run"),
        ("HKLM", r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
        ("HKCU", r"Software\Microsoft\Windows\CurrentVersion\Run"),
        ("HKCU", r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
    ]
    for hive, sub in roots:
        key = reg_open(hive, sub, READ)
        if not key:
            continue
        for name, value, vtype in reg_values(key):
            if vtype not in (winreg.REG_SZ, winreg.REG_EXPAND_SZ):
                continue
            target = extract_exe_path(value)
            if target:
                expanded = expand_env(target)
                if not os.path.exists(expanded):
                    items.append(reg_item(hive, sub, name, "risky",
                                          "失效启动项: " + name))
        try:
            winreg.CloseKey(key)
        except Exception:
            pass
    return items


def scan_reg_mru(drive=None):
    items = []
    cands = [
        ("HKCU", r"Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs",
         "最近文档记录"),
        ("HKCU", r"Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU",
         "运行命令历史"),
        ("HKCU", r"Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths",
         "地址栏输入历史"),
    ]
    for hive, sub, label in cands:
        key = reg_open(hive, sub, READ)
        if key is not None:
            items.append(reg_item(hive, sub, None, "optional", label))
            try:
                winreg.CloseKey(key)
            except Exception:
                pass
    return items


# ----------------------------------------------------------------------------
# 分类定义
# risk: safe(自动清理) / optional(默认不勾) / risky(需确认)
# per_file=True 的类目逐文件列出，用户精确到单个文件决定删不删
# ----------------------------------------------------------------------------

def scan_install_residue(drive='C'):
    """软件安装包 / 更新残留 / 未完成下载。

    这是「真正能清出效果」的一类：
      · 程序更新器留下的旧安装程序（xxx-updater\\installer.exe）
      · 应用安装包缓存（app_shell_cache_*）
      · 没下完就关掉的残留（.part/.crdownload/.download）

    性能：不遍历整棵树（那样要 20 秒），
    而是【只看一层目录名 + 已知的安装包缓存位置】。
    装机软件/update 目录基本都是 LOCALAPPDATA 下的一层子目录，
    扫完这两层就够找出 99% 的残留了，几秒钟搞定。
    """
    items = []
    seen = set()
    local = os.environ.get("LOCALAPPDATA", "")
    appdata = os.environ.get("APPDATA", "")
    userprofile = os.environ.get("USERPROFILE", "")

    # 候选根目录：只扫「一层」，找出名字带 updater / cache / installer 的
    roots = []
    for base in (local, appdata):
        if base and os.path.isdir(base):
            roots.append(base)
    # 已知的固定位置
    for p in [os.path.join(local, "Temp"), os.path.join(userprofile, "Downloads"),
              os.path.join(local, "LocModel", "engines", "downloads")]:
        if os.path.isdir(p):
            roots.append(p)

    INSTALL_EXT = (".exe", ".msi", ".tmp")
    for base in roots:
        try:
            entries = list(os.scandir(base))
        except OSError:
            continue
        # 第一层：base 下的每个子目录
        for e in entries:
            try:
                if not e.is_dir(follow_symlinks=False):
                    continue
            except OSError:
                continue
            name = e.name.lower()
            suspicious = ("updater" in name or "cache" in name
                          or "installer" in name or "setup" in name
                          or "download" in name or "temp" in name)
            if not suspicious:
                continue
            _collect_install_files(e.path, INSTALL_EXT, items, seen,
                                   max_depth=2)
        # base 自身目录里的散装文件（未完成的下载）
        _collect_install_files(base, INSTALL_EXT, items, seen,
                               max_depth=0, only_ext=(
                                   ".part", ".crdownload", ".download",
                                   ".partial"))
    items.sort(key=lambda x: -x["size"])
    return items[:300]


def _collect_install_files(root, exts, items, seen, max_depth=2,
                           only_ext=None, min_size=20 * 1024 ** 2):
    """在 root 下（最多 max_depth 层）找安装包 / 未完成下载残留。"""
    stack = [(root, 0)]
    while stack:
        cur, depth = stack.pop()
        try:
            entries = list(os.scandir(cur))
        except OSError:
            continue
        for e in entries:
            try:
                if e.is_dir(follow_symlinks=False):
                    if depth < max_depth:
                        stack.append((e.path, depth + 1))
                    continue
                lf = e.name.lower()
                if only_ext:
                    if not lf.endswith(only_ext):
                        continue
                else:
                    if not lf.endswith(exts):
                        continue
                sz = e.stat(follow_symlinks=False).st_size
                if sz < min_size:
                    continue
                if e.path in seen:
                    continue
                seen.add(e.path)
                if only_ext:
                    desc = "未完成的下载残留：下载到一半被中断的临时文件，可直接删除"
                    label = "未完成下载 " + e.name
                else:
                    desc = "软件更新/安装残留：安装器下载的安装包，装完就不再需要"
                    label = e.name
                items.append({"path": e.path, "size": sz, "kind": "file",
                              "label": label, "desc": desc,
                              "level": "install-residue"})
            except OSError:
                continue


# ----------------------------------------------------------------------------
# v2.9  软件缓存知识库：把「这个文件夹是干什么的 / 清了影响什么」讲清楚
# ----------------------------------------------------------------------------
# 背景：数据盘（E:/F:）跟系统盘完全不同。系统盘大头是临时文件和缓存，
# 数据盘大头是游戏本体、AI 模型、项目和用户资料 —— 这些绝对不能当垃圾清。
# 旧版数据盘扫描器只认几条硬编码路径（E:\Steam\...），实测 E 盘只扫出
# 628KB、F 盘 129 字节，等于完全没用。
#
# 三条铁律（对应「不能随便删东西」）：
#   1. 只有明确命中「已知缓存规则」的目录才会被列为可清理；
#      没认出来的一律不列为可删，最多在总览里标「未识别，建议保留」。
#   2. 模型权重 / 游戏资源包 / 聊天记录 / 个人文件一律 readonly，
#      界面上显示「—」不可勾选，也绝不计入可释放空间。
#   3. 所有软件缓存类目 risk 一律 optional（默认不勾），
#      一键清理（只取 risk == safe）永远不会碰到它们。
#
# 规则字段：
#   pattern  目录段序列；按顺序在路径段里出现即可（允许中间跳过）
#            段名前加 ~ 表示子串匹配（用来认中文目录名，如 ~备份）
#   app      软件名，用于按软件分组
#   what     这个文件夹是做什么的
#   impact   清理后会影响哪些功能  ← 用户最关心的一列
#   advice   建议
#   bucket   clean / rebuild / confirm / protected
# ----------------------------------------------------------------------------

SC_KB = [
    # ===== 第一优先：绝不能删（顺序必须在泛化规则之前）=====
    (('paks',), 'WeGame / 游戏本体',
     '游戏资源包：贴图、模型、关卡、过场动画数据',
     '游戏会打不开或报错，需要重新下载上百 GB。这不是缓存',
     '❌ 不建议清理', 'protected'),
    (('dlcpacks',), 'GTA5 / 游戏本体',
     '游戏 DLC 内容包（每个子目录是一个更新档）',
     '对应 DLC 内容丢失，游戏可能无法启动，要重新下载',
     '❌ 不建议清理', 'protected'),
    (('rail_apps',), 'WeGame 游戏库',
     'WeGame 下载安装的游戏本体目录',
     '等于卸载游戏，需重新下载安装',
     '❌ 不建议清理', 'protected'),
    (('steamapps', 'common'), 'Steam 游戏库',
     'Steam 已安装游戏本体',
     '等于卸载游戏，需重新下载安装',
     '❌ 不建议清理', 'protected'),
    (('comfyui-shared', 'models'), 'ComfyUI',
     'AI 绘画模型权重（diffusion_models / text_encoders / loras / vae）',
     '出图会直接报「模型不存在」；这些模型重新下载要几十 GB，有些已下架',
     '❌ 不建议清理', 'protected'),
    (('ollama_models',), 'Ollama',
     '本地大模型权重（blobs 里是模型本体）',
     '本地 LLM 不能用，要重新 pull 几个 GB 的模型',
     '❌ 不建议清理', 'protected'),
    (('ollama', 'models'), 'Ollama',
     '本地大模型权重目录',
     '本地 LLM 不能用，要重新 pull 模型',
     '❌ 不建议清理', 'protected'),
    (('models', 'blobs'), 'Ollama / AI 模型',
     '模型权重二进制块',
     '对应模型丢失，需重新下载',
     '❌ 不建议清理', 'protected'),
    (('llama.cpp', 'models'), 'llama.cpp',
     'GGUF 量化模型文件',
     '推理时找不到模型，需重新下载',
     '❌ 不建议清理', 'protected'),
    (('ai-models',), 'AI 模型库',
     'AI 模型权重集合',
     '模型丢失，需重新下载',
     '❌ 不建议清理', 'protected'),
    (('wsl',), 'WSL Linux 子系统',
     'WSL 发行版的虚拟磁盘（ext4.vhdx）与 Linux 根文件系统',
     '整个 Linux 环境连同里面装的东西全丢，无法恢复',
     '❌ 不建议清理', 'protected'),
    (('xwechat_files',), '微信',
     '聊天记录里的文件、图片、视频（按月份分目录）',
     '聊天记录里的附件永久丢失，微信里会显示「文件已过期」',
     '❌ 不建议清理', 'protected'),
    (('360movedata',), '360 迁移的用户数据',
     '360「C盘搬家」搬出来的用户目录（含微信/QQ 数据）',
     '是真实用户数据不是缓存，删了聊天记录就没了',
     '❌ 不建议清理', 'protected'),
    (('baidunetdiskdownload',), '百度网盘',
     '从网盘下载到本地的文件',
     '你主动下载的资料会丢失（可能云端也没有了）',
     '❌ 不建议清理', 'protected'),
    (('.git',), 'Git 仓库',
     '版本库元数据：提交历史、分支、暂存区',
     '丢掉全部提交历史，且工作区不再是 Git 仓库',
     '❌ 不建议清理', 'protected'),
    (('~备份',), '个人备份',
     '你手动备份的目录（从名称看是备份）',
     '备份内容永久丢失，无法恢复',
     '❌ 不建议清理', 'protected'),
    (('~录像',), '录像 / 录屏',
     '录制下来的视频文件',
     '录好的视频永久丢失',
     '❌ 不建议清理', 'protected'),
    (('~桌面',), '桌面文件',
     '桌面或桌面备份的文件',
     '个人文件永久丢失',
     '❌ 不建议清理', 'protected'),
    (('~照片',), '照片',
     '照片 / 图片素材',
     '照片永久丢失',
     '❌ 不建议清理', 'protected'),

    # ===== 可放心清理：删了软件会自动重建，不影响数据 =====
    (('psocache',), '三角洲行动 / WeGame',
     'PSO 着色器编译缓存（按游戏版本 + 显卡驱动分目录）',
     '下次进游戏首次加载会卡几秒重新编译着色器；旧驱动版本的目录留着没用',
     '✅ 可清理：旧版本目录尤其该删', 'clean'),
    (('comfyui-cache', 'download-cache'), 'ComfyUI',
     'ComfyUI Desktop 下载的环境包缓存（安装时解压用）',
     '只影响「以后重装 / 修复 ComfyUI 环境」时会重新下载；不影响现在出图',
     '✅ 可清理：已装好的环境不受影响', 'clean'),
    (('workbuddy-cache', 'logs'), 'WorkBuddy',
     '运行日志（sandbox / 会话日志，按日期分目录）',
     '只丢历史日志，排查旧问题时没有记录可查；软件功能不受影响',
     '✅ 可清理：日志会重新生成', 'clean'),
    (('workbuddy-cache', 'traces'), 'WorkBuddy',
     '调用链追踪记录（trace）',
     '只丢历史追踪数据，不影响任何功能',
     '✅ 可清理', 'clean'),
    (('code cache',), '360 / Chrome 系浏览器',
     '浏览器 JS 代码编译缓存',
     '网页首次打开会稍慢一点，缓存自动重建；书签、密码、历史都不受影响',
     '✅ 可清理', 'clean'),
    (('gpucache',), '浏览器',
     '浏览器 GPU 渲染缓存',
     '网页首次渲染稍慢，自动重建',
     '✅ 可清理', 'clean'),
    (('depotcache',), 'Steam',
     'Steam 游戏清单 / 清单缓存',
     'Steam 会自动重新拉取，不影响已装游戏',
     '✅ 可清理', 'clean'),
    (('steamapps', 'downloading'), 'Steam',
     '未完成 / 中断的游戏下载临时文件',
     '会中断正在进行的下载（本来也没下完）；已装好的游戏不受影响',
     '✅ 可清理：确认没有正在下载的游戏', 'clean'),
    (('shadercache',), '显卡 / 游戏',
     '着色器编译缓存',
     '游戏首次加载略慢，之后自动重建',
     '✅ 可清理', 'clean'),
    (('__pycache__',), 'Python',
     'Python 字节码缓存（.pyc）',
     '下次运行 Python 会重新生成，最多首次慢几毫秒',
     '✅ 可清理', 'clean'),
    (('crashdumps',), '软件崩溃转储',
     '程序崩溃时留下的 dump 文件',
     '只丢用于排查崩溃的旧记录，不影响软件运行',
     '✅ 可清理', 'clean'),
    (('thumbnails',), 'Windows / 看图软件',
     '缩略图缓存数据库',
     '文件夹缩略图首次显示会重新生成',
     '✅ 可清理', 'clean'),

    # ===== 可清但会自动重建 / 首次会慢，或需要重新下载 =====
    (('pnpm', 'files'), 'pnpm / Node',
     'pnpm 全局包仓库（所有项目共用的依赖文件）',
     '以后 npm/pnpm install 会重新下载依赖；当前已装好的项目不受影响',
     '🟡 可清理：网络不好时别删', 'rebuild'),
    (('.pnpm-store',), 'pnpm / Node',
     'pnpm 全局依赖仓库',
     '以后装依赖会重新下载；现有项目不受影响',
     '🟡 可清理', 'rebuild'),
    (('npm-cache',), 'npm / Node',
     'npm 下载过的 tarball 缓存',
     '以后装包要重新下载，现有项目不受影响',
     '🟡 可清理', 'rebuild'),
    (('pip', 'cache'), 'pip / Python',
     'pip 下载过的 wheel 安装包缓存',
     '以后 pip install 要重新下载，已装好的库不受影响',
     '🟡 可清理', 'rebuild'),
    (('node_modules',), 'Node 项目',
     '项目依赖包目录',
     '删掉后这个项目跑不起来，必须先 npm install 重装（可能耗时且要联网）',
     '🟠 需确认：确认这个项目不再用了再删', 'confirm'),
    (('.venv',), 'Python 虚拟环境',
     'Python 虚拟环境（含 torch 等大型库）',
     '对应项目跑不起来，要重建 venv 并重装全部依赖（含几个 GB 的 torch）',
     '🟠 需确认：别删正在用的环境', 'confirm'),
    (('standalone-env',), 'ComfyUI',
     'ComfyUI 自带的独立 Python 运行环境',
     'ComfyUI 会打不开，需要修复安装重新下载环境',
     '🟠 需确认：只有卸载 ComfyUI 时才建议删', 'confirm'),
    (('site-packages',), 'Python',
     'Python 第三方库目录',
     '依赖这些库的程序会报错，需 pip install 重装',
     '🟠 需确认', 'confirm'),
    (('modelscope_cache',), 'FunASR / ModelScope',
     '语音识别等模型的本地缓存（SenseVoice、VAD 等）',
     'ASR 功能首次使用会重新下载模型（几百 MB ~ 1GB），期间功能不可用',
     '🟡 可清理：没网时别删', 'rebuild'),
    (('models_cache',), 'AI 语音模型',
     'ASR / 标点模型的本地缓存',
     '语音识别首次使用要重新下载模型，期间功能不可用',
     '🟡 可清理：没网时别删', 'rebuild'),
    (('download-cache',), '软件下载缓存',
     '安装器 / 运行时下载缓存',
     '重装或修复时会重新下载，不影响当前已装好的功能',
     '🟡 可清理', 'rebuild'),
    (('logs',), '各类软件日志',
     '软件运行日志目录',
     '丢历史日志；个别软件靠日志排查问题，但功能一般不受影响',
     '🟠 建议先看一眼里面是什么再删', 'confirm'),

    # ===== 需你确认：名字像缓存，但内容可能有用 =====
    (('workbuddyai-huancun',), 'WorkBuddy AI 缓存',
     '名字叫「缓存」，但实测里面含「数字人一键安装包」等部署包',
     '里面可能是你还需要的安装包 / 部署包，删了要重新找',
     '🟠 请展开确认内容后再决定', 'confirm'),
    (('~huancun',), '自定义缓存目录',
     '以「缓存 / huancun」命名的目录，内容无法自动确认',
     '不确定：可能是纯缓存，也可能放着安装包或项目资料',
     '🟠 请展开确认内容后再决定', 'confirm'),
    (('aihuancun',), 'AI 缓存目录',
     'AI 相关缓存目录，内容无法自动确认',
     '不确定：可能含模型或生成结果',
     '🟠 请展开确认内容后再决定', 'confirm'),
    (('cache', 'pnpm'), 'pnpm / Node',
     'pnpm 全局包仓库（所有项目共用的依赖文件）',
     '以后 npm/pnpm install 会重新下载依赖；当前已装好的项目不受影响',
     '🟡 可清理：网络不好时别删', 'rebuild'),
    (('cache', 'npm'), 'npm / Node',
     'npm 下载缓存（tarball 与元数据）',
     '以后装包要重新下载，现有项目不受影响',
     '🟡 可清理', 'rebuild'),
    (('cache', 'uv'), 'uv / Python',
     'uv 包管理器缓存（已下载的 wheel）',
     '以后装包要重新下载，已装好的库不受影响',
     '🟡 可清理', 'rebuild'),
    (('cache', 'temp'), '临时文件',
     '集中放的临时文件目录',
     '一般可清；若有程序正在写这里的文件会被占用而跳过',
     '🟡 可清理', 'rebuild'),
    (('cache',), '通用缓存目录',
     '名字叫 Cache 的目录（可能是浏览器 / 软件 / 包管理器缓存）',
     '多数可删且会自动重建，但也可能混着配置文件',
     '🟠 请展开确认内容后再决定', 'confirm'),
    (('downloads',), '下载目录',
     '软件下载目录（安装包 / 更新包）',
     '可能还有你没装完或想留着的安装包',
     '🟠 请展开确认内容后再决定', 'confirm'),
    (('360downloads',), '360 软件管家',
     '360 下载的安装包',
     '删了之后想重装软件要重新下载',
     '🟠 可清理：确认包都已安装', 'confirm'),
    (('gameassistant', 'downloads'), '游戏助手',
     '游戏助手下载的更新包 / 安装包',
     '已装完就没用了，但没装完会中断',
     '🟠 可清理：确认没有正在下载', 'confirm'),
    (('liveaihelper', 'downloads'), '直播 AI 助手',
     'LiveAIHelper 下载的依赖与模型包',
     '可能含已下载的模型/依赖，删了首次运行要重下',
     '🟠 请展开确认内容后再决定', 'confirm'),
]

SC_BUCKETS = [
    # v3.0：名字前面的彩色圆点（🟢🟡🟠⚪）全部去掉。
    # Tk 对 emoji 支持不稳会渲染成黑方块，而且用户会把那个圆圈当成
    # 「可以点的单选按钮」，点了没反应就以为勾选坏了 —— 实际勾选框在
    # 右边「选择」列。现在名称前统一由树控件画真正的 ☐ / ☑。
    ('clean', '可放心清理的软件缓存（自动重建，不丢数据）', 'optional',
     '删了会自动重建的缓存：着色器缓存、下载缓存、日志、字节码等。默认不勾，逐项确认。'),
    ('rebuild', '清理后会自动重建 / 需重新下载', 'optional',
     '删了不丢数据，但首次使用会变慢或要联网重新下载依赖与模型。默认不勾。'),
    ('confirm', '需你确认（名字像缓存，内容可能有用）', 'risky',
     '无法自动确认用途的目录，请展开看清路径与说明再决定。默认不勾。'),
    ('protected', '不建议清理（游戏本体 / 模型权重 / 个人数据）', 'readonly',
     '只读展示：这些不是垃圾，删了会造成真实损失。不可勾选，也不计入可释放空间。'),
]

SC_MIN_SIZE = 4 * 1024 ** 2       # 小于 4MB 的碎片目录不列（避免刷屏）


def _kb_match_end(parts, pattern):
    """按顺序在路径段里找齐 pattern，返回「命中时最后一个段的下标」。

    返回 -1 表示没命中。这个下标很关键：它代表规则有多贴近这个目录自身。
    例如 F:////WeGameApps////rail_apps////...////Saved////PSOCache：
      ('rail_apps',)  命中在下标 2  → 只是「在游戏库里」
      ('psocache',)   命中在下标 7  → 这个目录本身就是着色器缓存
    必须选后者，否则 2.1GB 可清的着色器缓存会被当成游戏本体屏蔽掉。

    '~xxx' 前缀表示该段做子串匹配，用来认「桌面备份2026」这类中文目录名。
    """
    j, last = 0, -1
    for i, p in enumerate(parts):
        if j >= len(pattern):
            break
        pat = pattern[j]
        ok = (pat[1:] in p) if pat.startswith('~') else (p == pat)
        if ok:
            j += 1
            last = i
            if j == len(pattern):
                return last
    return -1


def _kb_match(parts, pattern):
    return _kb_match_end(parts, pattern) >= 0


def classify_software_dirs(drive, dir_own):
    """把一次全盘遍历得到的目录体积表，按知识库归类。零额外磁盘 I/O。

    去重写在前面：同一棵子树里父子目录都命中时只留最外层；
    命中「protected」的目录，其所有子目录都不再产出可清理项 —— 防止
    「游戏本体里有个 cache 子目录」被误列成能删的东西。
    """
    root_key = drive.upper() + ':'
    cand = []
    for path, size in dir_own.items():
        if size < SC_MIN_SIZE:
            continue
        parts = [s.lower() for s in str(path).replace('/', '\\').split('\\') if s]
        if len(parts) < 2 or parts[0] == root_key.lower() and len(parts) < 3:
            continue
        # 在所有命中的规则里挑「最贴近这个目录自身」的那条：
        # 命中位置越靠后 > 规则段数越多 > 规则表里越靠前（保护规则优先）。
        best_score, best_rule = None, None
        for idx, rule in enumerate(SC_KB):
            end = _kb_match_end(parts, rule[0])
            if end < 0:
                continue
            score = (end, len(rule[0]), -idx)
            if best_score is None or score > best_score:
                best_score, best_rule = score, rule
        if best_rule is not None:
            pattern, app, what, impact, advice, bucket = best_rule
            cand.append({
                'path': path, 'size': size, 'app': app, 'what': what,
                'impact': impact, 'advice': advice, 'bucket': bucket,
                'depth': len(parts),
            })
    # 深度升序：父目录先处理
    cand.sort(key=lambda x: (x['depth'], x['path'].lower()))
    # kept 记录 (路径, 桶)，只做「同桶父子去重」。
    # 不同桶之间不能互相吃掉：游戏本体(protected) 里的 PSOCache(clean)
    # 是真正能清的着色器缓存，必须照样列出来。
    kept, blocked, out = [], [], []
    for c in cand:
        p = c['path'].lower().rstrip('\\')
        # 被「不建议清理」的祖先保护住了。
        # 例外：clean 桶是明确的缓存规则（PSOCache / __pycache__ / Code Cache），
        # 游戏本体目录里的着色器缓存仍然可清，不该被父目录一起屏蔽。
        if (c['bucket'] != 'clean'
                and any(p == b or p.startswith(b + '\\') for b in blocked)):
            continue
        # 同一个桶内部的父子目录才去重（避免同一份空间被算两次）
        if any((p == k or p.startswith(k + '\\')) and kb == c['bucket']
               for k, kb in kept):
            continue
        if c['bucket'] == 'protected':
            blocked.append(p)
        kept.append((p, c['bucket']))
        out.append(c)
    out.sort(key=lambda x: -x['size'])
    return out


def scan_software_caches(drive, bucket=None):
    """软件缓存清单（复用同一次全盘扫描，不额外遍历）。"""
    r = scan_full_disk(drive)
    items = r.get('software_caches', [])
    if bucket:
        items = [i for i in items if i['bucket'] == bucket]
    out = []
    for c in items:
        protected = c['bucket'] == 'protected'
        out.append({
            'path': c['path'],
            'size': c['size'],
            'kind': 'readonly' if protected else 'dirclean',
            'label': f"[{c['app']}]  {c['path']}",
            'desc': c['what'],
            'impact': c['impact'],
            'advice': c['advice'],
            'app': c['app'],
            'level': c['bucket'],
        })
    return out


def _sc_profile(drive):
    """按软件汇总：这个软件占了多少、其中哪些能清、哪些别碰。只读。"""
    items = scan_full_disk(drive).get('software_caches', [])
    agg = {}
    for c in items:
        a = agg.setdefault(c['app'], {'size': 0, 'n': 0,
                                      'clean': 0, 'caution': 0, 'protected': 0})
        a['size'] += c['size']
        a['n'] += 1
        if c['bucket'] == 'clean':
            a['clean'] += c['size']
        elif c['bucket'] == 'protected':
            a['protected'] += c['size']
        else:
            a['caution'] += c['size']
    out = []
    for app, a in sorted(agg.items(), key=lambda kv: -kv[1]['size']):
        bits = []
        if a['clean']:
            bits.append(f"可放心清 {human_size(a['clean'])}")
        if a['caution']:
            bits.append(f"需确认 {human_size(a['caution'])}")
        if a['protected']:
            bits.append(f"别删 {human_size(a['protected'])}")
        out.append({
            'path': app, 'size': a['size'], 'kind': 'readonly',
            'label': f"{app}　（{a['n']} 个目录）",
            'desc': '按软件汇总的占用',
            'impact': '　·　'.join(bits) or '无可清理项',
            'advice': '📋 只读总览',
            'app': app, 'level': 'profile',
        })
    return out


# ----------------------------------------------------------------------------
# v2.9  顶层目录画像：根目录每个文件夹是干什么的
# ----------------------------------------------------------------------------
# 用户明确要求「把各种文件夹是做什么的正确识别，并且列出来建议」。
# 这一层只做说明，全部 readonly —— 认得出来就给解释，认不出来就老实说
# 「未识别，建议保留」，绝不因为名字陌生就当成垃圾。
# 键：小写目录名；'~xxx' 表示子串匹配。值：(是什么, 清理影响, 建议)
# ----------------------------------------------------------------------------

TOP_DIR_KB = {
    'comfy-desktop': ('ComfyUI Desktop 主目录：程序本体、AI 模型、Python 运行环境',
                      '里面有几十 GB 模型权重，删了要重装并重新下载模型',
                      '❌ 整体保留；只用本工具清其中的 download-cache'),
    'wegameapps': ('WeGame 游戏库：已安装游戏的本体与资源包',
                   '删了等于卸载游戏，重新下载要上百 GB',
                   '❌ 保留；可清里面的 PSOCache 着色器缓存'),
    'steamlibrary': ('Steam 游戏库（游戏本体）', '删了等于卸载游戏', '❌ 保留'),
    'steam': ('Steam 客户端与已安装游戏', '删了客户端和游戏都没了', '❌ 保留'),
    'battle.net': ('暴雪战网客户端与游戏', '删了要重新下载安装', '❌ 保留'),
    'games': ('游戏安装目录', '删了等于卸载游戏', '❌ 保留'),
    'game': ('游戏安装目录', '删了等于卸载游戏', '❌ 保留'),
    'gamedownload': ('游戏下载目录（安装包/更新包）',
                     '可能还有没装完的安装包', '🟠 确认都已安装后可清'),
    'gamevideos': ('游戏录像 / 精彩时刻视频', '删了录像就没了',
                   '❌ 个人录像，建议保留'),
    'gameassistant': ('游戏助手与其下载缓存', '删了要重新下载更新包',
                      '🟠 只建议清里面的 Downloads'),
    'ai-models': ('AI 模型权重集合', '删了要重新下载几十 GB', '❌ 保留'),
    'ai': ('AI 相关目录（模型 / 项目 / 生成结果）', '内容不确定，可能是重要模型或素材',
           '🟠 展开确认后再决定'),
    'llama.cpp': ('llama.cpp 推理程序与 GGUF 模型', '删了本地推理就不能用了',
                  '❌ 保留'),
    'liveaihelper': ('直播 AI 助手项目：Ollama 模型 + 语音模型 + Python 环境',
                     '删了项目跑不起来，模型要重下', '❌ 保留'),
    'locmodel': ('本地模型程序 / 模型文件', '删了相关 AI 功能不可用', '❌ 保留'),
    'workbuddyai': ('WorkBuddy AI 程序本体', '删了软件打不开', '❌ 保留'),
    'workbuddy-cache': ('WorkBuddy 运行缓存：日志与调用追踪',
                        '只丢历史日志，不影响功能', '✅ 可清其中的 logs / traces'),
    'doubao': ('豆包 AI 客户端', '删了要重装', '❌ 保留'),
    'douyin': ('抖音客户端数据', '删了要重装并重新登录', '❌ 保留'),
    'douyinbanlv': ('抖音直播伴侣', '删了直播工具不能用', '❌ 保留'),
    'jianyingpro': ('剪映专业版程序与草稿数据', '删了草稿可能丢失', '❌ 保留'),
    '剪映': ('剪映程序 / 草稿目录', '删了草稿可能丢失', '❌ 保留'),
    'kugou': ('酷狗音乐客户端与下载的音乐', '删了已下载歌曲会没', '❌ 保留'),
    'baidunetdisk': ('百度网盘客户端', '删了要重装', '❌ 保留'),
    'baidunetdiskdownload': ('从百度网盘下载到本地的文件',
                             '你主动下载的资料会丢失', '❌ 保留'),
    'wps software': ('WPS Office 程序目录', '删了 WPS 不能用', '❌ 保留'),
    'tencent': ('腾讯软件数据（QQ / 游戏等）', '可能含聊天记录', '❌ 保留'),
    'sunloginclient': ('向日葵远程控制', '删了远程控制不可用', '❌ 保留'),
    'purevpn': ('PureVPN 客户端', '删了要重装', '❌ 保留'),
    '同花顺': ('同花顺股票软件', '删了自选股/配置可能丢', '❌ 保留'),
    'flashcenter': ('Flash 中心组件', '删了依赖 Flash 的页面打不开', '❌ 保留'),
    'arec': ('录屏软件与录制文件', '删了录制视频会丢', '❌ 保留'),
    'git': ('Git 程序或本地仓库', '删了仓库会丢提交历史', '❌ 保留'),
    '.pnpm-store': ('pnpm 全局依赖包仓库',
                    '以后装依赖要重新下载，现有项目不受影响', '🟡 可清'),
    'cache': ('集中缓存目录（pnpm / npm / uv / temp）',
              '多为可重建缓存，但要按子目录分别确认', '🟡 按子目录清理'),
    'wsl': ('WSL Linux 子系统虚拟磁盘', '整个 Linux 环境连同数据全丢', '❌ 保留'),
    'users': ('用户目录（Windows 用户配置与个人文件）', '含真实个人数据', '❌ 保留'),
    'windows': ('Windows 系统核心目录：系统文件、驱动、组件库与 WinSxS',
                '删了系统无法启动，只能重装；18GB 左右属正常体积',
                '❌ 系统目录 · 禁止整体删除；只清里面的 Temp / 更新缓存'),
    'windows.old': ('升级 Windows 后留下的旧系统备份',
                    '删了不能回退旧版本，但当前系统照常运行',
                    '🟠 确认无需回退后，用系统自带「磁盘清理」删'),
    'winnt': ('旧版 Windows NT 系统目录（或系统镜像 / 备份）',
              '删了相关系统或备份不可用', '❌ 整体保留'),
    'system32': ('Windows 核心系统文件目录', '删了系统立即崩溃', '❌ 禁止清理'),
    'appdata': ('所有已装软件的配置、缓存、登录状态与本地数据',
                '整体删除会让几乎所有软件重置，聊天记录与登录态丢失',
                '❌ 整体保留；只展开清其中的 Cache / Temp'),
    'desktop': ('桌面文件', '删了桌面上的个人文件就没了', '🟠 人工逐个筛选'),
    'documents': ('文档文件夹', '个人文档，删了不可恢复', '❌ 保留'),
    'program files': ('已安装的 64 位程序', '删了等于卸载软件', '❌ 保留'),
    'program files (x86)': ('已安装的 32 位程序', '删了等于卸载软件', '❌ 保留'),
    'programdata': ('程序共享数据', '删了会破坏多个软件', '❌ 保留'),
    'programs': ('自行安装的程序目录', '删了等于卸载', '❌ 保留'),
    '$recycle.bin': ('回收站（本盘）', '清空后文件无法恢复', '✅ 确认无误后清空'),
    '360recyclebin': ('360 回收站', '清空后文件无法恢复', '✅ 确认无误后清空'),
    '360movedata': ('360「C盘搬家」搬出来的用户数据（与当前盘符无关）', '是真实数据，含微信聊天文件',
                    '❌ 保留'),
    '360downloads': ('360 软件管家下载的安装包', '删了重装软件要重新下载',
                     '🟠 确认都已安装后可清'),
    '$360rtlog$': ('360 安全卫士运行日志', '只丢日志', '✅ 可清'),
    '$360rtsys$': ('360 安全卫士系统文件', '删了防护功能可能异常', '❌ 保留'),
    '下载': ('下载文件夹', '里面是你下载的文件，不是缓存', '🟠 人工筛选'),
    'download': ('下载文件夹', '里面是你下载的文件，不是缓存', '🟠 人工筛选'),
    '录像': ('录像 / 录屏文件', '删了录像就没了', '❌ 保留'),
    'screenity': ('Screenity 录屏工具', '删了工具不能用', '❌ 保留'),
    'ecloud': ('天翼云盘客户端 / 同步目录', '删了可能丢同步文件', '❌ 保留'),
    '迅雷云盘': ('迅雷云盘目录', '删了可能丢下载文件', '❌ 保留'),
    'xiangmu': ('项目目录（你的开发项目）', '含源码与模型，删了不可恢复', '❌ 保留'),
    'useaitools_repo': ('useaitools.me 站点仓库', '含源码', '❌ 保留'),
    'mbti-china': ('MBTI 项目目录', '含源码与支付相关代码', '❌ 保留'),
    'godot-dev': ('Godot 开发项目', '含项目源码与资源', '❌ 保留'),
    'airi': ('AIRI 项目目录', '含项目源码与资源', '❌ 保留'),
    'system volume information': ('系统还原点与卷影副本',
                                  '删了无法系统还原，且一般无权限', '❌ 保留'),
    '~dsh': ('DSH 相关项目 / 数据目录', '含项目代码或运行数据', '❌ 保留'),
    '~huancun': ('名称含「缓存」的目录', '名字像缓存但内容需确认',
                 '🟠 展开确认后再决定'),
    '~缓存': ('名称含「缓存」的目录', '名字像缓存但内容需确认',
             '🟠 展开确认后再决定'),
    '~备份': ('个人备份目录', '备份内容删了不可恢复', '❌ 保留'),
    '~桌面': ('桌面文件 / 桌面备份', '个人文件删了不可恢复', '❌ 保留'),
    '~谢萌萌': ('个人工作资料', '个人文件删了不可恢复', '❌ 保留'),
    '~刺客': ('个人项目资料', '个人文件删了不可恢复', '❌ 保留'),
    '~工作': ('个人工作资料', '个人文件删了不可恢复', '❌ 保留'),
}


def _profile_user_name():
    """当前登录用户名。用户主目录名往往就是用户名（本机是 windos），
    静态字典认不出来，必须用 USERPROFILE 动态判断。"""
    p = (os.environ.get('USERPROFILE') or '').rstrip('\\/')
    return os.path.basename(p).lower()


_CURRENT_USER = _profile_user_name()


def _is_user_home_parts(parts):
    """形如 <盘>:\\Users\\<用户名> —— Windows 用户配置文件目录。"""
    return (len(parts) == 3 and parts[1] == 'users'
            and parts[2] not in ('', 'default', 'all users'))


def _top_dir_desc(name, drive=None, path=None):
    """根目录 / 浏览层的用途说明。

    drive 不能省：同一个 Users，在 C 盘是系统自带的用户目录，
    在 E/F 盘才可能是「从 C 盘搬过来的」。
    path 也不能省：展开 Users 后看到的 `windos\\` 是当前用户主目录，
    光看名字认不出来 —— v3.0 曾把它标成「未识别用途」，还允许整目录勾选。
    """
    low = name.lower()
    d = (drive or '').upper()
    p = (path or '').replace('/', '\\').lower().rstrip('\\')
    parts = p.split('\\') if p else []
    is_home = _is_user_home_parts(parts)
    if d == 'C' and _CURRENT_USER and low == _CURRENT_USER:
        is_home = True
    if is_home:
        who = ('当前登录账户' if (d == 'C' and low == _CURRENT_USER)
               else '某个 Windows 账户')
        return (f'Windows 用户主目录（{who}）：桌面、文档、下载、'
                f'AppData 与所有软件配置',
                '整体删除 = 个人文件、聊天记录、浏览器与软件登录态全丢；'
                'NTUSER.DAT 是账户配置单元且正被系统占用，删了账户会损坏',
                '⛔ 已锁定 · 只能展开后挑缓存 / 临时文件清')
    if low in ('users', '用户', 'documents and settings'):
        if d == 'C':
            return ('Windows 用户目录：桌面、文档、下载、AppData 与各软件的个人配置',
                    '含真实个人数据；整体删除会丢桌面文件、聊天记录和软件配置',
                    '❌ 整体保留；点左边箭头逐层展开，挑不需要的再删')
        return ('非系统盘上的 Users 目录：多为从 C 盘迁移 / 备份出来的用户数据',
                '是真实用户数据，不是缓存',
                '❌ 整体保留；可展开逐层查看')
    exact = TOP_DIR_KB.get(low)
    if exact:
        return exact
    for k, v in TOP_DIR_KB.items():
        if k.startswith('~') and k[1:] in low:
            return v
    return ('未识别用途的目录（可能是你的项目、软件或资料）',
            '无法自动判断内容，一律按「建议保留」处理',
            '📋 未识别 · 默认保留')


def classify_top_dirs(drive, dir_own):
    """根目录一级目录画像 + 根目录的系统大文件说明。只读，不产生任何可删项。"""
    out = []
    prefix = drive.upper() + ':\\'
    for path, size in dir_own.items():
        p = str(path)
        if not p.lower().startswith(prefix.lower()) or p == prefix.rstrip('\\'):
            continue
        rel = p[len(prefix):]
        if not rel or '\\' in rel:
            continue
        what, impact, advice = _top_dir_desc(rel, drive, p)
        out.append({
            'path': p, 'size': size, 'kind': 'readonly',
            'label': rel + '\\',
            'desc': what, 'impact': impact, 'advice': advice,
            'app': rel, 'level': 'folders',
            # v3.0：这行可以逐层展开看内容，但顶层目录本身永远不可整体删除
            'browse': True, 'is_dir': True, 'depth': 1,
            'selectable': False,
            'protected': _is_protected_browse(p, drive),
        })
    # 根目录直属的系统大文件：F 盘 pagefile.sys 实测 60GB，
    # 用户往往不知道这 60GB 是什么，必须说清楚。
    for fn, what, impact in (
        ('pagefile.sys', 'Windows 虚拟内存页面文件',
         '系统正在使用，普通删除删不掉；想缩小要在「系统属性 → 高级 → 虚拟内存」里改'),
        ('hiberfil.sys', 'Windows 休眠文件',
         '关休眠（powercfg /hibernate off）才会释放，直接删无效'),
        ('swapfile.sys', 'Windows 交换文件', '系统管理，不要手工删除'),
    ):
        fp = prefix + fn
        try:
            sz = os.path.getsize(fp)
        except OSError:
            continue
        if sz > 1024 ** 2:
            out.append({
                'path': fp, 'size': sz, 'kind': 'readonly',
                'label': fn, 'desc': what,
                'impact': impact,
                'advice': '❌ 系统文件 · 不可清理',
                'app': 'Windows 系统', 'level': 'folders',
                'browse': False, 'is_dir': False, 'selectable': False,
                'protected': True,
            })
    out.sort(key=lambda x: -x['size'])
    return out


# ----------------------------------------------------------------------------
# v3.0 大目录逐层浏览
#
# 用户原话：「这么大的占用，不能展开，不能选择要删除的文件夹或者文件」。
# 只读的用途说明层之前确实既不展开也不能选，用户只能干看着 47.9GB。
#
# 设计底线（不能随便删东西）：
#   · 顶层目录本身（C:\Users 这种）永远不可整体勾选 —— 防一手滑全没
#   · 展开只看一级子项，体积直接查全盘扫描算好的 dir_sizes，零额外读盘
#   · 系统路径硬锁，界面显示「×」且点到也不勾
#   · 所有子项默认不勾，一键清理不碰，清理前逐条列完整路径二次确认
#   · clean_item() 里再挡一次受保护路径，防止界面状态被改错
# ----------------------------------------------------------------------------

BROWSE_LIMIT = 60          # 每层最多列多少项（按体积降序）
BROWSE_MIN_SIZE = 8 * 1024 ** 2
BROWSE_MAX_DEPTH = 4       # 根目录 = 1，最多再往下 3 层

_PROTECTED_SYS_FILES = {
    'pagefile.sys', 'hiberfil.sys', 'swapfile.sys', 'ntuser.dat',
    'ntuser.ini', 'bootmgr', 'ntldr', 'bcd', 'boot.sdi',
}
_PROTECTED_C_ROOTS = (
    'c:\\windows', 'c:\\program files', 'c:\\program files (x86)',
    'c:\\programdata', 'c:\\recovery', 'c:\\boot', 'c:\\efi',
    'c:\\$sysreset', 'c:\\documents and settings',
    'c:\\users\\default', 'c:\\users\\all users',
)
_PROTECTED_SEGMENTS = {
    '$recycle.bin', 'system volume information', 'winsxs',
    'windowsapps', '$sysreset', 'config.msi',
}


def _is_protected_browse(path, drive=None):
    """这些路径下的东西绝不允许在本工具里勾选删除。"""
    # 统一分隔符：os.scandir 给反斜杠，但注册表 / 手填路径可能是正斜杠
    p = (path or '').replace('/', '\\').lower().rstrip('\\')
    if not p:
        return True
    name = p.rsplit('\\', 1)[-1]
    if name in _PROTECTED_SYS_FILES:
        return True
    if any(s in _PROTECTED_SEGMENTS for s in p.split('\\')[1:]):
        return True
    # v3.0.1：用户配置目录。展开 C:\Users 之后看到的 C:\Users\windos
    # 就是当前登录账户的主目录（实测 48.3GB），以前没锁，能整个勾上删掉。
    parts = p.split('\\')
    if len(parts) >= 2 and parts[1] == 'users':
        if len(parts) in (2, 3):
            return True
        if len(parts) == 4 and parts[3] == 'appdata':
            return True
        if (len(parts) == 5 and parts[3] == 'appdata'
                and parts[4] in ('local', 'roaming', 'locallow')):
            return True
    # 任何盘根目录下叫 Windows / WinNT / System32 的目录一律先锁，
    # 数据盘上同名目录多半是系统镜像或备份，也不该被一键端掉。
    if (len(parts) == 2
            and parts[1] in ('windows', 'winnt', 'windows.old', 'system32')):
        return True
    d = (drive or (p[0].upper() if len(p) > 1 and p[1] == ':' else '')).upper()
    if d == 'C':
        for root in _PROTECTED_C_ROOTS:
            if p == root or p.startswith(root + '\\'):
                return True
    return False


def _is_whole_dir_blocked(path):
    """clean_item() 的最后一道闸：不管界面状态怎么错，都不许整体端掉
    用户主目录 / 用户配置 / 系统一级目录。

    只匹配「目录本身」，不影响 C:\\Windows\\Temp、
    C:\\Users\\windos\\AppData\\Local\\Temp 这类深层合法清理项。
    """
    p = (path or '').replace('/', '\\').lower().rstrip('\\')
    if not p:
        return True
    parts = p.split('\\')
    if len(parts) == 2:
        return parts[1] in (
            'users', 'windows', 'winnt', 'windows.old', 'system32',
            'program files', 'program files (x86)', 'programdata')
    if len(parts) == 3 and parts[1] == 'users':
        return True
    if len(parts) == 4 and parts[1] == 'users' and parts[3] == 'appdata':
        return True
    if (len(parts) == 5 and parts[1] == 'users' and parts[3] == 'appdata'
            and parts[4] in ('local', 'roaming', 'locallow')):
        return True
    return False


_FILE_KIND_DESC = (
    (('.iso', '.msi', '.exe', '.zip', '.7z', '.rar'), '安装包 / 压缩包'),
    (('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv'), '视频文件'),
    (('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.heic', '.raw'), '图片文件'),
    (('.mp3', '.flac', '.wav', '.m4a'), '音频文件'),
    (('.gguf', '.safetensors', '.ckpt', '.pt', '.pth', '.bin', '.onnx'),
     'AI 模型权重文件（删了要重新下载 / 训练）'),
    (('.pak', '.ucas', '.utoc', '.wad', '.vpk'), '游戏资源包'),
    (('.log', '.tmp', '.temp', '.dmp', '.old', '.bak'), '日志 / 临时 / 备份文件'),
    (('.psd', '.ai', '.prproj', '.aep'), '设计 / 剪辑工程源文件'),
    (('.vhdx', '.vhd', '.vmdk'), '虚拟磁盘（可能内含完整系统）'),
)


def _browse_file_desc(name):
    ext = os.path.splitext(name)[1].lower()
    for exts, what in _FILE_KIND_DESC:
        if ext in exts:
            return what
    return '普通文件（未识别具体用途）'


def enumerate_browse_dir(drive, path, dir_sizes, depth=2, limit=BROWSE_LIMIT):
    """列出 path 的【一级】子项：体积查全盘扫描表，不递归、不额外读盘。

    返回 (items, total)。子目录带 browse=True，可继续下钻。
    """
    out = []
    try:
        with os.scandir(path) as it:
            entries = list(it)
    except OSError:
        return out, 0
    for e in entries:
        try:
            st = e.stat(follow_symlinks=False)
        except OSError:
            continue
        # 联接点 / 符号链接 / 云端占位符：跟进去会循环，也会重复计体积
        if getattr(st, 'st_file_attributes', 0) & _REPARSE_POINT:
            continue
        try:
            is_dir = e.is_dir(follow_symlinks=False)
        except OSError:
            continue
        size = (dir_sizes or {}).get(e.path, 0) if is_dir else st.st_size
        blocked = _is_protected_browse(e.path, drive)
        if is_dir:
            what, impact, advice = _top_dir_desc(e.name, drive, e.path)
            desc = what
            if blocked:
                impact = '整体删除会造成不可逆的数据 / 系统损坏，本工具已强制锁定'
                advice = '⛔ 已锁定：不可整体删除；可展开后挑里面的缓存'
        else:
            desc = _browse_file_desc(e.name)
            impact = ('系统正在使用，本工具不允许删除'
                      if blocked else '删除后不可恢复（不进回收站）')
            advice = ('系统关键文件 · 禁止清理' if blocked
                      else '⚠ 请核对完整路径后再勾选')
        out.append({
            'path': e.path, 'size': int(size or 0),
            'kind': 'dir' if is_dir else 'file',
            'label': e.name + ('\\' if is_dir else ''),
            'desc': desc, 'impact': impact, 'advice': advice,
            'browse': is_dir and depth < BROWSE_MAX_DEPTH,
            'is_dir': is_dir, 'depth': depth,
            'selectable': not blocked, 'protected': blocked,
        })
    total = len(out)
    out.sort(key=lambda x: -x['size'])
    big = [x for x in out if x['size'] >= BROWSE_MIN_SIZE]
    if len(big) >= 20:            # 小碎文件太多时只显示有意义的，但至少留 20 条
        out = big
    return out[:limit], total


def scan_top_dirs(drive):
    return scan_full_disk(drive).get('top_dirs', [])


def software_cache_categories(drive):
    """数据盘（其实 C 盘也适用）的软件缓存识别类目。"""
    cats = []
    for bucket, name, risk, desc in SC_BUCKETS:
        cats.append({
            'key': 'sc_' + bucket, 'name': name,
            'risk': risk,
            'readonly': risk == 'readonly',
            'per_file': True, 'desc': desc,
            'scan': (lambda b: (lambda d=None: scan_software_caches(d, b)))(bucket),
        })
    cats.append({
        'key': 'sc_folders', 'name': '根目录文件夹用途说明（可逐层展开）',
        'risk': 'optional', 'readonly': True, 'per_file': True,
        'desc': '逐个说明根目录下每个文件夹是干什么的、清理有什么影响；'
                '认不出来的明确标「未识别，默认保留」。'
                '点左边箭头可逐层展开，里面的子文件夹 / 文件可手动勾选删除；'
                '顶层目录本身不可整体删除，系统路径已锁定。',
        'scan': lambda d=None: scan_top_dirs(d),
    })
    cats.append({
        'key': 'sc_profile', 'name': '软件占用总览（只读）',
        'risk': 'optional', 'readonly': True, 'per_file': True,
        'desc': '按软件汇总：谁占了这个盘、哪些能清、哪些别碰。纯信息展示。',
        'scan': lambda d=None: _sc_profile(d),
    })
    return cats


def system_categories():
    return [
        {"key": "temp", "name": "系统临时文件", "risk": "safe",
         "desc": "TEMP 与 Windows\\Temp 中的临时文件，可安全删除",
         "scan": scan_temp},
        {"key": "update", "name": "Windows 更新缓存", "risk": "safe",
         "desc": "已安装更新留下的下载缓存，可安全删除",
         "scan": scan_windows_update},
        {"key": "delivery", "name": "传递优化缓存", "risk": "safe",
         "desc": "系统更新分发残留，可安全删除",
         "scan": scan_delivery_opt},
        {"key": "wer", "name": "Windows 错误报告", "risk": "safe",
         "desc": "WER 错误报告与队列，可安全删除",
         "scan": scan_wer},
        {"key": "recycle", "name": "回收站", "risk": "safe",
         "desc": "各盘回收站中待删除的文件",
         "scan": lambda d=None: scan_recycle(None)},
        {"key": "winlogs", "name": "系统日志缓存", "risk": "safe",
         "desc": "CBS / DISM / WindowsUpdate 日志，可安全删除",
         "scan": scan_windows_logs},
        {"key": "prefetch", "name": "预读取文件", "risk": "optional",
         "desc": "Prefetch 可加快启动；清理后首次启动略慢，按需勾选",
         "scan": scan_prefetch},
        {"key": "thumb", "name": "缩略图缓存", "risk": "optional",
         "desc": "Explorer 缩略图数据库，清理后重新生成，按需勾选",
         "scan": scan_thumbnails},
        {"key": "inetcache", "name": "IE/Edge 临时文件", "risk": "optional",
         "desc": "浏览器临时上网文件，按需勾选",
         "scan": scan_inet_cache},
        {"key": "browser", "name": "浏览器缓存", "risk": "optional",
         "desc": "Chrome / Edge / Firefox 缓存（不清书签与密码），按需勾选",
         "scan": scan_browser_cache},
        {"key": "shadercache", "name": "显卡着色器缓存", "risk": "optional",
         "desc": "NVIDIA / AMD 着色器缓存，清理后游戏首次加载略慢，按需勾选",
         "scan": scan_gpu_shader_cache},
        {"key": "appcache", "name": "应用软件缓存", "risk": "optional",
         "desc": "OneDrive / Teams / 微信 / QQ / Spotify / Adobe 等缓存，按需勾选",
         "scan": scan_app_caches},
        {"key": "store", "name": "应用商店缓存", "risk": "optional",
         "desc": "Microsoft Store 缓存，按需勾选",
         "scan": scan_store_cache},
        {"key": "fontcache", "name": "字体缓存", "risk": "optional",
         "desc": "系统字体缓存，清理后自动重建，按需勾选",
         "scan": scan_font_cache},
        {"key": "iconcache", "name": "图标缓存", "risk": "optional",
         "desc": "Explorer 图标缓存，按需勾选",
         "scan": scan_icon_cache},
        {"key": "wb", "name": "WorkBuddy 日志", "risk": "optional",
         "desc": "WorkBuddy 运行日志，按需勾选",
         "scan": scan_workbuddy_logs},
        {"key": "memdump", "name": "内存转储", "risk": "optional",
         "desc": "Minidump 与 MEMORY.DMP 崩溃转储，按需勾选",
         "scan": scan_mem_dumps},
        {"key": "winold", "name": "Windows.old 备份", "risk": "optional",
         "desc": "系统升级残留的旧系统，删除后无法回退，按需勾选",
         "scan": scan_windows_old},
        {"key": "dl_old", "name": "下载旧文件/安装包", "risk": "risky",
         "desc": "下载文件夹中超过 60 天的安装包/压缩包，确认后删除",
         "scan": lambda d=None: scan_downloads_old('C', 60)},
        {"key": "install_residue", "name": "安装包 / 更新残留 / 未完成下载",
         "risk": "safe",
         "desc": "更新器下载的旧安装包、安装器缓存、没下完就中断的残留；"
                 "装完的程序留着也没用，删了不影响软件运行",
         "scan": lambda d=None: scan_install_residue('C')},
        {"key": "reg_broken", "name": "注册表·无效卸载项", "risk": "risky",
         "desc": "指向不存在程序的卸载残留，清理前需确认",
         "scan": scan_reg_broken_uninstall},
        {"key": "reg_startup", "name": "注册表·失效启动项", "risk": "risky",
         "desc": "指向不存在文件的自启动项，清理前需确认",
         "scan": scan_reg_startup},
        {"key": "reg_mru", "name": "注册表·使用痕迹", "risk": "optional",
         "desc": "最近文档 / 运行历史等痕迹，按需勾选",
         "scan": scan_reg_mru},
    ]


def drive_categories(drive):
    return [
        {"key": "recycle", "name": "回收站", "risk": "safe",
         "desc": f"{drive}: 盘回收站待删除文件",
         "scan": lambda d=None: scan_recycle(drive)},
        {"key": "temp", "name": "临时文件夹", "risk": "safe",
         "desc": f"{drive}: 盘下的 Temp 临时目录",
         "scan": lambda d=None: scan_drive_temp(drive)},
        {"key": "tmpfiles", "name": ".tmp 临时文件", "risk": "optional",
         "desc": f"{drive}: 盘中残留的 .tmp 临时文件，按需勾选",
         "scan": lambda d=None: scan_drive_tmp_files(drive)},
        {"key": "appcache", "name": "应用/游戏缓存", "risk": "optional",
         "desc": f"{drive}: 盘中 Steam / NVIDIA / Unity 等缓存，按需勾选",
         "scan": lambda d=None: scan_drive_app_caches(drive)},
        {"key": "dl_old", "name": "下载旧文件/安装包", "risk": "risky",
         "desc": f"{drive}:\\Downloads 中超过 60 天的安装包/压缩包，确认后删除",
         "scan": lambda d=None: scan_downloads_old(drive, 60)},
    ]


def generic_file_categories(drive):
    """全盘文件扫描类目（所有盘通用，逐目录聚合）。

    关键改动：不再逐个文件列，而是按「所在目录」聚合成组。
    旧版 C 盘会列出 15788 + 11610 + 5000 = 3 万多个文件，
    界面根本没法看。现在压成几百个目录组，
    每组代表「这个目录里的这批垃圾」，一次删干净。
    """
    return [
        {"key": "g_junk", "name": "垃圾扩展名文件（.tmp/.log/.bak…）",
         "risk": "optional",
         "desc": "按目录聚合的残留文件；展开可看到具体是哪些文件，"
                 "删掉只影响这些文件，同目录的其它内容不动",
         "scan": lambda d=None: _agg_junk(d), "per_file": True},
        {"key": "g_large", "name": "大文件 (>500MB，需确认)",
         # 数据盘上 >500MB 的文件几乎全是游戏资源包 / AI 模型权重，
         # 整类勾上删掉要重下上百 GB —— 数据盘一律按风险项处理，
         # 触发二次确认，且默认不勾。
         "risk": "risky" if drive.upper() != "C" else "optional",
         "desc": ("数据盘上的大文件多为游戏资源包 / AI 模型权重，"
                  "删了要重新下载；请逐条确认路径再决定"
                  if drive.upper() != "C" else
                  "超过 500MB 的大文件，请确认非重要后再删"),
         "scan": lambda d=None: scan_all_files(d).get("g_large", []),
         "per_file": True},
        {"key": "g_old", "name": "长期未使用文件 (>1年，需确认)",
         "risk": "optional",
         "desc": "超过 1 年未修改的文件，按目录聚合；"
                 "建议先看「空间分析」确认这些是什么再决定",
         "scan": lambda d=None: _agg_old(d), "per_file": True},
        {"key": "g_dup", "name": "重复文件 (内容相同)",
         "risk": "optional",
         "desc": "内容完全相同的重复文件，保留原件删副本，逐个决定",
         "scan": lambda d=None: scan_all_files(d).get("g_dup", []),
         "per_file": True},
        {"key": "g_empty", "name": "空文件夹",
         "risk": "optional",
         "desc": "没有任何内容的空文件夹（按目录聚合），"
                 "删了不占空间、只让目录干净点",
         "scan": lambda d=None: _agg_empty(d),
         "per_file": True},
    ]


def _agg_empty(drive):
    """空文件夹 → 按父目录聚合（空文件夹占 0 字节，列 5000 行没意义）。"""
    items = scan_empty_dirs(drive)
    groups = {}
    for it in items:
        p = it.get("path", "")
        if not p:
            continue
        parent = os.path.dirname(p)
        groups.setdefault(parent, []).append(p)
    out = []
    for parent, paths in groups.items():
        out.append({
            "path": parent,
            "size": 0,
            "kind": "files",
            "paths": paths,
            "count": len(paths),
            "label": f"{parent}（{len(paths)} 个空文件夹）",
            "desc": f"该目录下有 {len(paths)} 个空文件夹，可一并删掉",
        })
    out.sort(key=lambda x: -x["count"])
    return out[:200]


def _agg_junk(drive):
    """垃圾扩展名文件 → 按目录聚合。"""
    items = scan_all_files(drive).get("g_junk", [])
    return group_items_by_dir(items, noun="个残留文件")


def _agg_old(drive):
    """长期未使用文件 → 按目录聚合。"""
    items = scan_all_files(drive).get("g_old", [])
    return group_items_by_dir(items, noun="个旧文件")


def get_categories(drive):
    inv = inventory_categories(drive)
    # v2.9：软件缓存识别对数据盘尤其重要（那里没有 Windows 临时文件可清）
    sc = software_cache_categories(drive)
    if drive.upper() == 'C':
        return system_categories() + sc + generic_file_categories(drive) + inv
    return sc + drive_categories(drive) + generic_file_categories(drive) + inv


RISK_BADGE = {
    "safe": ("安全·自动", "#1a7f37"),
    "optional": ("可选·默认不勾", "#b58100"),
    "risky": ("风险·需确认", "#c0392b"),
}


# ----------------------------------------------------------------------------
# 清理分发
# ----------------------------------------------------------------------------

def item_size(item):
    """估算一个待删项目实际占多少字节（清理前调用，删完就量不到了）。"""
    kind = item.get("kind")
    if kind == "files":
        return sum(safe_size(p) for p in item.get("paths", [])
                   if os.path.isfile(p))
    return int(item.get("size", 0) or 0)


def clean_item(item):
    """返回 True 表示确实清理成功；False 表示失败（如文件被系统锁定）。"""
    kind = item.get("kind")
    # v3.0.1 最后一道闸：用户主目录 / AppData / 系统一级目录永远不许整体删。
    # 界面已锁，这里防止旧状态、缓存清单或手工构造的项绕过界面。
    whole = item.get("path")
    if whole and _is_whole_dir_blocked(whole):
        return False
    if kind == "readonly":
        # 只读展示项（游戏本体 / 模型权重 / 个人数据 / 软件总览）
        # 永远不许进入删除路径 —— 哪怕界面状态被改错。
        return False
    if item.get("browse") and _is_protected_browse(item.get("path", "")):
        # v3.0：大目录浏览选出来的项，删之前再挡一次系统路径。
        # 界面已经锁了，这里防止状态被改错 / 手工构造清单时绕过。
        return False
    if kind == "dir":
        return force_rmtree(item["path"])
    elif kind == "dirclean":
        # 清空目录内容但保留目录本身（Temp / 缓存目录要用这种）
        return clear_dir_contents(item["path"])
    elif kind == "file":
        return force_remove_file(item["path"])
    elif kind == "files":
        # 聚合组：一个目录里的若干个文件。
        # 逐个 os.remove 对 1 万多个文件很慢，
        # 所以先按目录分组，用一条 del 命令批量删同目录的文件。
        ok = True
        paths = item.get("paths", [])
        by_dir = {}
        for p in paths:
            by_dir.setdefault(os.path.dirname(p), []).append(p)
        for parent, group in by_dir.items():
            if not group:
                continue
            files = [p for p in group if os.path.isfile(p)]
            dirs = [p for p in group if os.path.isdir(p)]
            if files:
                ok = _delete_files_batch(files) and ok
            for d in dirs:
                ok = force_rmtree(d) and ok
        return ok
    elif kind == "edir":
        try:
            if os.path.isdir(item["path"]) and not os.listdir(item["path"]):
                return force_rmtree(item["path"])
        except OSError:
            return False
        return False
    elif kind == "recycle":
        drive = item.get("drive")
        if drive:
            run_powershell(
                f"Clear-RecycleBin -DriveLetter {drive} -Force "
                f"-ErrorAction SilentlyContinue", timeout=180)
        else:
            run_powershell("Clear-RecycleBin -Force -ErrorAction SilentlyContinue",
                           timeout=180)
        return True
    elif kind == "command":
        try:
            subprocess.run(item.get("cmd", ""), shell=True, capture_output=True,
                           timeout=180, **_NO_WINDOW_KW)
            return True
        except Exception:
            return False
    elif kind == "reg":
        clean_reg(item)
        return True
    return False


# ----------------------------------------------------------------------------
# 主界面
# ----------------------------------------------------------------------------

class CleanMasterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("电脑清理大师  ·  xiaomo945")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 660)

        # ---- GC 调优（GUI 性能关键）----
        # 扫描一��盘会产生几十万个小对象（每条扫描结果都是一个 dict），
        # Python 的分代 GC 会频繁触发 full collection，
        # 每次都要遍历这些对象 —— 结果是「点一下类目就卡 3 秒」。
        # 这里把阈值调高并冻结已扫描完的对象：
        #   · 提高阈值  → 少触发 full GC
        #   · freeze()  → 已存活的对象不再参与扫描
        #   · disable() → 扫描期间完全不让 GC 打断 Tk
        # 扫描结束后再恢复（见 _gc_resume）。
        gc.collect()
        gc.freeze()
        gc.set_threshold(50000, 100, 100)

        self.q = queue.Queue()
        self.scanning = False
        self.cleaning = False
        self.stop_flag = threading.Event()   # 用户点击「停止」时置位
        self.cat_widgets = {}          # key -> dict(var, frame, ...)
        self.results_by_drive = {}     # drive -> {key: {items, size, meta, per_file}}
        self.checked_by_drive = {}     # drive -> {key: bool}
        # v3.0：树的行文本（不含 ☐ 前缀）与「大目录逐层浏览」状态
        self.row_text = {}             # iid -> 原始名称
        self.browse_nodes = {}         # iid -> {item, drive, loaded}
        self.browse_by_drive = {}      # drive -> {"sel": set(path), "items": {path: item}}
        self._browse_seq = 0
        self.drives = get_fixed_drives()
        self.current_drive = self.drives[0] if self.drives else "C"

        self.build_ui()
        self.refresh_free_space()
        # 常驻消息轮询（自续期，只启动一次）
        self.root.after(80, self.poll)
        self.refresh_admin_banner()

    # ------------------------- 提权相关 -------------------------
    def refresh_admin_banner(self):
        """更新顶部的权限提示条（提权按钮的显示与否）。

        用 self._elev_shown 标记状态，而不是 winfo_ismapped()——
        后者在窗口隐藏时恒为 False，会导致显隐逻辑错乱。
        """
        if is_admin():
            self.admin_label.config(
                text="✓ 已以管理员身份运行，可完整清理（含注册表与系统目录）",
                foreground="#1a7f37")
            if self._elev_shown:
                self._elev_shown = False
                self.elev_btn.pack_forget()
        else:
            self.admin_label.config(
                text="⚠ 当前未以管理员身份运行：用户目录下的文件可以正常清理，"
                     "但注册表(HKLM)与系统目录里的项目会被跳过。",
                foreground="#b58100")
            if not self._elev_shown:
                self._elev_shown = True
                self.elev_btn.pack(side="right")

    def on_elevate(self):
        """点了「以管理员身份重启」→ 拉起一个管理员实例，自己退出。"""
        if is_admin():
            return
        if not messagebox.askyesno(
                "以管理员身份重启",
                "接下来的清理需要管理员权限才能处理注册表(HKLM)"
                "和系统目录里的文件。\n\n"
                "是否以管理员身份重新启动本程序？\n"
                "（当前窗口会自动关闭）"):
            return
        if relaunch_as_admin():
            self.root.after(200, self.root.destroy)
        else:
            messagebox.showwarning(
                "提权未成功",
                "没能以管理员身份启动（可能 UAC 被拒绝，或被安全软件拦截）。\n\n"
                "你可以继续清理当前用户目录下的文件，"
                "注册表与系统目录里的项目会被自动跳过。")
    # ------------------------- UI -------------------------
    def build_ui(self):
        hdr = ttk.Frame(self.root)
        hdr.pack(fill="x", padx=12, pady=(10, 0))
        t = ttk.Label(hdr, text="电脑清理大师", font=("Microsoft YaHei", 18, "bold"))
        t.pack(side="left")
        sub = ttk.Label(hdr, text="  v3.0.2  ·  作者 xiaomo945",
                        font=("Microsoft YaHei", 10))
        sub.pack(side="left", padx=(6, 0), pady=(8, 0))
        self.free_label = ttk.Label(hdr, text="", font=("Microsoft YaHei", 10),
                                    foreground="#555")
        self.free_label.pack(side="right")
        # 当前盘信息（refresh_free_space 会更新它）
        self.drive_info_label = ttk.Label(hdr, text="",
                                           font=("Microsoft YaHei", 9),
                                           foreground="#777")
        self.drive_info_label.pack(side="right", padx=(0, 14))

        arow = ttk.Frame(self.root)
        arow.pack(fill="x", padx=12, pady=(2, 0))
        self.admin_label = ttk.Label(arow, text="",
                                     font=("Microsoft YaHei", 9))
        self.admin_label.pack(side="left")
        self.elev_btn = ttk.Button(arow, text="以管理员身份重启",
                                   command=self.on_elevate, width=16)
        self._elev_shown = False     # 提权按钮当前是否已 pack

        ctrl = ttk.Frame(self.root)
        ctrl.pack(fill="x", padx=12, pady=6)
        ttk.Label(ctrl, text="选择盘符：", font=("Microsoft YaHei", 10)).pack(
            side="left")
        self.drive_var = tk.StringVar(value=self.current_drive)
        self.drive_cb = ttk.Combobox(
            ctrl, values=self.drives, textvariable=self.drive_var,
            state="readonly", width=6)
        self.drive_cb.pack(side="left", padx=(0, 8))
        self.drive_cb.bind("<<ComboboxSelected>>", self.on_drive_change)
        self.scan_btn = ttk.Button(ctrl, text="扫描此盘", command=self.start_scan,
                                   width=10)
        self.scan_btn.pack(side="left", padx=(0, 6))
        self.scan_all_btn = ttk.Button(ctrl, text="扫描全部盘",
                                       command=self.start_scan_all, width=10)
        self.scan_all_btn.pack(side="left", padx=(0, 8))
        self.clean_btn = ttk.Button(ctrl, text="确认清理", command=self.confirm_clean,
                                    width=14, state="disabled")
        self.clean_btn.pack(side="left")
        # 「一键清理」：商业清理软件的标准动作 ——
        # 只清理「安全类」且已勾选的项目，不用用户逐项挑。
        self.quick_btn = ttk.Button(ctrl, text="⚡ 一键清理",
                                    command=self.quick_clean, width=12,
                                    state="disabled")
        self.quick_btn.pack(side="left", padx=(6, 0))
        self.progress = ttk.Progressbar(ctrl, mode="indeterminate", length=180)
        self.progress.pack(side="left", padx=10)
        self.status_label = ttk.Label(
            ctrl, text="选好盘符 → 点「扫描此盘」",
            font=("Microsoft YaHei", 9), foreground="#555")
        # 状态文字要留足空间（以前被进度条挤到只剩「选好盘符 → 点」）
        self.status_label.pack(side="left", padx=(6, 0), fill="x", expand=True)
        # 停止按钮：放在独立的右对齐容器里，位置固定，扫描/清理时才显示
        self.stop_holder = ttk.Frame(ctrl)
        self.stop_holder.pack(side="right", padx=(8, 0))
        self.stop_btn = ttk.Button(self.stop_holder, text="■ 停止",
                                   command=self.stop_scan, width=9)

        self.res_frame = ttk.LabelFrame(
            self.root,
            text="扫描结果（分组 → 类别 → 文件夹　·　点方框 / 点名称 = 勾选　·　"
                 "点左边箭头或双击 = 展开 / 收起　·　大目录可逐层展开后手动挑着删）")
        self.res_frame.pack(fill="both", expand=True, padx=12, pady=(4, 6))
        res_frame = self.res_frame

        # v3.0.2：清理结果直接写在界面里，不再弹「完成」窗口。
        # 默认隐藏，清理完成后插到结果区上方显示。
        self.result_banner = ttk.Label(
            self.root, text="", anchor="w", wraplength=1100,
            font=("Microsoft YaHei", 10, "bold"),
            foreground="#0a6b2e", padding=(10, 4))

        # ---- Treeview 分层树 ----
        # 为什么用 Treeview：旧版每条文件要建 4 个 ttk 控件，
        # 展开一个类目就几千个控件，Tk 直接卡死。
        # Treeview 是单控件，��部数据存内存、只渲染可见行，
        # 展开上万条也流畅。
        cols = ("sel", "size", "desc", "impact")
        self.tree = ttk.Treeview(res_frame, columns=cols, show="tree headings",
                                 selectmode="none")
        # v3.0 根因修复：identify_column() 里 #0 是树列，第一个数据列是 #1。
        # 旧版写死 "#2"（其实是「大小」列），于是点「选择」列的方框
        # 永远进不了勾选逻辑 —— 用户看到的就是「按钮不能打勾」。
        # 这里按列名算，以后调整列顺序也不会再错位。
        self.sel_col = "#%d" % (list(cols).index("sel") + 1)
        self.tree.heading("#0", text="项目 / 文件夹")
        self.tree.heading("sel", text="选择")
        self.tree.heading("size", text="大小")
        self.tree.heading("desc", text="这个文件夹是什么")
        self.tree.heading("impact", text="清理后会影响什么功能 / 建议")
        self.tree.column("#0", width=310, minwidth=160, stretch=True)
        self.tree.column("sel", width=42, minwidth=42, stretch=False,
                         anchor="center")
        self.tree.column("size", width=86, minwidth=70, stretch=False,
                         anchor="e")
        self.tree.column("desc", width=270, minwidth=100, stretch=True)
        self.tree.column("impact", width=330, minwidth=140, stretch=True)

        tvsb = ttk.Scrollbar(res_frame, orient="vertical",
                              command=self.tree.yview)
        thsb = ttk.Scrollbar(res_frame, orient="horizontal",
                              command=self.tree.xview)
        self.tree.configure(yscrollcommand=tvsb.set, xscrollcommand=thsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        tvsb.grid(row=0, column=1, sticky="ns")
        thsb.grid(row=1, column=0, sticky="ew")
        res_frame.rowconfigure(0, weight=1)
        res_frame.columnconfigure(0, weight=1)

        # 配色：已勾选 / 未勾选 / 分组标题 / 只读
        self.tree.tag_configure("on", foreground="#0a6b2e")
        self.tree.tag_configure("off", foreground="#333")
        self.tree.tag_configure("grp", foreground="#1a4d8f",
                                font=("Microsoft YaHei", 10, "bold"))
        self.tree.tag_configure("ro", foreground="#777")
        self.tree.tag_configure("more", foreground="#1a73c7")
        self.tree.tag_configure("note", foreground="#8a6d1f")

        self.tree.bind("<Double-1>", self.on_tree_double)
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<<TreeviewOpen>>", self.on_tree_open)
        # 展开箭头在某些 Tk 版本下不发 <<TreeviewOpen>>，
        # 这里只负责「补做懒加载」，绝不改写 open 状态 —— 旧版无条件
        # 设成 open=True，导致用户点减号收起时又被强行展开，收不回去。
        self.tree.bind("<ButtonRelease-1>", self._maybe_expand)

        self.empty_hint = ttk.Label(self.root,
                                    text="（尚未扫描，点击「开始扫描」）",
                                    foreground="#999")

        # ---- 结果区工具栏 ----
        tools = ttk.Frame(self.root)
        tools.pack(fill="x", padx=12, pady=(0, 2))
        ttk.Label(tools, text="结果区：", font=("Microsoft YaHei", 9),
                  foreground="#666").pack(side="left")
        ttk.Button(tools, text="全部展开", command=self.expand_all,
                   width=9).pack(side="left", padx=(0, 4))
        ttk.Button(tools, text="全部收起", command=self.collapse_all,
                   width=9).pack(side="left", padx=(0, 4))
        ttk.Button(tools, text="只看已勾选", command=self.show_only_checked,
                   width=11).pack(side="left", padx=(0, 4))
        ttk.Button(tools, text="全选/全不选",
                   command=self.toggle_all_categories, width=11).pack(side="left")
        self.tree_tip = ttk.Label(tools, text="",
                                  font=("Microsoft YaHei", 9), foreground="#888")
        self.tree_tip.pack(side="right")

        # ---- 磁盘占用条（商业清理软件的标准元素）----
        # 一眼看出：这个盘被占了多少、垃圾占多少、还剩多少。
        self.bar_frame = ttk.Frame(self.root)
        self.bar_frame.pack(fill="x", padx=12, pady=(0, 4))
        self.bar = tk.Canvas(self.bar_frame, height=16,
                             highlightthickness=0, bd=0)
        self.bar.pack(fill="x")
        self.bar.bind("<Configure>", lambda e: self._draw_bar())
        self.bar_tip = ttk.Label(self.bar_frame, text="",
                                 font=("Microsoft YaHei", 9),
                                 foreground="#666")
        self.bar_tip.pack(anchor="w")

        sum_frame = ttk.Frame(self.root)
        sum_frame.pack(fill="x", padx=12, pady=(0, 4))
        self.summary_label = ttk.Label(sum_frame, text="已勾选可释放：—",
                                       font=("Microsoft YaHei", 11, "bold"))
        self.summary_label.pack(side="left", fill="x", expand=True)
        self.max_label = ttk.Label(sum_frame, text="",
                                   font=("Microsoft YaHei", 9),
                                   foreground="#555")
        self.max_label.pack(side="right")

        log_frame = ttk.LabelFrame(self.root, text="运行日志")
        log_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        self.log_box = scrolledtext.ScrolledText(
            log_frame, height=6, font=("Consolas", 9), state="disabled",
            wrap="word")
        self.log_box.pack(fill="both", expand=True, padx=4, pady=4)

        self.tree.bind("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.tree.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ------------------------- 磁盘占用条 -------------------------
    def _draw_bar(self):
        """画磁盘占用条：已用 / 可清理 / 空闲 三段。

        商业清理软件都有这个条 —— 一眼看出这个盘到底还有多少空间、
        里面有多少是能清出来的垃圾。比一个数字有信息量得多。
        """
        if not hasattr(self, "bar"):
            return
        c = self.bar
        c.delete("all")
        w = c.winfo_width()
        if w <= 1:
            return
        free, total = get_drive_space(self.current_drive)
        if total <= 0:
            return
        used = max(0, total - free)
        # 可清理的空间（安全类 + 已勾选的）
        reclaim = 0
        try:
            reclaim = int(self._bar_reclaim())
        except Exception:
            reclaim = 0
        reclaim = max(0, min(reclaim, used))

        x = 0
        segs = [
            (used - reclaim, "#c8cdd4", "已用"),
            (reclaim, "#e8a33d", "可清理"),
            (free, "#3d9be9", "空闲"),
        ]
        for size, color, name in segs:
            seg_w = int(w * size / total)
            if seg_w <= 0:
                continue
            c.create_rectangle(x, 0, x + seg_w, 16, fill=color, outline="")
            x += seg_w
        self.bar_tip.config(
            text=f"{self.current_drive}: 盘 共 {human_size(total)}　"
                 f"已用 {human_size(used)}　"
                 f"可清理 {human_size(reclaim)}　"
                 f"空闲 {human_size(free)}")

    def _bar_reclaim(self):
        """占用条里「可清理」那一段该画多大。"""
        if not self.cat_widgets:
            return 0
        pairs = []
        for key in list(self.cat_widgets.keys()):
            cw = self.cat_widgets[key]
            if cw.get("readonly"):
                continue
            rec = self.results_by_drive.get(self.current_drive, {}).get(key, {})
            meta = rec.get("meta", {})
            _, sel = self._cat_state(key)
            if sel:
                pairs.extend((it.get("path", ""), it.get("size", 0)) for it in sel)
            elif meta.get("risk") == "safe":
                for it in rec.get("items", []) or []:
                    pairs.append((it.get("path", ""), it.get("size", 0)))
        pairs.extend((it.get("path", ""), it.get("size", 0))
                     for it in self._browse_picks())
        return _dedup_size(pairs)

    # ------------------------- 结果区工具栏 -------------------------
    def expand_all(self):
        """展开所有类目，每类只显示前 PAGE 条。

        旧版一次铺 4 万行，界面假死好几秒。
        现在每类最多 DISPLAY_PAGE 条 —— 一屏能看全，
        想看更多的可以点那一类下面的「还有 N 项」继续加载。
        """
        n = 0
        for key in list(self.cat_widgets.keys()):
            cw = self.cat_widgets[key]
            if cw.get("readonly") or not cw.get("items"):
                continue
            if not cw.get("loaded"):
                self._load_children(key)
            iid = cw["iid"]
            if self.tree.exists(iid):
                self.tree.item(iid, open=True)
            n += 1
        self.tree_tip.config(
            text=f"已展开 {n} 个类别（每类最多显示 {self.PAGE} 条，"
                 f"点「还有 N 项」可继续加载）")

    def collapse_all(self):
        """收起所有类目（只收树上的显示状态，不动选择）。"""
        for gnode in self.tree.get_children(""):
            if gnode.startswith("g:"):
                self.tree.item(gnode, open=False)
            for cnode in self.tree.get_children(gnode):
                if cnode.startswith("c:"):
                    self.tree.item(cnode, open=False)
        self.tree_tip.config(text="已全部收起")

    def show_only_checked(self):
        """只看已勾选：把未勾选的类目折叠/淡化，方便核对要删什么。

        再次点击恢复全部显示。
        """
        if getattr(self, "_only_checked", False):
            self._only_checked = False
            for cnode in self._all_category_nodes():
                if cnode.startswith("c:"):
                    self._load_children(cnode[2:])
                self.tree.item(cnode, open=True)
            self.tree_tip.config(text="已恢复全部显示")
            return
        self._only_checked = True
        shown = 0
        for key, cw in self.cat_widgets.items():
            iid = cw.get("iid")
            if not iid or not self.tree.exists(iid):
                continue
            _, sel = self._cat_state(key)
            if sel:
                shown += 1
                self._load_children(key)
                self.tree.item(iid, open=True)
                self.tree.item(iid, tags=("on",))
            else:
                self.tree.item(iid, open=False)
                self.tree.item(iid, tags=("off",))
        self.tree_tip.config(text=f"只看已勾选：{shown} 个类别有勾选")

    def _all_category_nodes(self):
        out = []
        for gnode in self.tree.get_children(""):
            for cnode in self.tree.get_children(gnode):
                if cnode.startswith("c:"):
                    out.append(cnode)
        return out

    def toggle_all_categories(self):
        """一键全选 / 全不选所有可清理的类目（只读的除外）。"""
        cats = [k for k, cw in self.cat_widgets.items()
                if not cw.get("readonly") and cw.get("items")]
        if not cats:
            return
        # 只要还有任一类是「开」的，就整体全不选；否则整体全选
        all_on = all(self.cat_widgets[k].get("master", False) for k in cats)
        target = not all_on
        for k in cats:
            cw = self.cat_widgets[k]
            cw["master"] = target
            cw["sel"] = {}
            cw["mark"] = "☑" if target else "☐"
            iid = cw["iid"]
            if self.tree.exists(iid):
                self._row_mark(iid, cw["mark"], "on" if target else "off")
            # 同步已渲染的子行（逐行 set，比删掉重建快 5 倍）
            shown = cw.get("shown", 0)
            if shown:
                mark = "☑" if target else "☐"
                tg = "on" if target else "off"
                for i in range(shown):
                    child = f"i:{k}:{i}"
                    if (self.tree.exists(child)
                            and self.tree.set(child, "sel") not in ("—", "×")):
                        self._row_mark(child, mark, tg)
        self.on_selection_changed()
        self.tree_tip.config(text="已全选" if target else "已全不选")

    # ------------------------- 日志 / 空间 -------------------------
    def _notice(self, text):
        """界面内提示：状态栏 + 日志，不弹任何窗口。

        v3.0.2 用户要求「点一键清理时只弹一次窗」——
        扫描中 / 未扫描 / 没有可清项这些提示一律改为界面内文字。
        """
        first = (text or "").strip().split("\n")[0]
        self.status_label.config(text=first[:80])
        self.tree_tip.config(text=first[:60])
        for line in (text or "").split("\n"):
            self.log("  " + line)

    def _show_clean_result(self, text, brief=None):
        """清理完成结果写进顶部结果条 + 日志，不再弹「完成」窗口。"""
        short = brief or "  ".join(
            x.strip() for x in (text or "").split("\n") if x.strip())[:170]
        self.result_banner.config(text="✓ " + short)
        if not self.result_banner.winfo_manager():
            self.result_banner.pack(fill="x", padx=12, pady=(2, 0),
                                    before=self.res_frame)
        for line in (text or "").split("\n"):
            self.log(line)

    def log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def refresh_free_space(self):
        free, total = get_drive_space(self.current_drive)
        self.free_label.config(
            text=f"{self.current_drive}: 盘剩余 {human_size(free)} / 共 {human_size(total)}")
        self.drive_info_label.config(
            text=f"当前显示：{self.current_drive}: 盘（共 {len(self.drives)} 个盘）")
        try:
            self._draw_bar()
        except Exception:
            pass

    # ------------------------- 扫描 -------------------------
    def start_scan(self):
        """只扫当前选中的盘 —— 一个盘一个盘来，不扫整个电脑。"""
        self._begin_scan([self.drive_var.get()])

    def start_scan_all(self):
        """扫描所有固定盘（用户明确要全扫时才用）。"""
        self._begin_scan(list(self.drives))

    def _begin_scan(self, drives):
        if self.scanning or self.cleaning:
            return
        self.scanning = True
        self.scan_drives = list(drives)
        self.stop_flag.clear()
        self.scan_btn.config(state="disabled")
        self.scan_all_btn.config(state="disabled")
        self.clean_btn.config(state="disabled")
        self.stop_btn.pack(side="left", padx=(0, 4))
        self.clear_results()
        self.progress.config(mode="indeterminate")
        self.progress.start(15)
        if len(drives) == 1:
            self.status_label.config(text=f"正在扫描 {drives[0]}: 盘…")
            self.log(f"=== 开始扫描 {drives[0]}: 盘 ===")
        else:
            self.status_label.config(text=f"正在扫描 {len(drives)} 个磁盘…")
            self.log(f"=== 开始扫描（共 {len(drives)} 个盘）===")
        threading.Thread(target=self.scan_worker, daemon=True).start()

    def stop_scan(self):
        if not (self.scanning or self.cleaning):
            return
        self.stop_flag.set()
        self.status_label.config(text="正在停止…（等当前目录扫完）")
        self.log("■ 已请求停止，等待当前操作结束…")

    def scan_worker(self):
        """后台扫描线程：逐盘扫描，每扫完一个盘立刻把结果发给界面。

        扫描期间完全关掉 GC —— 一盘会产生几十万个小对象，
        GC 一旦触发 full collection 就要遍历它们，
        那期间界面会明显卡顿（实测点一下类目能卡 3 秒）。
        """
        _FULL_CACHE.clear()
        gc_was_enabled = gc.isenabled()
        gc.disable()
        try:
            for drive in getattr(self, "scan_drives", None) or self.drives:
                if self.stop_flag.is_set():
                    self.q.put(("log", "■ 已被用户停止"))
                    break
                self.q.put(("log", f"--- 扫描 {drive}: 盘 ---"))
                # 一次遍历产出全部清单（垃圾 / 类型归类 / 最大文件夹 / 空文件夹…）
                self.q.put(("status", f"正在遍历 {drive}: 盘 · 分析文件…"))
                last = [0.0]
                last_log = [0.0]

                def on_progress(files, nbytes, cur_dir, _d=drive):
                    now = time.time()
                    if now - last[0] < 0.2:
                        return
                    last[0] = now
                    short = cur_dir[-46:] if cur_dir else ""
                    self.q.put(("scan_progress", files, nbytes, short))
                    # 日志每 8 秒给一条，让用户看到扫描在推进（不是卡死）
                    if now - last_log[0] >= 8:
                        last_log[0] = now
                        self.q.put(("log", f"  扫描中… 已扫描 {files:,} 个文件 · "
                                           f"{human_size(nbytes)} · {short}"))

                try:
                    scan_full_disk(drive, progress_cb=on_progress,
                                   should_stop=self.stop_flag.is_set)
                except Exception as e:
                    self.q.put(("log", f"  磁盘分析出错: {e}"))
                stopped_here = self.stop_flag.is_set()
                inv = {k: v for k, v in _FULL_CACHE.get(drive, {}).items()
                       if k.startswith('inv_')}
                self.q.put(("log",
                            f"  （{drive}: 盘共统计 "
                            f"{_FULL_CACHE.get(drive, {}).get('_file_count', 0)} 个文件，"
                            f"系统/程序占用 "
                            f"{human_size(inv.get('inv_system_total', 0))}）"))
                cats = get_categories(drive)
                store = {}
                for cat in cats:
                    self.q.put(("status", f"正在扫描 {drive}: 盘 · {cat['name']}"))
                    try:
                        items = cat["scan"](drive)
                    except Exception as e:
                        items = []
                        self.q.put(("log", f"  扫描『{cat['name']}』出错: {e}"))
                    if cat.get("readonly"):
                        # 只读类目显示「自己这一类」占多大。
                        # 旧版所有只读类目都填 inv_system_total（33.7GB），
                        # 结果十几个类目全是同一个数字 —— 毫无意义还误导人。
                        if cat["key"] == "inv_system":
                            size = inv.get("inv_system_total", 0)
                        else:
                            size = _dedup_size(
                                [(i.get("path", ""), i.get("size", 0))
                                 for i in items])
                    else:
                        # 去重后再算：父目录与它内部的子目录不能重复累加，
                        # 否则「最大的文件夹排行」会算出 399GB 这种虚高数字
                        size = _dedup_size([(i.get("path", ""), i.get("size", 0))
                                            for i in items])
                    store[cat["key"]] = {"items": items, "size": size,
                                         "meta": cat,
                                         "per_file": cat.get("per_file", False)}
                    self.q.put(("log", f"  {cat['name']}: {len(items)} 项 · "
                                       f"{human_size(size)}"))
                    # AI 缓存：逐条列出是什么、占多大
                    if cat["key"] == "ai_cache" and items:
                        self.q.put(("log", "  ── AI / 开发缓存明细 ──"))
                        for it in items[:25]:
                            self.q.put(("log",
                                        f"    {human_size(it.get('size', 0)):>10}  "
                                        f"{it.get('label', '')}\n"
                                        f"              ↳ {it.get('desc', '')}"))
                        if len(items) > 25:
                            self.q.put(("log",
                                        f"    …另有 {len(items) - 25} 项，"
                                        f"点『查看文件』查看完整清单"))
                # 该盘扫完立即把结果交给界面（不用等所有盘都扫完）
                # 被中断时同样提交 —— 已统计的部分结果不浪费
                self.q.put(("drive_done", drive, store))
                if stopped_here:
                    self.q.put(("log", f"■ {drive}: 盘扫描被停止"
                                       f"（已统计部分结果，保留可清理）"))
                    break
            self.q.put(("scan_done",))
        finally:
            # 扫描结束恢复 GC，并把这一轮新建的对象冻结，
            # 避免后面的界面操作再被 full GC 打断
            if gc_was_enabled:
                gc.enable()
            gc.set_threshold(50000, 100, 100)
            try:
                gc.collect()
                gc.freeze()
            except Exception:
                pass

    def clear_results(self):
        # Treeview 一次清空，不用逐个销毁控件
        for node in self.tree.get_children():
            self.tree.delete(node)
        self.cat_widgets.clear()
        self.row_text.clear()
        # 树重建后所有展开过的浏览节点都要重新按需加载；
        # 但按盘保存的「勾选了哪些路径」不能丢，见 browse_by_drive。
        self.browse_nodes.clear()
        self._max_cache = {}

    def _set_row_text(self, iid, label, mark=""):
        """登记一行的原始名称，返回带勾选前缀的显示文本。

        名称前放真正的 ☐ / ☑（以前放的是彩色 emoji 圆点，用户会误以为
        那是单选按钮，点了没反应）。名称文本存在 row_text 里，
        之后改勾选状态时只换前缀，不用重新拼长路径。
        """
        self.row_text[iid] = label
        return (mark + "  " + label) if mark else label

    def _row_mark(self, iid, mark, tag=None):
        """统一改一行的勾选状态：选择列 + 名称前缀 + 配色。"""
        if not iid or not self.tree.exists(iid):
            return
        self.tree.set(iid, "sel", mark)
        base = self.row_text.get(iid)
        if base is not None:
            self.tree.item(iid, text=(mark + "  " + base) if mark else base)
        if tag:
            self.tree.item(iid, tags=(tag,))

    def _bstate(self, drive=None):
        """某个盘的大目录浏览勾选状态（按路径保存，切盘不丢）。"""
        d = (drive or self.current_drive).upper()
        return self.browse_by_drive.setdefault(
            d, {"sel": set(), "items": {}})

    def _browse_picks(self):
        """当前盘手动勾选、且允许删除的浏览项（转成待删清单）。"""
        st = self._bstate()
        out = []
        for p in st["sel"]:
            it = st["items"].get(p)
            if not it or _is_protected_browse(p) or _is_whole_dir_blocked(p):
                continue
            out.append(dict(it, browse=True))
        return out
    def save_checked(self):
        """把当前的勾选状态存起来（切换盘符时恢复）。"""
        cur = self.checked_by_drive.setdefault(self.current_drive, {})
        for key, cw in self.cat_widgets.items():
            if cw.get("readonly"):
                continue
            cur[key] = cw.get("master", False)
            cur[key + "::over"] = dict(cw.get("sel", {}))
    def on_drive_change(self, event=None):
        if self.cleaning:
            return
        self.save_checked()
        self.current_drive = self.drive_var.get()
        self.refresh_free_space()
        self.render_current_drive()

    # 分组定义：把几十个类目归到 5 个大组，界面才有「分层」感
    GROUP_ORDER = [
        ("safe", "🟢 安全可清理（可放心删）", "#1a7f37"),
        ("soft", "📦 软件缓存与文件夹识别（按清理影响分级 · 默认不勾）", "#6b46a8"),
        ("ai", "🤖 AI / 开发工具缓存", "#7b4fbf"),
        ("opt", "⚪ 可选清理（逐项确认）", "#b58100"),
        ("risk", "⚠️ 需确认（删除后不可撤销）", "#c0392b"),
        ("big", "📊 空间占用分析（看清空间被谁占了·只读）", "#1a4d8f"),
        ("more", "⋯ 更多类别（点击展开）", "#666666"),
    ]

    # 精简模式：默认只显示这些类目，其余折进「更多类别」。
    # 解决「显示得太完整」—— 一屏之内看完全部可清的东西。
    PRIORITY_KEYS = {
        "temp", "update", "delivery", "wer", "recycle", "winlogs",
        "appcache", "browser", "shadercache", "thumb", "inetcache",
        "install_residue",
        "ai_cache", "inv_bigfolders", "inv_bigfiles",
        "g_junk", "g_large", "g_old", "g_dup", "g_empty",
        "sc_clean", "sc_rebuild", "sc_confirm", "sc_protected",
        "sc_folders", "sc_profile",
    }

    def _group_of(self, key, risk, readonly=False):
        """决定一个类目属于哪个分组。"""
        if key.startswith("sc_"):
            return "soft"
        if readonly:
            return "big"
        if key == "ai_cache":
            return "ai"
        if key.startswith("inv_"):
            return "big"
        if risk == "safe":
            return "safe"
        if risk == "risky":
            return "risk"
        return "opt"

    def render_current_drive(self):
        self.clear_results()
        data = self.results_by_drive.get(self.current_drive, {})
        if not data:
            self.empty_hint.config(
                text=f"（{self.current_drive}: 盘尚未扫描，点击右上角「开始扫描」）")
            self.empty_hint.pack(fill="x", pady=24)
            self.summary_label.config(text="已勾选可释放：—")
            self.max_label.config(text="")
            return
        self.empty_hint.pack_forget()

        saved = self.checked_by_drive.get(self.current_drive, {})
        # 按分组归拢；精简模式下非优先类目折进「更多类别」
        buckets = {}
        for key, rec in data.items():
            meta = rec["meta"]
            readonly = meta.get("readonly", False)
            g = self._group_of(key, meta.get("risk", "optional"), readonly)
            if (g not in ("safe", "soft", "ai", "big", "risk")
                    and key not in self.PRIORITY_KEYS):
                g = "more"
            buckets.setdefault(g, []).append((key, rec))

        for gkey, gname, gcolor in self.GROUP_ORDER:
            items = buckets.get(gkey)
            if not items:
                continue
            # 组内按风险再排一下：安全的排前面
            items.sort(key=lambda kv: 0 if kv[1]["meta"].get("risk") == "safe"
                       else (2 if kv[1]["meta"].get("risk") == "risky" else 1))
            gnode = self.tree.insert(
                "", "end", iid=f"g:{gkey}",
                text=self._set_row_text(f"g:{gkey}", gname),
                values=("", "", "", ""),
                tags=("grp",), open=(gkey != "more"))
            for key, rec in items:
                meta = rec["meta"]
                readonly = meta.get("readonly", False)
                risk = meta.get("risk", "optional")
                count = len(rec["items"])
                size = rec["size"]
                if readonly:
                    mark, tag = "—", "ro"
                    info = f"共占用 {human_size(size)}"
                elif count:
                    mark = "☑" if saved.get(key, risk == "safe") else "☐"
                    tag = "on" if mark == "☑" else "off"
                    info = f"{count} 项 · {human_size(size)}"
                else:
                    mark, tag = "", "off"
                    info = "未发现"
                ciid = f"c:{key}"
                self.tree.insert(
                    gnode, "end", iid=ciid,
                    text=self._set_row_text(ciid, meta["name"], mark),
                    values=(mark, info, meta.get("desc", ""), ""),
                    tags=(tag,))
                # 占位子节点：让类目行一开始就有展开箭头。
                # 真正的明细在点开时才懒加载，不用一次插几万行。
                if count:
                    self.tree.insert(
                        ciid, "end", iid=f"ph:{ciid}",
                        text="展开查看明细…",
                        values=("", "", "", ""), tags=("note",))
                self.cat_widgets[key] = {
                    "per_file": True,
                    "items": rec["items"],
                    "risk": risk, "readonly": readonly,
                    "mark": mark, "iid": f"c:{key}",
                    "count": count, "size": size,
                    "desc": meta.get("desc", ""),
                    "shown": 0, "meta": meta,
                    "master": saved.get(key, risk == "safe"),
                    "sel": dict(saved.get(key + "::over") or {}),
                    "loaded": False,
                }

    def _trim(self, p, n=82):
        if len(p) <= n:
            return p
        # "[软件名]  很长\很长的路径" → 保留软件名，路径留最有辨识度的尾段
        if p.startswith('[') and ']' in p[:40]:
            cut = p.index(']') + 1
            head, tail = p[:cut], p[cut:].strip()
            room = max(12, n - len(head) - 4)
            return head + " …" + tail[-room:]
        return p[:34] + " … " + p[-(n - 38):]

    # 每批插入的子项行数。
    # 商业清理软件的做法：默认只显示前几十条，剩下的折叠成「还有 N 项」。
    # 这既让界面清爽，也避免一次性插 2 万行把内存和渲染时间都吃掉。
    PAGE = DISPLAY_PAGE          # 默认显示 30 条
    PAGE_BIG = 100               # 点「显示更多」每次再加 100 条
    PAGE_MAX = DISPLAY_PAGE_MAX  # 单类目上限 300 条

    def on_tree_open(self, _evt=None):
        """展开某个节点 → 懒加载它的子项。

        focus() 在某些 Tk 版本下不跟着被展开的行走，所以额外扫一遍
        「已展开但还没加载」的节点（数量很小，一次点击几十微秒）。
        """
        iid = self.tree.focus()
        if iid:
            self._lazy_for(iid)
        for key, cw in list(self.cat_widgets.items()):
            ciid = cw.get("iid")
            if (not cw.get("loaded") and ciid and self.tree.exists(ciid)
                    and self.tree.item(ciid, "open")):
                self._load_children(key)
        for bid, node in list(self.browse_nodes.items()):
            if (not node.get("loaded") and self.tree.exists(bid)
                    and self.tree.item(bid, "open")):
                self._load_browse(bid)

    def _lazy_for(self, iid):
        """按节点类型补做懒加载；绝不改动 open 状态。"""
        if iid.startswith("c:"):
            self._load_children(iid[2:])
        elif iid.startswith(("i:", "b:")) and iid in self.browse_nodes:
            self._load_browse(iid)

    def _load_children(self, key):
        """给指定类目加载子项（只加载一次）。"""
        cw = self.cat_widgets.get(key)
        if not cw or cw.get("loaded"):
            return
        cw["loaded"] = True
        iid = cw["iid"]
        # 「重复文件」需要算 md5，是整个扫描里最慢的一步 ——
        # 所以只在用户真的展开这个类目时才做，不拖累整体扫描速度
        if key == "g_dup" and not cw["items"]:
            self._scan_dups_lazy(key)
        # 先插真明细、最后删占位：如果先把唯一子节点删掉，
        # Tk 会顺手把父节点折叠掉，用户就看到「刚展开又收回去了」。
        self._fill_children(key, self.PAGE)
        for ch in list(self.tree.get_children(iid)):
            if ch.startswith("ph:"):
                self.tree.delete(ch)

    def _scan_dups_lazy(self, key):
        """按需检测重复文件（后台线程，不卡界面）。"""
        cw = self.cat_widgets.get(key)
        if not cw:
            return
        drive = self.current_drive
        self.status_label.config(text="正在检测重复文件（比对文件内容）…")

        def work():
            try:
                items = _scan_dups_on_demand(drive)
            except Exception as e:
                self.q.put(("log", f"  重复文件检测出错: {e}"))
                return
            self.q.put(("dup_ready", drive, key, items))

        threading.Thread(target=work, daemon=True).start()

    def _maybe_expand(self, event):
        """点展开箭头 → 只补懒加载。

        v3.0 关键修复：这里以前无条件执行 `tree.item(iid, open=True)`，
        于是用户点减号收起时，Tk 先把 open 置 False、ButtonRelease
        又把它改回 True —— 表现就是「下一层的减号只能展开，不能收回」。
        现在折叠状态完全交给 Tk，本函数只负责把内容补上。
        """
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        try:
            elem = self.tree.identify_element(event.x, event.y) or ""
        except Exception:
            return
        if "indicator" not in elem:
            return
        if self.tree.item(iid, "open"):
            self._lazy_for(iid)

    def _fill_children(self, key, limit):
        """给类目节点填充子项行（最多 limit 条）。"""
        cw = self.cat_widgets.get(key)
        if not cw:
            return
        iid = cw["iid"]
        items = cw["items"]
        start = cw.get("shown", 0)
        end = min(len(items), start + limit)
        # 用 master 而不是 mark 判断：用户手动取消某一项后 mark 会变成「◪」，
        # 但总开关仍然是开的 —— 这时新加载的行必须显示为勾选，
        # 否则会出现「上面显示已全选、下面新加载的行却全是空的」这种自相矛盾。
        master_on = bool(cw.get("master", False))
        for i in range(start, end):
            it = items[i]
            label = it.get("label") or it.get("path", "")
            desc = (it.get("desc") or "").strip()
            if it.get("level") == "ai-model":
                desc = "⚠ " + desc + "（删除后需重新下载/重新训练）"
            # 手动改过的条目用它自己的状态；其余跟随总开关
            over = cw.get("sel", {}) or {}
            v = over.get(i)
            if v is None:
                v = master_on
            ro = bool(cw.get("readonly"))
            blocked = bool(it.get("protected"))
            can_expand = bool(it.get("browse") and it.get("is_dir"))
            if blocked:
                mark, tag = "×", "ro"       # 系统 / 受保护，锁住
            elif ro:
                mark, tag = "—", "ro"       # 说明层：可展开，但顶层整体不可删
            else:
                mark = "☑" if v else "☐"
                tag = "on" if v else "off"
            impact = (it.get("impact") or "").strip()
            advice = (it.get("advice") or "").strip()
            # Tk 对 emoji 支持不稳，✅/❌/📋 会显示成黑方块 → 去掉开头符号
            advice = re.sub(r'^[^\u4e00-\u9fffA-Za-z0-9\[]+', '', advice)
            if advice:
                impact = (impact + "　｜　" + advice).strip("　｜ ")
            child_iid = f"i:{key}:{i}"
            self.tree.insert(
                iid, "end", iid=child_iid,
                text=self._set_row_text(child_iid, self._trim(label), mark),
                values=(mark, human_size(it.get("size", 0)), desc, impact),
                tags=(tag,))
            # v3.0：大目录给一个占位子节点 → 有展开箭头，点开才枚举下一层
            if can_expand:
                self.browse_nodes[child_iid] = {
                    "item": it, "drive": self.current_drive, "loaded": False}
                self.tree.insert(
                    child_iid, "end", iid=f"ph:{child_iid}",
                    text="展开查看里面的文件夹和文件…",
                    values=("", "", "", "点左边箭头逐层展开，里面的项目可手动勾选"),
                    tags=("note",))
        cw["shown"] = end
        # 还有更多 → 加一行提示（点这一行的不同位置做不同的事）
        more_iid = f"m:{key}"
        total = len(items)
        if end < total:
            rest = total - end
            if self.tree.exists(more_iid):
                self.tree.delete(more_iid)
            can_more = end < self.PAGE_MAX
            if can_more:
                text = (f"… 还有 {rest} 项　▶ 点这行再显示 {min(self.PAGE_BIG, rest)} 条")
            else:
                text = f"… 共 {total} 项（已显示 {end} 项，达到显示上限）"
            self.tree.insert(
                iid, "end", iid=more_iid, text=text,
                values=("", "", f"共 {total} 项，已显示 {end} 项", ""),
                tags=("more",))
            cw["more_iid"] = more_iid
        else:
            cw.pop("more_iid", None)
            if self.tree.exists(more_iid):
                self.tree.delete(more_iid)

    def on_tree_click(self, event):
        """点「选择」列或名称 → 切换勾选；展开 / 折叠交给箭头或双击。

        v3.0：选择列号改成动态算出来的 self.sel_col（实测是 #1）。
        另外名称前的彩色圆点已换成真正的 ☐ / ☑，点名称也能勾 ——
        以前用户点那个圆点没反应，以为「按钮不能打勾」。
        """
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        try:
            elem = self.tree.identify_element(event.x, event.y) or ""
        except Exception:
            elem = ""
        if "indicator" in elem or elem == "padding":
            return                       # 减号：交给 Tk 自己展开 / 收起
        col = self.tree.identify_column(event.x)
        if col not in (self.sel_col, "#0"):
            return                       # 大小 / 用途 / 影响列不响应
        if iid.startswith("m:"):
            self._fill_children(iid[2:], self.PAGE_BIG)
            return
        if iid.startswith("c:"):
            key = iid[2:]
            cw = self.cat_widgets.get(key)
            if cw and cw.get("readonly"):
                self.tree_tip.config(
                    text="这一层只做用途说明：点左边箭头逐层展开，"
                         "勾选里面的文件夹 / 文件后再清理")
                return
            self.toggle_category(key)
        elif iid.startswith("i:"):
            _, key, idx = iid.split(":", 2)
            cw = self.cat_widgets.get(key)
            it = None
            try:
                it = cw["items"][int(idx)]
            except Exception:
                pass
            if cw and cw.get("readonly") and it and it.get("browse"):
                self._toggle_node(iid)   # 说明层的大目录：点名称就逐层展开
            else:
                self.toggle_item(key, int(idx))
        elif iid.startswith("b:"):
            self.toggle_browse(iid)

    def on_tree_double(self, _event=None):
        """双击展开 / 折叠任意可展开节点。"""
        iid = self.tree.focus()
        if iid and iid.startswith(("c:", "i:", "b:")):
            self._toggle_node(iid)

    def toggle_category(self, key):
        """类目行的勾选框 → 全选 / 全不选该类。"""
        cw = self.cat_widgets.get(key)
        if not cw or cw.get("readonly"):
            return
        # 现在勾的是「总开关」，单项的手动改动要清掉
        new_on = not cw.get("master", False)
        cw["master"] = new_on
        cw["sel"] = {}
        new_mark = "☑" if new_on else "☐"
        cw["mark"] = new_mark
        tag = "on" if new_on else "off"
        iid = cw["iid"]
        self._row_mark(iid, new_mark, tag)
        # 同步已渲染的子行。
        # 这里用「逐行 set + 换 tag」而不是「删掉重建」：
        #   · 删掉重建 1.6 万行 = 130ms（每次点击都做）
        #   · 逐行 set 1.6 万行 = 28ms（实测主线程）
        # 反复点总开关时后者明显更跟手。
        shown = cw.get("shown", 0)
        if shown:
            mark_on = new_mark
            tag_on = tag
            for i in range(shown):
                child = f"i:{key}:{i}"
                if (self.tree.exists(child)
                        and self.tree.set(child, "sel") not in ("—", "×")):
                    self._row_mark(child, mark_on, tag_on)
        self.on_selection_changed()

    def toggle_item(self, key, idx):
        """单个文件行的勾选框。"""
        cw = self.cat_widgets.get(key)
        if not cw or cw.get("readonly"):
            return          # 只读类目（游戏本体/模型/个人数据）绝不可勾选
        child = f"i:{key}:{idx}"
        if not self.tree.exists(child):
            return
        cur = self.tree.set(child, "sel")
        if cur in ("—", "×"):
            return          # 只读 / 系统锁定行不可勾选
        new_on = (cur != "☑")
        new_mark = "☑" if new_on else "☐"
        self._row_mark(child, new_mark, "on" if new_on else "off")
        # 记下这一条的手动状态（覆盖总开关）
        cw.setdefault("sel", {})[idx] = new_on
        # 类目行上的标记跟着变（部分选中显示 ◪）
        n_sel = self._count_selected(key)
        iid = cw["iid"]
        if n_sel == 0:
            cw["mark"] = "☐"
            self._row_mark(iid, "☐", "off")
        elif n_sel >= cw.get("count", 0):
            cw["mark"] = "☑"
            self._row_mark(iid, "☑", "on")
        else:
            cw["mark"] = "◪"
            self._row_mark(iid, "◪", "off")
        self.on_selection_changed()

    # ------------------- v3.0 大目录逐层浏览 -------------------
    def _toggle_node(self, iid):
        """双击 / 点说明层目录名：只切 open，并在展开时补懒加载。"""
        if not iid or not self.tree.exists(iid):
            return
        opening = not self.tree.item(iid, "open")
        self.tree.item(iid, open=opening)
        if opening:
            self._lazy_for(iid)

    def _load_browse(self, iid):
        """展开一个大目录 → 后台枚举它的【一级】子项。

        体积直接查本次全盘扫描算好的 dir_sizes，不重新遍历磁盘，
        所以展开 47.9GB 的 Users 也是秒开。
        """
        node = self.browse_nodes.get(iid)
        if not node or node.get("loaded"):
            return
        node["loaded"] = True
        it = node.get("item") or {}
        path = it.get("path", "")
        if not path or not os.path.isdir(path):
            return
        depth = int(it.get("depth", 1)) + 1
        if depth > BROWSE_MAX_DEPTH:
            self.tree_tip.config(text="已到最大展开层数（4 层）")
            return
        drive = node["drive"]
        self.tree_tip.config(text=f"正在读取 {self._trim(path, 52)} …")

        def work():
            try:
                sizes = _FULL_CACHE.get(drive, {}).get("dir_sizes", {})
                items, total = enumerate_browse_dir(drive, path, sizes, depth)
            except Exception as e:
                self.q.put(("log", f"  读取目录失败：{path} · {e}"))
                items, total = [], 0
            self.q.put(("browse_ready", drive, iid, items, total))

        threading.Thread(target=work, daemon=True).start()

    def _insert_browse_children(self, parent_iid, drive, items, total):
        """把枚举结果插到树上。目录行再挂占位节点，可继续下钻。

        顺序很重要：先把真实子行插进去，最后才删占位行。
        删空子节点会让 Tk 自动折叠父节点，先删的话用户点开就立刻缩回去。
        """
        ph_iid = f"ph:{parent_iid}"
        if not items:
            for ch in list(self.tree.get_children(parent_iid)):
                if ch.startswith("ph:"):
                    self.tree.delete(ch)
            self.tree.insert(
                parent_iid, "end", iid=ph_iid,
                text="（空目录 / 没有读取权限）",
                values=("", "", "", ""), tags=("note",))
            self.tree_tip.config(text="此目录没有可显示的内容")
            return
        st = self._bstate(drive)
        for it in items:
            self._browse_seq += 1
            bid = f"b:{self._browse_seq}"
            blocked = bool(it.get("protected"))
            picked = (not blocked) and (it["path"] in st["sel"])
            mark, tag = (("×", "ro") if blocked else
                         (("☑", "on") if picked else ("☐", "off")))
            st["items"][it["path"]] = it
            impact = (it.get("impact") or "").strip()
            advice = re.sub(r'^[^\u4e00-\u9fffA-Za-z0-9\[]+', '',
                            (it.get("advice") or "").strip())
            if advice:
                impact = (impact + "　｜　" + advice).strip("　｜ ")
            self.tree.insert(
                parent_iid, "end", iid=bid,
                text=self._set_row_text(bid, self._trim(it["label"]), mark),
                values=(mark, human_size(it["size"]),
                        it.get("desc", ""), impact),
                tags=(tag,))
            self.browse_nodes[bid] = {
                "item": it, "drive": drive, "loaded": False}
            if it.get("browse") and it.get("is_dir"):
                self.tree.insert(
                    bid, "end", iid=f"ph:{bid}",
                    text="展开查看下一层…",
                    values=("", "", "", ""), tags=("note",))
        for ch in list(self.tree.get_children(parent_iid)):
            if ch.startswith("ph:"):
                self.tree.delete(ch)
        more = max(0, total - len(items))
        self.tree_tip.config(
            text=f"已显示 {len(items)} 项（按体积降序）"
                 + (f" · 另有 {more} 个小项未显示" if more else ""))

    def toggle_browse(self, iid):
        """勾选一个手动挑出来的子文件夹 / 文件。"""
        node = self.browse_nodes.get(iid)
        if not node:
            return
        it = node["item"]
        if it.get("protected") or not it.get("selectable"):
            self.tree_tip.config(
                text="系统 / 受保护路径：不允许在本工具里删除（可展开查看）")
            return
        st = self._bstate(node["drive"])
        p = it["path"]
        if p in st["sel"]:
            st["sel"].discard(p)
            self._row_mark(iid, "☐", "off")
        else:
            st["sel"].add(p)
            st["items"][p] = it
            self._row_mark(iid, "☑", "on")
        self.on_selection_changed()

    def _count_selected(self, key):
        """该类目里被勾选的数量（按 master + 单项覆盖计算）。"""
        cw = self.cat_widgets.get(key)
        if not cw:
            return 0
        master = cw.get("master", False)
        over = cw.get("sel", {}) or {}
        n = len(cw["items"])
        picked = 0
        for i in range(n):
            v = over.get(i)
            if v is None:
                v = master
            if v:
                picked += 1
        return picked

    def add_category_row(self, key, name, count, size, risk, saved_state=None,
                         per_file=False, items=None, readonly=False, desc=""):
        """旧接口保留（Treeview 版不再需要），转调树版逻辑。"""
        return
    def toggle_expand(self, key):
        """旧接口保留：转成 Treeview 的展开/折叠。"""
        cw = self.cat_widgets.get(key)
        if not cw:
            return
        iid = cw.get("iid")
        if iid and self.tree.exists(iid):
            self.tree.item(iid, open=not self.tree.item(iid, "open"))
    def build_sub(self, key):
        """旧接口保留：转成 Treeview 的懒加载。"""
        cw = self.cat_widgets.get(key)
        if not cw or cw.get("loaded"):
            return
        cw["loaded"] = True
        self._fill_children(key, self.PAGE)
    def on_master_toggle(self, key):
        """旧接口保留，实际逻辑在 toggle_category()。"""
        self.toggle_category(key)
    def _cat_state(self, key):
        """返回该类目的 (全部条目, 已勾选条目)。

        状态模型：
          master = 类目总开关（安全类默认开，可选/风险类默认关）
          sel    = {下标: 是否勾选}，只记录用户手动改过的条目
        条目的最终状态 = sel 里有记录就用记录，否则跟随 master。
        这样即使一个类目有几万条（界面只渲染前几百条），
        勾选语义也和「全部列出来」完全一致。

        数据源统一取 cat_widgets（界面渲染用的那份），
        不要再从 results_by_drive 另取一份 —— 两份数据一旦不一致，
        就会出现「界面显示已勾选、数字却算 0」的诡异状态。
        """
        cw = self.cat_widgets.get(key) or {}
        if cw.get("readonly"):
            return cw.get("items", []) or [], []
        items = cw.get("items") or []
        master = cw.get("master", False)
        over = cw.get("sel", {}) or {}
        picked = []
        for i, it in enumerate(items):
            v = over.get(i)
            if v is None:
                v = master
            if v:
                picked.append(it)
        return items, picked
    def show_summary(self):
        """实时统计三个数字（对应商业清理软件的三个指标）：

          ① 已勾选可释放  —— 你勾中的项目实际能释放多少
          ② 一键可清理    —— 只算「安全类」垃圾，点「⚡ 一键清理」就是这个数
          ③ 软件缓存可清理 —— 只算 sc_* 软件缓存识别类目，全部默认不勾

        口径（v2.9 修正）：
          · 只读类目（空间分析 / 游戏本体 / 模型 / 个人数据）永不计入
          · ③ 不再把 g_large 之类的「大文件排行」算进来 ——
            数据盘上 g_large 里全是游戏 Paks 和模型权重，
            实测 E 盘会虚报出 298GB，跟 v2.8 修掉的 89.8GB 是同一个病根
          · 同一份空间被多个类目命中时只算一次（父目录优先）
        """
        picked = []      # 已勾选：(path, size)
        n_picked = 0
        safe_pairs = []  # 安全类全部：(path, size)
        review_pairs = []  # 需确认类全部：(path, size)
        for key in list(self.cat_widgets.keys()):
            rec = self.results_by_drive.get(self.current_drive, {}).get(key, {})
            meta = rec.get("meta", {})
            if meta.get("readonly"):
                continue          # 只读的空间分析不算可释放
            _, sel = self._cat_state(key)
            picked.extend((it.get("path", ""), it.get("size", 0))
                          for it in sel)
            n_picked += len(sel)
            all_items = rec.get("items", []) or []
            pairs = [(it.get("path", ""), it.get("size", 0)) for it in all_items]
            if meta.get("risk") == "safe":
                safe_pairs.extend(pairs)
            elif key.startswith("sc_"):
                # ③ 只统计软件缓存识别类目。通用文件类目（大文件/旧文件）
                # 是「逐文件挑着删」，给总量只会虚高，勾选后由 ① 反映。
                review_pairs.extend(pairs)

        # v3.0：大目录里手动挑的文件夹 / 文件也要计入「已勾选可释放」。
        # 它们不属于任何类目，所以不走上面的 cat_widgets 循环。
        browse = self._browse_picks()
        if browse:
            picked.extend((it.get("path", ""), it.get("size", 0))
                          for it in browse)
            n_picked += len(browse)

        total = _dedup_size(picked)
        safe_total = _dedup_size(safe_pairs)
        review_total = _dedup_size(review_pairs)

        self.summary_label.config(
            text=f"已勾选可释放：{human_size(total)}（{n_picked} 项）    ｜    "
                 f"一键可清理：{human_size(safe_total)}    ｜    "
                 f"软件缓存可清理：{human_size(review_total)}（需逐项确认）"
                 + (f"    ｜    手动挑选：{len(browse)} 项" if browse else ""))
        self.max_label.config(
            text=f"（{self.current_drive}: 盘 · 空间分析与游戏/模型占用不计入；"
                 f"软件缓存默认全不勾）")
        try:
            self._draw_bar()
        except Exception:
            pass
        return total

    def _get_max_total(self):
        """「全部可清理上限」—— 与勾选无关，缓存起来算一次就够。"""
        drive = self.current_drive
        if not hasattr(self, "_max_cache"):
            self._max_cache = {}
        cached = self._max_cache.get(drive)
        if cached is not None:
            return cached
        everything = []
        for key in list(self.cat_widgets.keys()):
            rec = self.results_by_drive.get(drive, {}).get(key, {})
            if rec.get("meta", {}).get("readonly"):
                continue
            for it in rec.get("items", []) or []:
                everything.append((it.get("path", ""), it.get("size", 0)))
        val = _dedup_size(everything)
        self._max_cache[drive] = val
        return val

    def on_selection_changed(self):
        """勾选变化 → 合并刷新（防抖）。

        旧版每次点勾选都立刻全量重算，连续点十下就是十次重算 → 卡。
        这里合并成一次，60ms 内的连续操作只算一次。
        """
        if getattr(self, "_sum_pending", None):
            try:
                self.root.after_cancel(self._sum_pending)
            except Exception:
                pass
        self._sum_pending = self.root.after(60, self._do_summary)

    def _do_summary(self):
        self._sum_pending = None
        self.show_summary()
    def quick_clean(self):
        """⚡ 一键清理 —— 商业清理软件的标准动作。

        只清理「安全类」里已勾选的项目：
          · 系统临时文件 / 更新缓存 / 错误报告 / 回收站 / 系统日志
          · 浏览器缓存 / 缩略图 / 显卡着色器缓存 等应用缓存
        绝不碰：用户数据、大文件、旧文件、AI 模型、注册表风险项。

        这解决了「工具没效果」的核心问题 ——
        以前用户面对几万个文件不知道该勾什么，最后什么都没清；
        现在点一下就有确定的效果。
        """
        if self.cleaning:
            return
        if self.scanning:
            self._notice("扫描还没完成，等一下再清理。")
            return

        data = self.results_by_drive.get(self.current_drive, {})
        if not data:
            self._notice("请先点「扫描此盘」，扫描完成后才能清理。")
            return

        # 只取 risk == "safe" 且有内容的类目
        plan = {}
        for key, cw in self.cat_widgets.items():
            if cw.get("readonly") or key.startswith("sc_"):
                continue        # 软件缓存识别类目一律不进一键清理
            meta = data.get(key, {}).get("meta", {})
            if meta.get("risk") != "safe":
                continue
            _, sel = self._cat_state(key)
            if sel:
                plan[key] = sel

        if not plan:
            self._notice("当前没有可一键清理的安全项目。\n"
                         "请先点「扫描此盘」，扫描完成后才能清理。")
            return

        picked = [(it.get("path", ""), it.get("size", 0))
                  for v in plan.values() for it in v]
        total = _dedup_size(picked)
        n_items = sum(len(v) for v in plan.values())
        names = "\n".join(
            f"  • {data[k]['meta']['name']}" for k in plan
            if k in data)[:600]

        ok = messagebox.askyesno(
            "⚡ 一键清理",
            f"将清理 {self.current_drive}: 盘的 {len(plan)} 类安全垃圾"
            f"（{n_items} 项），预计释放 {human_size(total)}：\n\n"
            f"{names}\n\n"
            f"只清理系统临时文件、缓存、回收站等可再生的内容，"
            f"不会碰你的文档、照片、聊天记录和任何软件数据。\n\n"
            f"这是本次唯一一次确认：点「是」之后不再弹任何窗口，"
            f"清理结果直接显示在界面上。\n\n"
            f"是否开始？")
        if not ok:
            return

        self._start_clean(plan, mode="quick")

    def confirm_clean(self):
        """手动清理：风险说明全部汇总进【唯一一次】确认弹窗。

        v3.0.2：原来风险项 / AI 模型 / 提权 / 手动挑选 / 最终确认最多
        连弹 5 个窗口，现在合并成一个，信息一条不少，只打断用户一次。
        """
        if self.cleaning:
            return
        if self.scanning:
            self._notice("扫描还在进行中。\n"
                         "可以点右上角「■ 停止」，已扫完的盘会保留结果。")
            return
        data = self.results_by_drive.get(self.current_drive, {})
        selected = []
        for key, cw in self.cat_widgets.items():
            if cw.get("readonly"):
                continue          # 只读项（系统/程序占用）不参与清理
            _, sel = self._cat_state(key)
            if sel:
                selected.append(key)
        # v3.0：大目录里手动挑的项目独立于类目，单独收集
        browse_picks = self._browse_picks()
        if not selected and not browse_picks:
            self._notice("没有勾选任何要清理的项。\n"
                         "大目录：点左边箭头逐层展开，再点子项前面的方框勾选。")
            return

        notes = []     # 所有需要提醒的内容，最后一次弹窗里统一展示

        risky = [key for key in selected
                 if data.get(key, {}).get("meta", {}).get("risk") == "risky"]
        if risky:
            names = "\n".join("  • " + data[k]["meta"]["name"] for k in risky)
            notes.append("【风险项】不影响系统运行，但会移除对应注册表残留 / 文件：\n"
                         + names)

        # AI 模型权重：删掉要重新下载/训练，单独再确认一次
        ai_model_items = []
        for key in selected:
            _, sel = self._cat_state(key)
            for it in sel:
                if it.get("level") == "ai-model":
                    ai_model_items.append(it)
        if ai_model_items:
            names = "\n".join(
                f"  • {it.get('label', it.get('path'))}\n"
                f"    {it.get('desc', '')}"
                for it in ai_model_items[:8])
            more = (f"\n  …等共 {len(ai_model_items)} 项"
                    if len(ai_model_items) > 8 else "")
            notes.append("【AI 模型 / 权重】删除后需重新下载甚至重新训练：\n"
                         + names + more)

        # 在主线程里把勾选结果固化成待删清单
        # （后台线程不再去读界面变量，避免跨线程操作 Tk 出问题）
        plan = {}
        picked = []
        for key in selected:
            _, sel = self._cat_state(key)
            if not sel:
                continue
            plan[key] = sel
            picked.extend((it.get("path", ""), it.get("size", 0)) for it in sel)
        if browse_picks:
            # 独立成一组，只走手动确认，永远不进「一键清理」
            plan["__browse__"] = browse_picks
            picked.extend((it.get("path", ""), it.get("size", 0))
                          for it in browse_picks)

        # 需要管理员权限的项目：只写进提示，不再弹提权询问 / 拉起 UAC。
        # 仍照常尝试删除（多数临时文件普通权限就能删），真正删不掉的
        # 会在清理日志里逐条显示「跳过/失败」，不会静默假装成功。
        if not is_admin():
            need = 0
            for items in plan.values():
                for it in items:
                    p = (it.get("path") or "").lower()
                    if (it.get("kind") == "reg"
                            or p.startswith(("c:\\windows", "c:\\program files",
                                             "c:\\program files (x86)"))):
                        need += 1
            if need:
                notes.append(
                    f"【权限提示】有 {need} 项位于系统目录或需要改注册表；"
                    "当前不是管理员身份，删不掉的会自动跳过并在日志里列出。\n"
                    "  需要完整清理可点右上角「以管理员身份重启」。")

        # 用与顶部一致的「去重后」算法统计实际会释放多少
        total = _dedup_size(picked)

        # v2.9：软件缓存逐条说明「清理会影响什么功能」，让用户删之前就知道代价
        sc_lines = []
        for key in selected:
            if not key.startswith("sc_"):
                continue
            _, sel = self._cat_state(key)
            for it in sel:
                if it.get("kind") == "readonly":
                    continue
                nm = (it.get("label") or it.get("path") or "")
                imp = (it.get("impact") or "").strip()
                sc_lines.append(f"  • {nm[:78]}\n      → {imp[:90]}")
        if sc_lines:
            shown = sc_lines[:10]
            more = (f"\n  …等共 {len(sc_lines)} 项"
                    if len(sc_lines) > 10 else "")
            notes.append("【软件缓存 · 清理影响】\n" + "\n".join(shown) + more)

        # v3.0：手动挑的用户数据最危险 —— 逐条列完整路径、写明不可恢复，
        # v3.0.2 起并入唯一一次确认，不再单独弹第二个窗口。
        if browse_picks:
            lines = "\n".join(f"  • {it.get('path', '')}"
                              for it in browse_picks[:12])
            more_b = (f"\n  …等共 {len(browse_picks)} 项"
                      if len(browse_picks) > 12 else "")
            browse_bytes = _dedup_size(
                [(it.get("path", ""), it.get("size", 0))
                 for it in browse_picks])
            notes.append(
                f"【手动挑选的项目 · {len(browse_picks)} 个，"
                f"共 {human_size(browse_bytes)}】这些是你自己的数据，"
                "删除后不可恢复、不进回收站：\n"
                + lines + more_b + "\n"
                "  · 系统路径已锁定，不会出现在清单里\n"
                "  · 「一键清理」永远不会碰这些内容\n"
                "  请逐条核对上面的完整路径。")

        warn = ("\n\n".join(notes) + "\n\n") if notes else ""
        warn = warn[:1800]          # 别把确认窗口撑出屏幕
        ok = messagebox.askyesno(
            "确认清理（唯一一次）",
            f"即将清理 {self.current_drive}: 盘 {len(selected)} 类项目"
            + (f" + {len(browse_picks)} 个手动挑选项" if browse_picks else "")
            + f"，预计释放 {human_size(total)}。\n\n"
            + warn
            + "（实际释放以磁盘剩余空间变化为准；锁定文件无法删除）\n"
              "这是本次唯一一次确认：点「是」之后不再弹任何窗口，"
              "清理结果直接显示在界面上。\n\n是否开始？")
        if not ok:
            return

        self._start_clean(plan, mode="manual")

    def _start_clean(self, plan, mode="manual"):
        """启动清理线程（主线程调用）。"""
        if self.result_banner.winfo_manager():
            self.result_banner.pack_forget()   # 收起上一次的完成结果
        self.cleaning = True
        self.stop_flag.clear()
        self.scan_btn.config(state="disabled")
        self.scan_all_btn.config(state="disabled")
        self.clean_btn.config(state="disabled")
        self.quick_btn.config(state="disabled")
        self.stop_btn.pack(side="left", padx=(0, 4))
        self.progress.config(mode="determinate", value=0, maximum=len(plan))
        self.status_label.config(text="正在清理…")
        title = "一键清理" if mode == "quick" else "确认清理"
        self.log(f"=== 开始{title} {self.current_drive}: 盘 ===")
        threading.Thread(target=self.clean_worker, args=(plan,),
                         daemon=True).start()

    def clean_worker(self, plan):
        """按主线程固化好的待删清单执行删除（只删用户勾选的那几项）。

        统计两件事：
          · freed_bytes —— 逐项累加「确实删掉的文件大小」，这是准确值
          · free_delta  —— 磁盘剩余空间的前后差，这是参考值

        为什么两个都要：
          磁盘剩余空间的差值不可靠 ——
          清理过程中别的程序还在写盘、Windows 后台也在写，
          差值可能是 0 甚至负数。用户看到「预计释放 1.4GB、实际释放 0B」
          就会觉得这是骗子。逐项累加才是真的删掉了多少。
        """
        data = self.results_by_drive.get(self.current_drive, {})
        free_before = get_drive_space(self.current_drive)[0]
        done = 0
        n_ok = 0
        n_fail = 0
        freed_bytes = 0
        for key, items in plan.items():
            if self.stop_flag.is_set():
                self.q.put(("log", "■ 清理已被用户停止"))
                break
            name = ("手动挑选的文件夹 / 文件" if key == "__browse__"
                    else data.get(key, {}).get("meta", {}).get("name", key))
            self.q.put(("clean_status", f"清理中：{name}"))
            for it in items:
                label = it.get('label') or it.get('path')
                before_sz = item_size(it)
                # 单项也要有超时保护 —— 免得一个被锁死的目录把整个清理卡住
                res = {}

                def _do(it=it, res=res):
                    try:
                        res['ok'] = clean_item(it)
                    except Exception:
                        res['ok'] = False
                th = threading.Thread(target=_do, daemon=True)
                th.start()
                th.join(90)
                ok = res.get('ok', False)
                if ok:
                    n_ok += 1
                    freed_bytes += before_sz
                    self.q.put(("log", f"  已清理：{label}"))
                else:
                    n_fail += 1
                    self.q.put(("log",
                                f"  跳过/失败（文件被占用或无权限）：{label}"))
            done += 1
            self.q.put(("clean_progress", done, len(plan)))
        free_after = get_drive_space(self.current_drive)[0]
        delta = max(0.0, free_after - free_before)
        self.q.put(("clean_done", delta, n_ok, n_fail, freed_bytes))

    # ------------------------- 消息轮询 -------------------------
    def poll(self):
        try:
            while True:
                msg = self.q.get_nowait()
                self.handle(msg)
        except queue.Empty:
            pass
        # 一直轮询：扫描结束后触发的「重复文件按需检测」等后台任务
        # 也要有人接收消息，否则结果永远送不到界面上
        self.root.after(80, self.poll)

    def handle(self, msg):
        kind = msg[0]
        if kind == "status":
            self.status_label.config(text=msg[1])
            self.log(msg[1])
        elif kind == "log":
            self.log(msg[1])
        elif kind == "scan_progress":
            # 扫描进度：只更新状态栏，不刷日志（避免日志框被刷屏）
            _, files, nbytes, short = msg
            txt = f"已扫描 {files:,} 个文件 · {human_size(nbytes)} · {short}"
            self.status_label.config(text=txt[:56])
        elif kind == "drive_done":
            # 某个盘扫完 → 立刻出结果，不必等所有盘
            _, drive, store = msg
            self.results_by_drive.setdefault(drive, {}).update(store)
            self.log(f"✓ {drive}: 盘扫描完成，结果已就绪")
            # v2.9：给一句诚实结论 —— 数据盘往往没有多少垃圾可清，
            # 大头是游戏 / 模型 / 个人数据。别让用户以为工具又没扫到东西。
            sc = _FULL_CACHE.get(drive, {}).get('software_caches', [])
            if sc:
                clean_b = sum(i['size'] for i in sc if i['bucket'] == 'clean')
                prot_b = sum(i['size'] for i in sc if i['bucket'] == 'protected')
                self.log(
                    f"  {drive}: 盘识别结论：可放心清 {human_size(clean_b)}；"
                    f"建议保留（游戏/模型/资料）{human_size(prot_b)}。"
                    f"其余见「软件缓存与文件夹识别」分组，默认全部不勾。")
            if drive == self.drive_var.get():
                self.refresh_free_space()
                self.render_current_drive()
                self.show_summary()
                self.quick_btn.config(state="normal")
        elif kind == "browse_ready":
            # v3.0：大目录下一层枚举完 → 回填到树上
            _, drive, iid, items, total = msg
            if self.tree.exists(iid):
                self._insert_browse_children(iid, drive, items, total)
        elif kind == "dup_ready":
            # 重复文件按需检测完成 → 回填到类目
            _, drive, key, items = msg
            rec = self.results_by_drive.get(drive, {}).get(key)
            if rec is not None and items:
                rec["items"] = items
                rec["size"] = _dedup_size(
                    [(it.get("path", ""), it.get("size", 0)) for it in items])
                cw = self.cat_widgets.get(key)
                if cw and drive == self.current_drive:
                    cw["items"] = items
                    cw["count"] = len(items)
                    cw["size"] = rec["size"]
                    iid = f"c:{key}"
                    if self.tree.exists(iid):
                        self.tree.set(iid, "size",
                                      f"{len(items)} 项 · "
                                      f"{human_size(rec['size'])}")
                    # 清掉已渲染的旧行，重新填
                    for child in self.tree.get_children(iid):
                        self.tree.delete(child)
                    cw["shown"] = 0
                    cw["loaded"] = False
                    self._fill_children(key, self.PAGE)
                self.log(f"  重复文件检测完成：{len(items)} 项")
                self.status_label.config(text="重复文件检测完成")
                self.show_summary()
        elif kind == "scan_done":
            self.scanning = False
            self.progress.stop()
            self.progress.config(mode="determinate", value=0)
            self.current_drive = self.drive_var.get()
            stopped = self.stop_flag.is_set()
            self.status_label.config(
                text="扫描已停止（部分结果）" if stopped
                else "扫描完成，可切换盘符查看结果并逐盘清理")
            self.render_current_drive()
            self.show_summary()
            self.scan_btn.config(state="normal")
            self.scan_all_btn.config(state="normal")
            self.clean_btn.config(state="normal")
            self.quick_btn.config(state="normal")
            self.stop_btn.pack_forget()
            self.log("=== 扫描已停止（保留已统计的部分结果）===" if stopped
                     else "=== 扫描完成 ===")
        elif kind == "clean_status":
            self.status_label.config(text=msg[1])
            self.log(msg[1])
        elif kind == "clean_progress":
            _, done, total = msg
            self.progress["value"] = done
            self.status_label.config(text=f"清理中… ({done}/{total})")
        elif kind == "clean_done":
            delta = msg[1] if len(msg) > 1 else 0.0
            n_ok = msg[2] if len(msg) > 2 else 0
            n_fail = msg[3] if len(msg) > 3 else 0
            freed_bytes = msg[4] if len(msg) > 4 else 0
            self.cleaning = False
            self.progress["value"] = self.progress["maximum"]
            # 以「实际删掉的字节数」为主，磁盘剩余空间变化作为参考
            self.status_label.config(
                text=f"✓ 清理完成 · 已删除 {human_size(freed_bytes)}"
                     f"（{n_ok} 项成功" + (f" / {n_fail} 项跳过" if n_fail else "")
                     + "）")
            self.scan_btn.config(state="normal")
            self.scan_all_btn.config(state="normal")
            self.clean_btn.config(state="normal")
            self.quick_btn.config(state="normal")
            self.stop_btn.pack_forget()
            self.refresh_free_space()
            free, total = get_drive_space(self.current_drive)
            self.log(f"=== 清理完成：已删除 {human_size(freed_bytes)}"
                     f"（磁盘剩余 +{human_size(delta)}）===")
            msg_txt = (
                f"{self.current_drive}: 盘清理完成！\n\n"
                f"已删除内容：{human_size(freed_bytes)}（{n_ok} 项）\n"
                f"磁盘剩余空间：{human_size(free)} / 共 {human_size(total)}")
            if delta > 0:
                msg_txt += f"\n本次磁盘空间实际增加：{human_size(delta)}"
            if n_fail:
                msg_txt += (f"\n\n有 {n_fail} 项没能删除"
                            f"（文件正被程序占用或权限不足），这部分空间还在。")
            # v3.0：手动挑的项目已删（或删失败），清掉勾选避免重复提交；
            # 目录体积表是扫描时的快照，删完会过期，提示重新扫描。
            st = self._bstate(self.current_drive)
            if st["sel"]:
                st["sel"].clear()
                for bid in list(self.browse_nodes):
                    if (self.tree.exists(bid)
                            and self.tree.set(bid, "sel") == "☑"):
                        self._row_mark(bid, "☐", "off")
                self.show_summary()
                msg_txt += ("\n\n（大目录体积是扫描时的快照，"
                            "想看最新占用请重新扫描此盘）")
            if freed_bytes < 1024 * 1024 and n_ok:
                msg_txt += ("\n\n（释放很少：多半是文件正被占用。"
                            "关掉浏览器、微信等软件后再清一次会明显更多。）")
            # v3.0.2：完成结果写在界面里，不再弹第二个窗口
            brief = (f"{self.current_drive}: 盘清理完成 · "
                     f"已删除 {human_size(freed_bytes)}（{n_ok} 项）"
                     + (f" · {n_fail} 项被占用跳过" if n_fail else "")
                     + f" · 剩余 {human_size(free)} / 共 {human_size(total)}")
            self._show_clean_result(msg_txt, brief)


def _crash_log(exc):
    try:
        import datetime as _dt
        tb = traceback.format_exc()
        base = "cleanmaster_crash.log"
        paths = []
        try:
            if getattr(sys, "frozen", False):
                paths.append(os.path.join(os.path.dirname(
                    os.path.abspath(sys.executable)), base))
        except Exception:
            pass
        paths.append(os.path.join(os.environ.get("TEMP", "."), base))
        for p in paths:
            try:
                with open(p, "a", encoding="utf-8") as f:
                    f.write(_dt.datetime.now().isoformat() + "\n" + tb + "\n\n")
            except Exception:
                pass
    except Exception:
        pass


def main():
    if MISSING_TK:
        sys.stderr.write(
            "错误：当前 Python 环境缺少 tkinter 图形库，无法启动界面。\n"
            "请使用完整版 Python（官网安装包默认包含 tkinter），"
            "或用 PyInstaller 打包时确保 tkinter 可用。\n")
        sys.exit(1)
    try:
        root = tk.Tk()
    except Exception:
        _crash_log(sys.exc_info()[1])
        sys.stderr.write("tkinter 初始化失败：\n" + traceback.format_exc())
        sys.exit(1)
    try:
        app = CleanMasterApp(root)
        root.mainloop()
    except Exception:
        _crash_log(sys.exc_info()[1])
        sys.stderr.write("运行时异常：\n" + traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
