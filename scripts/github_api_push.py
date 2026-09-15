"""用 GitHub REST API(Git Data API)把本地代码整包推到远端。

为什么不用 git push:
    沙箱环境里 github.com:443 是不可达的(curl 都超时),git 协议直接死;
    但 api.github.com 是通的,所以绕过 git 协议,用 HTTPS API 直接写对象。

做法(一次提交,不留中间态):
    1. git ls-files 取本地待传文件(天然排除 .env/.venv/__pycache__)
    2. 逐个 POST /git/blobs 建 blob(内容 base64)
    3. POST /git/trees 建一棵「只含本地文件」的树 —— 不带 base_tree,
       所以远端多出来的旧文件(比如已删除的 streamlit_app.py)会自动消失
    4. POST /git/commits 以远端 main 当前 head 为父提交
    5. PATCH /git/refs/heads/<branch> 移动分支指针

用法:
    python scripts/github_api_push.py --token <PAT>              # 预览
    python scripts/github_api_push.py --token <PAT> --apply      # 真正推送

token 需求:
    Fine-grained PAT,只有目标仓库的 Contents: Read and write 权限即可。

⚠️ .github/workflows/* 是例外(2026-09-16 实测):
    fine-grained token 只有 Contents 权限时,任何"创建/修改 .github/workflows/ 下文件"的
    操作都会返回 403 `Resource not accessible by personal access token` ——
    Git Data API(POST /git/trees)和 Contents API(PUT /contents/...)都是,
    而且这条报错看起来像"你权限不够",实际是**缺 Workflows 权限**,很容易误判成限流。
    两个办法:
      1. 给 token 补 Workflows: Read and write(推荐,能一次性推完)
      2. 用 --exclude ".github/workflows/ci.yml" 先推其余文件,CI 文件再走 GitHub 网页端手加

其他踩过的坑:
    - `git ls-files` 默认把非 ASCII 文件名输出成八进制转义,中文文件名会变成乱码路径,
      必须加 `-c core.quotepath=false` 并按 utf-8 解码。
    - 连发上百个 blob 请求会撞次级限流,返回的也是 403 + 同一句误导性文案;
      所以这里优先"本地算 blob sha 直接建树"(sha1(b"blob <len>\\0" + 内容)),
      只在仓库里确实缺 blob(422)时才回退到逐个上传。
"""

import argparse
import base64
import hashlib
import os
import subprocess
import sys
import time

import httpx

_API = "https://api.github.com"
_EXEC_SUFFIX = (".sh",)


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }


def local_files(root: str) -> list[str]:
    """取 git 追踪的文件列表(已排除 .gitignore 命中项)。"""
    # core.quotepath=false 必须加:git 默认把非 ASCII 文件名输出成八进制转义
    # (如 "346\231\256..."),不加这个参数中文文件名会变成一串乱码路径,
    # 结果就是"远端同名文件被判为多余要删掉,同时传上去一个乱码名的新文件"。
    out = subprocess.run(
        ["git", "-c", "core.quotepath=false", "ls-files"],
        cwd=root,
        capture_output=True,
        encoding="utf-8",
        check=True,
    ).stdout
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def remote_head(cl: httpx.Client, h: dict, owner: str, repo: str, branch: str) -> str:
    r = cl.get(f"{_API}/repos/{owner}/{repo}/git/ref/heads/{branch}", headers=h)
    r.raise_for_status()
    return r.json()["object"]["sha"]


def remote_files(cl: httpx.Client, h: dict, owner: str, repo: str, branch: str) -> set[str]:
    r = cl.get(
        f"{_API}/repos/{owner}/{repo}/git/trees/{branch}",
        headers=h,
        params={"recursive": "1"},
    )
    r.raise_for_status()
    return {t["path"] for t in r.json().get("tree", []) if t["type"] == "blob"}


def request(cl: httpx.Client, method: str, url: str, h: dict, **kw) -> httpx.Response:
    """带退避重试的请求。

    连发上百个 blob 请求会触发 GitHub 次级限流,此时它返回的是
    403 `Resource not accessible by personal access token` —— 一条看起来像是
    "你权限不够"的误导性错误信息,实际上歇几秒重试就好。
    """
    for attempt in range(1, 5):
        r = cl.request(method, url, headers=h, timeout=60, **kw)
        if r.status_code < 400 or r.status_code in (404, 422):
            return r
        wait = 2 ** attempt
        print(f"  [retry {attempt}/4] {r.status_code} -> 等 {wait}s 重试")
        time.sleep(wait)
    return r


def git_blob_sha(data: bytes) -> str:
    """本地算 git blob 的 sha1 —— 与 GitHub 的算法一致:sha1(b"blob <len>\\0" + 内容)。

    好处:如果 blob 之前已经 POST 过(比如上一轮跑到一半失败),可以直接复用,
    不必再发上百个请求,也就不会再撞次级限流。
    """
    h = hashlib.sha1()
    h.update(f"blob {len(data)}\0".encode())
    h.update(data)
    return h.hexdigest()


