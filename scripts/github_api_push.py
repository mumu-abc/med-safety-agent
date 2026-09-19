"""用 GitHub REST API(Git Data API)把本地代码整包推到远端。

为什么不用 git push:
    沙箱环境里 github.com:443 是不可达的(curl 都超时),git 协议直接死;
    但 api.github.com 是通的,所以绕过 git 协议,用 HTTPS API 直接写对象。

做法(一次提交,不留中间态):
    1. git ls-tree -r HEAD 取「已提交」的文件清单 (path, mode, blob sha)
    2. 直接用 git 自己的 blob sha 建树 —— 这些 blob 通常远端已经有了,0 次上传
    3. POST /git/trees 建一棵「只含这批文件」的树 —— 不带 base_tree,
       所以远端多出来的旧文件会自动消失(整树替换)
    4. POST /git/commits 以远端分支当前 head 为父提交
    5. PATCH /git/refs/heads/<branch> 移动分支指针

用法:
    python scripts/github_api_push.py --token <PAT>              # 预览
    python scripts/github_api_push.py --token <PAT> --apply      # 真正推送

token 需求:
    Fine-grained PAT 需要 Contents: Read and write;
    如果仓库里有 .github/workflows/*,还需要 Workflows: Read and write,
    否则推 CI 文件会 403(见下)。

⚠️ 基准是 HEAD,不是工作区(2026-09-15 修正,之前是个真 bug):
    旧版读工作区文件的原始字节上传。但本机 core.autocrlf=true ——
    git 仓库里存 LF、工作区结出 CRLF,于是"上传工作区字节"= 上传 CRLF 版本,
    建出来的树跟本地 HEAD^{tree} 对不上(97 个文件里 27 个中招),
    **任何人 clone 下来这 27 个文件都会显示成"已修改"**,仓库在别人机器上是脏的。
    现在改成取 git 对象库里的 blob(内容 + sha 都用 git 的),保证:
      - 远端树 == 本地 HEAD 树(可以用 tree sha 直接比对核验)
      - 工作区文件被删/被改都不影响推送结果(推的是提交,不是磁盘)

⚠️ .github/workflows/* 是例外(2026-09-16 实测):
    只有 Contents 权限时,任何"创建/修改 .github/workflows/ 下文件"的操作都会
    返回 403 `Resource not accessible by personal access token` ——
    Git Data API(POST /git/trees)和 Contents API(PUT /contents/...)都是,
    而且这条报错看起来像"你权限不够",实际是**缺 Workflows 权限**,容易误判成限流。
    两个办法:
      1. 给 token 补 Workflows: Read and write(推荐;或直接用本机
         Git Credential Manager 里的凭据,它的 scope 通常是 gist,repo,workflow)
      2. 用 --exclude ".github/workflows/ci.yml" 先推其余文件,CI 文件再走网页端手加

其他踩过的坑:
    - `git ls-tree` 默认把非 ASCII 文件名输出成八进制转义,中文文件名会变成乱码路径,
      必须加 `-c core.quotepath=false` 或直接用 `-z` 并按 utf-8 解码。
    - 连发上百个 blob 请求会撞次级限流,返回的也是 403 + 同一句误导性文案;
      所以这里优先"直接用 git 的 blob sha 建树"(0 上传),
      只在仓库里确实缺 blob(422 not a valid blob)时才回退到逐个上传。
    - 整树替换是"以这批文件为准"的:清单里少一个文件 = 远端少一个文件。
      所以下面会对"取不到内容的 blob"硬失败,不静默跳过。
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
_VALID_MODES = {"100644", "100755", "120000", "160000"}


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }


def _git(root: str, *args: str) -> bytes:
    # core.quotepath=false 必须加:git 默认把非 ASCII 文件名输出成八进制转义
    # (如 "346\231\256..."),不加这个参数中文文件名会变成一串乱码路径,
    # 结果就是"远端同名文件被判为多余要删掉,同时传上去一个乱码名的新文件"。
    return subprocess.run(
        ["git", "-c", "core.quotepath=false", *args],
        cwd=root, capture_output=True, check=True,
    ).stdout


def tracked_blobs(root: str) -> list[tuple[str, str, str]]:
    """取 HEAD 里所有 blob,返回 [(path, mode, blob_sha)]。

    用 HEAD 而不是 `ls-files`(索引):推的是"提交",不是"暂存区/工作区",
    这样远端树能跟本地 HEAD^{tree} 严格对上。
    """
    raw = _git(root, "ls-tree", "-r", "-z", "HEAD")
    out: list[tuple[str, str, str]] = []
    for rec in raw.split(b"\0"):
        if not rec.strip():
            continue
        meta, path = rec.split(b"\t", 1)
        mode, typ, sha = meta.split()
        if typ != b"blob":
            continue
        out.append((path.decode("utf-8"), mode.decode(), sha.decode()))
    return out


def cat_blobs(root: str, shas: list[str]) -> tuple[dict[str, bytes], list[str]]:
    """一次 `git cat-file --batch` 取回全部 blob 内容。

    返回 (内容字典, 取不到的 sha 列表)。
    """
    if not shas:
        return {}, []
    proc = subprocess.Popen(
        ["git", "cat-file", "--batch"], cwd=root,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    )
    raw, _ = proc.communicate(("\n".join(shas) + "\n").encode())
    got: dict[str, bytes] = {}
    missing: list[str] = []
    i = 0
    while i < len(raw):
        nl = raw.find(b"\n", i)
        if nl < 0:
            break
        parts = raw[i:nl].decode("utf-8", "replace").split()
        i = nl + 1
        if len(parts) != 3 or parts[1] != "blob":
            # 形如 "<sha> missing"
            missing.append(parts[0] if parts else "?")
            continue
        size = int(parts[2])
        got[parts[0]] = raw[i:i + size]
        i += size + 1
    return got, missing


def git_blob_sha(data: bytes) -> str:
    """本地算 git blob 的 sha1 —— 与 GitHub 的算法一致:sha1(b"blob <len>\\0" + 内容)。"""
    h = hashlib.sha1()
    h.update(f"blob {len(data)}\0".encode())
    h.update(data)
    return h.hexdigest()


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

    all_blobs = tracked_blobs(root)
    blobs = [b for b in all_blobs if b[0] not in excluded]
    weird = [b for b in blobs if b[1] not in _VALID_MODES]

    print("=" * 64)
    print(f"GitHub API 推送   {args.owner}/{args.repo}@{args.branch}")
    print("=" * 64)
    if excluded:
        print(f"本次排除 {len(excluded)} 个: {', '.join(sorted(excluded))}")
    print(f"HEAD 待传文件: {len(blobs)} (HEAD 共 {len(all_blobs)})")
    if weird:
        print("[FAIL] 出现 GitHub 不支持的 mode:")
        for p, m, _ in weird:
            print(f"  ! {p}  mode={m}")
        return 1

    contents, missing = cat_blobs(root, [s for _, _, s in blobs])
    # ⚠️ 整树替换是"以这批文件为准"的:清单里少一个 = 远端被删一个。
    # 所以取不到内容的 blob 必须硬失败,绝不静默跳过。
    # (2026-09-15 踩坑:scripts/ 下 13 个脚本从磁盘消失,旧版会静默跳过 ==> 远端被连带删除)
    if missing:
        print(f"\n[FAIL] 有 {len(missing)} 个 blob 在本机 git 对象库里取不到:")
        for s in missing:
            paths = [p for p, _, sh in blobs if sh == s]
            print(f"  ! {s}  <- {paths}")
        print("      整树替换会把它们从远端一并删除,已中止。")
        return 1

    h = _headers(args.token)
    with httpx.Client(timeout=60) as cl:
        me = cl.get(f"{_API}/repos/{args.owner}/{args.repo}", headers=h)
        if me.status_code >= 300:
            print(f"[FAIL] 仓库不可达或 token 无权限: {me.status_code} {me.text[:200]}")
            return 1
        print(f"仓库 OK: {me.json()['full_name']} (default={me.json()['default_branch']})")

        head = cl.get(
            f"{_API}/repos/{args.owner}/{args.repo}/git/ref/heads/{args.branch}", headers=h
        )
        head.raise_for_status()
        parent = head.json()["object"]["sha"]

        r = cl.get(
            f"{_API}/repos/{args.owner}/{args.repo}/git/trees/{parent}",
            headers=h, params={"recursive": "1"},
        )
        before = {t["path"] for t in r.json().get("tree", []) if t["type"] == "blob"}
        gone = sorted(before - {p for p, _, _ in blobs})
        print(f"远端当前 {len(before)} 个文件;本次将移除 {len(gone)} 个")
        for p in gone:
            print(f"  - {p}")

        local_tree = subprocess.run(
            ["git", "-c", "core.quotepath=false", "rev-parse", "HEAD^{tree}"],
            cwd=root, capture_output=True, encoding="utf-8",
        ).stdout.strip()
        print(f"本地 HEAD^{{tree}} = {local_tree}  (推完应与此一致)")

        if not args.apply:
            print("\n这是预览。加 --apply 真正推送。")
            return 0

        def build_tree(entries):
            return request(
                cl, "POST", f"{_API}/repos/{args.owner}/{args.repo}/git/trees", h,
                json={"tree": entries},
            )

        entries = [
            {"path": p, "mode": m, "type": "blob", "sha": s} for p, m, s in blobs
        ]
        print(f"用 git 自带的 {len(entries)} 个 blob sha 直接建树(0 次上传)...")
        r = build_tree(entries)

        if r.status_code == 422 and "not a valid blob" in r.text:
            print("  部分 blob 仓库里还没有,回退到逐个上传...")
            entries = []
            for i, (path, mode, sha) in enumerate(blobs, 1):
                up = make_blob(cl, h, args.owner, args.repo, path, contents[sha])
                if up != sha:
                    raise RuntimeError(f"{path}: 上传后 sha 变了 {sha} -> {up}")
                entries.append({"path": path, "mode": mode, "type": "blob", "sha": up})
                if i % 20 == 0 or i == len(blobs):
                    print(f"  blob {i}/{len(blobs)}")
            r = build_tree(entries)

        if r.status_code >= 300:
            print(f"[FAIL] tree: {r.status_code} {r.text[:300]}")
            return 1
        tree_sha = r.json()["sha"]

        if tree_sha != local_tree:
            print(f"[WARN] 远端树 {tree_sha} != 本地树 {local_tree}")

        r = request(
            cl, "POST", f"{_API}/repos/{args.owner}/{args.repo}/git/commits", h,
            json={"message": args.message, "tree": tree_sha, "parents": [parent]},
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
        print(f"       tree   {tree_sha}")
        print(f"       {args.owner}/{args.repo} 现在有 {len(entries)} 个文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
