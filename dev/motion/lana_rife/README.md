# ラナ通常攻撃 RIFE v4.6 候補

対象は dev/assets/sword.webp の12コマ。必殺技の岩・光ではない。
公式 https://github.com/nihui/rife-ncnn-vulkan/releases/tag/20221029 の実行ファイルと同梱rife-v4.6モデルを使用。実行環境はCPU Vulkan（Mesa lavapipe）。バイナリ・モデルは /tmp にのみ展開し同梱しない。

interpolate.py は premultiplied RGB とアルファを別々に補間し、straight RGBAへ戻す。元12コマを偶数番にそのまま保持し、中間12コマ（最終→先頭も含む）を追加。6列4行443×292、WebP lossless。復号後の元コマ12枚の画素完全一致を確認。生成35.48秒（この環境・サイズでの実測、他素材への保証ではない）。

比較 dev/mock/lana_attack_rife.html は元の可変コマ時間、命中55%、通常攻撃最大0.45秒を再現。命中0.2475秒と全体速度を維持。候補側は同じ連続コマ位置を2倍して選択。通常ゲームの素材・処理は未変更。

限界：急な振り抜き（特に7→8コマ）で剣の輪郭・マントに歪み／二重像が出る。元絵と見分けがつかない品質とは言えない。比較候補として公開し採用は未決定。キャラ本体の比較なので斬撃VFXは重ねない。

検証：ChromiumとLinux WebKit、393×852で透過スプライト描画・シーク・拡大・再開、JSエラーなし。実機iPhoneでの確認ではない。dev/reports/lana-attack-rife/参照。
