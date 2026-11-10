#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 CleanMaster 同步到 GitHub 仓库（增量版）。

沙箱代理会拦 git 协议（git push / clone 超时），所以走 gh api 的
blobs -> trees -> commits -> refs 链路。

只上传内容真正变过的文件：本地先算 Git blob sha1，与远端 tree 比对，
相同的直接复用远端 sha。这样改一行 README 不用重传 11MB 的 EXE，
也不会因代理偶发 TLS 超时半途而废。

用法：
    py -3 _push_gh.py
    CM_GH_MSG="fix: ..." py -3 _push_gh.py          # 自定义提交信息
    CM_GH_OWNER=xxx CM_GH_REPO=yyy py -3 _push_gh.py  # 推到别的账号/仓库
"""
import os
import sys
import json
import time
import base64
import hashlib
import shutil
import tempfile
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
OWNER = os.environ.get("CM_GH_OWNER", "xiaomo945")
REPO = os.environ.get("CM_GH_REPO", "cleanmaster")
BRANCH = os.environ.get("CM_GH_BRANCH", "main")
GH = shutil.which("gh") or "gh"

BASE = [
    ".gitignore",
    "README.md",
    "clean_master.py",
    "build.ps1",
    "电脑清理大师.spec",
    "dist/电脑清理大师.exe",
    "_push_gh.py",          # 本脚本也进仓库，换电脑 / 协作者才拿得到推送工具
    "_make_release.py",     # 一键生成「下载解压就能用」的绿色版 zip
]
TESTS = sorted(f for f in os.listdir(ROOT)
               if f.startswith("_test_") and f.endswith(".py"))
FILES = BASE + TESTS

DESCRIPTION = ("Windows 电脑清理大师 - 零依赖 Python/Tkinter 图形清理工具："
               "逐盘扫描、目录用途识别、软件缓存分级、只读保护、手动挑着删。"
               "附可直接运行的单文件 EXE")

# 沙箱代理偶发 TLS 握手超时；这些是瞬时故障，重试即可，不必整轮重推
TRANSIENT = ("TLS handshake timeout", "connection reset", "i/o timeout",
             "Client.Timeout", "unexpected EOF", "HTTP 502", "HTTP 503",
             "connection refused", "network is unreachable", "EOF")


def api(method, path, payload=None, timeout=300, retries=3):
    args = [GH, "api", "-X", method, path, "-H", "Content-Type: application/json"]
    tmp = None
    if payload is not None:
        fd, tmp = tempfile.mkstemp(suffix=".json", prefix="cm_gh_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        args += ["--input", tmp]
    last = ""
    try:
        for attempt in range(retries):
            r = None
            try:
                r = subprocess.run(args, capture_output=True, text=True,
                                   timeout=timeout, encoding="utf-8",
                                   errors="replace")
            except subprocess.TimeoutExpired:
                last = "subprocess timeout"
            if r is not None and r.returncode == 0:
                out = (r.stdout or "").strip()
                return json.loads(out) if out else {}
            last = ((r.stderr or "") + (r.stdout or "")) if r is not None else last
            if not any(k in last for k in TRANSIENT) or attempt == retries - 1:
                break
            print("    网络瞬断，重试 %d/%d：%s" %
                  (attempt + 1, retries - 1, path), flush=True)
            time.sleep(1.5 * (attempt + 1))
        raise RuntimeError("%s %s 失败: %s" % (method, path, last[:800]))
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)


def git_blob_sha(raw):
    """Git object sha1 = sha1(b"blob <len>\\0" + content)，与 GitHub blob sha 一致。"""
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def bootstrap_repo():
    """空仓库的 Git Database API 会报 409 "Git Repository is empty"。

    先用 Contents API 写一个小文件，让 GitHub 生成初始 commit / 默认分支，
    之后 blobs -> trees -> commits 链路才可用。
    """
    with open(os.path.join(ROOT, ".gitignore"), "rb") as f:
        content = base64.b64encode(f.read()).decode("ascii")
    api("PUT", "repos/%s/%s/contents/.gitignore" % (OWNER, REPO), {
        "message": "chore: initialize repository",
        "content": content,
    }, timeout=120)
    info = api("GET", "repos/%s/%s" % (OWNER, REPO), timeout=60)
    branch = info.get("default_branch") or "main"
    ref = api("GET", "repos/%s/%s/git/ref/heads/%s" %
              (OWNER, REPO, branch), timeout=60)
    print("已初始化仓库，默认分支 %s，初始 commit %s" %
          (branch, ref["object"]["sha"][:8]))
    return branch, ref["object"]["sha"]


def main():
    # 0) 前置检查
    missing = [f for f in FILES if not os.path.isfile(os.path.join(ROOT, f))]
    if missing:
        raise SystemExit("缺少文件: " + ", ".join(missing))
    total = sum(os.path.getsize(os.path.join(ROOT, f)) for f in FILES)
    print("本地清单 %d 个文件，共 %.2f MB" % (len(FILES), total / 1024 ** 2))

    # 1) 创建公开仓库（若已存在则跳过）
    try:
        info = api("GET", "repos/%s/%s" % (OWNER, REPO), timeout=60)
        print("仓库已存在: %s (private=%s)" % (info["html_url"], info["private"]))
    except RuntimeError:
        info = api("POST", "user/repos", {
            "name": REPO,
            "description": DESCRIPTION,
            "homepage": "https://github.com/%s" % OWNER,
            "private": False,
            "auto_init": False,
            "has_issues": True,
            "has_wiki": False,
            "has_projects": False,
        }, timeout=120)
        print("已创建公开仓库: %s" % info["html_url"])

    # 1.5) 确认默认分支与父 commit（空仓库先 bootstrap）
    info = api("GET", "repos/%s/%s" % (OWNER, REPO), timeout=60)
    branch = info.get("default_branch") or BRANCH
    try:
        ref = api("GET", "repos/%s/%s/git/ref/heads/%s" %
                  (OWNER, REPO, branch), timeout=60)
        parent = ref["object"]["sha"]
        print("现有分支 %s，父 commit %s" % (branch, parent[:8]))
    except RuntimeError:
        branch, parent = bootstrap_repo()

    # 2) 读远端 tree，逐个文件比对 blob sha，只上传变化的内容
    existing = {}
    if parent:
        rt = api("GET", "repos/%s/%s/git/trees/%s?recursive=1" %
                 (OWNER, REPO, branch), timeout=120)
        existing = {x["path"]: x["sha"] for x in rt.get("tree", [])
                    if x["type"] == "blob"}
    repo_paths = {f.replace("\\", "/") for f in FILES}
    removed = sorted(set(existing) - repo_paths)

    tree, changed, local_sha = [], [], {}
    for rel in FILES:
        rp = rel.replace("\\", "/")
        with open(os.path.join(ROOT, rel), "rb") as f:
            raw = f.read()
        sha = git_blob_sha(raw)
        local_sha[rp] = sha
        if existing.get(rp) == sha:
            tree.append({"path": rp, "mode": "100644", "type": "blob", "sha": sha})
            continue                       # 内容一致，零上传
        r = api("POST", "repos/%s/%s/git/blobs" % (OWNER, REPO), {
            "content": base64.b64encode(raw).decode("ascii"),
            "encoding": "base64",
        })
        assert r["sha"] == sha, "blob sha 不一致：%s" % rp
        tree.append({"path": rp, "mode": "100644", "type": "blob", "sha": sha})
        changed.append(rp)
        print("  上传 %-40s %8.2f KB" % (rp, len(raw) / 1024), flush=True)

    print("变更：新增/修改 %d 个，删除 %d 个，复用 %d 个（未重传）" %
          (len(changed), len(removed), len(FILES) - len(changed)))
    if not changed and not removed:
        print("本地与远端逐字节一致，无需提交（不造空提交）。")
        print("仓库地址: https://github.com/%s/%s" % (OWNER, REPO))
        return 0

    # 3) tree -> commit -> ref（完整 tree，不含的路径即视为删除）
    msg = os.environ.get("CM_GH_MSG") or (
        "Sync 电脑清理大师：更新 %d 个文件%s" %
        (len(changed), ("，删除 %d 个" % len(removed)) if removed else ""))
    t = api("POST", "repos/%s/%s/git/trees" % (OWNER, REPO), {"tree": tree})
    print("tree sha:", t["sha"])
    c = api("POST", "repos/%s/%s/git/commits" % (OWNER, REPO), {
        "message": msg, "tree": t["sha"], "parents": [parent] if parent else [],
    })
    print("commit sha:", c["sha"])
    api("PATCH", "repos/%s/%s/git/refs/heads/%s" % (OWNER, REPO, branch),
        {"sha": c["sha"], "force": True}, timeout=120)
    api("PATCH", "repos/%s/%s" % (OWNER, REPO),
        {"default_branch": branch}, timeout=120)
    print("已更新分支:", branch)

    # 4) 远端校验：不只比清单，比每个文件的 blob sha
    v = api("GET", "repos/%s/%s/git/trees/%s?recursive=1" %
            (OWNER, REPO, branch), timeout=120)
    remote = {x["path"]: x["sha"] for x in v.get("tree", [])
              if x["type"] == "blob"}
    ok = remote == local_sha
    print("\n远端文件 %d 个，本地 %d 个，内容逐字节一致：%s" %
          (len(remote), len(local_sha), ok))
    for p in sorted(remote):
        print("  ", p)
    print("仓库地址: https://github.com/%s/%s" % (OWNER, REPO))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
