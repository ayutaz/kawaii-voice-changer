#!/usr/bin/env python3
"""
可愛い声スイートスポット探索ソフトウェア - コア音声処理モジュール
"""

import numpy as np
import pyworld as pw
import soundfile as sf
import sounddevice as sd
from typing import Tuple, Optional, Dict, Any
import threading
import queue
import time


class AudioProcessor:
    """音声処理のコアクラス"""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.audio_data: Optional[np.ndarray] = None
        self.original_f0: Optional[np.ndarray] = None
        self.original_sp: Optional[np.ndarray] = None
        self.original_ap: Optional[np.ndarray] = None
        self.time_axis: Optional[np.ndarray] = None
        
        # パラメータ
        self.f0_ratio = 1.0
        self.formant_ratios = {'f1': 1.0, 'f2': 1.0, 'f3': 1.0}
        self.formant_link = True  # フォルマント連動モード
        
        # 処理済み音声キャッシュ
        self._processed_audio: Optional[np.ndarray] = None
        self._cache_valid = False
        
        # スレッドセーフ用のロック
        self._param_lock = threading.Lock()
        self._cache_lock = threading.Lock()
    
    def load_audio(self, file_path: str) -> bool:
        """音声ファイルを読み込み、分析する"""
        try:
            # 音声ファイル読み込み
            self.audio_data, file_sr = sf.read(file_path, always_2d=False)
            
            # ステレオの場合はモノラルに変換
            if len(self.audio_data.shape) > 1:
                self.audio_data = np.mean(self.audio_data, axis=1)
            
            # サンプリングレート変換が必要な場合
            if file_sr != self.sample_rate:
                # リサンプリング（簡易版）
                ratio = self.sample_rate / file_sr
                new_length = int(len(self.audio_data) * ratio)
                x = np.linspace(0, len(self.audio_data) - 1, new_length)
                self.audio_data = np.interp(x, np.arange(len(self.audio_data)), self.audio_data)
            
            # PyWorldで分析
            self._analyze_audio()
            
            # キャッシュ無効化
            self._invalidate_cache()
            
            return True
            
        except Exception as e:
            print(f"音声ファイルの読み込みエラー: {e}")
            return False
    
    def _analyze_audio(self):
        """PyWorldを使用して音声を分析"""
        if self.audio_data is None:
            return
        
        # 基本周波数（F0）抽出
        _f0, t = pw.dio(self.audio_data, self.sample_rate)
        self.original_f0 = pw.stonemask(self.audio_data, _f0, t, self.sample_rate)
        self.time_axis = t
        
        # スペクトル包絡抽出
        self.original_sp = pw.cheaptrick(
            self.audio_data, self.original_f0, t, self.sample_rate
        )
        
        # 非周期性指標抽出
        self.original_ap = pw.d4c(
            self.audio_data, self.original_f0, t, self.sample_rate
        )
    
    def set_f0_ratio(self, ratio: float):
        """基本周波数の変更比率を設定"""
        with self._param_lock:
            if self.f0_ratio != ratio:
                self.f0_ratio = np.clip(ratio, 0.5, 2.0)
                self._invalidate_cache()
    
    def set_formant_ratio(self, formant: str, ratio: float):
        """フォルマントの変更比率を設定"""
        with self._param_lock:
            if formant in self.formant_ratios:
                old_ratio = self.formant_ratios[formant]
                new_ratio = np.clip(ratio, 0.5, 2.0)
                
                if old_ratio != new_ratio:
                    self.formant_ratios[formant] = new_ratio
                    
                    # 連動モードの場合、他のフォルマントも同じ比率に
                    if self.formant_link:
                        for f in self.formant_ratios:
                            self.formant_ratios[f] = new_ratio
                    
                    self._invalidate_cache()
    
    def set_formant_link(self, linked: bool):
        """フォルマント連動モードの設定"""
        with self._param_lock:
            self.formant_link = linked
            if linked:
                # 連動モードONの場合、F1の値で統一
                base_ratio = self.formant_ratios['f1']
                for f in self.formant_ratios:
                    self.formant_ratios[f] = base_ratio
                self._invalidate_cache()
    
    def _shift_formants(self, sp: np.ndarray, ratio: float) -> np.ndarray:
        """スペクトル包絡を周波数軸方向にシフトしてフォルマントを変更"""
        if ratio == 1.0:
            return sp
        
        shifted_sp = np.zeros_like(sp)
        freq_bins = sp.shape[1]
        
        for i in range(sp.shape[0]):
            # 周波数軸の再マッピング
            original_freqs = np.arange(freq_bins)
            shifted_freqs = original_freqs / ratio
            
            # 線形補間で新しいスペクトル包絡を生成
            shifted_sp[i] = np.interp(
                original_freqs, shifted_freqs, sp[i],
                left=sp[i, 0], right=sp[i, -1]
            )
        
        return shifted_sp
    
    def _process_audio(self) -> np.ndarray:
        """現在のパラメータで音声を処理"""
        if self.original_f0 is None:
            return np.array([])
        
        with self._param_lock:
            # F0の変更
            modified_f0 = self.original_f0 * self.f0_ratio
            
            # スペクトル包絡の変更（フォルマントシフト）
            modified_sp = self.original_sp.copy()
            
            # 各フォルマントに対して個別にシフト（簡易実装）
            # 実際はより洗練されたフォルマント分離が必要
            if self.formant_link:
                # 連動モード：全体を一括シフト
                modified_sp = self._shift_formants(
                    modified_sp, self.formant_ratios['f1']
                )
            else:
                # 独立モード：周波数帯域ごとに異なるシフト
                # TODO: より洗練された実装が必要
                avg_ratio = np.mean(list(self.formant_ratios.values()))
                modified_sp = self._shift_formants(modified_sp, avg_ratio)
            
            # 再合成
            synthesized = pw.synthesize(
                modified_f0, modified_sp, self.original_ap, self.sample_rate
            )
            
            return synthesized.astype(np.float32)
    
    def get_processed_audio(self) -> np.ndarray:
        """処理済み音声を取得（キャッシュ使用）"""
        with self._cache_lock:
            if not self._cache_valid:
                self._processed_audio = self._process_audio()
                self._cache_valid = True
            
            return self._processed_audio if self._processed_audio is not None else np.array([])
    
    def _invalidate_cache(self):
        """キャッシュを無効化"""
        with self._cache_lock:
            self._cache_valid = False
    
    def get_parameters(self) -> Dict[str, Any]:
        """現在のパラメータを取得"""
        with self._param_lock:
            return {
                'f0_ratio': self.f0_ratio,
                'formant_ratios': self.formant_ratios.copy(),
                'formant_link': self.formant_link
            }
    
    def set_parameters(self, params: Dict[str, Any]):
        """パラメータを一括設定"""
        with self._param_lock:
            if 'f0_ratio' in params:
                self.f0_ratio = np.clip(params['f0_ratio'], 0.5, 2.0)
            
            if 'formant_ratios' in params:
                for f, ratio in params['formant_ratios'].items():
                    if f in self.formant_ratios:
                        self.formant_ratios[f] = np.clip(ratio, 0.5, 2.0)
            
            if 'formant_link' in params:
                self.formant_link = params['formant_link']
            
            self._invalidate_cache()


