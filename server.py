import os
import socket
import json
import math
import re
from collections import Counter
import threading


# ---------- RPCメソッドの定義 -------------------------------------------------
class RPCMethods:
    @staticmethod
    def add(x, y):
        return x + y

    @staticmethod
    def subtract(x, y):
        return x - y

    @staticmethod
    def multiply(x, y):
        return x * y


    @staticmethod
    def divide(x, y):
        if y == 0:
            raise ValueError("0で割ることはできません")
        return x / y


    @staticmethod
    def floor(x):
        return math.floor(x)


    @staticmethod
    def nroot(n, x):
        if n <= 0:
            raise ValueError("1以上の整数を指定してください")
        return math.pow(x, 1 / n)


    @staticmethod
    def reverse(s):
        return s[::-1]


    @staticmethod
    def validAnagram(str1, str2):
        str1_clean = re.sub(r"[^a-z0-9]", "", str1.lower())
        str2_clean = re.sub(r"[^a-z0-9]", "", str2.lower())

        if len(str1_clean) != len(str2_clean):
            return False

        str1_elem = Counter(str1_clean)
        str2_elem = Counter(str2_clean)
        return str1_elem == str2_elem


    @staticmethod
    def sort_list(array):
        if not array or len(array) < 2:
            raise ValueError("文字列を空白区切りで２つ以上入力してください")
        return sorted(array, key=str.lower)


    @staticmethod
    def help():
        return {
            "commands": [
                {"name": "add", "description": "足し算", "example": "add 1 2 --> 3"},
                {"name": "subtract", "description": "引き算", "example": "subtract 9 2 --> 7"},
                {"name": "multiply", "description": "掛け算", "example": "multiply 5 4 --> 20"},
                {"name": "divide", "description": "割り算", "example": "divide 10 2 --> 5"},
                {"name": "floor", "description": "切捨て", "example": "floor 1.35 --> 1"},
                {"name": "nroot", "description": "ｎ乗根", "example": "nroot 3 64 --> 4"},
                {"name": "reverse", "description": "文字を反転", "example": "reverse HelloWorld! --> !dlroWolleH"},
                {"name": "validAnagram", "description": "アナグラムか確認", "example": "validAnagram HelloWorld! olleH!dlroW --> true"},
                {"name": "sort", "description": "リストをソート", "example": "sort spade diamond clover heart --> ['clover', 'diamond', 'heart', 'spade']"},
                {"name": "help", "description": "このヘルプを表示"},
            ]
        }



# ---------- クライアントからのリクエストを処理するクラス ----------------------
class RequestHandler:
    def __init__(self, connection, client_address, client_map):
        self.connection = connection
        self.client_address = client_address
        # RPCメソッドをハッシュマップにまとめる
        self.methods = {
                "add": RPCMethods.add,
                "subtract": RPCMethods.subtract,
                "multiply": RPCMethods.multiply,
                "divide": RPCMethods.divide,
                "floor": RPCMethods.floor,
                "nroot": RPCMethods.nroot,
                "reverse": RPCMethods.reverse,
                "validAnagram": RPCMethods.validAnagram,
                "sort": RPCMethods.sort_list,
                "help": RPCMethods.help,
            }

    def handle_client(self):
        try:
            current_thread_id = threading.get_ident()
            print(f"connection from: {self.client_address}")

            welcome_message = {
                "result": "サーバに接続しました。\nコマンドを入力してください（helpでコマンド一覧、exitで終了）",
                "result_type": "str",
                "id": None,
            }
            self.connection.sendall((json.dumps(welcome_message) + "\n").encode())

            data_str = ""

            # クライアントからの新しいメッセージを待ち続ける
            while True:
                # 接続からデータを読み込む（最大4096byte)
                data = self.connection.recv(4096)
                if not data:
                    break

                # 受け取ったデータを文字列に変換する
                data_str += data.decode("utf-8")

                # 受け取ったデータを表示する
                print(f"Received on thread{current_thread_id}: {data_str}")

                # while "\n" in data_str:
                #     request_json, data_str = data_str.split("\n", 1)
                lines = data_str.splitlines()
                data_str = ""
                for request_json in lines:

                    # json形式にパース
                    try:
                        request = json.loads(request_json)
                        method = request.get("method")
                        params = request.get("params", {})
                        response_id = request.get("id", None)

                        # 存在するメソッドの場合
                        if method in self.methods:
                            if isinstance(params, dict):
                                result = self.methods[method](**params)
                            elif isinstance(params, list):
                                if method == "sort":
                                    result = self.methods[method](params)
                                else:
                                    result = self.methods[method](*params)
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

                # 処理したメッセージをバイナリ形式に変換してクライアントに送り返す
                print(f"Response on thread{current_thread_id}: {response}")
                self.connection.sendall((json.dumps(response) + "\n").encode())

        # 最終的に接続を閉じる
        finally:
            print("Closing current connection")
            print(f"[DEBUG] closed thread {current_thread_id}")

            self.connection.close()


# ---------- ソケットを管理するクラス ------------------------------------------
class RPCServer:
    def __init__(self, config_path="config.json"):
        try:
            # ストリームのエンドポイントとなるソケットを作成する
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

            # サーバの UNIX ソケットの場所を設定する
            with open(config_path) as f:
                config = json.load(f)
                self.server_address = config["filepath"]
        except FileNotFoundError:
            print(
                "設定ファイル（config.json）が見つかりません。プログラムを終了します。"
            )
            exit(1)

        # 以前の接続が残っていた場合に備えて、サーバアドレスを削除する（unlink）
        try:
            os.unlink(self.server_address)
        except FileNotFoundError:
            pass

        print("Starting up on {}".format(self.server_address))

        # サーバのアドレスにソケットを接続する（bind）
        self.sock.bind(self.server_address)

        # ソケットが接続要求を待機するようにする
        self.sock.listen()
        self.client_map = {}


    def start_server(self):
        try:
            # クライアントからの接続を待ち続ける
            while True:

                # クライアントからの接続を受け入れる
                connection, client_address = self.sock.accept()

                # client_address が空の場合の処理
                if not client_address:
                    client_address = "Unix socket(no client address)"

                # クライアントごとにインスタンスを作成
                client = RequestHandler(connection, client_address, self.client_map)

                # クライアントごとにスレッドを作成
                client_thread = threading.Thread(target=client.handle_client)

                # クライアントプログラムを終了したらスレッドも終了
                client_thread.daemon = True
                client_thread.start()
                self.client_map[client_thread.ident] = connection
                print(f"[DEBUG] client_map: {self.client_map}")
                print(f"[DEBUG] threads: {threading.enumerate()}")

        except Exception as e:
            print(f"エラーが発生しました: {e}")

        finally:
            if 'connection' in locals():
                connection.close()
            self.sock.close()


# ---------- メイン処理 --------------------------------------------------------
if __name__ == "__main__":
    server = RPCServer()
    server.start_server()
    exit(0)