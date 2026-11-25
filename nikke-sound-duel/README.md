# NIKKE SOUND DUEL

勝利の女神：NIKKEの楽曲を二曲ずつ比べる、非公式のファンサイトです。

## 公開場所

- サイト: https://hanayumir.github.io/nikke-sound-duel/
- トップページからのリンク: https://hanayumir.github.io/

## 曲情報と試聴

- scripts/import-apple-catalog.py がApple Music日本カタログの曲情報とジャケット画像URLを取得します。音源・プレビュー・画像ファイルは保存せず、Appleの画像URLをページ上で表示します。
- scripts/import-cosmograph-matches.py がYouTube Data API v3でCosmograph公式チャンネルの公開アップロード一覧を読み、Apple Musicの曲名と照合します。
- 曲名はUnicode正規化後に完全一致させます。曲名が重複するときは、YouTube動画タイトルのアルバム部分もApple Musicのアルバム名と照合します。曖昧な候補は採用しません。
- Webサイトの音声はYouTube公式IFrameプレーヤーから直接再生します。音源ファイルはダウンロードしません。YouTubeのプレーヤー上で再生を始めると、ジャケットからレコードが直径の3分の1だけ出て回転します。
- 同じ曲名の公式動画が見つからない曲はCosmograph公式チャンネルでの検索リンクを表示します。Cosmographチャンネルにない曲を別チャンネルの動画へ自動で結び付けません。

Apple Music日本カタログで検索できた905曲を含みます。Cosmographチャンネルにない曲や、Apple Musicに掲載されていない曲は再生・掲載できないため、「NIKKEの全ゲーム内楽曲」とは限りません。

## YouTube API key

動画一覧の自動照合にはYouTube Data API v3のAPI keyが必要です。キーは公開HTMLに含めず、このGitHubリポジトリのActions secret YOUTUBE_API_KEY に登録してください。

1. Google CloudのプロジェクトでYouTube Data API v3を有効にし、API keyを作成します。
2. API keyのAPI制限をYouTube Data API v3だけにします。
3. GitHubリポジトリの Settings → Secrets and variables → Actions で YOUTUBE_API_KEY を作成します。
4. Actions → Refresh NIKKE Sound Duel Catalog → Run workflow でカタログと動画照合を更新します。

この処理はCosmographチャンネルIDを固定し、同チャンネルのアップロード一覧だけを対象にします。更新ワークフローは手動実行です。現在の照合表は確認済み動画のみを含みます。全チャンネル動画とのタイトル照合にはAPI keyをActions secretに登録して実行してください。

## 投票

GitHub Pages上の共有投票にはSupabaseを使います。成人管理者のSupabaseプロジェクトを用意してから、次の手順で接続します。

1. Supabase SQL Editorで `supabase/schema.sql` を実行します。
2. SupabaseのProject URLとPublishable keyを `config.js` に設定します。
3. サイトをGitHub Pagesへ再デプロイすると、投票数とランキングが全訪問者で共有されます。

ブラウザー内のランダムIDで同じ曲への重複投票を抑えます。名前やメールアドレスは収集しません。公開keyはブラウザー用ですが、Secret keyやservice_role keyは設定しないでください。

## 権利・出典

Apple Musicの曲情報、Cosmograph公式YouTubeチャンネルの動画、NIKKEに関する各権利はそれぞれの権利者に帰属します。本サイトはSHIFT UP、PROXIMA BETA、Cosmograph、Apple、Google/YouTubeとは関係ありません。