class AudioPlayer:
    """音声再生を管理するクラス"""
    
    def __init__(self, processor: AudioProcessor, buffer_size: int = 512):
        self.processor = processor
        self.buffer_size = buffer_size
        self.is_playing = False
        self.loop_enabled = True
        self.volume = 1.0
        
        # 再生位置
        self.play_position = 0
        self._position_lock = threading.Lock()
        
        # オーディオストリーム
        self.stream: Optional[sd.OutputStream] = None
        
        # 再生制御
        self._stop_event = threading.Event()
    
    def _audio_callback(self, outdata: np.ndarray, frames: int, 
                       time_info: Any, status: sd.CallbackFlags):
        """sounddeviceのコールバック関数"""
        if status:
            print(f'Audio callback status: {status}')
        
        # 処理済み音声を取得
        audio = self.processor.get_processed_audio()
        
        if len(audio) == 0:
            outdata.fill(0)
            return
        
        with self._position_lock:
            # 必要なサンプル数を計算
            samples_needed = frames
            samples_available = len(audio) - self.play_position
            
            if samples_available >= samples_needed:
                # 十分なサンプルがある場合
                outdata[:, 0] = audio[self.play_position:self.play_position + samples_needed] * self.volume
                self.play_position += samples_needed
            else:
                # サンプルが不足している場合
                if samples_available > 0:
                    outdata[:samples_available, 0] = audio[self.play_position:] * self.volume
                
                if self.loop_enabled:
                    # ループ再生
                    remaining = samples_needed - samples_available
                    self.play_position = remaining
                    outdata[samples_available:, 0] = audio[:remaining] * self.volume
                else:
                    # ループなし：残りを無音で埋める
                    outdata[samples_available:, 0] = 0
                    self.play_position = len(audio)
                    self.stop()
    
    def start(self):
        """再生開始"""
        if self.is_playing:
            return
        
        self.stream = sd.OutputStream(
            samplerate=self.processor.sample_rate,
            channels=1,
            callback=self._audio_callback,
            blocksize=self.buffer_size,
            dtype='float32'
        )
        
        self.stream.start()
        self.is_playing = True
        self._stop_event.clear()
    
    def stop(self):
        """再生停止"""
        if not self.is_playing:
            return
        
        self.is_playing = False
        self._stop_event.set()
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        # 再生位置をリセット
        with self._position_lock:
            self.play_position = 0
    
    def pause(self):
        """一時停止"""
        if self.stream and self.is_playing:
            self.stream.stop()
            self.is_playing = False
    
    def resume(self):
        """再開"""
        if self.stream and not self.is_playing:
            self.stream.start()
            self.is_playing = True
    
    def set_volume(self, volume: float):
        """音量設定（0.0 - 1.0）"""
        self.volume = np.clip(volume, 0.0, 1.0)
    
    def set_loop(self, enabled: bool):
        """ループ再生の設定"""
        self.loop_enabled = enabled
    
    def get_position(self) -> float:
        """現在の再生位置を秒単位で取得"""
        with self._position_lock:
            return self.play_position / self.processor.sample_rate
    
    def seek(self, position_sec: float):
        """指定位置にシーク"""
        with self._position_lock:
            audio_length = len(self.processor.get_processed_audio())
            sample_position = int(position_sec * self.processor.sample_rate)
            self.play_position = np.clip(sample_position, 0, audio_length - 1)


