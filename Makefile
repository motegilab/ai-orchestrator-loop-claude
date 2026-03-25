# AI Orchestrator Loop — Makefile
# Windows (PowerShell/cmd) + macOS/Linux 両対応
# シェル依存ロジックは全て tools/scripts/*.py に委譲
#
# 入口: loop-start / loop-stop / loop-status / setup

.PHONY: loop-start loop-start-detach loop-run loop-stop loop-status setup ssot-check ssot-edit-start ssot-edit-end ssot-fix diagnose test help codex-enable codex-disable

## ループ開始（同じウィンドウ — Hook の stdin/stdout が正しく動く）
loop-start:
	python tools/scripts/loop_start.py

## ループ開始（別ウィンドウ — Windows Terminal or cmd.exe で新規起動）
loop-start-detach:
	python tools/scripts/loop_start.py --detach

## 自動連続ループ（pending タスクがなくなるまで / N回指定可: make loop-run N=3）
loop-run:
	python tools/scripts/loop_run.py $(N)

## 前回ループの状態確認
loop-status:
	python tools/scripts/loop_status.py

## 停止案内（Stop Hook は Claude Code が自動で実行する）
loop-stop:
	python -c "print('[loop-stop] Claude Code セッション内で Ctrl+C または /stop を入力してください。'); print('Stop Hook (on_stop.py) が自動でレポートを生成します。')"

## プロジェクト自己診断（Hooks整合性・Skill YAML・未対応Proposal・未使用Skill・停滞タスク・Upstream差分）
diagnose:
	python tools/scripts/diagnose.py

## インフラ単体テスト（ssot_check / on_stop / loop_run のロジック検証）
test:
	python -m pytest tests/infra/ -v

## SSOT 品質チェック（loop-run の前に自動実行される）
ssot-check:
	python tools/scripts/ssot_check.py

## SSOT 編集モード開始（バックアップ取得 + ゲート解除）
ssot-edit-start:
	python -c "import shutil,datetime,pathlib; pathlib.Path('runtime').mkdir(exist_ok=True); dest=f'runtime/ssot_backup_{datetime.datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.md'; shutil.copy('SSOT.md', dest); print(f'✅ バックアップ: {dest}')"
	python .claude/hooks/ssot_gate.py --disable

## SSOT 編集モード終了（ゲート再有効化 + ハッシュ更新）
ssot-edit-end:
	python .claude/hooks/ssot_gate.py --enable

## ハッシュ不一致エラーを修復（誤送信・強制停止後にエラーが出たら実行）
ssot-fix:
	python .claude/hooks/ssot_gate.py --update-hash

## オプションSkill: codex を有効化（Codex CLI + OPENAI_API_KEY が必要）
codex-enable:
	python -c "import json,pathlib; f=pathlib.Path('policy/optional_skills.json'); d=json.loads(f.read_text(encoding='utf-8')); d['skills']['codex']['enabled']=True; f.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8'); print('✅ codex Skill: 有効化しました')"

## オプションSkill: codex を無効化
codex-disable:
	python -c "import json,pathlib; f=pathlib.Path('policy/optional_skills.json'); d=json.loads(f.read_text(encoding='utf-8')); d['skills']['codex']['enabled']=False; f.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8'); print('🔒 codex Skill: 無効化しました')"

## 初回セットアップ（ツール確認 + runtime/ 作成 + SSOT hash 更新）
setup:
	python tools/scripts/setup.py

## ヘルプ
help:
	python -c "print('make loop-start         ループ開始 (同ウィンドウ)'); print('make loop-start-detach  ループ開始 (新規ウィンドウ, Windows)'); print('make loop-run           自動連続ループ (pending タスクがなくなるまで)'); print('make loop-run N=3       最大3ループ実行'); print('make loop-status        前回ループの状態を表示'); print('make loop-stop          停止案内を表示'); print('make ssot-check         SSOT 品質チェック'); print('make diagnose           プロジェクト自己診断'); print('make test               インフラ単体テスト実行'); print('make setup              初回セットアップ')"
