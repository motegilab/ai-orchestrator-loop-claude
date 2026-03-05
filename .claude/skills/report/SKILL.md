---
name: report
description: セッション結果をレポートするSkill。作業終了時、Stopの直前、「レポートして」「まとめて」と言われた時に自動invokeする。
---

# Report Skill

## MUST READ FIRST
1. verify Skillの出力

## Steps
1. 今回セッションのDONE/NEXT/FAIL/FIX/VERIFYを書く
2. runtime/reports/REPORT_LATEST.md を更新する
3. runtime/runs/latest.json の summary フィールドを更新する
4. on_stop.py が自動生成するnext_session.mdの補足情報を書く

## next_session.md の必須セクション
- DONE: 完了したこと
- NEXT: 次にやること（優先順に）
- FAIL: 失敗したこと（なければ「なし」）
- FIX: 適用した修正（1原因1修正）
- VERIFY: 実行した検証コマンドと結果
- CONTEXT: 次回セッションに必要な状態情報

## Outputs
- runtime/reports/REPORT_LATEST.md（更新）
- runtime/logs/next_session.md（次回セッション用）
