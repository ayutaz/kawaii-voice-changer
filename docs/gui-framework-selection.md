# GUI フレームワーク選定理由書

## 選定結果：PySide6を推奨

### PySide6を選んだ理由

#### 1. 音声アプリケーションに最適な成熟度
- **Qt Multimedia Framework**: 音声・動画処理の豊富な機能
- **リアルタイム処理**: 低レイテンシーのUI更新が可能
- **波形表示**: pyqtgraphとの統合で高速な音声波形描画

#### 2. ライセンスの優位性
- **LGPL v3**: 商用利用可能、ソース公開不要
- **PyQt6との比較**: PyQt6は商用利用時に有料ライセンスが必要

#### 3. 開発効率とエコシステム
- **豊富なウィジェット**: スライダー、ボタン等の音声制御UI完備
- **Qt Designer**: GUI設計ツールで視覚的にUI作成可能
- **日本語対応**: 完全な国際化サポート

#### 4. パフォーマンス
- **C++バックエンド**: ネイティブレベルの処理速度
- **マルチスレッド**: QThreadで音声処理とUI分離が容易
- **GPU活用**: OpenGLウィジェットで高速描画

## 他のフレームワークとの比較

### Flet（Flutter for Python）
**検討結果**: 不採用

**利点**:
- モダンなUI
- 簡単な開発開始
- クロスプラットフォーム対応

**不採用理由**:
- 音声処理向けの機能が不足
- PyWorldとの統合が複雑
- リアルタイム音声可視化の実績が少ない
- Flutter SDKへの依存（PyInstallerより複雑）

### Dear PyGui
**検討結果**: 代替案として保持

**利点**:
- GPU アクセラレーション
- 超高速レンダリング（60+ FPS）
- リアルタイムプロット機能

**PySide6を優先する理由**:
- より成熟したエコシステム
- 音声専用機能の充実
- ドキュメントとサンプルの豊富さ

### その他のフレームワーク

#### Tkinter / CustomTkinter
- **不採用理由**: リアルタイム描画性能が不足

#### Kivy
- **不採用理由**: デスクトップアプリには過剰、主にモバイル向け

#### Textual（TUI）
- **不採用理由**: ターミナルベースで音声可視化に不適

#### NiceGUI / Streamlit
- **不採用理由**: Webベース、デスクトップ配布が複雑

## 音声アプリケーション固有の要件への対応

### PySide6が満たす要件

1. **リアルタイム波形表示**
   ```python
   # pyqtgraphとの統合例
   import pyqtgraph as pg
   self.plot_widget = pg.PlotWidget()
   self.curve = self.plot_widget.plot()
   # 高速更新（30-60 FPS）
   ```

2. **低レイテンシーパラメータ更新**
   ```python
   # Signalによる非同期更新
   self.slider.valueChanged.connect(self.on_param_changed)
   ```

3. **スレッド分離**
   ```python
   # QThreadで音声処理分離
   class AudioThread(QThread):
       audio_ready = Signal(np.ndarray)
   ```

4. **ドラッグ&ドロップ**
   ```python
   # ネイティブなD&Dサポート
   self.setAcceptDrops(True)
   ```

## 結論

**PySide6**は以下の理由から最適な選択です：

1. **音声処理との親和性**: Qt Multimediaとpyqtgraphによる完全なサポート
2. **パフォーマンス**: C++バックエンドによる高速処理
3. **開発効率**: 成熟したツールチェーンとドキュメント
4. **将来性**: Qtの継続的な開発とサポート

Fletは魅力的な新しい選択肢ですが、音声処理アプリケーションの専門的な要件には**PySide6の成熟度と機能性**が必要です。

### 推奨アクション
- **メイン開発**: PySide6で進める
- **将来の検討**: Dear PyGuiでのプロトタイプ作成（GPU活用が必要な場合）
- **Fletの評価**: 簡易版やデモアプリでの使用を検討