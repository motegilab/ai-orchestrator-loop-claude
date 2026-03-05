---
name: patch
description: 最小差分でファイルを修正するSkill。修正・実装依頼時、observe Skillの結果を受けて修正に入る時、「直して」「実装して」と言われた時に自動invokeする。
---

# Patch Skill

## MUST READ FIRST
1. SSOT.md（§1 絶対ルール）
2. observe Skillの出力（hypothesis_one_cause）

## 鉄則
- 1修正 = 1原因 = 1ファイル（複数ファイルにまたがる場合は最小範囲に絞る）
- SSOT.md / policy/ssot_integrity.json は絶対に触らない

## Steps
1. hypothesis_one_causeを確認する
2. 修正対象ファイルを特定する（1ファイル原則）
3. 最小差分で修正する（EditまたはMultiEdit）
4. 変更内容を1行で記述する（one_fix）
5. verify Skillに引き継ぐ

## Outputs
- one_fix: 修正内容の1行説明
- files_changed: 変更したファイル一覧
- verify_commands: 検証に使うコマンド

## Failure modes
- 修正が大規模になりそうな場合 → スコープを縮小して最小限の修正に留める
- 依存ファイルが多い場合 → 最も根本のファイルのみ修正し、依存先はnext_sessionに書く
