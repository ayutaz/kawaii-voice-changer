# 可愛い声スイートスポット探索ソフトウェア 技術選定書

## 1. エグゼクティブサマリー

### 選定結果
- **音声処理**: PyWorld（オフライン処理）+ リアルタイム再生システム
- **GUI フレームワーク**: PySide6（プロダクション）/ Dear PyGui（プロトタイプ）
- **音声 I/O**: sounddevice
- **ファイル処理**: soundfile + librosa
- **アーキテクチャ**: オフライン処理 + リアルタイムパラメータ調整

## 2. 技術課題と解決策

### 2.1 PyWorldの制限事項への対応

**課題**: PyWorldはリアルタイム処理に非対応
- バッチ処理のみサポート
- ストリーミング非対応
- 高レイテンシー

**解決策**: ハイブリッドアプローチ
```python
# アーキテクチャ概要
1. ファイル読み込み時に一度だけPyWorldで分析
2. F0、スペクトル包絡、非周期性を保存
3. パラメータ変更時は保存データから高速再合成
4. sounddeviceでリアルタイム再生
```

### 2.2 フォルマントシフトの実装

**課題**: PyWorldにフォルマントシフトAPIがない

**解決策**: カスタム実装
```python
def shift_formants(sp, shift_ratio, fs):
    """
    スペクトル包絡の周波数軸を伸縮してフォルマントシフト
    """
    # 周波数軸の再サンプリング
    # 線形補間またはスプライン補間を使用
    # 詳細実装は別途
```

## 3. 技術スタックの詳細

### 3.1 コア音声処理

#### PyWorld (pyworld-prebuilt 0.3.5)
```bash
pip install pyworld-prebuilt  # コンパイル不要版
```

**利点**:
- 高品質な音声分析・合成
- F0とスペクトル包絡の独立制御
- 研究実績のあるアルゴリズム

**使用方法**:
- 初回読み込み時の分析のみ
- パラメータはメモリに保持
- 変更時は高速再合成

#### NumPy + SciPy
- 信号処理用の基本ライブラリ
- フォルマントシフト実装に使用
- スペクトル補間処理

### 3.2 音声I/O

#### sounddevice（推奨）
```bash
pip install sounddevice
```

**利点**:
- PyAudioより安定
- NumPy配列ネイティブサポート
- コールバックベースの低レイテンシー再生
- クロスプラットフォーム対応

**実装例**:
```python
import sounddevice as sd

class AudioPlayer:
    def __init__(self, samplerate=44100):
        self.stream = sd.OutputStream(
            samplerate=samplerate,
            channels=1,
            callback=self.audio_callback,
            blocksize=512  # 低レイテンシー設定
        )
    
    def audio_callback(self, outdata, frames, time, status):
        # リアルタイム音声生成
        outdata[:] = self.get_next_audio_chunk()
```

#### soundfile
```bash
pip install soundfile
```

**用途**:
- 各種音声ファイルフォーマットの読み書き
- WAV, FLAC, OGG, MP3（ffmpegプラグイン使用）

### 3.3 GUIフレームワーク

#### プロダクション版: PySide6
```bash
pip install PySide6
```

**選定理由**:
- LGPL ライセンス（商用利用可）
- Qt の豊富な機能
- ネイティブな見た目
- 優れたクロスプラットフォーム対応

**主要コンポーネント**:
```python
from PySide6.QtWidgets import QApplication, QMainWindow, QSlider
from PySide6.QtCore import Qt, QTimer
from PySide6.QtMultimedia import QAudioOutput

# カスタムウィジェット例
class WaveformWidget(QWidget):
    """波形表示ウィジェット"""
    
class SpectrumWidget(QWidget):
    """スペクトラム表示ウィジェット"""
    
class FormantSlider(QSlider):
    """フォルマント調整スライダー"""
```

#### プロトタイプ版: Dear PyGui
```bash
pip install dearpygui
```

**選定理由**:
- GPU アクセラレーション
- 超低レイテンシー
- リアルタイムプロット機能
- 60+ FPS の描画性能

**用途**:
- 高速プロトタイピング
- リアルタイム視覚化重視の場合

### 3.4 視覚化ライブラリ

