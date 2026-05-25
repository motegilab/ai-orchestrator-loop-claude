#!/usr/bin/env python3
"""たまごっちパラダイス 予約受付 巡回監視ツール.

商品ページを定期巡回し、「予約受付中 → 受付終了/在庫なし」の状態を判定して、
受付中（unavailable/unknown から available への変化）になった瞬間に通知する。

【重要】Claude のクラウド実行環境ではネット送信が全遮断されるため動かない。
        必ず自分のPC（通常のネット接続あり）で実行すること。

取得エンジン:
    --engine requests   (既定) 軽量。ただし大手リテールは Bot 対策で 403 になりがち。
    --engine playwright  実ブラウザ(Chromium)でページを開くので 403 を回避しやすい。
                         事前に:  pip install playwright
                                  playwright install chromium

使い方:
    cd tools/tamagotchi_monitor
    python monitor.py --engine playwright --once     # まず1回で動作確認
    python monitor.py --engine playwright            # 本番巡回（Ctrl+Cで停止）
    python monitor.py --interval 120                 # 巡回間隔(秒)を上書き
    set TAMA_DISCORD_WEBHOOK=https://discord.com/api/webhooks/...   # (Windows) Discord通知
        # 受付中になったら Discord にも通知。リポジトリの notifications.json に
        # discord.webhook_url があればそれも自動利用。

判定ルール（targets.json で個別上書き可）:
    - unavailable キーワードに1つでも一致 → 受付なし
    - 上記なし & available キーワードに一致 → 受付中（通知対象）
    - どちらも一致しない → unknown（ページ構造が変わった等。手動確認を促す）
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

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": UA,
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


# --- 取得エンジン: fetch(url) -> ("ok", html) | ("error", メッセージ) ---

class RequestsFetcher:
    def __init__(self) -> None:
        self.session = requests.Session()

    def fetch(self, url: str) -> tuple[str, str]:
        try:
            resp = self.session.get(url, headers=HEADERS, timeout=20)
        except requests.RequestException as e:
            return ERROR, f"接続失敗: {e.__class__.__name__}"
        if resp.status_code in (403, 503, 429):
            return ERROR, f"HTTP {resp.status_code}（Bot対策／--engine playwright を試す）"
        if resp.status_code != 200:
            return ERROR, f"HTTP {resp.status_code}"
        return "ok", resp.text

    def close(self) -> None:
        self.session.close()


class PlaywrightFetcher:
    def __init__(self) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            sys.exit(
                "Playwright が未インストールです。次を実行してください:\n"
                "    pip install playwright\n"
                "    playwright install chromium"
            )
        self._pw = sync_playwright().start()
        try:
            self._browser = self._pw.chromium.launch(headless=True)
        except Exception:
            self._pw.stop()
            sys.exit(
                "Chromium が見つかりません。次を実行してください:\n"
                "    playwright install chromium"
            )
        self._context = self._browser.new_context(
            locale="ja-JP", user_agent=UA, viewport={"width": 1280, "height": 900}
        )

    def fetch(self, url: str) -> tuple[str, str]:
        page = self._context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1800)  # JS描画/在庫表示の反映待ち
            return "ok", page.content()
        except Exception as e:  # TimeoutError 等で1件失敗しても巡回は続行
            return ERROR, f"取得失敗: {e.__class__.__name__}"
        finally:
            page.close()

    def close(self) -> None:
        self._context.close()
        self._browser.close()
        self._pw.stop()


def check(target: dict, fetcher) -> tuple[str, str]:
    kind, payload = fetcher.fetch(target["url"])
    if kind == ERROR:
        return ERROR, payload
    status, hits = classify(payload, target)
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


def run_once(targets: list[dict], state: dict, fetcher) -> None:
    for t in targets:
        name, url = t["name"], t["url"]
        status, detail = check(t, fetcher)
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
    ap.add_argument("--engine", choices=["requests", "playwright"], default="requests",
                    help="取得エンジン。大手リテールは playwright 推奨")
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
    fetcher = PlaywrightFetcher() if args.engine == "playwright" else RequestsFetcher()

    print(f"監視対象 {len(targets)} 件 / engine={args.engine} / "
          f"間隔 {interval}±{jitter}秒 / Discord通知: {'ON' if discord_webhook() else 'OFF'}")
    try:
        if args.once:
            run_once(targets, state, fetcher)
            return 0
        while True:
            run_once(targets, state, fetcher)
            wait = interval + random.uniform(0, jitter)
            print(f"--- 次の巡回まで {wait:.0f} 秒待機 (Ctrl+C で停止) ---", flush=True)
            time.sleep(wait)
    except KeyboardInterrupt:
        print("\n停止しました。")
        return 0
    finally:
        fetcher.close()


if __name__ == "__main__":
    sys.exit(main())
