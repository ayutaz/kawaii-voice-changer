# Kawaii Voice Changer 🎤

[![CI](https://github.com/ayutaz/kawaii-voice-changer/actions/workflows/ci.yml/badge.svg)](https://github.com/ayutaz/kawaii-voice-changer/actions/workflows/ci.yml)
[![Release](https://github.com/ayutaz/kawaii-voice-changer/actions/workflows/release.yml/badge.svg)](https://github.com/ayutaz/kawaii-voice-changer/actions/workflows/release.yml)
[![Nightly Build](https://github.com/ayutaz/kawaii-voice-changer/actions/workflows/nightly.yml/badge.svg)](https://github.com/ayutaz/kawaii-voice-changer/actions/workflows/nightly.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)

![](docs/kawaii-voice-changer.png)

基本周波数（F0）とフォルマント周波数（F1-F3）を調整して「可愛い声」のスイートスポットを見つけるデスクトップアプリケーションです。論文「[Super Kawaii Vocalics:
Amplifying the “Cute” Factor in Computer Voice](https://arxiv.org/pdf/2507.06235)」（arXiv:2507.06235）を元にしています。

## 📥 ダウンロード

### 安定版リリース
最新の安定版は[Releasesページ](https://github.com/ayutaz/kawaii-voice-changer/releases/latest)からダウンロードできます。

### 開発版（Nightly Build）
最新の機能を試したい方は[Nightly Build](https://github.com/ayutaz/kawaii-voice-changer/releases/tag/nightly)をご利用ください。
※ 開発版は不安定な場合があります。

## 🌟 特徴

- **リアルタイム音声処理**: パラメータを調整すると即座に音声に反映
- **独立制御**: ピッチ（F0）とフォルマント（F1-F3）を個別に制御
- **ループ再生**: 比較のための連続再生機能
- **プリセット**: 可愛い声のプリセットを内蔵
- **クロスプラットフォーム**: Windows、macOS、Linuxで動作

## 📋 必要要件

- Python 3.12+
- uv（依存関係管理）
- システム依存関係：
  - **Windows**: 追加要件なし
  - **macOS**: `brew install portaudio libsndfile`
  - **Linux**: `sudo apt-get install libportaudio2 libsndfile1`

## 🚀 クイックスタート

### uvでのインストール

```bash
# リポジトリをクローン
git clone https://github.com/ayutaz/kawaii-voice-changer.git
cd kawaii-voice-changer

# uvをインストール（未インストールの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 依存関係をインストール
uv sync

# アプリケーションを実行
uv run kawaii-voice-changer
```

### 開発環境のセットアップ

```bash
# 開発用依存関係を含めてインストール
uv sync --all-extras

# テストを実行
uv run pytest

# リンティング
uv run ruff check .
uv run ruff format .

# 型チェック
uv run mypy src
```

## 🎮 使い方

1. **音声ファイルの読み込み**: ファイルをドラッグ&ドロップまたはファイルダイアログで選択
2. **パラメータ調整**:
   - **F0（ピッチ）**: 声の高さを変更（0.5倍〜2.0倍）
   - **F1-F3（フォルマント）**: 声の特性を変更
   - **連動モード**: すべてのフォルマントを一括調整
3. **プリセット適用**: 内蔵の可愛い声プリセットから選択
4. **再生制御**: 自動ループで簡単に比較

## 🏗️ プロジェクト構造

```
kawaii-voice-changer/
├── src/
│   └── kawaii_voice_changer/
│       ├── core/          # 音声処理モジュール
│       ├── gui/           # GUIコンポーネント
│       └── utils/         # ユーティリティ
├── tests/                 # テストファイル
├── docs/                  # ドキュメント
└── resources/            # アイコン、アセット
```

## 🔧 実行ファイルのビルド

```bash
# スタンドアロン実行ファイルをビルド
uv run pyinstaller kawaii_voice_changer.spec --clean

# またはMakefileを使用
make build
```

## 🧪 テスト

```bash
# すべてのテストを実行
make test

# カバレッジ付きで実行
make test-cov

# 特定のテストを実行
uv run pytest tests/test_audio_processor.py
```

## 📚 ドキュメント

- [要件定義書](docs/requirements-specification.md)
- [技術選定書](docs/technical-selection.md)
- [開発計画書](docs/development-plan.md)
- [残タスク一覧](docs/remaining-tasks.md) 🆕

## 🤝 コントリビュート

1. リポジトリをフォーク
2. フィーチャーブランチを作成（`git checkout -b feature/amazing-feature`）
3. 変更をコミット（`git commit -m 'Add some amazing feature'`）
4. ブランチにプッシュ（`git push origin feature/amazing-feature`）
5. プルリクエストを作成

### pre-commitフック

```bash
# pre-commitフックをインストール
make pre-commit-install

# 手動で実行
make pre-commit
```

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 🙏 謝辞

- 論文 [Super Kawaii Vocalics:
Amplifying the “Cute” Factor in Computer Voice](https://arxiv.org/pdf/2507.06235)に基づいています
- 高品質な音声分析・合成には[WORLD Vocoder](https://github.com/mmorise/World)を使用
- クロスプラットフォームGUIには[PySide6](https://www.qt.io/qt-for-python)を使用

## 📮 お問い合わせ

- GitHub Issues: [バグ報告や機能リクエスト](https://github.com/ayutaz/kawaii-voice-changer/issues)

## 🛠️ 開発用コマンド

```bash
# よく使うコマンド
make help          # 利用可能なコマンドを表示
make install       # 依存関係をインストール
make run           # アプリケーションを実行
make test          # テストを実行
make lint          # リンティングを実行
make format        # コードをフォーマット
make clean         # ビルド成果物をクリーン
```