def make_blob(cl: httpx.Client, h: dict, owner: str, repo: str, path: str, data: bytes) -> str:
    r = request(
        cl, "POST", f"{_API}/repos/{owner}/{repo}/git/blobs", h,
        json={"content": base64.b64encode(data).decode(), "encoding": "base64"},
    )
    if r.status_code >= 300:
        raise RuntimeError(f"blob {path}: {r.status_code} {r.text[:160]}")
    return r.json()["sha"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", default=os.getenv("GITHUB_TOKEN", "").strip())
    ap.add_argument("--owner", default="mumu-abc")
    ap.add_argument("--repo", default="med-safety-agent")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--message", default="chore: 同步本地最新版（bugfix + LangSmith trace + 文档校准）")
    ap.add_argument("--exclude", default="", help="逗号分隔、本次不上传的路径")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not args.token:
        print("[FAIL] 缺 token:用 --token 或 GITHUB_TOKEN 环境变量传入")
        return 1

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    excluded = {p.strip() for p in args.exclude.split(",") if p.strip()}
    files = [f for f in local_files(root) if f not in excluded]
    print("=" * 64)
    print(f"GitHub API 推送   {args.owner}/{args.repo}@{args.branch}")
    print("=" * 64)
    if excluded:
        print(f"本次排除 {len(excluded)} 个: {', '.join(sorted(excluded))}")
    print(f"本地待传文件: {len(files)}")

    h = _headers(args.token)
    with httpx.Client(timeout=60) as cl:
        # 先验 token + 仓库可达
        me = cl.get(f"{_API}/repos/{args.owner}/{args.repo}", headers=h)
        if me.status_code >= 300:
            print(f"[FAIL] 仓库不可达或 token 无权限: {me.status_code} {me.text[:200]}")
            return 1
        print(f"仓库 OK: {me.json()['full_name']} (default={me.json()['default_branch']})")

        head = remote_head(cl, h, args.owner, args.repo, args.branch)
        before = remote_files(cl, h, args.owner, args.repo, args.branch)
        gone = sorted(before - set(files))
        print(f"远端当前 {len(before)} 个文件;本次将移除 {len(gone)} 个")
        for p in gone:
            print(f"  - {p}")

        if not args.apply:
            print("\n这是预览。加 --apply 真正推送。")
            return 0

        # 先走"零上传"路径:上一轮(如果跑到一半失败)已经把 blob 都建过了,
        # 本地算出 sha 直接建树即可,避免再发上百个请求撞限流。
        payload = []
        for path in files:
            full = os.path.join(root, path)
            if not os.path.isfile(full):
                continue
            with open(full, "rb") as f:
                data = f.read()
            mode = "100755" if path.endswith(_EXEC_SUFFIX) else "100644"
            payload.append((path, mode, data))

        def build_tree(entries):
            return request(
                cl, "POST", f"{_API}/repos/{args.owner}/{args.repo}/git/trees", h,
                json={"tree": entries},
            )

        entries = [
            {"path": p, "mode": m, "type": "blob", "sha": git_blob_sha(d)}
            for p, m, d in payload
        ]
        print(f"用本地计算的 {len(entries)} 个 blob sha 直接建树(0 次上传)...")
        r = build_tree(entries)

        if r.status_code == 422 and "not a valid blob" in r.text:
            print("  部分 blob 仓库里还没有,回退到逐个上传...")
            entries = []
            for i, (path, mode, data) in enumerate(payload, 1):
                entries.append(
                    {
                        "path": path,
                        "mode": mode,
                        "type": "blob",
                        "sha": make_blob(cl, h, args.owner, args.repo, path, data),
                    }
                )
                if i % 20 == 0 or i == len(payload):
                    print(f"  blob {i}/{len(payload)}")
            r = build_tree(entries)

        if r.status_code >= 300:
            print(f"[FAIL] tree: {r.status_code} {r.text[:300]}")
            return 1
        tree_sha = r.json()["sha"]

        r = request(
            cl, "POST", f"{_API}/repos/{args.owner}/{args.repo}/git/commits", h,
            json={"message": args.message, "tree": tree_sha, "parents": [head]},
        )
        if r.status_code >= 300:
            print(f"[FAIL] commit: {r.status_code} {r.text[:300]}")
            return 1
        commit_sha = r.json()["sha"]

        r = request(
            cl, "PATCH",
            f"{_API}/repos/{args.owner}/{args.repo}/git/refs/heads/{args.branch}", h,
            json={"sha": commit_sha},
        )
        if r.status_code >= 300:
            print(f"[FAIL] update ref: {r.status_code} {r.text[:300]}")
            return 1

        print(f"\n[完成] commit {commit_sha}")
        print(f"       {args.owner}/{args.repo} 现在有 {len(entries)} 个文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
