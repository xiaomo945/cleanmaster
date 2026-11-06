# -*- coding: utf-8 -*-
"""v2.7.1 真机全流程性能：扫描 → 展开 → 勾选 → 工具栏。"""
import importlib.util, threading, time

spec = importlib.util.spec_from_file_location("cm", "clean_master.py")
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)
import tkinter as tk

root = tk.Tk()
app = cm.CleanMasterApp(root)
root.geometry("1200x820")
root.update()

results = {}


def pump(sec):
    end = time.time() + sec
    while time.time() < end:
        root.update()
        time.sleep(0.02)


def run():
    pump(0.4)
    app.drive_var.set("C")
    t0 = time.time()
    app.start_scan()
    while app.scanning:
        pump(0.3)
    results["scan"] = time.time() - t0
    pump(0.8)
    print(f"扫描: {results['scan']:.1f}s")

    # 展开各类目计时
    print("\n展开计时:")
    for key in ("g_junk", "g_large", "g_old", "ai_cache", "inv_bigfolders",
                "appcache", "inv_image"):
        if not app.tree.exists(f"c:{key}"):
            continue
        t1 = time.time()
        app._load_children(key)
        app.tree.item(f"c:{key}", open=True)
        root.update()
        el = (time.time() - t1) * 1000
        n = len(app.tree.get_children(f"c:{key}"))
        results[key] = el
        flag = "✗ 卡" if el > 300 else "✓"
        print(f"  {flag} {key:<16} {el:7.1f} ms   ({n} 行)")

    # 总开关计时
    print("\n总开关切换计时:")
    for key in ("g_junk", "g_large"):
        if app.tree.exists(f"c:{key}"):
            t1 = time.time()
            app.toggle_category(key)
            root.update()
            el = (time.time() - t1) * 1000
            print(f"  {'✗ 卡' if el > 300 else '✓'} {key:<16} {el:7.1f} ms")
            results["toggle_" + key] = el

    # 连续 30 次点击
    t1 = time.time()
    for i in range(30):
        app.toggle_category("g_junk")
        root.update()
    el = (time.time() - t1) * 1000
    print(f"\n  {'✗ 卡' if el/30 > 100 else '✓'} 连续 30 次切换: {el:.0f} ms "
          f"(平均 {el/30:.1f} ms/次)")
    results["burst"] = el / 30

    # 工具栏
    print("\n工具栏:")
    for name, fn in (("全部展开", app.expand_all),
                     ("全部收起", app.collapse_all),
                     ("只看已勾选", app.show_only_checked),
                     ("全选/全不选", app.toggle_all_categories)):
        t1 = time.time()
        fn()
        root.update()
        el = (time.time() - t1) * 1000
        print(f"  {'✗ 卡' if el > 1000 else '✓'} {name:<12} {el:8.1f} ms")

    print("\n最终:", app.summary_label.cget("text"))
    root.after(400, root.destroy)


threading.Thread(target=run, daemon=True).start()
root.mainloop()

print()
print("=== 汇总 ===")
print(f"扫描 {results['scan']:.1f}s")
worst = max(v for k, v in results.items() if k != "scan")
print(f"最慢的展开/切换操作: {worst:.0f} ms")
print("结论:", "流畅" if worst < 300 else "有卡顿")
