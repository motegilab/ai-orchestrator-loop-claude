---
name: verify
description: 変更後の検証を行うSkill。patch Skillの後、「確認して」「テストして」「動くか確認」と言われた時に自動invokeする。
---

# Verify Skill

## MUST READ FIRST
1. patch Skillの出力（verify_commands）

## Steps
1. verify_commandsを実行する
2. exit codeを記録する（0=success, それ以外=fail）
3. stdoutの末尾を記録する（最大20行）
4. stderrにエラーがあれば記録する
5. 成功/失敗を判定してreport Skillに引き継ぐ

## Outputs
- verify_commands: 実行したコマンド
- exit_codes: 各コマンドの終了コード
- stdout_tail: 標準出力の末尾
- evidence_paths: ログファイルのパス

## Failure modes
- コマンドが存在しない場合 → make loop-status で確認可能なものを代替として使う
- タイムアウトの場合 → failed として記録。成功扱いにしない
