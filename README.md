# 概要

henngeのユーザーをジョーシスのメンバーとして同期するサンプルコードです。下記のステップに分割して実行されます

1. ジョーシスAPIからメンバー一覧を取得し、`josys_members.csv`に保存（入社前、在籍中のメンバーのみを取得）
2. HENNGE APIからユーザー一覧を取得し、`source_members.csv`に保存
3. 1と2の一覧の差分を算出し、新規に追加すべきメンバーと、更新されたメンバーの一覧を作成。それぞれ、`new_members.csv`、`updated_members.csv`に保存
4. ジョーシスAPIで、新規メンバーと更新メンバー（の更新値）をジョーシスに書き込む

# できること
上記の各種ステップに基づき、複数のコマンドから実行したい内容を選択できます

## getJosysMembers
ジョーシスAPIからメンバー一覧を取得し、`josys_members.csv`に保存し、処理を終了します

## getSourceMembers
HENNGE APIからユーザー一覧を取得し、`source_members.csv`に保存し、処理を終了します

## compareMembers
`josys_members.csv`と`source_members.csv`に書き込まれているメンバー一覧の差分を算出し、新規に追加すべきメンバーと、更新されたメンバーの一覧をそれぞれ、`new_members.csv`、`updated_members.csv`に保存します。
APIからのメンバー一覧の取得は実行されません。

## syncMembersFromAPI
APIからのメンバー取得〜ジョーシスへの書き込みまで、すべてのステップを実行します。

## syncMembersFromFile
APIからのメンバー取得を新たに行わずに、`josys_members.csv`と`source_members.csv`のデータを元にジョーシスへの書き込みを実行します。

# 使い方

環境構築、同期設定を完了した後、プログラムを実行してください。

## 1. 環境構築

1. Python3のコードを実行できる環境を用意してください（ご必要に応じて、venvなどの仮想環境を用意してください）
2. 各ファイルを同一のフォルダ内に展開してください（`main.py`, `hennge_controller.py`などすべての.pyファイルと`requirements.txt`、`integration_config.yaml`が同じフォルダにある状態） 
3. PowerShellを上記フォルダ内で開き、`pip3 install -r requirements.txt`を実行し、必要なpythonモジュールをダウンロードしてください

## 2. 認証情報・同期設定

`integration_config.yaml`の内容を埋めてください。必要な項目は下記の通りです

1. ジョーシスAPIの認証情報
2. HENNGE APIの認証情報
3. ジョーシスメンバーをCSVに保存する際に、保存する項目と保存名
4. HENNGEユーザーをCSVに保存する際に、保存する項目と保存名（選択可能な項目は[こちらのAPI](https://developers.hennge.com/docs/hac-api/43f08ee59c0ef-download-users-as-csv)に依存します）
5. ジョーシス項目とHENNGE項目のマッピング、及びメンバー比較の際のマッチキー

（各種項目の記載方法は省略します）

## 3. 実行方法
PowerShellで`python3 main.py <コマンド>`を入力し、お好みの処理を実行してください。

`<コマンド>`は、上記の「できること」セクションで記載されている各種コマンドからお選びください

例：
- ジョーシスメンバーの取得：`python3 main.py getJosysMembers`
- すべてのステップの実行：`python3 main.py syncMembersFromAPI`

# 拡張方法

HENNGEのAPI値に基づいて何らかの処理を行いたい場合：
`hennge_controller.py`の`_custom_functions_per_item()`で関数を実装し、配列にappendする


# 参照
- HENNGE API: https://developers.hennge.com/docs/hac-api/2erp90rbav7lt-english-hennge-access-control-api-quick-start
- ジョーシス API: https://developer.josys.com/docs/ja/ud86k5qivzzva-v2
（メンバーv2のエンドポイントを利用します）