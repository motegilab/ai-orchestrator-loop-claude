"""
tests/infra/test_on_stop_helpers.py

on_stop.py の get_next_task() ロジックを単体テスト。
MILESTONES グローバルを monkeypatch で差し替えて実際のファイルを使わない。
"""
import json
import sys
import types
from pathlib import Path

import pytest

# on_stop.py を import するため hooks ディレクトリをパスに追加
HOOKS_DIR = Path(__file__).parent.parent.parent / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))


def _load_get_next_task(milestones_path: Path):
    """
    on_stop モジュールを都度リロードし、MILESTONES を差し替えた上で
    get_next_task 関数を返す。
    importlib を使わず sys.modules を直接操作して副作用を最小化する。
    """
    import importlib
    # キャッシュを消してリロード
    if "on_stop" in sys.modules:
        del sys.modules["on_stop"]
    mod = importlib.import_module("on_stop")
    mod.MILESTONES = milestones_path
    return mod.get_next_task


def _make_milestones(tmp_path, data: dict) -> Path:
    p = tmp_path / "milestones.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


# ─── 基本動作 ─────────────────────────────────────────────────────────────────

def test_returns_first_pending_task(tmp_path):
    data = {"milestones": [{
        "id": "M1", "title": "M1", "status": "pending",
        "waves": [{"id": "W1", "title": "W1", "tasks": [
            {"id": "T1", "title": "最初のタスク", "status": "done"},
            {"id": "T2", "title": "二番目のタスク", "status": "pending"},
        ]}],
    }]}
    get_next_task = _load_get_next_task(_make_milestones(tmp_path, data))
    result = get_next_task()
    assert result is not None
    assert result["task_id"] == "T2"
    assert result["task_title"] == "二番目のタスク"


def test_returns_none_when_all_done(tmp_path):
    data = {"milestones": [{
        "id": "M1", "title": "M1", "status": "done",
        "waves": [{"id": "W1", "title": "W1", "tasks": [
            {"id": "T1", "title": "完了済み", "status": "done"},
        ]}],
    }]}
    get_next_task = _load_get_next_task(_make_milestones(tmp_path, data))
    assert get_next_task() is None


def test_skips_done_milestones(tmp_path):
    data = {"milestones": [
        {
            "id": "M1", "title": "M1", "status": "done",
            "waves": [{"id": "W1", "title": "W1", "tasks": [
                {"id": "T1", "title": "M1のタスク", "status": "pending"},
            ]}],
        },
        {
            "id": "M2", "title": "M2", "status": "pending",
            "waves": [{"id": "W2", "title": "W2", "tasks": [
                {"id": "T2", "title": "M2のタスク", "status": "pending"},
            ]}],
        },
    ]}
    get_next_task = _load_get_next_task(_make_milestones(tmp_path, data))
    result = get_next_task()
    assert result["task_id"] == "T2"


# ─── checkpoint フィールド ────────────────────────────────────────────────────

def test_checkpoint_false_by_default(tmp_path):
    data = {"milestones": [{
        "id": "M1", "title": "M1", "status": "pending",
        "waves": [{"id": "W1", "title": "W1", "tasks": [
            {"id": "T1", "title": "普通のタスク", "status": "pending"},
        ]}],
    }]}
    get_next_task = _load_get_next_task(_make_milestones(tmp_path, data))
    result = get_next_task()
    assert result["checkpoint"] is False


def test_checkpoint_true_when_set(tmp_path):
    data = {"milestones": [{
        "id": "M1", "title": "M1", "status": "pending",
        "waves": [{"id": "W1", "title": "W1", "tasks": [
            {"id": "T1", "title": "停止ポイントのタスク", "status": "pending", "checkpoint": True},
        ]}],
    }]}
    get_next_task = _load_get_next_task(_make_milestones(tmp_path, data))
    result = get_next_task()
    assert result["checkpoint"] is True


# ─── エッジケース ─────────────────────────────────────────────────────────────

def test_returns_none_when_file_missing(tmp_path):
    get_next_task = _load_get_next_task(tmp_path / "nonexistent.json")
    assert get_next_task() is None


def test_returns_none_when_milestones_empty(tmp_path):
    data = {"milestones": []}
    get_next_task = _load_get_next_task(_make_milestones(tmp_path, data))
    assert get_next_task() is None


def test_result_contains_expected_keys(tmp_path):
    data = {"milestones": [{
        "id": "M1", "title": "マイルストーン1", "status": "pending",
        "waves": [{"id": "W1", "title": "ウェーブ1", "tasks": [
            {"id": "T1", "title": "タスクのタイトルです", "status": "pending"},
        ]}],
    }]}
    get_next_task = _load_get_next_task(_make_milestones(tmp_path, data))
    result = get_next_task()
    assert set(result.keys()) >= {"milestone_title", "wave_title", "task_id", "task_title", "checkpoint"}
