import sys, time, tkinter as tk, os
sys.argv=['x']
import clean_master as cm

root = tk.Tk()
app = cm.CleanMasterApp(root)
root.update()
app.start_scan()
deadline=time.time()+300
while app.scanning and time.time()<deadline:
    root.update(); time.sleep(0.2)
root.update()
print("scan done")

app.show_summary()
print("summary:", app.summary_label.cget('text'))

# 模拟 quick_clean 的选单逻辑（跳过弹窗）
plan={}
for key,cw in app.cat_widgets.items():
    if cw.get('readonly'): continue
    meta=app.results_by_drive['C'].get(key,{}).get('meta',{})
    if meta.get('risk')!='safe': continue
    _,sel=app._cat_state(key)
    if sel: plan[key]=sel
print("quick plan categories:", list(plan.keys()))
picked=[(it.get('path',''),it.get('size',0)) for v in plan.values() for it in v]
print("quick plan items:", len(picked), "expected size:", cm.human_size(cm._dedup_size(picked)))

# 实际清理（真删！只删安全类）
free_before=cm.get_drive_space('C')[0]
t0=time.time()
for key,items in plan.items():
    for it in items:
        cm.clean_item(it)
free_after=cm.get_drive_space('C')[0]
print("clean secs", round(time.time()-t0,1))
print("freed:", cm.human_size(max(0,free_after-free_before)))
root.destroy()
