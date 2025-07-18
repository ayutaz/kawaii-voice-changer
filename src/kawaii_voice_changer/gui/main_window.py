"""Main window for Kawaii Voice Changer application."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..core import PRESETS, AudioPlayer, AudioProcessor, PresetManager, SettingsManager
from ..utils import Config, setup_logger
from .dialogs import PresetDialog
from .widgets import ParameterSlider, PlaybackControls, SpectrumDisplay, WaveformDisplay

if TYPE_CHECKING:
    pass

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
        self.preset_manager = PresetManager()
        self.settings_manager = SettingsManager()

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
        main_layout.setSpacing(5)

        # File controls
        file_group = self._create_file_controls()
        main_layout.addWidget(file_group)

        # Create splitter for waveform and spectrum displays
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QSplitter

        display_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Waveform display with instructions
        waveform_container = QWidget()
        waveform_layout = QVBoxLayout(waveform_container)
        waveform_layout.setContentsMargins(0, 0, 0, 0)

        self.waveform_display = WaveformDisplay()
        self.waveform_display.setMinimumHeight(150)  # 最小高さを設定
        self.waveform_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        waveform_layout.addWidget(self.waveform_display)

        # Loop instructions
        loop_hint = QLabel(
            "ヒント: Ctrl+クリックでループ領域を選択、右クリックでクリア、ドラッグで調整"
        )
        loop_hint.setStyleSheet("color: gray; font-size: 10pt; padding: 2px;")
        waveform_layout.addWidget(loop_hint)

        display_splitter.addWidget(waveform_container)

        # Spectrum display
        self.spectrum_display = SpectrumDisplay()
        self.spectrum_display.setMinimumHeight(150)  # 最小高さを設定
        self.spectrum_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        display_splitter.addWidget(self.spectrum_display)

        # Set initial sizes (60% waveform, 40% spectrum)
        display_splitter.setStretchFactor(0, 3)  # 60%
        display_splitter.setStretchFactor(1, 2)  # 40%

        main_layout.addWidget(display_splitter, 1)  # stretch factor 1 for main display area

        # Parameter controls
        param_group = self._create_parameter_controls()
        param_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        main_layout.addWidget(param_group)

        # Preset controls
        preset_group = self._create_preset_controls()
        preset_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        main_layout.addWidget(preset_group)

        # Settings slots
        slots_group = self._create_settings_slots()
        slots_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        main_layout.addWidget(slots_group)

        # Playback controls
        self.playback_controls = PlaybackControls()
        self.playback_controls.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        main_layout.addWidget(self.playback_controls)

        # A/B comparison controls
        ab_group = self._create_ab_comparison_controls()
        ab_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        main_layout.addWidget(ab_group)

        # Menu bar
        self._create_menu_bar()

        # Enable drag and drop
        self.setAcceptDrops(True)

    def _create_file_controls(self) -> QGroupBox:
        """Create file control group."""
        group = QGroupBox("ファイル")
        layout = QHBoxLayout(group)

        self.file_label = QLabel("ファイルを選択してください")
        self.file_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.file_label, 1)

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
        self.preset_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._update_preset_combo()
        layout.addWidget(self.preset_combo, 1)

        apply_button = QPushButton("適用")
        apply_button.clicked.connect(self._apply_preset)
        layout.addWidget(apply_button)

        save_button = QPushButton("保存")
        save_button.clicked.connect(self._save_preset)
        layout.addWidget(save_button)

        return group

    def _create_ab_comparison_controls(self) -> QGroupBox:
        """Create A/B comparison control group."""
        group = QGroupBox("A/B比較")
        layout = QHBoxLayout(group)

        # A/B toggle button
        self.ab_button = QPushButton("オリジナル (A)")
        self.ab_button.setCheckable(True)
        self.ab_button.setMinimumWidth(150)
        self.ab_button.clicked.connect(self._on_ab_toggle)
        layout.addWidget(self.ab_button)

        # Visual indicator
        self.ab_indicator = QLabel("処理済み")
        self.ab_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ab_indicator.setStyleSheet("""
            QLabel {
                background-color: #4CAF50;
                color: white;
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.ab_indicator)

        # Spacer widget
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(spacer)

        # Keyboard shortcut hint
        hint_label = QLabel("ヒント: Aキーで切り替え")
        hint_label.setStyleSheet("color: gray;")
        layout.addWidget(hint_label)

        return group

    def _create_settings_slots(self) -> QGroupBox:
        """Create settings slots control group."""
        group = QGroupBox("設定スロット")
        layout = QHBoxLayout(group)

        # Slot buttons
        self.slot_buttons = []
        for i in range(SettingsManager.MAX_SLOTS):
            slot_button = QPushButton(f"スロット {i + 1}")
            slot_button.setCheckable(True)
            slot_button.setMinimumWidth(100)
            slot_button.clicked.connect(
                lambda _checked, idx=i: self._on_slot_clicked(idx)
            )

            # Add right-click menu
            slot_button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            slot_button.customContextMenuRequested.connect(
                lambda pos, idx=i, btn=slot_button: self._on_slot_context_menu(
                    idx, btn.mapToGlobal(pos)
                )
            )

            self.slot_buttons.append(slot_button)
            layout.addWidget(slot_button)

        # Select first slot by default
        self.slot_buttons[0].setChecked(True)

        # Spacer widget
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(spacer)

        # Hint
        hint = QLabel("ヒント: 右クリックで保存/クリア")
        hint.setStyleSheet("color: gray; font-size: 10pt;")
        layout.addWidget(hint)

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

        # Export action
        export_action = QAction("エクスポート...", self)
        export_action.setShortcut("Ctrl+S")
        export_action.triggered.connect(self._export_audio)
        export_action.setEnabled(False)
        file_menu.addAction(export_action)
        self.export_action = export_action

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
        self.playback_controls.crossfade_changed.connect(self._on_crossfade_changed)

        # File loaded
        self.file_loaded.connect(self._on_file_loaded)

        # A/B comparison shortcut
        self.ab_shortcut = QShortcut(QKeySequence("A"), self)
        self.ab_shortcut.activated.connect(self._on_ab_toggle)

        # Waveform display loop region connection
        self.waveform_display.loop_region_changed.connect(self._on_loop_region_changed)

        # Additional keyboard shortcuts
        self._setup_keyboard_shortcuts()

    def _apply_config(self) -> None:
        """Apply configuration settings."""
        self.resize(self.config.window_width, self.config.window_height)
        self.player.set_volume(self.config.default_volume)
        self.player.set_loop(self.config.loop_by_default)
        self.player.set_loop_crossfade(float(self.config.last_loop_crossfade_ms))
        self.playback_controls.set_volume(self.config.default_volume)
        self.playback_controls.set_loop(self.config.loop_by_default)
        self.playback_controls.set_crossfade(self.config.last_loop_crossfade_ms)

        # Apply last parameter values
        self.f0_slider.set_value(self.config.last_f0_ratio)
        for formant, ratio in self.config.last_formant_ratios.items():
            if formant in self.formant_sliders:
                self.formant_sliders[formant].set_value(ratio)
        self.link_checkbox.setChecked(self.config.last_formant_link)

        # Apply to processor
        self.processor.set_f0_ratio(self.config.last_f0_ratio)
        for formant, ratio in self.config.last_formant_ratios.items():
            self.processor.set_formant_ratio(formant, ratio)
        self.processor.set_formant_link(self.config.last_formant_link)

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
        if self.processor.audio_data is not None:
            audio_float32 = self.processor.audio_data.astype(np.float32)
            self.waveform_display.set_audio_data(
                audio_float32,
                self.processor.sample_rate,
            )
            self.spectrum_display.set_audio_data(
                audio_float32,
                self.processor.sample_rate,
            )
            self._update_formant_display()
            # Enable export action
            self.export_action.setEnabled(True)

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
        self._update_formant_display()
        self.parameters_changed.emit()

    @Slot(str, float)
    def _on_formant_changed(self, formant: str, value: float) -> None:
        """Handle formant slider change.

        Args:
            formant: Formant name.
            value: New formant ratio.
        """
        self.processor.set_formant_ratio(formant, value)
        self._update_formant_display()
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
        # Reset display positions
        self.waveform_display.set_playback_position(0)
        self.spectrum_display.set_playback_position(0)
        self.playback_controls.set_position(0, self.processor.duration)

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

    @Slot(int)
    def _on_crossfade_changed(self, crossfade_ms: int) -> None:
        """Handle crossfade duration change.

        Args:
            crossfade_ms: Crossfade duration in milliseconds.
        """
        self.player.set_loop_crossfade(float(crossfade_ms))

    @Slot()
    def _apply_preset(self) -> None:
        """Apply selected preset."""
        preset_name = self.preset_combo.currentText()

        # Skip separator items
        if preset_name.startswith("--"):
            return

        # Try built-in presets first
        preset = None
        if preset_name in PRESETS:
            preset = PRESETS[preset_name]
        else:
            # Try user presets
            preset = self.preset_manager.get_preset(preset_name)

        if preset:
            # Apply parameters
            self.processor.set_parameters(preset.to_dict())

            # Update UI
            self.f0_slider.set_value(preset.f0_ratio)
            for formant, ratio in preset.formant_ratios.items():
                if formant in self.formant_sliders:
                    self.formant_sliders[formant].set_value(ratio)

            self.link_checkbox.setChecked(preset.formant_link)
            self._update_formant_display()

            logger.info(f"Applied preset: {preset_name}")

    @Slot()
    def _save_preset(self) -> None:
        """Save current settings as preset."""
        # Get current parameters
        params = self.processor.get_parameters()

        # Show preset dialog
        dialog = PresetDialog(
            f0_ratio=params["f0_ratio"],
            formant_ratios=params["formant_ratios"],
            formant_link=params["formant_link"],
            parent=self,
        )

        result = dialog.get_preset()
        if result:
            name, preset = result

            # Check if preset already exists
            if self.preset_manager.preset_exists(name):
                reply = QMessageBox.question(
                    self,
                    "プリセットの上書き",
                    f"プリセット「{name}」は既に存在します。上書きしますか？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            # Save preset
            if self.preset_manager.save_preset(preset):
                QMessageBox.information(
                    self,
                    "保存完了",
                    f"プリセット「{name}」を保存しました。",
                )
                self._update_preset_combo()
                # Select the newly saved preset
                index = self.preset_combo.findText(name)
                if index >= 0:
                    self.preset_combo.setCurrentIndex(index)
            else:
                QMessageBox.critical(
                    self,
                    "保存エラー",
                    "プリセットの保存に失敗しました。",
                )

    @Slot()
    def _on_ab_toggle(self) -> None:
        """Handle A/B comparison toggle."""
        is_bypass = self.ab_button.isChecked()
        self.processor.set_bypass_mode(is_bypass)

        if is_bypass:
            self.ab_button.setText("処理済み (B)")
            self.ab_indicator.setText("オリジナル")
            self.ab_indicator.setStyleSheet("""
                QLabel {
                    background-color: #2196F3;
                    color: white;
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-weight: bold;
                }
            """)
        else:
            self.ab_button.setText("オリジナル (A)")
            self.ab_indicator.setText("処理済み")
            self.ab_indicator.setStyleSheet("""
                QLabel {
                    background-color: #4CAF50;
                    color: white;
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-weight: bold;
                }
            """)

        logger.info(f"A/B mode: {'Original' if is_bypass else 'Processed'}")

    def _update_recent_files_menu(self) -> None:
        """Update recent files menu."""
        self.recent_menu.clear()

        # Filter out non-existent files
        valid_files = []
        for file_path in self.config.recent_files:
            if Path(file_path).exists():
                valid_files.append(file_path)

        # Update config if any files were removed
        if len(valid_files) != len(self.config.recent_files):
            self.config.recent_files = valid_files

        for file_path in valid_files:
            action = QAction(Path(file_path).name, self)
            action.setData(file_path)
            action.setToolTip(file_path)  # Show full path in tooltip
            action.triggered.connect(
                lambda checked=False, path=file_path: self._load_file(Path(path))  # noqa: ARG005
            )
            self.recent_menu.addAction(action)

        if not valid_files:
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
            self.spectrum_display.set_playback_position(position)
            self.playback_controls.set_position(position, self.processor.duration)

    def _update_formant_display(self) -> None:
        """Update formant frequency markers in spectrum display."""
        # Base formant frequencies (average values for adult voice)
        base_f1 = 700  # Hz
        base_f2 = 1200  # Hz
        base_f3 = 2500  # Hz

        # Apply ratios to get actual frequencies
        if self.processor.formant_link:
            # In link mode, all formants use the same ratio
            ratio = self.processor.formant_ratios["f1"]
            f1 = base_f1 * ratio
            f2 = base_f2 * ratio
            f3 = base_f3 * ratio
        else:
            # Independent mode
            f1 = base_f1 * self.processor.formant_ratios["f1"]
            f2 = base_f2 * self.processor.formant_ratios["f2"]
            f3 = base_f3 * self.processor.formant_ratios["f3"]

        # Update spectrum display
        self.spectrum_display.update_formant_markers(f1, f2, f3)

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

    def closeEvent(self, event: Any) -> None:  # type: ignore[override]
        """Handle close event.

        Args:
            event: Close event.
        """
        # Stop playback
        self.player.stop()

        # Save config
        self.config.window_width = self.width()
        self.config.window_height = self.height()

        # Save parameter values
        self.config.last_f0_ratio = self.processor.f0_ratio
        self.config.last_formant_ratios = self.processor.formant_ratios.copy()
        self.config.last_formant_link = self.processor.formant_link
        self.config.last_loop_crossfade_ms = self.playback_controls.get_crossfade()

        # Save config to file
        config_path = Path.home() / ".kawaii_voice_changer" / "config.json"
        self.config.save(config_path)

        logger.info("Application closed")
        event.accept()

    @Slot()
    def _export_audio(self) -> None:
        """Export processed audio to file."""
        if self.current_file is None:
            return

        # Create suggested filename
        original_name = self.current_file.stem
        suggested_name = f"{original_name}_processed.wav"

        # Show export dialog with options
        from PySide6.QtWidgets import QDialog, QDialogButtonBox, QRadioButton

        dialog = QDialog(self)
        dialog.setWindowTitle("音声をエクスポート")
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)

        # Export type selection
        export_label = QLabel("エクスポートする音声を選択:")
        layout.addWidget(export_label)

        processed_radio = QRadioButton("処理済み音声")
        processed_radio.setChecked(True)
        layout.addWidget(processed_radio)

        original_radio = QRadioButton("オリジナル音声")
        layout.addWidget(original_radio)

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get export type
            export_processed = processed_radio.isChecked()

            # Show file save dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "音声ファイルを保存",
                str(Path(self.config.last_directory) / suggested_name)
                if self.config.last_directory
                else suggested_name,
                "WAV Files (*.wav);;All Files (*.*)",
            )

            if file_path:
                # Export audio
                if self.processor.export_audio(
                    Path(file_path), processed=export_processed
                ):
                    QMessageBox.information(
                        self,
                        "エクスポート完了",
                        f"音声ファイルを保存しました:\n{file_path}",
                    )
                    logger.info(f"Exported audio to: {file_path}")
                else:
                    QMessageBox.critical(
                        self,
                        "エクスポートエラー",
                        "音声ファイルの保存に失敗しました。",
                    )

    def _update_preset_combo(self) -> None:
        """Update preset combo box with built-in and user presets."""
        self.preset_combo.clear()

        # Add built-in presets
        self.preset_combo.addItem("-- ビルトインプリセット --")
        for preset_name in PRESETS:
            self.preset_combo.addItem(preset_name)

        # Add user presets
        user_presets = self.preset_manager.list_presets()
        if user_presets:
            self.preset_combo.addItem("-- ユーザープリセット --")
            for preset_name in user_presets:
                self.preset_combo.addItem(preset_name)

    @Slot(float, float)
    def _on_loop_region_changed(self, start: float, end: float) -> None:
        """Handle loop region change from waveform display.

        Args:
            start: Loop start time in seconds.
            end: Loop end time in seconds.
        """
        self.player.set_loop_region(start, end)
        logger.info(f"Loop region changed: {start:.2f}s - {end:.2f}s")

    @Slot(int)
    def _on_slot_clicked(self, index: int) -> None:
        """Handle slot button click.

        Args:
            index: Slot index (0-3).
        """
        # Update button states
        for i, button in enumerate(self.slot_buttons):
            button.setChecked(i == index)

        # Set current slot
        self.settings_manager.set_current_slot(index)

        # Load settings from slot if not empty
        settings = self.settings_manager.load_from_slot(index)
        if settings:
            # Apply settings
            self.processor.set_parameters(settings)

            # Update UI
            self.f0_slider.set_value(settings["f0_ratio"])
            for formant, ratio in settings["formant_ratios"].items():
                if formant in self.formant_sliders:
                    self.formant_sliders[formant].set_value(ratio)
            self.link_checkbox.setChecked(settings["formant_link"])
            self._update_formant_display()

            logger.info(f"Loaded settings from slot {index + 1}")
        else:
            logger.info(f"Switched to empty slot {index + 1}")

    def _on_slot_context_menu(self, index: int, pos: Any) -> None:
        """Show context menu for slot button.

        Args:
            index: Slot index.
            pos: Global position for menu.
        """
        menu = QMenu(self)

        # Save action
        save_action = QAction("現在の設定を保存", self)
        save_action.triggered.connect(lambda: self._save_to_slot(index))
        menu.addAction(save_action)

        # Load action (only if slot is not empty)
        slot_info = self.settings_manager.get_slot_info(index)
        if slot_info and not slot_info["is_empty"]:
            load_action = QAction("設定を読み込み", self)
            load_action.triggered.connect(lambda: self._on_slot_clicked(index))
            menu.addAction(load_action)

            # Clear action
            menu.addSeparator()
            clear_action = QAction("クリア", self)
            clear_action.triggered.connect(lambda: self._clear_slot(index))
            menu.addAction(clear_action)

        menu.exec(pos)

    def _save_to_slot(self, index: int) -> None:
        """Save current settings to a slot.

        Args:
            index: Slot index.
        """
        # Get current parameters
        params = self.processor.get_parameters()

        # Save to slot
        if self.settings_manager.save_to_slot(
            index,
            f0_ratio=params["f0_ratio"],
            formant_ratios=params["formant_ratios"],
            formant_link=params["formant_link"],
        ):
            # Update button appearance
            slot_info = self.settings_manager.get_slot_info(index)
            if slot_info:
                button = self.slot_buttons[index]
                button.setStyleSheet("""
                    QPushButton {
                        font-weight: bold;
                    }
                    QPushButton:checked {
                        background-color: #2196F3;
                        color: white;
                    }
                """)

            logger.info(f"Saved settings to slot {index + 1}")
            QMessageBox.information(
                self,
                "保存完了",
                f"現在の設定をスロット {index + 1} に保存しました。",
            )

    def _clear_slot(self, index: int) -> None:
        """Clear a settings slot.

        Args:
            index: Slot index.
        """
        reply = QMessageBox.question(
            self,
            "スロットをクリア",
            f"スロット {index + 1} をクリアしますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes and self.settings_manager.clear_slot(
            index
        ):
            # Reset button appearance
            button = self.slot_buttons[index]
            button.setStyleSheet("")

            logger.info(f"Cleared slot {index + 1}")

    def _setup_keyboard_shortcuts(self) -> None:
        """Set up keyboard shortcuts."""
        # Playback shortcuts
        play_shortcut = QShortcut(QKeySequence("Space"), self)
        play_shortcut.activated.connect(self._on_play_clicked)

        stop_shortcut = QShortcut(QKeySequence("Escape"), self)
        stop_shortcut.activated.connect(self._on_stop_clicked)

        # Loop toggle
        loop_shortcut = QShortcut(QKeySequence("L"), self)
        loop_shortcut.activated.connect(
            lambda: self.playback_controls.loop_checkbox.toggle()
        )

        # Parameter reset shortcuts
        reset_f0_shortcut = QShortcut(QKeySequence("Ctrl+1"), self)
        reset_f0_shortcut.activated.connect(lambda: self.f0_slider.reset())

        reset_f1_shortcut = QShortcut(QKeySequence("Ctrl+2"), self)
        reset_f1_shortcut.activated.connect(lambda: self.formant_sliders["f1"].reset())

        reset_f2_shortcut = QShortcut(QKeySequence("Ctrl+3"), self)
        reset_f2_shortcut.activated.connect(lambda: self.formant_sliders["f2"].reset())

        reset_f3_shortcut = QShortcut(QKeySequence("Ctrl+4"), self)
        reset_f3_shortcut.activated.connect(lambda: self.formant_sliders["f3"].reset())

        # Formant link toggle
        link_shortcut = QShortcut(QKeySequence("F"), self)
        link_shortcut.activated.connect(lambda: self.link_checkbox.toggle())

        # Settings slot shortcuts
        for i in range(4):
            slot_shortcut = QShortcut(QKeySequence(f"{i + 1}"), self)
            slot_shortcut.activated.connect(lambda idx=i: self._on_slot_clicked(idx))

            save_slot_shortcut = QShortcut(QKeySequence(f"Ctrl+Shift+{i + 1}"), self)
            save_slot_shortcut.activated.connect(lambda idx=i: self._save_to_slot(idx))

        # Volume shortcuts
        vol_up_shortcut = QShortcut(QKeySequence("Up"), self)
        vol_up_shortcut.activated.connect(self._increase_volume)

        vol_down_shortcut = QShortcut(QKeySequence("Down"), self)
        vol_down_shortcut.activated.connect(self._decrease_volume)

        # Export shortcut is already in menu (Ctrl+S)

        # Clear loop region
        clear_loop_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        clear_loop_shortcut.activated.connect(lambda: self.player.clear_loop_region())

    def _increase_volume(self) -> None:
        """Increase volume by 10%."""
        current = self.playback_controls.volume_slider.value()
        self.playback_controls.volume_slider.setValue(min(100, current + 10))

    def _decrease_volume(self) -> None:
        """Decrease volume by 10%."""
        current = self.playback_controls.volume_slider.value()
        self.playback_controls.volume_slider.setValue(max(0, current - 10))
