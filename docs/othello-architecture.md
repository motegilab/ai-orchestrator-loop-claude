# Othello — コンポーネント設計仕様

Claude ループが自律実装するためのアーキテクチャ定義。
各コンポーネントはこのファイルのインターフェース契約に従って実装する。

---

## ディレクトリ構成

```
src/othello/
  __init__.py
  board.py       # Component 1: Board（依存なし）
  rules.py       # Component 2: Rules（依存: board）
  game_state.py  # Component 3: GameState（依存: board, rules）
  ai.py          # Component 4: AIPlayer（依存: board, rules）
  cli.py         # Component 5: CLI（依存: game_state, ai）
  main.py        # Entry point

tests/othello/
  __init__.py
  test_board.py
  test_rules.py
  test_game_state.py
  test_ai.py
```

---

## 依存関係ルール（絶対守ること）

| コンポーネント | import してよいもの |
|---|---|
| board.py | なし（stdlib のみ） |
| rules.py | `from src.othello.board import ...` のみ |
| game_state.py | board, rules のみ |
| ai.py | board, rules のみ（game_state は import 禁止） |
| cli.py | game_state, ai のみ |
| main.py | cli, game_state, ai |

---

## コンポーネント 1: Board（board.py）

依存: なし / stdlib のみ

```python
EMPTY = 0
BLACK = 1
WHITE = 2

class Board:
    def __init__(self) -> None:
        """8x8 空ボード + 中央4マスに初期配置"""

    def get(self, row: int, col: int) -> int:
        """(row, col) の石を返す。範囲外は ValueError"""

    def set(self, row: int, col: int, color: int) -> None:
        """(row, col) に石を置く"""

    def copy(self) -> "Board":
        """独立したコピーを返す"""

    def count(self, color: int) -> int:
        """color の石の数を返す"""
```

---

## コンポーネント 2: Rules（rules.py）

依存: board のみ

```python
def get_valid_moves(board: Board, color: int) -> list[tuple[int, int]]:
    """color が置ける (row, col) のリストを返す。なければ []"""

def apply_move(board: Board, row: int, col: int, color: int) -> Board:
    """指定位置に置いて反転した新しい Board を返す（元の board は変更しない）"""

def is_game_over(board: Board) -> bool:
    """両色とも有効手がなければ True"""

def get_winner(board: Board) -> int:
    """BLACK / WHITE / EMPTY（引き分け）を返す"""
```

---

## コンポーネント 3: GameState（game_state.py）

依存: board, rules のみ

```python
class GameState:
    def __init__(self) -> None:
        """Board() で初期化、current_color = BLACK"""

    @property
    def board(self) -> Board: ...

    @property
    def current_color(self) -> int: ...

    def score(self) -> dict[int, int]:
        """例: {BLACK: 2, WHITE: 2}"""

    def make_move(self, row: int, col: int) -> bool:
        """有効手なら置いてターン交代、True を返す。無効なら False"""

    def pass_turn(self) -> None:
        """パス（有効手がないとき）"""

    @property
    def is_over(self) -> bool: ...

    @property
    def winner(self) -> int:
        """BLACK / WHITE / EMPTY（引き分け）"""
```

---

## コンポーネント 4: AIPlayer（ai.py）

依存: board, rules のみ（game_state を import しない）

```python
class RandomAI:
    def __init__(self, color: int) -> None: ...

    def choose_move(self, board: Board) -> tuple[int, int] | None:
        """有効手からランダムに選ぶ。有効手なければ None"""

class MinimaxAI:
    def __init__(self, color: int, depth: int = 4) -> None: ...

    def choose_move(self, board: Board) -> tuple[int, int] | None:
        """minimax (alpha-beta pruning) で最善手を返す。
        評価関数: コーナー(+100) / 辺(+10) / 通常(+1) の重み付きスコア差"""
```

---

## コンポーネント 5: CLI（cli.py）

依存: game_state, ai のみ

```python
class CLI:
    def __init__(
        self,
        game_state: GameState,
        black_player,   # RandomAI | MinimaxAI | None (=Human)
        white_player,   # RandomAI | MinimaxAI | None (=Human)
    ) -> None: ...

    def run(self) -> None:
        """ゲームループ。終了まで回す"""

    def display_board(self) -> None:
        """以下の形式でボードを表示:
          a b c d e f g h
        1 . . . . . . . .
        ...
        4 . . . W B . . .
        黒: 2  白: 2
        """
```

---

## main.py 起動オプション

```
python src/othello/main.py              # Human(黒) vs RandomAI(白)
python src/othello/main.py --minimax    # Human(黒) vs MinimaxAI(白)
python src/othello/main.py --ai-vs-ai  # RandomAI(黒) vs MinimaxAI(白) 自動完走
```

---

## テスト要件

統合確認タスク（T23, T26, T32）は必ず以下を実行して全 PASS を確認する:

```bash
python -m pytest tests/othello/ -v
```

各テストファイルの最低限の検証項目:

| ファイル | 検証項目 |
|---|---|
| test_board.py | 初期配置確認, get/set, copy が独立, count |
| test_rules.py | 初期有効手4マス, apply_move で反転, is_game_over, get_winner |
| test_game_state.py | make_move 成功/失敗, pass_turn, is_over, score |
| test_ai.py | RandomAI が有効手を返す, MinimaxAI がコーナー優先 |
