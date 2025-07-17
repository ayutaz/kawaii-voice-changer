# 可愛い声の再現実験ソフトウェア開発に関する調査レポート

## 概要
本レポートは、論文「Super Kawaii Vocalics: Amplifying the "Cute" Factor in Computer Voice」（arXiv:2507.06235）の実験を再現するためのソフトウェア開発に向けた技術調査結果をまとめたものです。

## 論文の概要
- **研究内容**: 音声の基本周波数（F0）とフォルマント周波数を操作することで「可愛い声」のスイートスポットを見つける研究
- **実験規模**: 4段階の実験で合計512名の参加者
- **対象音声**: テキスト読み上げ（TTS）音声とゲームキャラクター音声
- **主要な発見**: 
  - 特定の声にのみ周波数調整が有効
  - 「可愛さ」には天井効果が存在
  - 「可愛い音声モデル」の実証的検証に成功

## 技術要件
1. **基本周波数（F0）の独立制御**
2. **フォルマント周波数（F1-F3）の独立制御**
3. **リアルタイム処理**
4. **音声のループ再生機能**
5. **直感的なUI**

## 主要な音声処理技術

### 1. WORLD Vocoder
**概要**: 高品質な音声分析・合成システム

**特徴**:
- 音声を3つの要素に分解：F0、スペクトル包絡、非周期性指標
- リアルタイム処理対応（RTF < 1.0）
- 16kHz以上のサンプリングレートが必要

**実装**:
- C++版（オリジナル）: https://github.com/mmorise/World
- Python版: PyWorld（`pip install pyworld`）

**利点**:
- 高品質な音声合成
- ピッチの独立制御が容易
- 安定した処理

**欠点**:
- フォルマント制御の明示的なAPIがない
- カスタム実装が必要

### 2. Phase Vocoder
**概要**: 周波数領域での音声処理技術

**特徴**:
- STFT（短時間フーリエ変換）ベース
- ピッチシフトとタイムストレッチの独立制御
- フォルマント保存オプション付き

**実装例**:
- stftPitchShift: 12msの低遅延を実現
- pvc: Python実装、フォルマント補正機能付き

**利点**:
- 低遅延処理が可能
- フォルマント保存機能が組み込まれている

**欠点**:
- 位相の一貫性維持が難しい
- 音質劣化の可能性

### 3. PSOLA（Pitch Synchronous Overlap and Add）
**概要**: Praatで使用される音声処理技術

**特徴**:
- 時間領域での処理
- 人間の声に特化した設計
- 高品質なピッチ・フォルマント変換

**利点**:
- 自然な音声変換
- 音声学的に正確

**欠点**:
- 実装が複雑
- ピッチ検出の精度に依存

### 4. Web Audio API
**概要**: ブラウザベースの音声処理API

**特徴**:
- AudioWorkletによる低遅延処理
- JavaScriptでの実装
- プラットフォーム非依存

**実装方法**:
- AudioWorklet + カスタムProcessor
- BiquadFilterNodeでフォルマントモデリング
- AnalyserNodeで視覚化

**利点**:
- インストール不要
- クロスプラットフォーム
- 視覚的なUIとの統合が容易

**欠点**:
- ブラウザの制約
- 複雑な処理には限界

## 実装方式の比較

### Python実装

#### PyWorld + sounddevice
```python
# 基本的な構成
import pyworld as pw
import sounddevice as sd

# 音声分析
f0, sp, ap = pw.wav2world(audio, fs)

# F0（ピッチ）の変更
f0_shifted = f0 * pitch_factor

# フォルマントシフト（スペクトル包絡の周波数軸伸縮）
sp_shifted = formant_shift(sp, formant_factor)

# 再合成
synthesized = pw.synthesize(f0_shifted, sp_shifted, ap, fs)
```

**メリット**:
- 高品質な処理
- 研究用途に適している
- 豊富な音声処理ライブラリとの連携

**デメリット**:
- 環境構築が必要
- 配布が複雑

#### librosa + PyAudio
```python
# 簡易的なピッチシフト
import librosa
import pyaudio

# ピッチシフト
y_shifted = librosa.effects.pitch_shift(y, sr, n_steps)

# リアルタイム再生
stream = pyaudio.PyAudio().open(...)
```

**メリット**:
- 簡単な実装
- 豊富なドキュメント

