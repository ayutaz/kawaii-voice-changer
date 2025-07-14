# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-14

### 🎉 初回リリース

Kawaii Voice Changerの最初の公式リリースです。論文「Finding Kawaii」（arXiv:2507.06235）の研究成果に基づいた、声を「可愛く」変換するデスクトップアプリケーションです。

### ✨ 主な機能

#### 音声処理
- **リアルタイムピッチ調整**: F0（基本周波数）を0.5倍〜2.0倍で調整
- **独立フォルマント制御**: F1、F2、F3を個別に調整可能
- **連動モード**: すべてのフォルマントを一括調整
- **高品質音声処理**: WORLD Vocoderによる自然な音声変換

#### ユーザーインターフェース
- **波形表示**: 音声ファイルの視覚化とループ領域選択
- **スペクトラム表示**: リアルタイムFFT解析とフォルマントマーカー
- **A/B比較**: オリジナルと処理済み音声をワンクリックで切り替え
- **ドラッグ&ドロップ**: 簡単なファイル読み込み

#### プリセット機能
- **5つの内蔵プリセット**: 
  - Bright Kawaii
  - Soft Kawaii
  - Natural Kawaii
  - Childlike
  - Anime Voice
- **カスタムプリセット**: 独自の設定を保存・管理
- **設定スロット**: 最大4つの設定を保存して比較

#### 再生機能
- **ループ再生**: 自動ループで簡単に比較
- **ループ領域選択**: 波形上で視覚的に選択
- **クロスフェード**: スムーズなループ再生（50ms）

#### エクスポート機能
- **WAV形式出力**: 16bit/24bit対応
- **選択的エクスポート**: オリジナル/処理済みを選択可能

#### ショートカット
- **Space**: 再生/一時停止
- **Tab**: A/B切り替え
- **R**: パラメータリセット
- **1-4**: 設定スロット切り替え
- **5-9**: プリセット切り替え
- **L**: ループ切り替え
- **Ctrl+O**: ファイルを開く
- **Ctrl+E**: エクスポート

### 🛠️ 技術仕様

#### 開発環境
- **Python 3.12**: 最新の言語機能を活用
- **PySide6**: Qt6ベースのクロスプラットフォームGUI
- **PyWorld**: 高品質音声分析・合成
- **pyqtgraph**: 高速データ可視化

#### ビルドシステム
- **uv**: 高速な依存関係管理
- **PyInstaller**: スタンドアロン実行ファイル生成
- **GitHub Actions**: CI/CDパイプライン
- **自動リリース**: タグプッシュで自動ビルド・リリース

#### 品質保証
- **pytest**: 81個の包括的なテスト
- **ruff**: 高速リンティング・フォーマット
- **mypy**: 静的型チェック
- **pre-commit**: コミット前の自動チェック

### 📦 配布形式

#### Windows
- `KawaiiVoiceChanger-1.0.0-windows.zip`: ポータブル版
- 展開して`KawaiiVoiceChanger.exe`を実行

#### macOS
- `KawaiiVoiceChanger-1.0.0-macos.zip`: アプリケーションバンドル
- 展開して`KawaiiVoiceChanger.app`を実行
- 初回実行時はセキュリティ設定の確認が必要

#### Linux
- `KawaiiVoiceChanger-1.0.0-linux.tar.gz`: 実行ファイル
- 展開して`./KawaiiVoiceChanger`を実行
- 依存関係: `libportaudio2`, `libsndfile1`

### 🙏 謝辞

- 論文「Finding Kawaii」の著者の皆様
- WORLD Vocoderの開発者 森勢将雅様
- オープンソースコミュニティの皆様

### 📝 既知の問題

- CI環境でのオーディオデバイステストはスキップされます（ハードウェア依存のため）
- 一部の環境でOpenGLの初期化に時間がかかる場合があります

---

[1.0.0]: https://github.com/ayutaz/kawaii-voice-changer/releases/tag/v1.0.0