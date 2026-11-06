# -*- coding: utf-8 -*-
"""v2.6 扫描引擎真机验证：数字必须落在物理可能范围内。"""
import time, importlib.util, sys, os

spec = importlib.util.spec_from_file_location("cm", "clean_master.py")
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)

drive = sys.argv[1] if len(sys.argv) > 1 else "C"
t0 = time.time()
last = [0.0]
def prog(n, b, d):
    now = time.time()
    if now - last[0] > 3:
        last[0] = now
        print(f"   ... {n:,} 文件 {cm.human_size(b)} | {d[-50:]}", flush=True)

r = cm.scan_full_disk(drive, progress_cb=prog)
el = time.time() - t0

free, total = cm.get_drive_space(drive)
used = total - free
scanned = r.get('_scan_bytes', 0)
print(f"\n=== {drive}: 盘扫描完成，用时 {el:.1f}s ===")
print(f"文件总数        : {r['_file_count']:,}")
print(f"扫描字节        : {cm.human_size(scanned)}")
print(f"磁盘已用        : {cm.human_size(used)}")
print(f"系统/程序占用   : {cm.human_size(r['inv_system_total'])}")
print(f"AI 缓存条目     : {len(r['ai_cache'])}")
print(f"最大文件夹 top10:")
for it in r['inv_bigfolders'][:10]:
    print(f"   {cm.human_size(it['size']):>10}  {it['path']}")
print(f"最大文件 top8:")
for it in r['inv_bigfiles'][:8]:
    print(f"   {cm.human_size(it['size']):>10}  {it['path']}")
print(f"AI 缓存 top10:")
for it in r['ai_cache'][:10]:
    print(f"   {cm.human_size(it['size']):>10}  [{it['level']}] {it['path']}")
print(f"类型统计: " + " | ".join(
    f"{k}={cm.human_size(sum(i['size'] for i in r[k]))}" for k in cm.INV_CAT_META))

# --- 一致性检查 ---
print("\n=== 校验 ===")
ok = True
if scanned > used * 1.05:
    print(f"✗ 扫描字节 {cm.human_size(scanned)} 超过磁盘已用 {cm.human_size(used)}")
    ok = False
else:
    print(f"✓ 扫描字节未超过磁盘已用量")
sys_part = r['inv_system_total']
if sys_part > used * 1.05:
    print(f"✗ 系统占用超出磁盘已用量")
    ok = False
else:
    print(f"✓ 系统占用 {cm.human_size(sys_part)} 在合理范围")
paths = [i['path'] for i in r['inv_bigfolders']]
if len(paths) != len(set(p.lower() for p in paths)):
    print("✗ 最大文件夹列表有重复路径")
    ok = False
else:
    print(f"✓ 文件夹列表无重复")
# 所有分类文件总量不应超过扫描字节
cat_sum = sum(sum(i['size'] for i in r[k]) for k in cm.INV_CAT_META)
cat_sum += sum(i['size'] for i in r['inv_other'])
if cat_sum > scanned * 1.05:
    print(f"✗ 分类合计 {cm.human_size(cat_sum)} 超过扫描字节")
    ok = False
else:
    print(f"✓ 分类合计 {cm.human_size(cat_sum)} ≤ 扫描字节")
print("结果:", "PASS" if ok else "FAIL")
