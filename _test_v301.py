#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3.0.1 回归测试：用户主目录识别 + 整体删除硬锁。

起因：C:\\Users\\windos（48.3GB）被标成「未识别用途」且能整目录勾选。
全程只读，不删除任何真实文件。
运行：py -3 _test_v301.py
"""
import os
import sys
import importlib.util

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


HOME = r"C:\Users\windos"


def main():
    print("\n[1] 用户主目录识别（不再显示「未识别用途」）")
    d = cm._top_dir_desc("windos", "C", HOME)
    check("识别成 Windows 用户主目录", "用户主目录" in d[0], d[0])
    check("说明里点名当前登录账户", "当前登录账户" in d[0])
    check("不再出现「未识别」", "未识别" not in d[0] + d[2])
    check("写明整体删除的后果", "NTUSER.DAT" in d[1], d[1])
    check("建议里写明已锁定", "锁定" in d[2], d[2])
    w = cm._top_dir_desc("Windows", "C", r"C:\Windows")
    check("C:\\Windows 识别为系统核心目录", "系统核心目录" in w[0], w[0])
    check("C:\\Windows 不再显示未识别", "未识别" not in w[0])

    print("\n[2] 保护判定：用户主目录 / 系统目录锁住，深层缓存照常可清")
    locked = [
        HOME, r"C:\Users", r"C:\Users\windos\AppData",
        r"C:\Users\windos\AppData\Local",
        r"C:\Users\windos\AppData\Roaming",
        r"C:\Windows", r"E:\windows", r"F:\Windows.old",
    ]
    for p in locked:
        check("锁住 " + p, cm._is_protected_browse(p) is True)
    for p in locked:
        check("clean_item 闸口挡住 " + p,
              cm._is_whole_dir_blocked(p) is True)

    open_paths = [
        r"C:\Windows\Temp",
        r"C:\Users\windos\AppData\Local\Temp",
        r"C:\Users\windos\Downloads\old_installer.exe",
        r"C:\Users\windos\AppData\Local\Google\Chrome\User Data\Default\Cache",
    ]
    for p in open_paths:
        check("深层清理项不被 whole 闸口误伤 " + p,
              cm._is_whole_dir_blocked(p) is False)

    print("\n[3] 真实枚举 C:\\Users（只读 scandir，不递归）")
    items, total = cm.enumerate_browse_dir("C", r"C:\Users", {}, depth=2)
    home = [i for i in items if i["path"].lower() == HOME.lower()]
    check("枚举到 windos 主目录", len(home) == 1,
          [i["label"] for i in items])
    if home:
        h = home[0]
        check("主目录 protected=True", h["protected"] is True)
        check("主目录 selectable=False", h["selectable"] is False)
        check("主目录说明是用户主目录", "用户主目录" in h["desc"], h["desc"])
        check("主目录影响列写明已锁定", "锁定" in h["impact"], h["impact"])
        check("主目录仍可展开（能挑缓存）", h["browse"] is True)

    print("\n[4] clean_item 绝不整体删用户主目录")
    assert os.path.isdir(HOME), "测试机没有该用户目录"
    got = cm.clean_item({"kind": "dir", "path": HOME, "size": 48 * 1024 ** 3,
                         "browse": True})
    check("clean_item 返回 False", got is False)
    check("目录仍然存在（没被真删）", os.path.isdir(HOME))
    check("即使没有 browse 标记也挡住",
          cm.clean_item({"kind": "dir", "path": HOME}) is False)
    check("AppData 整体也挡住",
          cm.clean_item({"kind": "dir",
                         "path": r"C:\Users\windos\AppData"}) is False)

    print("\n[5] GUI：windos 行显示 ×，点了也勾不上")
    tk = cm.tk
    root = tk.Tk()
    root.geometry("1200x800")
    app = cm.CleanMasterApp(root)
    app.current_drive = app.drive_var.get()
    grp = app.tree.insert("", "end", iid="g:t", text="测试分组",
                          values=("", "", "", ""), open=True)
    par = app.tree.insert(grp, "end", iid="p:t", text="Users\\",
                          values=("", "", "", ""), open=True)
    app._insert_browse_children(par, "C", items, total)
    root.update()

    rows = [x for x in app.tree.get_children(par) if x.startswith("b:")]
    home_rows = [x for x in rows
                 if app.browse_nodes.get(x, {}).get("item", {})
                 .get("path", "").lower() == HOME.lower()]
    check("树里渲染了 windos 行", len(home_rows) == 1, len(rows))
    if home_rows:
        bid = home_rows[0]
        app.tree.see(bid)
        root.update()
        check("显示 × 而不是 ☐/☑", app.tree.set(bid, "sel") == "×",
              app.tree.set(bid, "sel"))
        check("名称前缀也是 ×",
              app.tree.item(bid, "text").startswith("×"),
              app.tree.item(bid, "text"))
        app.toggle_browse(bid)
        check("toggle_browse 勾不上", app.tree.set(bid, "sel") == "×")
        n_before = len(app._browse_picks())
        app.browse_by_drive["C"]["sel"].add(HOME)
        app.browse_by_drive["C"]["items"][HOME] = (
            app.browse_nodes[bid]["item"])
        check("旧勾选状态也进不了待删清单",
              len(app._browse_picks()) == n_before,
              (n_before, len(app._browse_picks())))
        check("windos 不在待删清单里",
              all(x.get("path", "").lower() != HOME.lower()
                  for x in app._browse_picks()))

    root.destroy()

    print("\n" + "=" * 60)
    print(f"PASS {len(PASS)}   FAIL {len(FAIL)}")
    if FAIL:
        for f in FAIL:
            print("  FAILED: " + f)
        sys.exit(1)
    print("v3.0.1 全部回归通过（全程只读）")


if __name__ == "__main__":
    main()