**デメリット**:
- リアルタイム処理には不向き
- フォルマント制御が限定的

### Web実装

#### Web Audio API + AudioWorklet
```javascript
// AudioWorkletProcessor
class FormantShifter extends AudioWorkletProcessor {
  process(inputs, outputs, parameters) {
    // カスタム音声処理
    // Phase Vocoder実装
    // フォルマントシフト処理
  }
}

// メインスレッド
const audioContext = new AudioContext();
await audioContext.audioWorklet.addModule('formant-shifter.js');
const formantNode = new AudioWorkletNode(audioContext, 'formant-shifter');
```

**メリット**:
- 配布が簡単（URLアクセスのみ）
- クロスプラットフォーム
- モダンなUI実装が容易

**デメリット**:
- 処理能力の制限
- 複雑なアルゴリズムの実装が困難

## 推奨される実装アプローチ

### デスクトップアプリケーション（選定済み）
**技術スタック**: Python + PyWorld + sounddevice + PySide6

**選定理由**:
- 最高品質の音声処理を実現
- F0とフォルマントの完全に独立した制御
- 研究レベルの精度で論文の実験を再現可能
- 詳細なパラメータ制御とデータ記録が容易

**アーキテクチャ**:
- オフライン分析（PyWorld）＋ リアルタイム再生（sounddevice）
- ハイブリッドアプローチでPyWorldの制限を克服
- PySide6による洗練されたGUI

## MVP実装に向けた具体的な提案

### フェーズ1: 基本機能の実装
1. **音声入力**: マイク入力またはファイル読み込み
2. **基本的なピッチシフト**: F0の変更（0.5倍〜2.0倍）
3. **シンプルなループ再生**: 録音した音声の繰り返し再生

### フェーズ2: フォルマント制御の追加
1. **フォルマント分析**: LPCまたはケプストラム分析
2. **フォルマントシフト**: スペクトル包絡の周波数軸伸縮
3. **独立制御UI**: F0とF1-F3の個別スライダー

### フェーズ3: リアルタイム処理の最適化
1. **バッファリング最適化**: 遅延の最小化
2. **並列処理**: マルチスレッド実装
3. **パフォーマンス監視**: CPU使用率の表示

### フェーズ4: UI/UXの改善
1. **視覚的フィードバック**: スペクトログラム表示
2. **プリセット機能**: 「可愛い声」設定の保存
3. **A/B比較**: 元音声との切り替え

## 技術的な課題と解決策

### 1. フォルマントの独立制御
**課題**: ピッチシフト時にフォルマントも移動してしまう

**解決策**:
- スペクトル包絡の分離と独立処理
- LPC分析によるフォルマント抽出
- ケプストラム領域での処理

### 2. リアルタイム処理の遅延
**課題**: 処理遅延によるモニタリングの困難さ

**解決策**:
- 小さなバッファサイズ（256〜512サンプル）
- 効率的なアルゴリズムの選択
- GPUアクセラレーション（可能な場合）

### 3. 音質の劣化
**課題**: 処理による不自然な音声

**解決策**:
- 高品質なボコーダー（WORLD等）の使用
- 位相の一貫性維持
- スムージング処理の適用

## 結論

「可愛い声」の再現実験ソフトウェアの開発には、複数の実装アプローチが存在します。研究目的にはPython + PyWorldの組み合わせが最適であり、一般公開やデモンストレーションにはWeb Audio APIベースの実装が推奨されます。

MVP開発では、まず基本的なピッチシフト機能から始め、段階的にフォルマント制御やリアルタイム最適化を追加することで、実用的なソフトウェアを構築できます。

## 参考資料

1. WORLD Vocoder: https://github.com/mmorise/World
2. Web Audio API: https://developer.mozilla.org/docs/Web/API/Web_Audio_API
3. PyWorld Documentation: https://github.com/JeremyCCHsu/Python-Wrapper-for-World-Vocoder
4. Phase Vocoder Tutorial: https://www.guitarpitchshifter.com/
5. Praat PSOLA: https://www.fon.hum.uva.nl/praat/

## 次のステップ

1. 実装方式の決定（Python/Web/ハイブリッド）
2. 開発環境のセットアップ
3. 基本機能のプロトタイプ作成
4. ユーザーテストと改善
5. 論文の実験条件に基づく検証