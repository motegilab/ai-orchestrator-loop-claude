---
name: INDEX
description: Skill Graph の MOC（Map of Content）。全 Skill の概要・トリガー・関連を一覧する
type: index
---

# Skill Graph — INDEX

> このファイルは `.claude/skills/` の全 Skill を俯瞰するナビゲーションハブです。
> 各 Skill への `[[wikilink]]` で移動できます。

---

## コアループ（Observe → Patch → Verify → Report）

| Skill | 役割 | 自動トリガー |
|---|---|---|
| [[observe]] | 問題・タスクの調査と仮説立案 | エラー検出時、セッション開始時 |
| [[patch]] | 最小差分でのファイル修正 | observe 完了後、「直して」「実装して」 |
| [[verify]] | 変更後の検証と結果記録 | patch 完了後、「確認して」「テストして」 |
| [[report]] | セッション結果を REPORT_LATEST.md に書く | Stop 直前、「まとめて」 |

### ループの流れ

```
セッション開始
  └→ [[observe]]  : REPORT_LATEST.md + milestones.json を読んで仮説を立てる
       └→ [[patch]]   : hypothesis_one_cause を 1 修正で解決する
            └→ [[verify]]  : exit code と stdout を記録する
                 └→ [[report]] : REPORT_LATEST.md を書いて Stop
```

---

## 特殊用途 Skill

| Skill | 役割 | 自動トリガー |
|---|---|---|
| [[release]] | OSS 公開前のリリース準備チェック | "release" "リリース" "公開チェック" |
| [[milestone-review]] | マイルストーン完了時のHTMLチェックリスト生成 | milestone_completed 検出時 |

---

## Skill 詳細

### [[observe]]
- **入力**: REPORT_LATEST.md, milestones.json
- **出力**: issue_candidates, hypothesis_one_cause, evidence_paths
- **次へ**: → [[patch]]

### [[patch]]
- **入力**: hypothesis_one_cause (observe から)
- **出力**: one_fix, files_changed, verify_commands
- **次へ**: → [[verify]]
- **制約**: 1修正 = 1原因。SSOT.md / ssot_integrity.json は触らない

### [[verify]]
- **入力**: verify_commands (patch から)
- **出力**: exit_codes, stdout_tail, evidence_paths
- **次へ**: → [[report]]
- **制約**: タイムアウトは failed として記録（成功扱い禁止）

### [[report]]
- **入力**: verify の出力、変更ファイル一覧
- **出力**: runtime/reports/REPORT_LATEST.md (`decision: written_by_claude`)
- **制約**: on_stop.py との役割分担 — latest.json は on_stop.py が書く

### [[release]]
- **入力**: git status, policy/, SSOT.md
- **出力**: REPORT_LATEST.md の release_check_results
- **チェック**: Safety / Required Files / Template Neutrality / Integrity / Smoke Test

### [[milestone-review]]
- **入力**: milestones.json, SSOT.md, REPORT_LATEST.md, latest.json
- **出力**: runtime/reports/MANUAL_CHECK_{milestone_id}.html
- **用途**: 人間がブラウザで開いてチェックする

---

## 自己改善の仕組み

Skill が期待通り動かない場合は `runtime/proposals/SKILL_PROPOSAL_{name}.md` に提案を書く。
次のセッション開始時に自動通知される。SKILL.md の変更は人間が判断する。

提案ファイルの状況を確認: `make diagnose`

---

## 関連ファイル

- [CLAUDE.md](../../CLAUDE.md) — ワークフロー定義
- [SSOT.md](../../SSOT.md) — 設計の正本
- [tools/scripts/diagnose.py](../../tools/scripts/diagnose.py) — Skill/Hook 健全性チェック
