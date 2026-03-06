---
name: report
description: セッション結果をレポートするSkill。作業終了時、Stopの直前、「レポートして」「まとめて」と言われた時に自動invokeする。
allowed-tools: Write, Read
---

# Report Skill

## MUST READ FIRST
1. verify Skillの出力（exit_codes, stdout_tail）
2. 今回セッションで変更したファイル一覧

## ⚠️ 重要: on_stop.py との役割分担

| 担当 | 処理 |
|------|------|
| **Claude（このSkill）** | `runtime/reports/REPORT_LATEST.md` を書く |
| **on_stop.py（自動）** | `runtime/runs/latest.json` を生成する |
| **on_stop.py（自動）** | `runtime/logs/next_session.md` を生成する |

→ latest.json と next_session.md はClaudeが書かなくてよい。on_stop.pyが自動生成する。

## Steps
1. 今回セッションの作業結果をまとめる
2. 下記テンプレートで `runtime/reports/REPORT_LATEST.md` を Write ツールで上書きする
3. PLACEHOLDER_MARKERS（後述）を含まないことを確認する

## REPORT_LATEST.md テンプレート

```
# REPORT_LATEST.md
run_id: （on_stop.pyが付与するため "current_session" と書く）
generated_at: （今日の日付 YYYY-MM-DD）
status: written_by_claude
generated_by: report Skill

## hypothesis_one_cause
（今回対処した問題の根本原因を1文で）

## one_fix
（適用した修正を1行で）

## files_changed
- （変更したファイルのパス）

## verify_commands
\`\`\`
（検証に使ったコマンド）
\`\`\`

## exit_codes
- （コマンド名: exit=0/1/2）

## evidence_paths
- runtime/artifacts/audit_log.jsonl
- docs/go-checklist.md（該当する場合）

## decision
written_by_claude

## DONE
（完了したこと箇条書き）

## NEXT
（次タスクのID と タイトル）

## FAIL
（失敗したことがあれば。なければ「なし」）
```

## ⚠️ PLACEHOLDER_MARKERS（これらの文字列を含むと on_stop.py が上書きする）
- `Claudeが作業中に更新する`
- `実施した修正`
- `変更ファイル`

→ テンプレートの () 内を必ず実際の内容で埋めること。

## Outputs
- `runtime/reports/REPORT_LATEST.md`（Write ツールで書き込み済み）

## 完了確認
- `## decision` が `written_by_claude` になっていること
- ファイルにPLACEHOLDER_MARKERSが含まれていないこと
