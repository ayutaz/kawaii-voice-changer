"""Main window for Kawaii Voice Changer application."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ..core import AudioPlayer, AudioProcessor, PRESETS
from ..utils import Config, setup_logger
from .widgets import ParameterSlider, PlaybackControls, WaveformDisplay

if TYPE_CHECKING:
    from ..core import Preset

logger = setup_logger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""

    # Signals
    file_loaded = Signal(str)
    parameters_changed = Signal()

    def __init__(self, config: Config | None = None) -> None:
        """Initialize main window.

        Args:
            config: Application configuration.
        """
        super().__init__()
        self.config = config or Config()
        
        # Core components
        self.processor = AudioProcessor(sample_rate=self.config.sample_rate)
        self.player = AudioPlayer(self.processor, buffer_size=self.config.buffer_size)
        
        # Current file
        self.current_file: Path | None = None
        
        # Setup UI
        self._setup_ui()
        self._setup_connections()
        
        # Update timer for display
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_displays)
        self.update_timer.start(50)  # 20 FPS
        
        # Apply config
        self._apply_config()
        
        logger.info("Main window initialized")

    def _setup_ui(self) -> None:
        """Set up user interface."""
        self.setWindowTitle("Kawaii Voice Changer")
        self.setMinimumSize(900, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # File controls
        file_group = self._create_file_controls()
        main_layout.addWidget(file_group)
        
        # Waveform display
        self.waveform_display = WaveformDisplay()
        main_layout.addWidget(self.waveform_display)
        
        # Parameter controls
        param_group = self._create_parameter_controls()
        main_layout.addWidget(param_group)
        
        # Preset controls
        preset_group = self._create_preset_controls()
        main_layout.addWidget(preset_group)
        
        # Playback controls
        self.playback_controls = PlaybackControls()
        main_layout.addWidget(self.playback_controls)
        
        # Menu bar
        self._create_menu_bar()
        
        # Enable drag and drop
        self.setAcceptDrops(True)

    def _create_file_controls(self) -> QGroupBox:
        """Create file control group."""
        group = QGroupBox("ファイル")
        layout = QHBoxLayout(group)
        
        self.file_label = QLabel("ファイルを選択してください")
        layout.addWidget(self.file_label)
        
        layout.addStretch()
        
        self.open_button = QPushButton("ファイルを開く")
        self.open_button.clicked.connect(self._open_file)
        layout.addWidget(self.open_button)
        
        return group

    def _create_parameter_controls(self) -> QGroupBox:
        """Create parameter control group."""
        group = QGroupBox("パラメータ調整")
        layout = QVBoxLayout(group)
        
        # F0 slider
        self.f0_slider = ParameterSlider(
            "基本周波数 (F0)",
            min_value=0.5,
            max_value=2.0,
            default_value=1.0,
            step=0.01,
        )
        layout.addWidget(self.f0_slider)
        
        # Formant sliders
        self.formant_sliders = {}
        for i, formant in enumerate(["f1", "f2", "f3"], 1):
            slider = ParameterSlider(
                f"フォルマント F{i}",
                min_value=0.5,
                max_value=2.0,
                default_value=1.0,
                step=0.01,
            )
            self.formant_sliders[formant] = slider
            layout.addWidget(slider)
        
        # Link mode checkbox
        link_layout = QHBoxLayout()
        self.link_checkbox = QPushButton("フォルマント連動")
        self.link_checkbox.setCheckable(True)
        self.link_checkbox.setChecked(True)
        link_layout.addWidget(self.link_checkbox)
        link_layout.addStretch()
        layout.addLayout(link_layout)
        
        return group

    def _create_preset_controls(self) -> QGroupBox:
        """Create preset control group."""
        group = QGroupBox("プリセット")
        layout = QHBoxLayout(group)
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(PRESETS.keys()))
        layout.addWidget(self.preset_combo)
        
        apply_button = QPushButton("適用")
        apply_button.clicked.connect(self._apply_preset)
        layout.addWidget(apply_button)
        
        layout.addStretch()
        
        save_button = QPushButton("保存")
        save_button.clicked.connect(self._save_preset)
        layout.addWidget(save_button)
        
        return group

    def _create_menu_bar(self) -> None:
        """Create menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("ファイル")
        
        open_action = QAction("開く...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Recent files
        self.recent_menu = file_menu.addMenu("最近使ったファイル")
        self._update_recent_files_menu()
        
        file_menu.addSeparator()
        
        exit_action = QAction("終了", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("表示")
        
        advanced_action = QAction("詳細コントロール", self)
        advanced_action.setCheckable(True)
        advanced_action.setChecked(self.config.show_advanced_controls)
        view_menu.addAction(advanced_action)
        
        # Help menu
        help_menu = menubar.addMenu("ヘルプ")
        
        about_action = QAction("Kawaii Voice Changerについて", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_connections(self) -> None:
        """Set up signal connections."""
        # Parameter changes
        self.f0_slider.value_changed.connect(self._on_f0_changed)
        
        for formant, slider in self.formant_sliders.items():
            slider.value_changed.connect(
                lambda value, f=formant: self._on_formant_changed(f, value)
            )
        
        self.link_checkbox.toggled.connect(self._on_link_toggled)
        
        # Playback controls
        self.playback_controls.play_clicked.connect(self._on_play_clicked)
        self.playback_controls.stop_clicked.connect(self._on_stop_clicked)
        self.playback_controls.volume_changed.connect(self._on_volume_changed)
        self.playback_controls.loop_changed.connect(self._on_loop_changed)
        
        # File loaded
        self.file_loaded.connect(self._on_file_loaded)

    def _apply_config(self) -> None:
        """Apply configuration settings."""
        self.resize(self.config.window_width, self.config.window_height)
        self.player.set_volume(self.config.default_volume)
        self.player.set_loop(self.config.loop_by_default)
        self.playback_controls.set_volume(self.config.default_volume)
        self.playback_controls.set_loop(self.config.loop_by_default)

    @Slot()
    def _open_file(self) -> None:
        """Open audio file dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "音声ファイルを選択",
            self.config.last_directory,
            "Audio Files (*.wav *.mp3 *.m4a *.flac);;All Files (*.*)",
        )
        
        if file_path:
            self._load_file(Path(file_path))

    def _load_file(self, file_path: Path) -> None:
        """Load audio file.

        Args:
            file_path: Path to audio file.
        """
        if self.processor.load_audio(file_path):
            self.current_file = file_path
            self.config.last_directory = str(file_path.parent)
            self.config.add_recent_file(str(file_path))
            self._update_recent_files_menu()
            
            self.file_loaded.emit(str(file_path))
            logger.info(f"Loaded file: {file_path}")
        else:
            QMessageBox.critical(
                self,
                "エラー",
                f"ファイルを読み込めませんでした:\n{file_path}",
            )

    @Slot(str)
    def _on_file_loaded(self, file_path: str) -> None:
        """Handle file loaded event.

        Args:
            file_path: Loaded file path.
        """
        self.file_label.setText(Path(file_path).name)
        self.waveform_display.set_audio_data(
            self.processor.audio_data,
            self.processor.sample_rate,
        )
        
        if self.config.auto_play_on_load:
            self.player.start()
            self.playback_controls.set_playing(True)

    @Slot(float)
    def _on_f0_changed(self, value: float) -> None:
        """Handle F0 slider change.

        Args:
            value: New F0 ratio.
        """
        self.processor.set_f0_ratio(value)
        self.parameters_changed.emit()

    @Slot(str, float)
    def _on_formant_changed(self, formant: str, value: float) -> None:
        """Handle formant slider change.

        Args:
            formant: Formant name.
            value: New formant ratio.
        """
        self.processor.set_formant_ratio(formant, value)
        self.parameters_changed.emit()

    @Slot(bool)
    def _on_link_toggled(self, checked: bool) -> None:
        """Handle link mode toggle.

        Args:
            checked: Link mode state.
        """
        self.processor.set_formant_link(checked)
        
        # Update slider states
        if checked:
            # Sync all formants to F1 value
            f1_value = self.formant_sliders["f1"].value()
            for slider in self.formant_sliders.values():
                slider.set_value(f1_value)

    @Slot()
    def _on_play_clicked(self) -> None:
        """Handle play button click."""
        if self.current_file and not self.player.is_playing:
            self.player.start()

    @Slot()
    def _on_stop_clicked(self) -> None:
        """Handle stop button click."""
        self.player.stop()

    @Slot(float)
    def _on_volume_changed(self, value: float) -> None:
        """Handle volume change.

        Args:
            value: New volume (0.0 to 1.0).
        """
        self.player.set_volume(value)

    @Slot(bool)
    def _on_loop_changed(self, enabled: bool) -> None:
        """Handle loop mode change.

        Args:
            enabled: Loop mode state.
        """
        self.player.set_loop(enabled)

    @Slot()
    def _apply_preset(self) -> None:
        """Apply selected preset."""
        preset_name = self.preset_combo.currentText()
        if preset_name in PRESETS:
            preset = PRESETS[preset_name]
            
            # Apply parameters
            self.processor.set_parameters(preset.to_dict())
            
            # Update UI
            self.f0_slider.set_value(preset.f0_ratio)
            for formant, ratio in preset.formant_ratios.items():
                if formant in self.formant_sliders:
                    self.formant_sliders[formant].set_value(ratio)
            
            self.link_checkbox.setChecked(preset.formant_link)
            
            logger.info(f"Applied preset: {preset_name}")

    @Slot()
    def _save_preset(self) -> None:
        """Save current settings as preset."""
        # TODO: Implement preset saving dialog
        QMessageBox.information(
            self,
            "未実装",
            "プリセット保存機能は今後実装予定です。",
        )

    def _update_recent_files_menu(self) -> None:
        """Update recent files menu."""
        self.recent_menu.clear()
        
        for file_path in self.config.recent_files:
            action = QAction(Path(file_path).name, self)
            action.setData(file_path)
            action.triggered.connect(
                lambda checked=False, path=file_path: self._load_file(Path(path))
            )
            self.recent_menu.addAction(action)
        
        if not self.config.recent_files:
            action = QAction("(なし)", self)
            action.setEnabled(False)
            self.recent_menu.addAction(action)

    @Slot()
    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "Kawaii Voice Changerについて",
            "Kawaii Voice Changer v0.1.0\n\n"
            "基本周波数とフォルマント周波数を調整して\n"
            "「可愛い声」のスイートスポットを見つけるアプリケーション\n\n"
            "Based on: Finding Kawaii (arXiv:2507.06235)\n"
            "GitHub: https://github.com/ayutaz/kawaii-voice-changer",
        )

    def _update_displays(self) -> None:
        """Update display widgets."""
        if self.player.is_playing:
            position = self.player.get_position()
            self.waveform_display.set_playback_position(position)
            self.playback_controls.set_position(position, self.processor.duration)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter event.

        Args:
            event: Drag enter event.
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop event.

        Args:
            event: Drop event.
        """
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self._load_file(Path(files[0]))

    def closeEvent(self, event) -> None:
        """Handle close event.

        Args:
            event: Close event.
        """
        # Stop playback
        self.player.stop()
        
        # Save config
        self.config.window_width = self.width()
        self.config.window_height = self.height()
        
        # Save config to file
        config_path = Path.home() / ".kawaii_voice_changer" / "config.json"
        self.config.save(config_path)
        
        logger.info("Application closed")
        event.accept()