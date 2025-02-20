## インストール方法

### 1. 必要なプログラム

まずは以下のプログラムを準備する．
- VTube Studio
- OBS Studio
- VOICEVOX
- Discord
- [VB-Audio Virtual Cable](https://vb-audio.com/Cable/index.htm?gad_source=1&gclid=CjwKCAiAn9a9BhBtEiwAbKg6frvITk93w2NI4KmQSbutkmGvcBcq2PnenMAfQ0YCUVByy_cgc4OjEBoCFA4QAvD_BwE)

### 2. NVIDIA CUDAに関連するソフトをインストールする

まず，Nvidiaドライバを最新版にすることを推奨する．
次に，NVIDIA CUDA Toolkitをインストールする．テスト環境では，CUDA Toolkit 12.1を使用した．

### 3. プロジェクトをダウンロードする
プロジェクトを本レポジトリからダウンロードする．

```bash
git clone https://github.com/kysing02/ai_vtuber.git
```

### 4. Python環境を構築する
Pythonのパッケージをインストールする前に，仮想環境を立てることを**強くお勧め**する．condaとvenvの両方があるが，どっちを使ってもいい．詳しい環境の構築は説明しない．

### 5. PythonのDependencyインストールする
仮想環境がアクティブになったら，以下のコマンドからPythonのdependencyをインストールする．本プロジェクトでは，`requirements.txt`しか提供しないが，自分のPython仮想環境に合わせて変換してください．

```bash
pip install -r requirements.txt
```

エラーが出る場合は自分まで連絡ください．
pytorchの環境は，[公式サイト](https://pytorch.org/get-started/locally/)で自分のCUDAバージョンに合わせる必要がある．

### 6. `.env`ファイルを作成する
Pythonのローカル環境変数を扱うには以下のように作成する必要がある．

プロジェクトのルートディレクトリで`.env`ファイルを作成してください．

```
OPENAI_API_KEY=""               # OpenAIのAPIキー
consumer_key=""                 # Twitter関連のキー 
consumer_secret=""              # Twitter関連のキー
bearer_token=""                 # Twitter関連のキー
access_token=""                 # Twitter関連のキー
access_token_secret=""          # Twitter関連キー
OBS_WS_PASSWORD=""              # OBS関連キー 
OBS_WS_HOST="localhost"         # OBS関連キー
OBS_WS_PORT=""                  # OBS関連キー
DISCORD_BOT_TOKEN=""            # Discord関連キー
GUILD_ID=""                     # Discord関連キー
VOICE_CHANNEL_NAME="General"    # Discord関連キー
VTS_AUTHENTICATION_TOKEN=""     # VTube Studio関連キー
DEV_DM_ID=""                    # Discord関連キー
```
AIriについての詳細は公開しない．
TwitterとDiscord関連のキーの取得方法は後日に書く．

#### 6.1 OBS関連のパラメータの取得方法

以下の画像のサーバポート，サーバーパスワードを`.env`に設定する．
![OBS Settings](/readme-img/obs-settings.png)

#### 6.2 Discord関連パラメータの取得方法

DEV_DM_IDには，自分のAIriとのDMプライベートチャットのIDを入れる．
具体的な取得方法：AIriとDMチャットのアイコンを選択>Channel IDをコピー
![AIri Channel ID](/readme-img/airi-channel-id.png)

### 6.3 VTube Studio関連パラメータの取得方法

まず，VTube Studioを起動し，プラグインを有効にする．以下のように，設定からAPIの起動を有効にする．
![Vtube Studio Plugin](/readme-img/vtube-studio-plugin.png)

VTube Studioを初回使うとき，最初に一回Authentication Tokenを取得する必要がある．やり方はいくつかあるが，詳細は[VTubeStudio公式APIの説明](https://github.com/DenchiSoft/VTubeStudio?tab=readme-ov-file#authentication)を参照する．以下のリクエストをVTube Studioに送信する．（詳しいやり方は載せない．`curl`や`websocket`などの方法もあるが，[Postman](https://www.postman.com/)を使用する方法が一番簡単．）

```
{
	"apiName": "VTubeStudioPublicAPI",
	"apiVersion": "1.0",
	"requestID": "SomeID",
	"messageType": "AuthenticationTokenRequest",
	"data": {
		"pluginName": "My Cool Plugin",         # ここは自分のプラグインの名前を入れる（任意でいい）
		"pluginDeveloper": "My Name",           # 開発者の名前（任意でいい）
	}
}
```

### 7. VTube Studioのセットアップ

VTube Studioを使うには，Hotkeyをいくつか設定する必要がある．具体的には，以下のように設定した．


それから，リップシンク（口パク）のために，以下のように設定しておく必要がある．より詳しい設定は論文15ページ目を参照する．
![VTube Studio Mic](/readme-img/vtube-studio-mic.png)

### 8. OBS Studioのセットアップ

OBSの設定は少し複雑である．設定するOBS Studioの画面を以下のようになる．
![OBS Studio Overview](/readme-img/obs-studio-overview.png)

詳しい設定方法しか記載しないが，大まかに言うとソースと音声を設定する必要がある．

簡単のために，シーンをエクスポートしておいてので，試しに以下のパスからインポートしてみてください．

**(シーンコレクション>インポート>以下のパスを指定)**
`assets\obs_pics\profiles\StorytellingScene.json`

以上の方法ができなかった場合，手動で以下のように設定してください．

**左下のソースを設定**
![OBS Studio Source](/readme-img/obs-studio-source.png)
 - '+'アイコン > テキスト(GDI+) > Answerという名前にする
 - '+'アイコン > テキスト(GDI+) > Questionという名前にする
 - '+'アイコン > ゲームキャプチャ > 新規作成 > モード：特定のウィンドウをキャプチャー > ウィンドウ：VTube Studio > 透過を許可
 - '+'アイコン > 背景(画像は何でもいいが，`assets\obs_pics\bedroom-test.webp`にサンプル背景を準備してある)

**右下の設定>音声タブ**
![OBS Studio Audio](/readme-img/obs-studio-audio.png)

**真ん中下の音声ミクサー>設定アイコン**
![OBS Studio Audio Desc](/readme-img/obs-studio-audio-desc.png)

### 9. その他のセットアップ
#### 9.1 FasterWhisperモデルのインストール
VLifeシステムは，ASRのローカルモデルモードでは，[faster-whisper-large-v3-turbo-ct2](https://huggingface.co/deepdml/faster-whisper-large-v3-turbo-ct2)を使用する．ここで，このモデルをHugging Faceからダウンロードする．

```bash
git clone https://huggingface.co/deepdml/faster-whisper-large-v3-turbo-ct2
```

#### 9.2 TTSモデルをインストールする
本システムも[Style-Bert-VITS2](https://github.com/litagin02/Style-Bert-VITS2)を使用している．実装では，Pythonが提供しているpipパッケージである`style-bert-vits2`を使用しているため，gitからダウンロードする必要がない．

しかし，使用するモデルは別途でダウンロードする必要がある．ここで，`initialize.py`を用意した．以下のコマンドを実行することで，使用するモデルを自動的にダウンロードすることができる．
```bash
python initialize.py
```

#### 9.3 正しく認識するためにsetup.pyを使用してモジュールをインストールする

ここでは説明を省略する．以下のコマンドをそのまま実行してください．
```bash
pip install -e .
```

環境構築は以上となる．次はVLifeシステムの起動プログラムの詳しい設定に入る．

<hr>

## 起動
最後に起動する前に，いくつか調整する必要があるパラメータがある．

`vlife.py`の40行目のパラメータを，自分のサウンドデバイスに変更してください．
```python
self.play_sound_narrator = PlaySound(output_device_name="スピーカー") # スピーカーを自分のデバイスの名前に変更してください
```
![Output Sound Device](/readme-img/output-sound-device.png)

これで準備が全部完了した．以下のコマンドを実行してVLifeシステムを起動してください．
```python
python vlife.py
```