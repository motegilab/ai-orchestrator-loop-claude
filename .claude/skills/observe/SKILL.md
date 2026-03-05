---
name: observe
description: >
  問題調査・現状把握のためのSkill。
  以下の状況で自動invokeされる:
  - エラーや問題の調査を依頼された時
  - runtime/reports/REPORT_LATEST.md にエラー・失敗が記録されている時
  - "調べて" "確認して" "何が起きてる" などの調査依頼時
  - セッション開始直後にstatus=failedが検出された時
allowed-tools: Read, Bash, Glob, Grep
---

# Observe Skill

## MUST READ FIRST
1. `SSOT.md` — §0 設計原則、§1 絶対ルール
2. `runtime/runs/latest.json` — 前回ループの結果
3. `runtime/reports/REPORT_LATEST.md` — 前回の詳細レポート
4. `tasks/milestones.json` — 現在のタスク状況

## Inputs
- 問題の概要（プロンプトから）
- `runtime/reports/REPORT_LATEST.md` のエラー記録
- 対象ファイル・ディレクトリ（指定された場合）

## Steps
1. 前回レポートを読む: `cat runtime/reports/REPORT_LATEST.md`
2. エラーの証拠を収集する（ファイルパスと行番号を特定）
3. 仮説を1つ立てる（1原因1修正の原則）
4. 証拠パスをリストアップする

## Outputs
- `issue_candidates`: 発見した問題のリスト（最大3件）
- `hypothesis_one_cause`: 最優先の仮説（1文）
- `evidence_paths`: 根拠ファイルのパスリスト

## Failure Modes
| 症状 | 対処 |
|------|------|
| runtime/が存在しない | 初回起動。milestones.jsonのT1.1.xを確認する |
| latest.jsonが壊れている | runtime/runs/内の最新ファイルを直接読む |