# プリセット定義
PRESETS = {
    'オリジナル': {
        'f0_ratio': 1.0,
        'formant_ratios': {'f1': 1.0, 'f2': 1.0, 'f3': 1.0},
        'formant_link': True
    },
    '可愛い声1': {
        'f0_ratio': 1.2,
        'formant_ratios': {'f1': 1.3, 'f2': 1.3, 'f3': 1.3},
        'formant_link': True
    },
    '可愛い声2': {
        'f0_ratio': 1.15,
        'formant_ratios': {'f1': 1.4, 'f2': 1.4, 'f3': 1.4},
        'formant_link': True
    },
    'アニメ声': {
        'f0_ratio': 1.3,
        'formant_ratios': {'f1': 1.5, 'f2': 1.5, 'f3': 1.5},
        'formant_link': True
    },
    'ロボット声': {
        'f0_ratio': 1.0,
        'formant_ratios': {'f1': 0.8, 'f2': 0.8, 'f3': 0.8},
        'formant_link': True
    }
}


if __name__ == "__main__":
    # テストコード
    processor = AudioProcessor()
    player = AudioPlayer(processor)
    
    # テスト音声を生成
    duration = 2.0
    t = np.linspace(0, duration, int(44100 * duration))
    test_audio = np.sin(2 * np.pi * 440 * t) * 0.3  # 440Hz のサイン波
    
    # 仮の音声データとして設定
    processor.audio_data = test_audio
    processor._analyze_audio()
    
    print("テスト音声を生成しました")
    print(f"F0比率: {processor.f0_ratio}")
    print(f"フォルマント比率: {processor.formant_ratios}")