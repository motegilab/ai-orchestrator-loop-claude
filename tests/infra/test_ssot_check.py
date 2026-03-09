"""
tests/infra/test_ssot_check.py

ssot_check.py の run_checks() / calc_result() を単体テスト。
実際のファイルは使わず、tmp_path に fixture ファイルを作って渡す。
"""
import json
import sys
from pathlib import Path

import pytest

# tools/scripts を import パスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools" / "scripts"))
from ssot_check import run_checks, calc_result  # noqa: E402

VALID_SSOT = """\
## §0 設計原則
原則の説明

## §1 絶対ルール（v1）
ルールの説明。依存関係は board → rules → game_state の順とする。

## §2 環境スタック
環境の説明

GOチェックリスト参照
"""

VALID_MILESTONES = {
    "milestones": [
        {
            "id": "M1",
            "title": "Phase 1: セットアップ",
            "status": "pending",
            "waves": [
                {
                    "id": "W1-1",
                    "title": "環境構築",
                    "tasks": [
                        {"id": "T1", "title": "pytest で全テストが通ることを確認する", "status": "pending"},
                        {"id": "T2", "title": "verify: 統合テストを実行して全 PASS を確認", "status": "pending"},
                    ],
                }
            ],
        }
    ]
}


# ─── SSOT.md 系 ───────────────────────────────────────────────────────────────

def test_valid_ssot_returns_no_errors(tmp_path):
    ssot = tmp_path / "SSOT.md"
    ms   = tmp_path / "milestones.json"
    ssot.write_text(VALID_SSOT, encoding="utf-8")
    ms.write_text(json.dumps(VALID_MILESTONES), encoding="utf-8")
    issues = run_checks(ssot, ms)
    _, _, exit_code = calc_result(issues)
    assert exit_code == 0


def test_missing_ssot_is_error(tmp_path):
    ms = tmp_path / "milestones.json"
    ms.write_text(json.dumps(VALID_MILESTONES), encoding="utf-8")
    issues = run_checks(tmp_path / "SSOT.md", ms)
    errors = [m for s, m in issues if s == "ERROR"]
    assert any("SSOT.md が存在しません" in e for e in errors)


def test_missing_section_s0_is_error(tmp_path):
    ssot = tmp_path / "SSOT.md"
    ms   = tmp_path / "milestones.json"
    # §0 を抜いた SSOT
    ssot.write_text("## §1 絶対ルール\n## §2 環境\nGOチェックリスト\n", encoding="utf-8")
    ms.write_text(json.dumps(VALID_MILESTONES), encoding="utf-8")
    issues = run_checks(ssot, ms)
    errors = [m for s, m in issues if s == "ERROR"]
    assert any("§0" in e for e in errors)


def test_missing_section_s1_is_error(tmp_path):
    ssot = tmp_path / "SSOT.md"
    ms   = tmp_path / "milestones.json"
    ssot.write_text("## §0 設計原則\n## §2 環境\nGOチェックリスト\n", encoding="utf-8")
    ms.write_text(json.dumps(VALID_MILESTONES), encoding="utf-8")
    issues = run_checks(ssot, ms)
    errors = [m for s, m in issues if s == "ERROR"]
    assert any("§1" in e for e in errors)


def test_missing_section_s2_is_error(tmp_path):
    ssot = tmp_path / "SSOT.md"
    ms   = tmp_path / "milestones.json"
    ssot.write_text("## §0 設計原則\n## §1 絶対ルール\nGOチェックリスト\n", encoding="utf-8")
    ms.write_text(json.dumps(VALID_MILESTONES), encoding="utf-8")
    issues = run_checks(ssot, ms)
    errors = [m for s, m in issues if s == "ERROR"]
    assert any("§2" in e for e in errors)


# ─── milestones.json 系 ───────────────────────────────────────────────────────

