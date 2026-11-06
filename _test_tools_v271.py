# -*- coding: utf-8 -*-
"""v2.7.1 新增功能测试：工具栏四个按钮 + 提权 + 分页。"""
import importlib.util, time
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

# 造两个假类目：一大一小
big_items = [{"path": f"C:\\tmp\\f{i}.tmp", "size": i * 100, "kind": "file",
              "label": f"C:\\tmp\\f{i}.tmp", "desc": "临时文件"} for i in range(1500)]
small_items = [{"path": "C:\\tmp\\a.log", "size": 10, "kind": "file",
                "label": "C:\\tmp\\a.log", "desc": "日志文件"}]

for key, items in (("bigcat", big_items), ("smallcat", small_items)):
    app.cat_widgets[key] = {
        "per_file": True, "items": items, "risk": "optional", "readonly": False,
        "mark": "☐", "iid": f"c:{key}", "count": len(items), "size": 0,
        "desc": "", "shown": 0, "meta": {},
        "master": False, "sel": {}, "loaded": False,
    }
    app.tree.insert("", "end", iid=f"c:{key}", text=key, values=("☐", "", ""))
app.root.update()

# 1) v2.8 起改成【按需加载】：默认只渲染 PAGE 条，其余折进「还有 N 项」
app._load_children("bigcat")
root.update()
n_loaded = len(app.tree.get_children("c:bigcat"))
check("展开只渲染 PAGE 条（不刷屏）", n_loaded <= app.PAGE + 1,
      f"{n_loaded} 行 / 共 {len(big_items)} 项 / PAGE={app.PAGE}")

# 2) 剩余条目折成「还有 N 项」提示行
check("有「还有 N 项」提示行", app.tree.exists("m:bigcat"))

# 3) 点「还有 N 项」能继续加载；且任何时候都不该出现重复行
before = len(app.tree.get_children("c:bigcat"))
app._fill_children("bigcat", app.PAGE_BIG)
root.update()
after = len(app.tree.get_children("c:bigcat"))
check("加载更多能增加行数", after > before, f"{before} → {after}")
app._fill_children("bigcat", app.PAGE_BIG)
root.update()
kids = app.tree.get_children("c:bigcat")
check("重复加载不产生重复行", len(kids) == len(set(kids)),
      f"{len(kids)} 行 / {len(set(kids))} 个唯一 iid")
check("加载的行数不超过总条目数",
      len([k for k in kids if k.startswith("i:")]) <= len(big_items),
      f"{len([k for k in kids if k.startswith('i:')])} / {len(big_items)}")

# 4) 总开关切换：数字联动
app.toggle_category("bigcat")
root.update()
_, sel = app._cat_state("bigcat")
check("总开关全选生效", len(sel) == len(big_items), f"{len(sel)}/{len(big_items)}")

# 5) 取消总开关
app.toggle_category("bigcat")
root.update()
_, sel = app._cat_state("bigcat")
check("总开关全不选生效", len(sel) == 0, f"{len(sel)} 项")

# 6) 手动取消一项后，加载更多的新行应跟随总开关
app.toggle_category("bigcat")
root.update()
app.toggle_item("bigcat", 0)
root.update()
check("单项覆盖被记录", app.cat_widgets["bigcat"]["sel"].get(0) is False)
# 第 0 项被手动取消 → 它应是 ☐，其余跟随总开关应是 ☑
marks = [app.tree.set(f"i:bigcat:{i}", "sel") for i in range(5)]
check("手动取消项显示 ☐、其余显示 ☑",
      marks[0] == "☐" and all(m == "☑" for m in marks[1:]), f"{marks[:3]}")

# 7) 全部收起
app.expand_all()
root.update()
app.collapse_all()
root.update()
opens = [app.tree.item(c, "open") for c in app._all_category_nodes()]
check("全部收起生效", not any(opens), f"{opens}")

# 8) 全选/全不选
app.toggle_all_categories()
root.update()
allsel = sum(len(app._cat_state(k)[1]) for k in ("bigcat", "smallcat"))
check("一键全选生效", allsel == len(big_items) + len(small_items), f"{allsel} 项")
app.toggle_all_categories()
root.update()
allsel = sum(len(app._cat_state(k)[1]) for k in ("bigcat", "smallcat"))
check("一键全不选生效", allsel == 0, f"{allsel} 项")

# 9) 只看已勾选
app.toggle_category("smallcat")
root.update()
app.show_only_checked()
root.update()
check("只看已勾选不崩", True, app.tree_tip.cget("text"))
app.show_only_checked()
root.update()
check("恢复全部显示不崩", True)

# 10) 提权相关
check("提权按钮存在", app.elev_btn is not None)
check("权限条有内容", bool(app.admin_label.cget("text").strip()))

root.destroy()
print()
print(f"通过 {10 - len(fails)} 项，失败 {len(fails)} 项")
print("结果:", "PASS" if not fails else "FAIL")
