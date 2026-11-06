# -*- coding: utf-8 -*-
"""v2.8 一键清理流程测试（不弹窗，直接验证选单逻辑）。"""
import importlib.util, sys, time, tkinter as tk
spec = importlib.util.spec_from_file_location("cm", "clean_master.py")
cm = importlib.util.module_from_spec(spec); spec.loader.exec_module(cm)

root = tk.Tk(); root.withdraw()
app = cm.CleanMasterApp(root)
app.current_drive="C"; app.drive_var.set("C")
app.start_scan()
dl=time.time()+300
while app.scanning and time.time()<dl:
    root.update(); time.sleep(0.2)
root.update()

fails=[]
def check(n,c,e=""):
    print(("  ✓ " if c else "  ✗ ")+n+("  "+e if e else ""))
    if not c: fails.append(n)

# 1) 一键清理的选单：只有 safe 类
plan={}
for key,cw in app.cat_widgets.items():
    if cw.get("readonly"): continue
    meta=app.results_by_drive['C'].get(key,{}).get('meta',{})
    if meta.get('risk')!='safe': continue
    _,sel=app._cat_state(key)
    if sel: plan[key]=sel
check("一键清理只选安全类", set(plan) <= {c['key'] for c in cm.system_categories() if c['risk']=='safe'},
      str(sorted(plan)))

# 2) 一键清理绝不包含用户数据类目
forbidden = {"g_old","g_large","g_dup","inv_bigfolders","inv_bigfiles",
             "inv_image","inv_video","inv_audio","inv_doc","inv_archive",
             "inv_installer","inv_other","inv_system","ai_cache","dl_old"}
check("一键清理不含用户数据", not (set(plan) & forbidden), str(sorted(set(plan)&forbidden)))

# 3) 空间分析类目全是只读
ro_ok = all(app.cat_widgets[k].get('readonly')
            for k in ('inv_bigfolders','inv_bigfiles','inv_image','inv_video',
                      'inv_audio','inv_doc','inv_archive','inv_installer','inv_other','inv_system'))
check("空间分析类目全部只读", ro_ok)

# 4) 顶部数字不含只读
app.show_summary()
txt=app.summary_label.cget('text')
print("  顶部:", txt)
import re
m=re.search(r"一键可清理：([\d.]+ [A-Z]+)", txt)
def tob(s):
    v,u=s.split(); return float(v)*{"B":1,"KB":1024,"MB":1024**2,"GB":1024**3,"TB":1024**4}[u]
free,total=cm.get_drive_space("C"); used=total-free
safe_t=tob(m.group(1))
check("一键可清理 ≤ 磁盘已用", safe_t<=used*1.02, f"{cm.human_size(safe_t)} vs {cm.human_size(used)}")
# 关键回归：不能把 80GB 的 inv_bigfolders 算进去
check("可释放数字不含空间分析(80GB级)", safe_t < 10*1024**3, cm.human_size(safe_t))

# 5) 条目数量：模型里不能有几万个
total_items=sum(len(cw['items']) for cw in app.cat_widgets.values())
print(f"  模型条目总数: {total_items}")
check("模型条目数 < 6000（不再几万）", total_items < 6000, str(total_items))

# 6) 渲染行数：展开所有类目后树上的行数
app.expand_all(); root.update()
rows=sum(len(app.tree.get_children(iid)) for iid in app.tree.get_children(""))
print(f"  全部展开后树行数: {rows}")
check("全部展开后行数 < 3000", rows < 3000, str(rows))

# 7) 一键清理按钮存在
check("一键清理按钮存在", hasattr(app,'quick_clean') and app.quick_btn is not None)

print("\n结果:", "PASS" if not fails else "FAIL -> "+", ".join(fails))
root.destroy()
