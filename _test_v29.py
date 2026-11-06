# -*- coding: utf-8 -*-
"""v2.9 软件缓存识别：E/F 盘 GUI 与安全回归（只读，不删任何文件）。"""
import sys, time, tkinter as tk
sys.argv=['x']
import clean_master as cm
fails=[]
def check(n,c,e=""):
    print(("  ✓ " if c else "  ✗ ")+n+("  "+e if e else ""))
    if not c: fails.append(n)

root=tk.Tk(); root.withdraw()
app=cm.CleanMasterApp(root)
root.update()

for drive in ('F','E'):
    print(f"\n=== 扫描 {drive}: 盘 ===")
    app.current_drive=drive; app.drive_var.set(drive)
    t=time.time(); app.start_scan()
    dl=time.time()+400
    while app.scanning and time.time()<dl:
        root.update(); time.sleep(0.15)
    root.update()
    print(f"  扫描耗时 {time.time()-t:.1f}s")
    data=app.results_by_drive.get(drive,{})
    check(f"{drive} 结果非空", len(data)>0, str(len(data)))

    # 新分组
    check(f"{drive} soft 分组存在", app.tree.exists('g:soft'))
    for k in ('sc_clean','sc_rebuild','sc_confirm','sc_protected','sc_folders','sc_profile'):
        check(f"{drive} 类目 {k}", k in app.cat_widgets,
              f"n={len(app.cat_widgets.get(k,{}).get('items',[]))}")

    # 清理影响列
    cols=app.tree.cget('columns')
    check(f"{drive} 有 impact 列", 'impact' in str(cols), str(cols))

    # 展开 clean / protected，看行数据与只读保护
    app._load_children('sc_clean'); root.update()
    kids=app.tree.get_children('c:sc_clean')
    check(f"{drive} sc_clean 有子项", len(kids)>0, str(len(kids)))
    if kids:
        v=app.tree.item(kids[0],'values')
        check(f"{drive} 行有4列", len(v)==4, str(len(v)))
        check(f"{drive} 影响列有内容", len(str(v[3]))>10, str(v[3])[:70])
        check(f"{drive} 用途列有内容", len(str(v[2]))>5, str(v[2])[:50])
        print(f"    示例: {str(app.tree.item(kids[0],'text'))[:70]}")
        print(f"    影响: {str(v[3])[:100]}")

    app._load_children('sc_protected'); root.update()
    pkids=app.tree.get_children('c:sc_protected')
    check(f"{drive} protected 子项显示—",
          all(app.tree.set(k,'sel')=='—' for k in pkids), str(len(pkids)))
    before=app.tree.set(pkids[0],'sel') if pkids else ''
    if pkids: app.toggle_item('sc_protected',0)
    check(f"{drive} readonly 勾不动", before=='—' and (not pkids or app.tree.set(pkids[0],'sel')=='—'))

    # 顶层目录画像
    tops=app.cat_widgets['sc_folders']['items']
    check(f"{drive} 根目录画像有条目", len(tops)>20, str(len(tops)))
    known=sum(1 for i in tops if not i['desc'].startswith('未识别'))
    print(f"    画像 {len(tops)} 项，已识别 {known}，未识别 {len(tops)-known}")

    # 一键清理绝不含 sc_
    plan={}
    for key,cw in app.cat_widgets.items():
        if cw.get('readonly') or key.startswith('sc_'): continue
        meta=data.get(key,{}).get('meta',{})
        if meta.get('risk')!='safe': continue
        _,sel=app._cat_state(key)
        if sel: plan[key]=sel
    check(f"{drive} 一键清理不含 sc_", not any(k.startswith('sc_') for k in plan), str(sorted(plan)))

    # 所有 sc_ 可清类目默认不勾
    sc_sel=[k for k in app.cat_widgets if k.startswith('sc_') and app.cat_widgets[k].get('master')]
    check(f"{drive} sc_ 默认全不勾", not sc_sel, str(sc_sel))

    # 顶部数字不含 protected 的 250GB
    app.show_summary()
    txt=app.summary_label.cget('text')
    print(f"    顶部: {txt}")
    import re
    m=re.search(r'已勾选可释放：([\d.]+ [A-Z]+)',txt)
    def tob(s):
        v,u=s.split(); return float(v)*{'B':1,'KB':1024,'MB':1024**2,'GB':1024**3,'TB':1024**4}[u]
    check(f"{drive} 已勾选可释放 < 50GB", tob(m.group(1))<50*1024**3, m.group(1))

    # clean_item 绝不删 readonly
    ro=app.cat_widgets['sc_protected']['items'][0]
    check(f"{drive} clean_item 拒绝 readonly",
          cm.clean_item({'kind':'readonly','path':ro['path']}) is False)

print("\n结果:", "PASS" if not fails else "FAIL -> "+", ".join(fails))
root.destroy()
