"""校验推送后的远端仓库状态(不靠人肉点网页)。"""
import json
import sys

import httpx

OWNER, REPO = "mumu-abc", "med-safety-agent"
H = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
B = f"https://api.github.com/repos/{OWNER}/{REPO}"

with httpx.Client(timeout=60) as cl:
    repo = cl.get(B, headers=H).json()
    head = cl.get(f"{B}/git/ref/heads/main", headers=H).json()["object"]["sha"]
    tree = cl.get(f"{B}/git/trees/main?recursive=1", headers=H).json()
    files = [t["path"] for t in tree["tree"] if t["type"] == "blob"]

    print(f"仓库: {repo['full_name']}   默认分支: {repo['default_branch']}")
    print(f"head: {head}")
    print(f"文件数: {len(files)}")
    print(f"z_probe.txt 残留: {'z_probe.txt' in files}")
    print(f"streamlit 残留: {[f for f in files if 'streamlit' in f.lower()]}")
    print(f"CI 文件: {[f for f in files if 'workflows' in f]}")
    print(f"关键文件: {[f for f in files if f in ('README.md', 'requirements-dev.txt', 'render.yaml', 'docs/langsmith-trace.png')]}")

    rd = cl.get(
        f"https://raw.githubusercontent.com/{OWNER}/{REPO}/main/README.md",
        headers=H,
    ).text
    for kw in ("88.3", "100%", "单进程单端口", "0.27%", "Streamlit"):
        print(f"  README 含 {kw!r}: {kw in rd}")
