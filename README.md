# quarto

Quarto(クアルト)ボードゲームの実装と、遺伝的アルゴリズムで評価関数を進化させた対戦bot。

## 構成

```
quarto/
  piece.py        駒(4属性・16種)の表現
  board.py        4x4盤面と勝利判定(行・列・斜め、オプションで2x2)
  game.py         ターン進行(駒選択→配置)を管理するステートマシン
  ai/
    evaluation.py 盤面特徴量とパラメータ化された評価関数
    search.py     評価関数を使ったミニマックス探索(alpha-beta)
    ga.py         評価関数の重みを進化させる遺伝的アルゴリズム
    players.py    RandomPlayer / MinimaxPlayer などのプレイヤー実装
  web/
    app.py        Flaskアプリ(REST API, 状態はセッションcookieに保持)
    templates/    index.html
    static/       app.js, style.css
scripts/
  train_ga.py     GA学習を実行し重みをJSONに保存するCLI
weights/
  default.json    デフォルトで同梱されている学習済み重み
tests/             pytestによるユニットテスト
```

## Quartoのルール

4x4の盤に、高さ/色/形/中空-実体の4つの二値属性を持つ16種類の駒を置いていく。
自分の手番では**相手が選んだ駒を盤に置き**、その後**自分が次に置かせる駒を選んで相手に渡す**。
縦・横・斜めのいずれかの4マスに置かれた駒が、4属性のうち少なくとも1つを共通して持っていれば、
その並びを完成させた(=置いた)プレイヤーの勝ち。

## セットアップ

```bash
pip install -r requirements.txt
```

## テスト

```bash
python3 -m pytest tests/ -q
```

## botの学習(遺伝的アルゴリズム)

```bash
python3 scripts/train_ga.py --population 24 --generations 30 --depth 2 --out weights/default.json
```

- 個体 = 評価関数の重みベクトル
- 適応度 = 深さ制限付きミニマックス(重みを使用)で、(1) 個体群内の総当たり戦、
  (2) ランダムプレイヤーとの対戦、を行った勝率
- 選択はトーナメント選択、交叉は一様交叉、突然変異はガウスノイズ + エリート保存

`--depth` を上げるほど1ゲームの計算量が増える(探索の分岐数が大きいため)。
まずは `--depth 1` で世代数を増やして探索し、仕上げに `--depth 2` 程度で追加学習するのがおすすめ。

学習結果は `weights/default.json` に保存すると、Webアプリがそのままbotの脳として読み込む
(環境変数 `QUARTO_BOT_DEPTH` でWebアプリ上のbotの探索深さを変更可能、デフォルト2)。

## Web GUIで対戦する

```bash
export FLASK_APP=quarto.web.app
python3 -m flask run
```

`http://127.0.0.1:5000` を開き、"New Game" で対戦を開始。先手・後手や2x2ルール(4隅などの
2x2ブロックも勝利条件に含めるオプションルール)の有無を選べる。

## 実装メモ

- 評価関数は「(盤面上の各ライン(行・列・斜め、任意で2x2)について、埋まっている駒数と、
  それらが共通して持つ属性数)」を特徴量とし、その組み合わせごとの重みをGAで学習する。
- 探索はGAが評価する対局・Webアプリでのbotの着手の両方で共通のミニマックス
  (alpha-beta枝刈り)を使用し、深さ・重みだけを差し替えられる設計になっている。
