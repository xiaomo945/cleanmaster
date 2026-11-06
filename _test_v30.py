#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3.0 回归测试：勾选 / 折叠 / 大目录逐层浏览 / 盘符描述 / 保护锁定。

全程只读，不删除任何真实文件。
运行：py -3 _test_v30.py
"""
import os
import sys
import tempfile
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


def main():
    tk = cm.tk
    root = tk.Tk()
    root.geometry("1200x800")
    app = cm.CleanMasterApp(root)

    # ---------------- 1. 描述按盘符生成 ----------------
    print("\n[1] 根目录用途描述")
    d_c = cm._top_dir_desc("Users", "C")
    d_f = cm._top_dir_desc("Users", "F")
    check("C 盘 Users 不再写「从 C 盘迁移来的」", "迁移" not in d_c[0], d_c[0])
    check("C 盘 Users 说明是 Windows 用户目录", "Windows 用户目录" in d_c[0])
    check("F 盘 Users 保留迁移说明", "迁移" in d_f[0], d_f[0])
    check("C 盘 Users 提示可逐层展开", "逐层展开" in d_c[2])

    tops = cm.classify_top_dirs("C", {"C:" + os.sep + "Users": 47 * 1024 ** 3})
    # 根目录真有 pagefile.sys 时会额外产出系统大文件说明行，属正常
    check("classify_top_dirs 至少产出 1 条", len(tops) >= 1, len(tops))
    check("Users 排在最前（按体积降序）",
          bool(tops) and tops[0]["label"].lower() == "users\\",
          [t["label"] for t in tops])
    if tops:
        t = tops[0]
        check("顶层目录带 browse 展开标记", t.get("browse") is True)
        check("顶层目录不可整体删除", t.get("selectable") is False)
        check("顶层目录 kind=readonly", t.get("kind") == "readonly")
        check("顶层目录描述不含迁移", "迁移" not in t["desc"])

    # ---------------- 2. 系统路径硬锁 ----------------
    print("\n[2] 受保护路径判定")
    cases = [
        (r"C:\Windows\SoftwareDistribution", "C", True),
        (r"C:\Program Files\NVIDIA", "C", True),
        (r"C:\ProgramData\Package Cache", "C", True),
        (r"C:\$Recycle.Bin\S-1-5-21", "C", True),
        (r"F:\pagefile.sys", "F", True),
        (r"C:/Windows/System32", "C", True),   # 正斜杠也要认
        (r"C:\Users", "C", True),          # v3.0.1 起顶层用户目录也硬锁
        (r"C:\Users\windos", "C", True),   # 当前账户主目录，禁止整体删除
        (r"C:\Users\windos\AppData\Local\Temp", "C", False),
        (r"C:\Users\windos\Downloads", "C", False),
        (r"E:\Games\SteamLibrary", "E", False),
        (r"F:\xiangmu\aizhibo", "F", False),
    ]
    for p, d, want in cases:
        got = cm._is_protected_browse(p, d)
        check(f"protected({p}) == {want}", got == want, got)
    check("clean_item 拒绝受保护的浏览项",
          cm.clean_item({"kind": "dir", "path": r"C:\Windows\Temp\__never__",
                         "browse": True}) is False)

    # ---------------- 3. 一级枚举 ----------------
    print("\n[3] 大目录一级枚举（体积查表、不递归读盘）")
    tmp = tempfile.mkdtemp(prefix="cm_v30_")
    os.mkdir(os.path.join(tmp, "BigFolder"))
    with open(os.path.join(tmp, "BigFolder", "a.bin"), "wb") as f:
        f.write(b"x" * 4096)
    with open(os.path.join(tmp, "small.txt"), "w") as f:
        f.write("x")
    sizes = {os.path.join(tmp, "BigFolder"): 5 * 1024 ** 3}
    items, total = cm.enumerate_browse_dir("C", tmp, sizes, depth=2)
    check("枚举到 2 个子项", total == 2, (total, [i["label"] for i in items]))
    check("按体积降序（大的在前）",
          bool(items) and items[0]["label"].startswith("BigFolder"),
          [i["label"] for i in items])
    big = [i for i in items if i["label"].startswith("BigFolder")][0]
    check("目录体积直接查 dir_sizes", big["size"] == 5 * 1024 ** 3, big["size"])
    check("子目录可继续展开", big["browse"] is True)
    check("文件不可展开", all(not i["browse"] for i in items if not i["is_dir"]))
    check("用户临时目录下的项可勾选", all(i["selectable"] for i in items))

    # ---------------- 4. 注入一份假扫描结果 ----------------
    print("\n[4] 树渲染 / 勾选 / 折叠")
    store = {
        "temp": {
            "items": [{"path": os.path.join(tmp, "small.txt"), "size": 1,
                       "kind": "file", "label": "small.txt", "desc": "测试文件"}],
            "size": 1,
            "meta": {"key": "temp", "name": "系统临时文件",
                     "risk": "safe", "desc": "测试类目"},
            "per_file": True,
        },
        "sc_folders": {
            "items": [dict(tops[0])],
            "size": 47 * 1024 ** 3,
            "meta": {"key": "sc_folders",
                     "name": "根目录文件夹用途说明（可逐层展开）",
                     "risk": "optional", "readonly": True,
                     "per_file": True, "desc": "测试只读类目"},
            "per_file": True,
        },
    }
    app.current_drive = app.drive_var.get()
    app.results_by_drive[app.current_drive] = store
    app.render_current_drive()
    root.update()

    check("选择列编号 = #1（不是旧版的 #2）", app.sel_col == "#1", app.sel_col)

    ciid = "c:temp"
    check("类目行存在", app.tree.exists(ciid))
    check("类目行预置展开箭头占位",
          any(x.startswith("ph:") for x in app.tree.get_children(ciid)))
    check("名称前有真实 ☐ / ☑ 前缀",
          app.tree.item(ciid, "text").startswith(("☐", "☑", "—", "×")),
          app.tree.item(ciid, "text"))

    class E:
        def __init__(self, x, y):
            self.x, self.y = x, y

    def at(iid, col="sel", dx=None):
        bb = app.tree.bbox(iid, col)
        x = bb[0] + (dx if dx is not None else bb[2] // 2)
        return E(x, bb[1] + bb[3] // 2)

    before = app.tree.set(ciid, "sel")
    app.on_tree_click(at(ciid))
    after = app.tree.set(ciid, "sel")
    check("点「选择」列能真正打勾/取消", before != after, (before, after))
    check("名称前缀跟着勾选变化",
          app.tree.item(ciid, "text").startswith(after))

    # 关键回归：模拟 Tk 折叠后，ButtonRelease 不能把 open 改回 True
    app.tree.item(ciid, open=True)
    app._maybe_expand(at(ciid, "#0", dx=13))     # indicator 位置
    check("展开时点箭头不会被强制改写", bool(app.tree.item(ciid, "open")))
    app.tree.item(ciid, open=False)               # Tk 自己折叠
    app._maybe_expand(at(ciid, "#0", dx=13))
    check("★ 折叠后能收回（旧版会被强行展开）",
          not bool(app.tree.item(ciid, "open")),
          app.tree.item(ciid, "open"))

    # 点名称文字也能勾选
    before = app.tree.set(ciid, "sel")
    app.on_tree_click(at(ciid, "#0", dx=60))
    check("点名称也能勾选（原来点圆点没反应）",
          app.tree.set(ciid, "sel") != before,
          (before, app.tree.set(ciid, "sel")))

    # ---------------- 5. 大目录展开 + 手动勾选 ----------------
    print("\n[5] 大目录逐层展开与手动选择")
    app._load_children("sc_folders")
    root.update()
    top_iid = "i:sc_folders:0"
    check("顶层 Users 行已渲染", app.tree.exists(top_iid))
    check("顶层 Users 行显示只读标记（不可整体删）",
          app.tree.set(top_iid, "sel") in ("—", "×"),
          app.tree.set(top_iid, "sel"))
    check("顶层 Users 行有展开箭头",
          any(x.startswith("ph:") for x in app.tree.get_children(top_iid)))

    # 同步走一遍后台枚举的产物（不真的起线程）
    app._insert_browse_children(top_iid, app.current_drive, items, total)
    root.update()
    b_rows = [x for x in app.tree.get_children(top_iid) if x.startswith("b:")]
    check("展开后出现可勾选子项", len(b_rows) == len(items), len(b_rows))
    if b_rows:
        bid = b_rows[0]
        app.tree.see(bid)          # 展开祖先节点，让 bbox 可见
        root.update()
        node = app.browse_nodes[bid]
        check("子项登记了浏览节点", node["item"]["path"].startswith(tmp))
        before = app.tree.set(bid, "sel")
        app.on_tree_click(at(bid))
        check("子项点击可勾选", app.tree.set(bid, "sel") != before,
              (before, app.tree.set(bid, "sel")))
        picks = app._browse_picks()
        check("手动选择进入待删清单", len(picks) == 1, len(picks))
        app.show_summary()
        check("顶部统计出现「手动挑选」",
              "手动挑选" in app.summary_label.cget("text"),
              app.summary_label.cget("text")[:120])

    # 受保护子项不许勾选
    lock_iid = "b:999999"
    app.tree.insert(top_iid, "end", iid=lock_iid, text="×  模拟系统目录",
                    values=("×", "1 GB", "系统目录", "锁定"), tags=("ro",))
    app.browse_nodes[lock_iid] = {
        "item": {"path": r"C:\Windows\System32\__fake__", "size": 1,
                 "kind": "dir", "protected": True, "selectable": False},
        "drive": app.current_drive, "loaded": True}
    app._set_row_text(lock_iid, "模拟系统目录", "×")
    n_before = len(app._browse_picks())
    app.toggle_browse(lock_iid)
    check("受保护子项点不动", len(app._browse_picks()) == n_before)
    check("受保护子项仍显示 ×", app.tree.set(lock_iid, "sel") == "×")

    # ---------------- 6. 一键清理不碰手动项 ----------------
    print("\n[6] 一键清理边界")
    plan_keys = [k for k in app.cat_widgets if not k.startswith("sc_")]
    check("一键清理的类目里不含 __browse__", "__browse__" not in plan_keys)
    check("sc_folders 是只读类目（不进一键清理）",
          app.cat_widgets.get("sc_folders", {}).get("readonly") is True)

    root.destroy()
    # 清理临时目录（只删本次测试自己造的，不用工具链的删除函数）
    import shutil
    try:
        shutil.rmtree(tmp)
    except OSError:
        pass

    print("\n" + "=" * 60)
    print(f"PASS {len(PASS)}   FAIL {len(FAIL)}")
    if FAIL:
        for f in FAIL:
            print("  FAILED: " + f)
        sys.exit(1)
    print("v3.0 全部回归通过")


if __name__ == "__main__":
    main()
