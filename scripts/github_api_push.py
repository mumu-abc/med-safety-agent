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
"""

import argparse
import base64
import os
import subprocess
import sys

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
    out = subprocess.run(
        ["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True
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


def make_blob(cl: httpx.Client, h: dict, owner: str, repo: str, path: str, data: bytes) -> str:
    r = cl.post(
        f"{_API}/repos/{owner}/{repo}/git/blobs",
        headers=h,
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
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not args.token:
        print("[FAIL] 缺 token:用 --token 或 GITHUB_TOKEN 环境变量传入")
        return 1

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = local_files(root)
    print("=" * 64)
    print(f"GitHub API 推送   {args.owner}/{args.repo}@{args.branch}")
    print("=" * 64)
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

        tree_entries = []
        for i, path in enumerate(files, 1):
            full = os.path.join(root, path)
            if not os.path.isfile(full):
                continue
            with open(full, "rb") as f:
                data = f.read()
            sha = make_blob(cl, h, args.owner, args.repo, path, data)
            mode = "100755" if path.endswith(_EXEC_SUFFIX) else "100644"
            tree_entries.append({"path": path, "mode": mode, "type": "blob", "sha": sha})
            if i % 20 == 0 or i == len(files):
                print(f"  blob {i}/{len(files)}")

        r = cl.post(
            f"{_API}/repos/{args.owner}/{args.repo}/git/trees",
            headers=h,
            json={"tree": tree_entries},
        )
        if r.status_code >= 300:
            print(f"[FAIL] tree: {r.status_code} {r.text[:300]}")
            return 1
        tree_sha = r.json()["sha"]

        r = cl.post(
            f"{_API}/repos/{args.owner}/{args.repo}/git/commits",
            headers=h,
            json={"message": args.message, "tree": tree_sha, "parents": [head]},
        )
        if r.status_code >= 300:
            print(f"[FAIL] commit: {r.status_code} {r.text[:300]}")
            return 1
        commit_sha = r.json()["sha"]

        r = cl.patch(
            f"{_API}/repos/{args.owner}/{args.repo}/git/refs/heads/{args.branch}",
            headers=h,
            json={"sha": commit_sha},
        )
        if r.status_code >= 300:
            print(f"[FAIL] update ref: {r.status_code} {r.text[:300]}")
            return 1

        print(f"\n[完成] commit {commit_sha}")
        print(f"       {args.owner}/{args.repo} 现在有 {len(tree_entries)} 个文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
