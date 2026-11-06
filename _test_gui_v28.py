import sys, time, tkinter as tk
sys.argv=['x']
import clean_master as cm

root = tk.Tk()
app = cm.CleanMasterApp(root)
root.update()

# 扫描 C 盘（后台线程），等结果
t0=time.time()
app.start_scan()
deadline=time.time()+300
while app.scanning and time.time()<deadline:
    root.update()
    time.sleep(0.2)
print("scan wall", round(time.time()-t0,1),"s")
root.update()

data=app.results_by_drive.get('C',{})
print("categories:", len(data))
total_rows=0
for key,cw in app.cat_widgets.items():
    total_rows += len(cw['items'])
    ro = cw.get('readonly')
    print(f"  {key:22s} items={len(cw['items']):5d} size={cm.human_size(cw['size']):>11s} ro={ro}")
print("total items in model:", total_rows)

app.show_summary()
print("summary:", app.summary_label.cget('text'))
print("max:", app.max_label.cget('text'))

# 渲染树（展开一个类目测性能）
def click_open(key):
    iid=f"c:{key}"
    if app.tree.exists(iid):
        app._load_children(key)
        app.tree.item(iid, open=True)
for k in ('g_junk','g_old','temp'):
    t=time.time(); click_open(k); root.update()
    print(f"  expand {k}: {round((time.time()-t)*1000)}ms  shown={app.cat_widgets[k]['shown']}")
rows=len(app.tree.get_children())
print("tree root children:", rows)
root.destroy()
print("OK")
