# Physical AI Learning

Physical AI / Deep Learning / ROS 2 / Robot Learningの学習を記録する個人用Webアプリです。
Streamlitで画面を作り、Python標準のSQLiteで保存します。HTML・JavaScriptやデータベースサーバーの設定は不要です。

## 起動方法

Python 3.12を推奨します。このREADMEのあるフォルダーで実行してください。

### Windows（PowerShell）

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

`python`が使えない場合はPythonをインストールし、PATHを有効にしてターミナルを開き直してください。
`py -3.12`が使えるPCでは、最初のコマンドを`py -3.12 -m venv .venv`に置き換えられます。
仮想環境の有効化は不要なので、PowerShellの実行ポリシーを変更する必要はありません。

### macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

### uvを利用する場合（Pythonの取得も含む）

```powershell
uv venv --python 3.12
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

ブラウザーで http://localhost:8501 を開きます。停止はターミナルで`Ctrl+C`。
2回目以降は最後の起動コマンドだけです。設定により接続先はこのPC（127.0.0.1）に限定しています。

## 使い方

1. **ダッシュボード**：全体・分野別の進捗、完了件数、現在学習中、今日のおすすめ最大3件を確認します。
2. **トピック**：分野・状態で絞り込み、追加・編集する項目を選びます。理解度、メモ、次にやることを入力して保存します。
3. **学習ログ**：日付を選び、学んだこと・手を動かしたこと・疑問・次回の予定を記録します。同じ日付は読み込んで更新します。
4. **理解度チェック**：トピックを選び、問題・自分の回答・理解度を登録します。回答は折り畳まれ、登録済みの問題も編集できます。自動採点はありません。
5. **成果物**：既存トピックの編集欄の下に、実験やコードの名前とURL・ローカルパスを登録します。複数登録できます。URLはリンクとして開けますが、パスの実行や存在確認は行いません。

### 進捗と初期データ

| 状態 | 進捗への換算 |
| --- | ---: |
| 未学習 | 0% |
| 学習中 | 25% |
| 概念理解 | 50% |
| 実装済み | 75% |
| 完了 | 100% |

進捗は登録トピックの到達度の平均です。完了件数の割合とは異なります。理解度1〜5は別の自己評価です。
未登録の分野は「トピック未登録」と表示し、全体平均の分母には含めません。
理解度の目安は、1：説明できない、2：見覚えがある、3：要点を説明できる、4：応用できる、5：人に教えられる、です。

おすすめは完了以外を「学習中→概念理解→実装済み→未学習」、同じ状態なら登録順に最大3件選びます。
「次にやること」があればその文章を表示し、空なら状態に応じた提案を表示します。
日付ごとに消えるチェックリストではありません。学習後に状態や次の作業を更新してください。

指定の20トピックを初回だけ登録します。初期の理解度は未評価です。
応用編1の分野名は、初期データの表記に合わせて「Physical AI 応用編」としています。
「#4 ROS 2：概念理解、一部実装」は、状態を「概念理解」、メモを「一部実装」とします。
他の6分野も追加先として用意しますが、進捗を仮定するトピックは登録しません。

## ファイル構成と、読む順番

```text
app.py                   画面、入力フォーム、ページ切り替え
learning.py              状態・分野の定義、進捗計算、おすすめ
database.py              SQLiteテーブル作成、保存と読み込み
seed_data.py             初回の20トピック
requirements.txt         Streamlitと互換性のある依存関係のバージョン指定
.streamlit/config.toml   配色、ローカル接続設定
tests/                   保存・計算・画面操作のテスト
data/learning.db         初回起動時に自動作成（Git管理対象外）
```

重要度順に次を読むと、アプリを理解しやすくなります。

1. **app.py：topics_page()とsave()**。入力→保存ボタン→DB更新→`st.rerun()`で再表示、という流れです。`st.form`で入力をまとめ、保存前の変更をDBに書き込みません。
2. **learning.py：STATUS_PROGRESSとprogress()**。状態を数値へ変えて平均します。重みの変更はここで行えます。`today_tasks()`でおすすめ順を変えられます。
3. **database.py：connection()とsave_topic()**。接続を必ず閉じ、保存成功時に確定します。SQLの`?`には値を別に渡し、入力文をSQLへ直接埋め込みません。
4. **seed_data.pyとinitialize()**。初期データは初回だけ登録します。後でseed_data.pyを編集しても既存DBには反映されないため、登録済みの項目は画面から変更します。

実装は「初期データ・保存・計算」「画面」「動作確認」の順に進めています。
画面と保存を分けているため、将来画面を追加しても保存処理を再利用できます。

## データ保存・バックアップ

保存先はアプリ内の`data/learning.db`。アプリを停止してファイルをコピーすればバックアップできます。
復元は停止中に同じ場所へバックアップDBをコピーしてから再起動します。
サイドバーからJSONで全学習データを出力することもできます。JSON取り込みはMVPに含めません。
個人メモを公開しないよう、`data/`はGit管理から除外しています。
開発用には環境変数`PHYSICAL_AI_DB`で保存先を変更できます。

## 将来の拡張

`topics.id`を軸に`questions.topic_id`と`artifacts.topic_id`を結びつけています。
トピック名を変えても、確認問題・成果物の関連が維持されます。
GitHub APIの処理は将来別ファイルに追加し、成果物にリポジトリ・Issue・コミット識別子を追加できます。
GitHub同期、削除機能、アカウント、クラウド同期、自動採点はMVPの対象外です。

## テスト

Python標準のunittestとStreamlit付属のAppTestを使用します。一時DBで確認し、学習データを変更しません。

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

参考：[Streamlit公式API](https://docs.streamlit.io/develop/api-reference)、[AppTest公式ドキュメント](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest)。
