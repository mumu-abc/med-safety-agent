"""校验推送后远端 README 的关键内容(走 api.github.com,raw 域名在沙箱里不通)。"""
import base64

import httpx

OWNER, REPO = "mumu-abc", "med-safety-agent"
H = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}

with httpx.Client(timeout=60) as cl:
    r = cl.get(
        f"https://api.github.com/repos/{OWNER}/{REPO}/contents/README.md",
        headers=H,
        params={"ref": "main"},
    ).json()
    txt = base64.b64decode(r["content"]).decode("utf-8")

print(f"README 大小: {len(txt)} 字符")
checks = {
    "88.3% holdout": "88.3",
    "新 Q5 措辞(先说当前数字)": "先说当前数字",
    "单进程单端口(无 Streamlit)": "单进程单端口",
    "密度 0.27%": "0.27%",
    "CI badge": "actions/workflows/ci.yml/badge.svg",
    "demo 链接": "app.workbuddy.host",
    "旧值 86.7%": "86.7",
    "旧值 91.3%": "91.3",
    "Streamlit": "Streamlit",
}
for label, kw in checks.items():
    print(f"  {label:<32} {kw in txt}")
