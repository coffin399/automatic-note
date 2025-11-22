# Note.com AI Writer (Multi-Genre Report)

AIが自動でニュースを収集し、Note.com向けの「簡単レポート」を作成・下書き保存するツールです。
金融、政治、カルチャー、サブカルチャーの最新ニュースを、中学生でもわかる平易な言葉で要約します。

## 特徴
- **全自動収集**: DuckDuckGoを使って指定ジャンルの最新ニュースを検索します。
- **AI要約**: Google Gemini Proを使って、ニュースをわかりやすく要約します。
- **自動投稿**: 作成した記事をNote.comの下書きとして自動保存します。

## 必要なもの
- Windows PC
- Google Gemini APIキー ([取得はこちら](https://aistudio.google.com/app/apikey))
- Note.comのアカウント（セッションCookieが必要です）

## セットアップ手順

### 1. 初回起動
フォルダ内の `run.bat` をダブルクリックしてください。
自動的に必要なライブラリがインストールされ、設定ファイル `config.yaml` が作成されます。

### 2. 設定
作成された `config.yaml` をメモ帳などで開き、以下の項目を入力してください。

**方法A: セッションCookieを使う（推奨）**
最も安全で確実な方法です。
```yaml
gemini_api_key: "ここにGeminiのAPIキー"
note_session_cookie: "ここにNoteのセッションCookie"
# note_email, note_password は空欄でOK
```

**方法B: 自動ログインを使う**
Cookieの取得が面倒な場合に使います。
※ パスワードがファイルに保存されるため、取り扱いに注意してください。
```yaml
gemini_api_key: "ここにGeminiのAPIキー"
note_session_cookie: "" # 空欄にする
note_email: "あなたのメールアドレス"
note_password: "あなたのパスワード"
```

> **NoteのセッションCookieの取得方法**:
> 1. ブラウザで [note.com](https://note.com) にログインします。
> 2. F12キーを押して開発者ツールを開きます。
> 3. 「アプリケーション (Application)」タブ → 「Cookie」を選択します。
> 4. `https://note.com` を選択し、名前が `session` の値（長い文字列）をコピーしてください。

## 使い方
設定完了後、もう一度 `run.bat` をダブルクリックしてください。

1. ニュースの収集が始まります。
2. AIがレポートを作成します。
3. Note.comに「YYYY-MM-DD 簡単レポート」というタイトルで下書き保存されます。
4. 完了すると、作成された記事のURLが表示されます。

## 注意事項
- アカウントの安全のため、まずは `upload_status: "draft"`（下書き）での運用を推奨します。

## 実運用（自動化）について

このプログラムは**常駐型**として動作するように設計されています。
起動すると、以下のタイミングで自動的に記事を作成・投稿します。

1. **起動直後**
2. **毎日 08:00**
3. **毎日 20:00**

### 使い方
1. `run.bat` をダブルクリックして起動します。
2. 黒い画面（コマンドプロンプト）が開いたままになります。**この画面を閉じないでください。**
3. PCをつけっぱなしにしておけば、指定の時間に自動で処理が行われます。

### 自動公開設定
`config.yaml` の `upload_status` を変更すると、下書きではなく即時公開されます。

```yaml
# draft（下書き）または published（公開）
upload_status: "published"
```

