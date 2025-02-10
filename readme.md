# RPC クライアント・サーバーアプリケーション

## 概要

このプロジェクトは、RPCを利用した **軽量なクライアント・サーバーアプリケーション** です。 クライアントはコマンドを送信し、サーバーは JSON 形式でレスポンスを返します。

**特徴**
- Unix ドメインソケットを利用した通信
- クライアントがコマンドを送信し、サーバーが適切な処理を実行
- 複数クライアントもスレッドで並列処理します

## 動作環境

- python 3.8 以上
- Node.js 18 以上
- Linux / MacOS（Unix ドメインソケットを利用するため）

## 使用方法
1. 次のコマンドでサーバを起動します。

```sh
python3 server.py
```

2. 別のターミナルを開き、次のコマンドでクライアントを起動します

```sh
node client.js
```

3. コマンド一覧

コマンド名 | 説明 | 例
---- | ---- | ----
add | 足し算 | add 1 2 --> 3
subtract | 引き算 | subtract 9 2 --> 7
multiply | 掛け算 | multiply 5 4 --> 20
divide | 割り算 | divide 10 2 --> 5
floor | 切捨て | floor 1.35 --> 1
nroot | ｎ乗根 | nroot 3 64 --> 4
reverse | 文字を反転 | reverse HelloWorld! --> !dlroWolleH
validAnagram | アナグラムか確認 | validAnagram HelloWorld! olleH!dlroW --> true
sort | リストをソート | sort spade diamond clover heart --> ['clover', 'diamond', 'heart', 'spade']
help | コマンド一覧の表示 | help
