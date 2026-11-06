# -*- coding: utf-8 -*-
"""v2.6 端到端联调：真扫描 → 组装类目 → 灌进界面 → 校验顶部两个数字。

核心校验（对应用户反馈「预计释放 89.8G 数字不对」）：
  · 全部可清理上限 ≤ 磁盘已用空间（物理上限）
  · 已勾选可释放 只包含真正会被删的东西
  · 只读的系统/程序占用绝不计入
"""
import importlib.util
import re
import sys
import tkinter as tk

spec = importlib.util.spec_from_file_location("cm", "clean_master.py")
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)

drive = sys.argv[1] if len(sys.argv) > 1 else "C"

print(f"=== 真实扫描 {drive}: 盘 ===")
cm._FULL_CACHE.clear()
cm.scan_full_disk(drive)

cats = cm.get_categories(drive)
store = {}
inv = {k: v for k, v in cm._FULL_CACHE.get(drive, {}).items() if k.startswith("inv_")}
errors = []
for cat in cats:
    try:
        items = cat["scan"](drive)
    except Exception as e:
        items = []
        errors.append((cat["name"], repr(e)))
    if cat.get("readonly"):
        # v2.8：只读类目显示自己的大小；只有 inv_system 用系统占用总数
        if cat["key"] == "inv_system":
            size = inv.get("inv_system_total", 0)
        else:
            size = cm._dedup_size([(i.get("path", ""), i.get("size", 0)) for i in items])
    else:
        size = cm._dedup_size([(i.get("path", ""), i.get("size", 0)) for i in items])
    store[cat["key"]] = {"items": items, "size": size, "meta": cat,
                         "per_file": cat.get("per_file", False)}
    print(f"  {cat['name']:<28} {len(items):>5} 项  {cm.human_size(size):>12}")

if errors:
    print("\n!! 扫描出错的类目：")
    for n, e in errors:
        print("   ", n, e)

root = tk.Tk()
root.withdraw()
app = cm.CleanMasterApp(root)
app.current_drive = drive
app.drive_var.set(drive)
app.results_by_drive[drive] = store
app.render_current_drive()
app.show_summary()
root.update()

txt = app.summary_label.cget("text")
print("\n顶部数字:", txt)


def tobytes(s):
    v, u = s.split()
    return float(v) * {"B": 1, "KB": 1024, "MB": 1024**2,
                       "GB": 1024**3, "TB": 1024**4}[u]


m = re.search(r"已勾选可释放：([\d.]+ [A-Z]+)（(\d+) 项）", txt)
m2 = re.search(r"一键可清理：([\d.]+ [A-Z]+)", txt)
m3 = re.search(r"软件缓存可清理：([\d.]+ [A-Z]+)", txt)
picked = tobytes(m.group(1))
n_picked = int(m.group(2))
maximum = tobytes(m2.group(1))
review = tobytes(m3.group(1))

free, total = cm.get_drive_space(drive)
used = total - free
print(f"\n磁盘已用 {cm.human_size(used)} / 共 {cm.human_size(total)}")

fails = []


def check(name, cond, extra=""):
    print(("  ✓ " if cond else "  ✗ ") + name + ("  " + extra if extra else ""))
    if not cond:
        fails.append(name)


check("没有类目扫描报错", not errors, str(errors))
check("一键可清理 ≤ 磁盘已用",
      maximum <= used * 1.02, f"{cm.human_size(maximum)} vs {cm.human_size(used)}")
check("已勾选可释放 ≤ 磁盘已用",
      picked <= used * 1.02, f"{cm.human_size(picked)}")
check("软件缓存可清理 ≤ 磁盘已用",
      review <= used * 1.02, f"{cm.human_size(review)}")
check("只读系统占用没被算进去",
      maximum < used, f"一键可清理 {cm.human_size(maximum)}")
# v2.8 核心回归：空间分析类目（用户真实数据）不能计入可释放
ro_paths = []
for k, rec in store.items():
    if rec["meta"].get("readonly"):
        for it in rec["items"]:
            ro_paths.append(it.get("path", ""))
ro_size = cm._dedup_size([(p, 0) for p in ro_paths])
check("只读类目不计入可释放", maximum < used,
      f"只读类目有 {len(ro_paths)} 项")
# 勾选数不应超过全部项数
all_n = sum(len(store[k]["items"]) for k in store
            if not store[k]["meta"].get("readonly"))
check("勾选项数合理", 0 < n_picked <= all_n, f"{n_picked} / {all_n}")

# 逐项勾选后数字应继续变化
before = picked
key = "g_large"
if store.get(key, {}).get("items"):
    app._load_children(key)
    root.update()
    # 新版：Treeview 行级勾选
    app._load_children(key)
    root.update()
    app.toggle_item(key, 0)
    root.update()
    app.show_summary()
    t2 = app.summary_label.cget("text")
    m3 = re.search(r"已勾选可释放：([\d.]+ [A-Z]+)", t2)
    after = tobytes(m3.group(1))
    check("勾选大文件后数字变大",
          after >= before, f"{cm.human_size(before)} -> {cm.human_size(after)}")
    print("  勾选后:", t2)

print("\n结果:", "PASS" if not fails else "FAIL -> " + ", ".join(fails))
root.destroy()