def test_tbd_in_pending_task_is_error(tmp_path):
    ssot = tmp_path / "SSOT.md"
    ms   = tmp_path / "milestones.json"
    ssot.write_text(VALID_SSOT, encoding="utf-8")
    data = {
        "milestones": [{
            "id": "M1", "title": "M1", "status": "pending",
            "waves": [{"id": "W1", "title": "W1", "tasks": [
                {"id": "T1", "title": "TBD: あとで決める", "status": "pending"},
                {"id": "T2", "title": "verify: 統合テストを実行して確認する", "status": "pending"},
            ]}],
        }]
    }
    ms.write_text(json.dumps(data), encoding="utf-8")
    issues = run_checks(ssot, ms)
    errors = [m for s, m in issues if s == "ERROR"]
    assert any("T1" in e for e in errors)


def test_tbd_in_done_task_is_not_error(tmp_path):
    """完了済みタスクの TBD は無視する"""
    ssot = tmp_path / "SSOT.md"
    ms   = tmp_path / "milestones.json"
    ssot.write_text(VALID_SSOT, encoding="utf-8")
    data = {
        "milestones": [{
            "id": "M1", "title": "M1", "status": "pending",
            "waves": [{"id": "W1", "title": "W1", "tasks": [
                {"id": "T1", "title": "TBD: もう終わった", "status": "done"},
                {"id": "T2", "title": "verify: 統合テストを実行して全 PASS を確認", "status": "pending"},
            ]}],
        }]
    }
    ms.write_text(json.dumps(data), encoding="utf-8")
    issues = run_checks(ssot, ms)
    errors = [m for s, m in issues if s == "ERROR"]
    assert not any("T1" in e for e in errors)


def test_short_title_pending_is_warn(tmp_path):
    ssot = tmp_path / "SSOT.md"
    ms   = tmp_path / "milestones.json"
    ssot.write_text(VALID_SSOT, encoding="utf-8")
    data = {
        "milestones": [{
            "id": "M1", "title": "M1", "status": "pending",
            "waves": [{"id": "W1", "title": "W1", "tasks": [
                {"id": "T1", "title": "短すぎ", "status": "pending"},  # 4 文字
                {"id": "T2", "title": "verify: 統合テストを実行して全 PASS を確認する", "status": "pending"},
            ]}],
        }]
    }
    ms.write_text(json.dumps(data), encoding="utf-8")
    issues = run_checks(ssot, ms)
    warns = [m for s, m in issues if s == "WARN"]
    assert any("T1" in w for w in warns)


def test_no_verify_task_is_warn(tmp_path):
    ssot = tmp_path / "SSOT.md"
    ms   = tmp_path / "milestones.json"
    ssot.write_text(VALID_SSOT, encoding="utf-8")
    data = {
        "milestones": [{
            "id": "M1", "title": "何かのフェーズ", "status": "pending",
            "waves": [{"id": "W1", "title": "W1", "tasks": [
                {"id": "T1", "title": "コードを書くだけのタスクです", "status": "pending"},
            ]}],
        }]
    }
    ms.write_text(json.dumps(data), encoding="utf-8")
    issues = run_checks(ssot, ms)
    warns = [m for s, m in issues if s == "WARN"]
    assert any("M1" in w and "統合確認" in w for w in warns)


def test_invalid_json_milestones_is_error(tmp_path):
    ssot = tmp_path / "SSOT.md"
    ms   = tmp_path / "milestones.json"
    ssot.write_text(VALID_SSOT, encoding="utf-8")
    ms.write_text("{ broken json", encoding="utf-8")
    issues = run_checks(ssot, ms)
    errors = [m for s, m in issues if s == "ERROR"]
    assert any("不正な JSON" in e for e in errors)


# ─── calc_result ─────────────────────────────────────────────────────────────

def test_calc_result_all_ok():
    issues = [("OK", "a"), ("OK", "b")]
    verdict, score, code = calc_result(issues)
    assert verdict == "OK"
    assert code == 0
    assert score > 0


def test_calc_result_warn_gives_exit_1():
    issues = [("OK", "a"), ("WARN", "w")]
    verdict, _, code = calc_result(issues)
    assert verdict == "WARN"
    assert code == 1


def test_calc_result_error_gives_exit_2():
    issues = [("OK", "a"), ("ERROR", "e")]
    verdict, _, code = calc_result(issues)
    assert verdict == "ERROR"
    assert code == 2
