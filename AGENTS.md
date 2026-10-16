# Naraku（本番）制作指示 ※テスト版 Naraku-test と共通の内容

スキル・攻撃・着弾などのVFXを制作、変更、レビューするときは、先に [.agents/skills/naraku-vfx/SKILL.md](.agents/skills/naraku-vfx/SKILL.md) を読み、その工程と評価傾向を踏襲する。ユーザーが継続適用を指定した制作スキルである。新しいユーザー指示を優先する。

現在地と過去の判断は dev/HANDOFF.md の最新追記、制作手順は dev/godot/quake/README.md を確認する。候補演出の公開と通常ゲームへの採用を区別する。

## 公開ビルド（2026-10-16〜リンク方式。Claude・Codex共通）

- 公開ページの index.html は画像を埋め込まない「リンク方式」で作る：`python3 dev/tools/embed.py dev/naraku_src.html index.html dev/assets --link dev/assets/`。画像は dev/assets から読む（`?v=<中身のハッシュ>` 付き）。
- 確認は http で行う（file:// では canvas の getImageData が使えない）：リポジトリ直下で `python3 -m http.server 8765` → `python3 dev/tests/smoke.py http://127.0.0.1:8765/index.html …` と `python3 dev/tools/dev/boot.py http://127.0.0.1:8765/index.html …`。
- 画像入りの1ファイル版は必要なときだけ `--link` なしで作業フォルダへ出し、コミットしない。
- 本番 yyvape-dev/Naraku もテスト版と同じ dev/ 構成・同じリンク方式（2026-10-16 にテスト版の内容をそのまま本番へ反映）。本番へ出すときは、テスト版の dev/ と index.html をコピーする。
