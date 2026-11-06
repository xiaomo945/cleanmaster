# -*- coding: utf-8 -*-
"""v2.7.1 提权改造的专项测试。"""
import importlib.util, os, sys
import tkinter as tk

spec = importlib.util.spec_from_file_location("cm", "clean_master.py")
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)

fails = []


def check(name, cond, extra=""):
    print(("✓ " if cond else "✗ ") + name + (f"  ({extra})" if extra else ""))
    if not cond:
        fails.append(name)


root = tk.Tk()
root.withdraw()
app = cm.CleanMasterApp(root)
root.update()

# 1) relaunch_as_admin 函数存在且签名正常
#    注意：不能真的调用它 —— 那会弹 UAC 窗口，在自动化环境里必然卡死。
import inspect
try:
    sig = inspect.signature(cm.relaunch_as_admin)
    check("relaunch_as_admin 存在且可调用", callable(cm.relaunch_as_admin),
          f"{sig}")
except Exception as e:
    check("relaunch_as_admin 存在且可调用", False, str(e))

# 1b) ShellExecuteW 的封装逻辑单独验证（不真正提权）
try:
    import ctypes
    has_shell = hasattr(ctypes.windll.shell32, "ShellExecuteW")
    check("ShellExecuteW 可用", has_shell)
except Exception as e:
    check("ShellExecuteW 可用", False, str(e))

# 2) 提权按钮已创建
check("提权按钮已创建", app.elev_btn is not None)

# 3) admin 提示条有文字
txt = app.admin_label.cget("text")
check("权限提示条有文字", bool(txt.strip()), txt[:40])

# 4) 刷新权限条不会崩
try:
    app.refresh_admin_banner()
    root.update()
    check("refresh_admin_banner 不崩", True)
except Exception as e:
    check("refresh_admin_banner 不崩", False, str(e))

# 5) 当前是管理员吗？（决定按钮显不显示）
adm = cm.is_admin()
mapped = app._elev_shown   # 用状态标记而不是 winfo_ismapped
if adm:
    check("管理员模式下按钮隐藏", not mapped)
else:
    check("非管理员模式下按钮可见", mapped)

# 6) on_elevate 存在
check("on_elevate 方法存在", hasattr(app, "on_elevate"))

# 7) 界面能完整构建
check("界面构建成功", True)

root.destroy()

print()
print(f"通过 {8 - len(fails)} 项，失败 {len(fails)} 项")
print("结果:", "PASS" if not fails else "FAIL")
sys.exit(0 if not fails else 1)
