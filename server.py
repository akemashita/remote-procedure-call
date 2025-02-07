import os
import socket
import json
import math
import re
from collections import Counter
import threading


# RPCメソッドの定義
def add(x, y):
    return x + y


def subtract(x, y):
    return x - y


def multiply(x, y):
    return x * y


def divide(x, y):
    if y == 0:
        raise ValueError("0で割ることはできません")
    return x / y


def floor(x):
    return math.floor(x)


def nroot(n, x):
    if n <= 0:
        raise ValueError("1以上の整数を指定してください")
    return math.pow(x, 1 / n)


def reverse(s):
    return s[::-1]


def validAnagram(str1, str2):
    str1_clean = re.sub(r"[^a-z0-9]", "", str1.lower())
    str2_clean = re.sub(r"[^a-z0-9]", "", str2.lower())
    str1_elem = Counter(str1_clean)
    str2_elem = Counter(str2_clean)
    return str1_elem == str2_elem


def sort_list(array):
    if len(array) < 2:
        raise ValueError("文字列を空白区切りで２つ以上入力してください")
    return sorted(array, key=str.lower)


def help():
    return "利用可能なコマンド一覧:\n" + "\n".join(
        [
            "add:      足し算　例）add 1 2 --> 3",
            "subtract: 引き算　例）subtract 9 2 --> 7",
            "multiply: 掛け算　例）multiply 5 4 --> 20",
            "divide:   割り算　例）divide 10 2 --> 5",
            "floor:    切捨て　例）floor 1.35 --> 1",
            "nroot:    ｎ乗根　例）nroot 3 64 --> 4",
            "reverse:  文字を反転　例）reverse HelloWorld! --> !dlroWolleH",
            "validAnagram:  アナグラムか確認　例）validAnagram HelloWorld! olleH!dlroW --> true",
            "sort:     リストをソート　例）sort spade diamond clover heart --> ['clover', 'diamond', 'heart', 'spade']",
            "help:     このヘルプを表示",
        ]
    )


# RPCメソッドをハッシュマップにまとめる
methods = {
    "add": add,
    "subtract": subtract,
    "multiply": multiply,
    "divide": divide,
    "floor": floor,
    "nroot": nroot,
    "reverse": reverse,
    "validAnagram": validAnagram,
    "sort": sort_list,
    "help": help,
}


def handle_client(connection, client_address, client_map):
    try:
        print("connection from: {}".format(client_address))

        welcome_message = {
            "result": "サーバに接続しました。\nコマンドを入力してください（helpでコマンド一覧、exitで終了）",
            "result_type": "str",
            "id": None,
        }
        connection.sendall((json.dumps(welcome_message) + "\n").encode())

        data_str = ""

        # クライアントからの新しいメッセージを待ち続ける
        while True:
            # 接続からデータを読み込む（最大4096byte)
            data = connection.recv(4096)
            if not data:
                break

            # 受け取ったデータを文字列に変換する
            data_str += data.decode("utf-8")

            # 受け取ったデータを表示する
            print(f"Received: {data_str}")

            while "\n" in data_str:
                request_json, data_str = data_str.split("\n", 1)

            # json形式にパース
            try:
                request = json.loads(request_json)
                method = request.get("method")
                params = request.get("params", {})
                response_id = request.get("id", None)
                request_id = request.get("id", None)
                if request_id is not None:
                    client_map[request_id] = connection

                # 存在するメソッドの場合
                if method in methods:
                    if isinstance(params, dict):
                        result = methods[method](**params)
                    elif isinstance(params, list):
                        if method == "sort":
                            result = methods[method](params)
                        else:
                            result = methods[method](*params)
                    else:
                        result = "Invalid parameter format"

                    response = {
                        "result": result,
                        "result_type": type(
                            result
                        ).__name__,  # 実際の型を動的に取得して返す
                        "id": response_id,
                    }

                # 存在しないメソッドの場合
                else:
                    response = {
                        "error": "指定されたメソッドは実装されていません",
                        "id": response_id,
                    }
            except Exception as e:
                response = {
                    "error": str(e),
                    "id": None,
                }

            print(f"[DEBUG] client_map: {client_map}")
            # 処理したメッセージをバイナリ形式に変換してクライアントに送り返す
            if response_id in client_map:
                client_socket = client_map.pop(response_id)
                client_socket.sendall((json.dumps(response) + "\n").encode())
                print(f"Response: {response}")
            print(f"[DEBUG] client_map: {client_map}")

    # 最終的に接続を閉じる
    finally:
        print("Closing current connection")
        connection.close()


def start_server():
    client_map = {}
    try:
        # ストリームのエンドポイントとなるソケットを作成する
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # サーバの UNIX ソケットの場所を設定する
        try:
            config = json.load(open("config.json"))
            server_address = config["filepath"]
        except FileNotFoundError:
            print(
                "設定ファイル（config.json）が見つかりません。プログラムを終了します。"
            )
            exit(1)

        # 以前の接続が残っていた場合に備えて、サーバアドレスを削除する（unlink）
        try:
            os.unlink(server_address)
        except FileNotFoundError:
            pass

        print("Starting up on {}".format(server_address))

        # サーバのアドレスにソケットを接続する（bind）
        sock.bind(server_address)

        # ソケットが接続要求を待機するようにする
        sock.listen()

        # クライアントからの接続を待ち続ける
        while True:

            print(f"[DEBUG] client_map: {client_map}")
            # クライアントからの接続を受け入れる
            connection, client_address = sock.accept()

            # client_address が空の場合の処理
            if not client_address:
                client_address = "Unix socket(no client address)"

            # クライアントごとにスレッドを作成
            client_thread = threading.Thread(
                target=handle_client, args=(connection, client_address, client_map)
            )
            client_thread.daemon = (
                True  # クライアントプログラムを終了したらスレッドも終了
            )
            client_thread.start()
            print(f"[DEBUG] {str(client_thread)}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        connection.close()

    finally:
        sock.close()



if __name__ == "__main__":
    start_server()
    exit(0)