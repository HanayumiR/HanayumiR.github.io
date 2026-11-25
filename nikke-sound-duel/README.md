# NIKKE SOUND DUEL

勝利の女神：NIKKE の楽曲を2曲ずつ聴き比べる静的サイトです。

- 楽曲情報: Apple Music Japan のカタログ
- 再生: Cosmograph 公式 YouTube チャンネルの動画（照合済み曲のみ）
- 投票: ブラウザー内に保存
- 公開先: GitHub Pages

`data/nikke-ost.json` は楽曲の表示用メタデータ、`data/cosmograph-matches.json` は公式動画との対応表です。YouTube Data API のキーを `YOUTUBE_API_KEY` として GitHub Actions Secrets に登録すると、週次更新ワークフローで動画候補を更新できます。キーはリポジトリへ追加しないでください。
