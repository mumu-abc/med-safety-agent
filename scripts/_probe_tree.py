"""临时诊断 2:区分「某个 entry 有问题」还是「突发限流」。"""
import hashlib
import os
import subprocess
import sys
import time

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TOKEN = sys.argv[1]
OWNER, REPO = "mumu-abc", "med-safety-agent"
H = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def sha(data: bytes) -> str:
    h = hashlib.sha1()
    h.update(f"blob {len(data)}\0".encode())
    h.update(data)
    return h.hexdigest()


root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = subprocess.run(
    ["git", "-c", "core.quotepath=false", "ls-files"],
    cwd=root, capture_output=True, encoding="utf-8", check=True,
).stdout
files = [ln.strip() for ln in out.splitlines() if ln.strip()]

entries = []
for p in files:
    full = os.path.join(root, p)
    if not os.path.isfile(full):
        continue
    with open(full, "rb") as f:
        d = f.read()
    entries.append({"path": p, "mode": "100644", "type": "blob", "sha": sha(d)})

url = f"https://api.github.com/repos/{OWNER}/{REPO}/git/trees"
with httpx.Client(timeout=60) as cl:
    print("--- A. 同一个 2-entry 请求连发 6 次(每次隔 1s) ---")
    for i in range(6):
        r = cl.post(url, headers=H, json={"tree": entries[:2]})
        print(f"  第{i+1}次 -> {r.status_code}")
        time.sleep(1)

    print("--- B. 逐个单独提交 index 2..6 ---")
    for i in range(2, 7):
        r = cl.post(url, headers=H, json={"tree": [entries[i]]})
        print(f"  [{i}] {entries[i]['path']:<40} -> {r.status_code} {r.text[:80]}")
        time.sleep(1)
