#!/usr/bin/env python3
"""たまごっちパラダイス 予約受付 巡回監視ツール.

商品ページを定期巡回し、「予約受付中 → 受付終了/在庫なし」の状態を判定して、
受付中（unavailable/unknown から available への変化）になった瞬間に通知する。

【重要】Claude のクラウド実行環境ではネット送信が全遮断されるため動かない。
        必ず自分のPC（通常のネット接続あり）で実行すること。

使い方:
    cd tools/tamagotchi_monitor
    python3 monitor.py                       # targets.json を使って巡回
    python3 monitor.py --once                # 1回だけ巡回して結果表示（動作確認用）
    python3 monitor.py --interval 120        # 巡回間隔(秒)を上書き
    TAMA_DISCORD_WEBHOOK=https://discord.com/api/webhooks/... python3 monitor.py
        # 受付中になったら Discord にも通知（リポジトリの notifications.json の
        #  discord.webhook_url があれば自動でそれも使う）

判定ルール（targets.json で個別上書き可）:
    - unavailable キーワードに1つでも一致 → 受付なし
    - 上記なし & available キーワードに一致 → 受付中（通知対象）
    - どちらも一致しない → unknown（ページ構造が変わった等。手動確認を促す）

依存: requests のみ（pip install requests）。
JS描画でしか在庫が出ない/Bot対策が強いサイト(Amazon・楽天等)は requests では
403/503 になりやすい。その場合は末尾の「Playwrightで強化」コメントを参照。
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
TARGETS_FILE = HERE / "targets.json"
STATE_FILE = HERE / "state.json"

# だいすけさんの環境でブロックされにくいよう実ブラウザ風のヘッダを送る
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en-US;q=0.8,en;q=0.5",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

DEFAULT_UNAVAILABLE = [
    "予約受付終了", "予約受付は終了", "受付を終了", "ご予約受付は終了",
    "販売を終了", "販売終了", "在庫なし", "在庫切れ", "売り切れ", "完売",
    "入荷お知らせ", "再入荷", "SOLD OUT", "sold out",
]
DEFAULT_AVAILABLE = [
    "予約受付中", "予約する", "ご予約はこちら", "予約注文", "今すぐ予約",
    "カートに入れる", "カートへ入れる", "ご購入手続き", "買い物かごに入れる",
]

AVAILABLE, UNAVAILABLE, UNKNOWN, ERROR = "available", "unavailable", "unknown", "error"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_targets() -> dict:
    with open(TARGETS_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def classify(html: str, target: dict) -> tuple[str, list[str]]:
    unavailable_kw = target.get("unavailable", DEFAULT_UNAVAILABLE)
    available_kw = target.get("available", DEFAULT_AVAILABLE)
    hit_unavail = [k for k in unavailable_kw if k in html]
    if hit_unavail:
        return UNAVAILABLE, hit_unavail
    hit_avail = [k for k in available_kw if k in html]
    if hit_avail:
        return AVAILABLE, hit_avail
    return UNKNOWN, []


def check(target: dict, session: requests.Session) -> tuple[str, str]:
    try:
        resp = session.get(target["url"], headers=HEADERS, timeout=20)
    except requests.RequestException as e:
        return ERROR, f"接続失敗: {e.__class__.__name__}"
    if resp.status_code in (403, 503, 429):
        return ERROR, f"HTTP {resp.status_code}（Bot対策の可能性／Playwright推奨）"
    if resp.status_code != 200:
        return ERROR, f"HTTP {resp.status_code}"
    status, hits = classify(resp.text, target)
    detail = ("一致: " + ", ".join(hits)) if hits else "判定キーワード未検出"
    return status, detail


def discord_webhook() -> str | None:
    env = os.environ.get("TAMA_DISCORD_WEBHOOK")
    if env:
        return env
    cfg = HERE.parents[1] / "notifications.json"
    if cfg.exists():
        try:
            data = json.load(open(cfg, encoding="utf-8"))
            url = data.get("discord", {}).get("webhook_url", "")
            if url and "YOUR_ID" not in url:
                return url
        except (json.JSONDecodeError, OSError):
            pass
    return None


def notify(name: str, url: str, detail: str) -> None:
    line = f"🟢 予約受付中になりました: {name}\n{url}\n（{detail}）"
    print("\a" + "=" * 60)
    print(f"[{now()}] {line}")
    print("=" * 60, flush=True)
    hook = discord_webhook()
    if hook:
        try:
            requests.post(hook, json={"content": line}, timeout=15)
        except requests.RequestException as e:
            print(f"  ! Discord通知失敗: {e.__class__.__name__}", flush=True)


def run_once(targets: list[dict], state: dict, session: requests.Session) -> None:
    for t in targets:
        name, url = t["name"], t["url"]
        status, detail = check(t, session)
        prev = state.get(url, {}).get("status")
        mark = {AVAILABLE: "🟢", UNAVAILABLE: "⚪", UNKNOWN: "🟡", ERROR: "🔴"}[status]
        print(f"[{now()}] {mark} {status:<11} {name}  ({detail})", flush=True)
        if status == AVAILABLE and prev != AVAILABLE:
            notify(name, url, detail)
        state[url] = {"status": status, "checked_at": now(), "name": name}
        time.sleep(random.uniform(1.0, 3.0))  # サイト間は軽く間を空ける
    save_state(state)


def main() -> int:
    ap = argparse.ArgumentParser(description="たまごっちパラダイス予約 巡回監視")
    ap.add_argument("--once", action="store_true", help="1回だけ巡回して終了")
    ap.add_argument("--interval", type=int, help="巡回間隔(秒) を上書き")
    args = ap.parse_args()

    conf = load_targets()
    targets = conf.get("targets", [])
    if not targets:
        print("targets.json に監視対象がありません。", file=sys.stderr)
        return 1
    interval = args.interval or conf.get("poll_interval_sec", 180)
    jitter = conf.get("jitter_sec", 30)
    state = load_state()
    session = requests.Session()

    print(f"監視対象 {len(targets)} 件 / 間隔 {interval}±{jitter}秒 / "
          f"Discord通知: {'ON' if discord_webhook() else 'OFF'}")
    if args.once:
        run_once(targets, state, session)
        return 0
    try:
        while True:
            run_once(targets, state, session)
            wait = interval + random.uniform(0, jitter)
            print(f"--- 次の巡回まで {wait:.0f} 秒待機 (Ctrl+C で停止) ---", flush=True)
            time.sleep(wait)
    except KeyboardInterrupt:
        print("\n停止しました。")
        return 0


if __name__ == "__main__":
    sys.exit(main())

# --- Playwrightで強化したい場合（Amazon/楽天などBot対策が強いサイト向け） ---
# pip install playwright && playwright install chromium
# check() の中身を、requests.get の代わりに
#   from playwright.sync_api import sync_playwright
#   with sync_playwright() as p:
#       b = p.chromium.launch(); pg = b.new_page(); pg.goto(url, timeout=30000)
#       html = pg.content(); b.close()
# に差し替えれば、JS描画後のHTMLで classify() 判定できる。
