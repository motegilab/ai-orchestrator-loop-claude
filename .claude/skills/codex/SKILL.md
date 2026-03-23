---
name: codex
description: |
  Codex CLI（OpenAI）を使ってコードレビュー・設計相談・バグ調査を行うオプションSkill。
  トリガー: "codex", "codexと相談", "codexに聞いて", "コードレビュー", "レビューして"
  使用場面: (1) コードレビュー (2) 設計相談 (3) バグ調査 (4) UIレビュー (5) 文言検討
  ※ オプションSkill: Codex CLI + OPENAI_API_KEY が必要。make codex-enable で有効化。
allowed-tools: "Read, Bash, Glob, Grep"
metadata:
  version: 1.0.0
  optional: true
  requires:
    - "Codex CLI (npm install -g @openai/codex)"
    - "OPENAI_API_KEY 環境変数"
---

# Codex Skill — 別AIによるセカンドオピニオン

## このSkillの目的

Claude とは異なるモデル（OpenAI Codex）によるセカンドオピニオンを得る。
特に「SSOTの抜け」「コードレビュー」「設計上の盲点」を発見するのに有効。

---

## Step 0: 前提確認（必ず最初に実行）

```bash
# オプションSkillの有効化状態を確認
python -c "
import json, pathlib, sys
f = pathlib.Path('policy/optional_skills.json')
if not f.exists():
    print('DISABLED: optional_skills.json が存在しません')
    sys.exit(1)
cfg = json.loads(f.read_text(encoding='utf-8'))
skill = cfg.get('skills', {}).get('codex', {})
if not skill.get('enabled', False):
    print('DISABLED: codex Skill は無効です。有効化: make codex-enable')
    sys.exit(1)
print('OK')
"
```

**Step 0 が DISABLED を返した場合**: ユーザーに以下を伝えて終了する。

```
codex Skill は現在無効です。
有効化するには:
  1. make codex-enable を実行
  2. Codex CLI がインストール済みか確認: codex --version
  3. OPENAI_API_KEY 環境変数が設定済みか確認
```

---

## Step 1: 依頼内容の整理

ユーザーの依頼から以下を決定する:
- **対象ディレクトリ**: 現在の作業ディレクトリ（または指定があれば使用）
- **依頼内容**: 何をレビュー・相談するか
- **タイプ**: コードレビュー / 設計相談 / バグ調査 / UIレビュー / 文言検討

---

## Step 2: Codex 実行

```bash
codex exec --full-auto --sandbox read-only --cd <対象ディレクトリ> "<依頼内容>。確認や質問は不要です。具体的な提案・修正案・コード例まで自主的に出力してください。"
```

**パラメータ**:
| パラメータ | 説明 |
|---|---|
| `--full-auto` | 完全自動モード |
| `--sandbox read-only` | 読み取り専用（ファイル書き換え禁止） |
| `--cd <dir>` | 対象プロジェクトのディレクトリ |

**プロンプト末尾に必ず追加**: `「確認や質問は不要です。具体的な提案まで自主的に出力してください。」`

---

## 用途別プロンプト例

### コードレビュー
```
このプロジェクトのコードをレビューして、改善点を指摘してください。確認や質問は不要です。具体的な修正案とコード例まで自主的に出力してください。
```

### SSOTレビュー（ssot-review Skillと組み合わせる）
```
SSOT.md を読んで、メインプログラマーとして実装上の抜けや曖昧点を指摘してください。確認や質問は不要です。具体的な補足案まで自主的に出力してください。
```

### バグ調査
```
[エラー内容] の原因を調査してください。確認や質問は不要です。原因の特定と具体的な修正案まで自主的に出力してください。
```

### 設計相談
```
[設計の概要] について、見落としやリスクを指摘してください。確認や質問は不要です。改善提案まで自主的に出力してください。
```

---

## 関連

- [[ssot-review]] — Claude 自身による SSOT のメインプログラマーシミュレーション
- [[observe]] — 問題調査・現状把握
