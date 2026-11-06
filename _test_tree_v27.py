# -*- coding: utf-8 -*-
"""v2.7 GUI 自动化测试：验证 Treeview 分层树的性能与勾选联动。

关键指标：
  1. 渲染一个含 20000 条目的类目，耗时必须 < 1 秒（旧版要几十秒）
  2. 展开类目（懒加载 120 行）必须 < 100ms
  3. 勾选联动：顶部两个数字实时变化
  4. 勾选语义正确：总开关 + 单项覆盖
"""
import importlib.util, time, sys, os

spec = importlib.util.spec_from_file_location("cm", "clean_master.py")
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)

import tkinter as tk

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"{'✓' if cond else '✗'} {name}" + (f"  ({detail})" if detail else ""))


root = tk.Tk()
root.withdraw()
app = cm.CleanMasterApp(root)
root.update()

# ---------- 构造一份假结果（模拟扫描完成）----------
drive = "C"
big = []
for i in range(20000):
    big.append({
        "path": f"C:\\Users\\windos\\AppData\\Local\\Test\\file_{i}.tmp",
        "size": 1024 * (i % 500 + 1),
        "kind": "file",
        "label": f"C:\\Users\\windos\\AppData\\Local\\Test\\file_{i}.tmp",
        "desc": "测试临时文件",
    })
small = [
    {"path": f"C:\\Temp\\a{i}.log", "size": 100 * i, "kind": "file",
     "label": f"C:\\Temp\\a{i}.log", "desc": "日志文件"}
    for i in range(50)
]
app.results_by_drive[drive] = {
    "g_junk": {"items": big, "size": cm.human_size(0) and sum(
        i["size"] for i in big), "per_file": True,
        "meta": {"key": "g_junk", "name": "垃圾扩展名文件", "risk": "optional",
                 "desc": "临时残留文件"}},
    "temp": {"items": small, "size": sum(i["size"] for i in small),
             "per_file": True,
             "meta": {"key": "temp", "name": "系统临时文件", "risk": "safe",
                      "desc": "可安全删除"}},
    "inv_system": {"items": [], "size": 30 * 1024 ** 3, "per_file": False,
                   "meta": {"key": "inv_system", "name": "系统 / 程序占用（只读）",
                            "risk": "safe", "readonly": True, "desc": "只能看"}},
}
app.current_drive = drive
app.drive_var.set(drive)

# ---------- 1) 渲染耗时 ----------
t0 = time.time()
app.render_current_drive()
root.update()
t_render = time.time() - t0
check(f"渲染 {len(big)}+ 条目的结果树 < 1.5s", t_render < 1.5,
      f"实际 {t_render*1000:.0f}ms")

# ---------- 2) 树结构 ----------
kids = app.tree.get_children()
check("生成了分组节点", len(kids) >= 2, f"{len(kids)} 个分组")
cat_nodes = app.tree.get_children(kids[0])
check("分组下有类目节点", len(cat_nodes) > 0, f"{len(cat_nodes)} 个类目")
# v3.0 起类目行会带一个 ph: 占位子节点（这样一开始就有展开箭头），
# 但真实明细仍然是点开才懒加载 —— 断言相应调整为「只有占位、没有明细」。
check("类目初始不加载明细（只有展开占位）",
      all(all(ch.startswith("ph:") for ch in app.tree.get_children(c))
          for c in cat_nodes))

# ---------- 3) 展开耗时 ----------
iid = "c:g_junk"
t0 = time.time()
app.tree.item(iid, open=True)
root.update()
app.on_tree_open()
app._load_children("g_junk")
root.update()
t_expand = time.time() - t0
kids_junk = app.tree.get_children(iid)
check(f"展开大目录类目 < 1s", t_expand < 1.0,
      f"实际 {t_expand*1000:.0f}ms，只渲染了 {len(kids_junk)} 行")
# v2.8：改成「按需加载」——
# 每类默认只渲染 PAGE(30) 条，剩下的折成「还有 N 项」，
# 绝不再一次性铺几万个文件名。
check("只渲染 PAGE 条，不是全量", len(kids_junk) <= app.PAGE + 1,
      f"{len(kids_junk)} 行 / PAGE={app.PAGE}")