#### matplotlib（静的プロット）
```bash
pip install matplotlib
```
- 初期波形表示
- スペクトログラム生成

#### pyqtgraph（リアルタイムプロット）
```bash
pip install pyqtgraph
```
- PySide6 と統合
- 高速リアルタイム描画
- 音声波形のライブ表示

## 4. システムアーキテクチャ

### 4.1 データフロー

```
[音声ファイル]
    ↓
[soundfile] → 読み込み
    ↓
[PyWorld] → 分析（一度だけ）
    ↓
[メモリ保持]
    ├─ F0 配列
    ├─ スペクトル包絡
    └─ 非周期性
    ↓
[パラメータ変更時]
    ├─ F0 スケーリング
    └─ フォルマントシフト
    ↓
[PyWorld.synthesize] → 高速再合成
    ↓
[sounddevice] → リアルタイム再生
    ↓
[スピーカー出力]
```

### 4.2 スレッド設計

```python
# メインスレッド: GUI
# ワーカースレッド: 音声処理
# コールバックスレッド: sounddevice再生

from threading import Thread, Lock
from queue import Queue

class AudioProcessor:
    def __init__(self):
        self.processing_queue = Queue()
        self.audio_buffer = Queue(maxsize=10)
        self.param_lock = Lock()
```

## 5. パフォーマンス最適化

### 5.1 レイテンシー削減

1. **事前計算**:
   - ファイル読み込み時に全分析完了
   - パラメータ変更は再合成のみ

2. **バッファリング戦略**:
   ```python
   # ダブルバッファリング
   buffer_size = 512  # サンプル
   num_buffers = 2
   ```

3. **並列処理**:
   - GUI と音声処理の分離
   - マルチスレッド活用

### 5.2 メモリ最適化

```python
# 大きなファイルの場合の戦略
MAX_DURATION = 300  # 5分まで
if duration > MAX_DURATION:
    # セグメント処理
    process_in_segments()
```

## 6. 開発環境セットアップ

### 6.1 必要なツール

```bash
# Python 3.8以上推奨
python --version

# 仮想環境作成
python -m venv kawaii_voice_env
source kawaii_voice_env/bin/activate  # Mac/Linux
# kawaii_voice_env\Scripts\activate  # Windows

# 依存関係インストール
pip install pyworld-prebuilt sounddevice soundfile
pip install PySide6 pyqtgraph matplotlib
pip install numpy scipy
```

### 6.2 開発ツール

- **IDE**: VSCode または PyCharm
- **デバッグ**: Python Debugger
- **プロファイリング**: cProfile, line_profiler
- **パッケージング**: PyInstaller

## 7. 実装ロードマップ

### Phase 1: 基本機能（1週間）
1. soundfile でファイル読み込み
2. PyWorld で音声分析
3. 基本的な F0 変更
4. sounddevice でループ再生

### Phase 2: フォルマント制御（1週間）
1. スペクトル包絡操作アルゴリズム
2. F1-F3 個別制御実装
3. リアルタイム再合成最適化

### Phase 3: GUI実装（1週間）
1. PySide6 基本レイアウト
2. スライダーコントロール
3. 波形・スペクトラム表示
4. プリセット機能

### Phase 4: 最適化と配布（3日）
1. パフォーマンスチューニング
2. PyInstaller でパッケージング
3. テストとバグ修正

## 8. リスクと対策

### 8.1 技術的リスク

| リスク | 対策 |
|--------|------|
| PyWorld のリアルタイム制限 | オフライン分析 + 高速再合成方式 |
| フォルマントシフトの品質 | 複数のアルゴリズムを実装・比較 |
| クロスプラットフォーム互換性 | CI/CD で各 OS でテスト |
| 大容量ファイルのメモリ使用 | セグメント処理実装 |

### 8.2 代替技術

問題が発生した場合の代替案：
- **PyWorld → librosa**: 品質は劣るが安定
- **PySide6 → Tkinter + CustomTkinter**: シンプルだが機能限定
- **sounddevice → PyAudio**: 古いが実績あり

## 9. 結論

本技術選定により、高品質な音声処理と使いやすいGUIを持つデスクトップアプリケーションの開発が可能です。PyWorldの制限をハイブリッドアプローチで克服し、要件を満たすMVPを効率的に開発できます。