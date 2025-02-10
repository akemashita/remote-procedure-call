const net = require('net');
const fs = require('fs');
const readline = require('readline');

// 設定ファイルを読み込む
const config = JSON.parse(fs.readFileSync('config.json', 'utf-8'));
const SOCKET_PATH = config.filepath;

// ユーザ入力を受け付けるインターフェースを作成
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// クライアントソケットを作成
const client = net.createConnection(SOCKET_PATH);

// dataイベントを監視する
client.on('data', (data) => {
  // console.log(`[DEBUG] received buffer: ${data}`);
  data.toString().trim().split('\n').forEach((line) => {
    try {
      const response = JSON.parse(line.trim());

      if (response.error) {
        console.error('エラーが発生しました: ', response.error);
      }
      else {
        if (response.id !== null && response.result?.commands) {
          console.log('---- 利用可能なコマンド一覧 ----');

          for (const { name, description, example = null } of response.result['commands']) {
            console.log(`${name}: ${description}`);
            if (example) console.log(`  例）${example}`);
          }
        }
        else {
          console.log(`${response.result}`);
        }
      }
    }
    catch (e) {
      console.error('サーバから受け取ったデータの解析に失敗しました: ', e.message);
    }

  });

  promptUser();
});

// ユーザの入力処理
function promptUser() {
  rl.question('> ', (input) => {
    if (input === 'exit') {
      console.log('接続を終了します。');
      client.end();
      rl.close();
      return;
    }

    const [command, ...args] = input.split(' ');
    const parsedArgs = args.map(arg => isNaN(arg) ? arg : Number(arg));

    sendRequest(command, parsedArgs);
  });
}

// サーバへのリクエストを送信
function sendRequest(method, params) {
  const request = {
    method: method,
    params: params,
    id: Math.floor(Math.random() * 1000)
  };

  client.write(JSON.stringify(request) + '\n');
}

// エラーハンドリング
client.on('error', (err) => {
  console.error('接続エラー: ', err.message);
});

// 接続終了時の処理
client.on('close', () => {
  console.log('サーバとの接続を終了しました。');
})