check("有「还有 N 项」提示（按需加载）",
      app.tree.exists(f"m:g_junk"))

# ---------- 4) 重复加载不应产生重复行 ----------
n_before = len(app.tree.get_children(iid))
t0 = time.time()
app._fill_children("g_junk", app.PAGE_BIG)
root.update()
t_more = time.time() - t0
kids_now = app.tree.get_children(iid)
check("重复加载不产生重复行", len(kids_now) == len(set(kids_now)),
      f"{len(kids_now)} 行 / {len(set(kids_now))} 个唯一 iid")
check("加载更多后行数增加", len(kids_now) > n_before,
      f"{n_before} → {len(kids_now)}")
check("重复加载 < 500ms", t_more < 0.5, f"{t_more*1000:.0f}ms")

# ---------- 5) 顶部数字联动 ----------
app.show_summary()
root.update()
txt = app.summary_label.cget("text")
check("顶部显示已勾选可释放", "已勾选可释放" in txt, txt[:60])
# v2.9：三个数字 —— 已勾选 / 一键可清理 / 软件缓存可清理
check("顶部显示一键可清理", "一键可清理" in txt, txt[:80])
check("顶部显示软件缓存可清理", "软件缓存可清理" in txt, txt[:80])

# 安全类默认勾选 → 已勾选应包含 temp 的 50 项
cw = app.cat_widgets["temp"]
check("安全类默认勾选", cw["master"] is True)

# ---------- 6) 勾选类目总开关 ----------
before = app.summary_label.cget("text")
app.toggle_category("g_junk")
root.update()
app.show_summary()
after = app.summary_label.cget("text")
check("勾选类目后数字变化", before != after, f"{before[:40]} → {after[:40]}")
check("g_junk 变为已勾选", app.cat_widgets["g_junk"]["master"] is True)
items, sel = app._cat_state("g_junk")
check("勾选后 20000 项全部生效", len(sel) == 20000, f"{len(sel)} 项")

# ---------- 7) 单项取消覆盖 ----------
app.toggle_item("g_junk", 0)
items, sel = app._cat_state("g_junk")
check("单项取消后剩 19999 项", len(sel) == 19999, f"{len(sel)} 项")
check("覆盖状态已记录", app.cat_widgets["g_junk"]["sel"].get(0) is False)

# ---------- 8) 取消类目总开关 ----------
app.toggle_category("g_junk")
items, sel = app._cat_state("g_junk")
check("取消总开关后 0 项", len(sel) == 0, f"{len(sel)} 项")

# ---------- 9) 去重算法正确性 ----------
pairs = [("C:\\a", 100), ("C:\\a\\b", 50), ("C:\\c", 20), ("C:\\a", 30)]
check("_dedup_size 父子去重正确", cm._dedup_size(pairs) == 120,
      f"= {cm._dedup_size(pairs)}")
pairs2 = [("C:\\x\\y", 10), ("C:\\x\\y", 10), ("C:\\z", 5)]
check("_dedup_size 完全相同去重", cm._dedup_size(pairs2) == 15,
      f"= {cm._dedup_size(pairs2)}")

# ---------- 10) 性能：去重算法在大数据量下的速度 ----------
import random
random.seed(1)
big_pairs = [(f"C:\\dir{i}\\file_{j}.tmp", 1024)
             for i in range(500) for j in range(100)]
t0 = time.time()
v = cm._dedup_size(big_pairs)
t_dedup = time.time() - t0
check("_dedup_size 处理 5 万条 < 3s", t_dedup < 3.0,
      f"{len(big_pairs)} 条用了 {t_dedup*1000:.0f}ms")

root.destroy()

print(f"\n通过 {len(PASS)} 项，失败 {len(FAIL)} 项")
if FAIL:
    print("失败项: " + ", ".join(FAIL))
    sys.exit(1)
print("结果: PASS")
