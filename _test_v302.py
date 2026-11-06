#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3.0.2 回归测试：清理时零黑框 + 只弹一次窗。

全程只读真实磁盘；只在临时目录里造测试文件，不删除任何用户文件。
运行：py -3 _test_v302.py
"""
import os
import sys
import types
import inspect
import tempfile
import importlib.util
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "cm", os.path.join(HERE, "clean_master.py"))
cm = importlib.util.module_from_spec(spec)
sys.modules["cm"] = cm
spec.loader.exec_module(cm)

PASS = []
FAIL = []


def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(("  PASS  " if cond else "  FAIL  ") + name +
          (("  -> " + str(extra)) if extra else ""))


class FakeMsg:
    """记录所有弹窗调用，askyesno 一律返回 True（模拟用户点「是」）。"""
    def __init__(self):
        self.calls = []

    def askyesno(self, *a, **k):
        self.calls.append("askyesno")
        return True

    def showinfo(self, *a, **k):
        self.calls.append("showinfo")

    def showwarning(self, *a, **k):
        self.calls.append("showwarning")

    def showerror(self, *a, **k):
        self.calls.append("showerror")

    def askokcancel(self, *a, **k):
        self.calls.append("askokcancel")
        return True

    def clear(self):
        self.calls.clear()


def main():
    print("\n[1] 子进程调用全部隐藏控制台窗口")
    kw = cm._NO_WINDOW_KW
    check("带 CREATE_NO_WINDOW (0x08000000)",
          bool(kw.get("creationflags", 0) & 0x08000000), kw.get("creationflags"))
    check("带 STARTUPINFO / SW_HIDE",
          kw.get("startupinfo") is not None
          and getattr(kw["startupinfo"], "wShowWindow", None) == 0)

    tmp = tempfile.mkdtemp(prefix="cm_v302_")
    p1 = os.path.join(tmp, "a.tmp")
    p2 = os.path.join(tmp, "b.tmp")
    for p in (p1, p2):
        with open(p, "wb") as f:
            f.write(b"x" * 128)

    captured = []

    def fake_run(*a, **k):
        captured.append(k)
        return types.SimpleNamespace(returncode=0, stdout="")

    with mock.patch.object(cm.subprocess, "run", side_effect=fake_run):
        cm._delete_files_batch([p1, p2])       # cmd /c del 分批
        cm.run_powershell("Write-Output hi")   # powershell 清回收站
        cm.clean_item({"kind": "command", "cmd": "echo hi"})
    check("三条子进程路径都实际走到了", len(captured) == 3, len(captured))
    check("每次调用都带隐藏窗口参数",
          all(bool(k.get("creationflags", 0) & 0x08000000) for k in captured),
          [k.get("creationflags") for k in captured])
    for fn in (cm.force_rmtree, cm.force_remove_file,
               cm._delete_files_batch, cm.run_powershell, cm.clean_item):
        src = inspect.getsource(fn)
        if "subprocess.run(" in src:
            check(fn.__name__ + " 的 subprocess.run 带 _NO_WINDOW_KW",
                  "_NO_WINDOW_KW" in src)

    # 关键：隐藏窗口不能把删除功能本身搞坏（CREATE_NO_WINDOW 只影响窗口）
    real = tempfile.mkdtemp(prefix="cm_v302_real_")
    rps = [os.path.join(real, "r%d.tmp" % i) for i in range(3)]
    for p in rps:
        with open(p, "wb") as f:
            f.write(b"hello")
    ok = cm._delete_files_batch(rps)
    check("★ 隐藏窗口下 cmd 批量删除仍然有效",
          ok and not any(os.path.exists(p) for p in rps),
          [os.path.exists(p) for p in rps])
    import shutil
    shutil.rmtree(real, ignore_errors=True)

    print("\n[2] 一键清理：只弹一次确认")
    root = cm.tk.Tk()
    root.geometry("1200x800")
    app = cm.CleanMasterApp(root)
    fake = FakeMsg()
    cm.messagebox = fake
    started = []
    app._start_clean = lambda plan, mode="manual": started.append(mode)

    app.current_drive = app.drive_var.get()
    store = {
        "temp": {
            "items": [
                {"path": p1, "size": 128, "kind": "file",
                 "label": "a.tmp", "desc": "测试临时文件"},
                {"path": p2, "size": 128, "kind": "file",
                 "label": "b.tmp", "desc": "测试临时文件",
                 "level": "ai-model"},
            ],
            "size": 256,
            "meta": {"key": "temp", "name": "系统临时文件",
                     "risk": "safe", "desc": "测试类目"},
            "per_file": True,
        },
        "g_risk": {
            "items": [{"path": p1, "size": 128, "kind": "file",
                       "label": "风险项", "desc": "测试"}],
            "size": 128,
            "meta": {"key": "g_risk", "name": "测试风险项",
                     "risk": "risky", "desc": "测试"},
            "per_file": True,
        },
    }
    app.results_by_drive[app.current_drive] = store
    app.render_current_drive()
    root.update()
    app.cat_widgets["temp"]["master"] = True
    app.cat_widgets["g_risk"]["master"] = True
    app.scanning = False
    app.cleaning = False

    fake.clear()
    app.quick_clean()
    check("★ 一键清理只调用一次 askyesno",
          fake.calls.count("askyesno") == 1, fake.calls)
    check("一键清理没有任何提示/警告弹窗",
          not [c for c in fake.calls if c != "askyesno"], fake.calls)
    check("确认后启动了清理", started == ["quick"], started)

    fake.clear()
    n = len(started)
    app.scanning = True
    app.quick_clean()
    check("扫描中前置提示不弹窗", fake.calls == [], fake.calls)
    check("扫描中不启动清理", len(started) == n)
    app.scanning = False

    print("\n[3] 手动确认清理：5 连弹合并成 1 次")
    st = app._bstate()
    st["sel"].add(p2)
    st["items"][p2] = {"path": p2, "size": 128, "kind": "file",
                       "label": "b.tmp", "desc": "手动挑的"}
    fake.clear()
    app.confirm_clean()
    check("★ 确认清理只调用一次 askyesno",
          fake.calls.count("askyesno") == 1, fake.calls)
    check("确认清理没有任何提示/警告弹窗",
          not [c for c in fake.calls if c != "askyesno"], fake.calls)
    check("确认后启动了清理", started[-1] == "manual", started)

    print("\n[4] 完成结果写进界面，不再弹第二个窗")
    fake.clear()
    app.cleaning = True
    app.handle(("clean_done", 0.0, 2, 1, 5 * 1024 ** 2))
    root.update()
    check("★ 清理完成零弹窗", fake.calls == [], fake.calls)
    banner = app.result_banner.cget("text")
    check("界面结果条显示完成信息", "清理完成" in banner, banner)
    check("结果条已 pack 到界面上", app.result_banner.winfo_manager() == "pack")
    check("状态栏也显示结果",
          "清理完成" in app.status_label.cget("text"),
          app.status_label.cget("text"))

    fake.clear()
    app._notice("这是一条界面内提示")
    check("_notice 不弹窗", fake.calls == [], fake.calls)

    root.destroy()
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)

    print("\n" + "=" * 60)
    print(f"PASS {len(PASS)}   FAIL {len(FAIL)}")
    if FAIL:
        for f in FAIL:
            print("  FAILED: " + f)
        sys.exit(1)
    print("v3.0.2 全部回归通过（全程只读真实磁盘）")


if __name__ == "__main__":
    main()
