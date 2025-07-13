"""Preset management dialog."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
)

from ...core import Preset

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


class PresetDialog(QDialog):
    """Dialog for saving custom presets."""

    # Signals
    preset_saved = Signal(str, Preset)  # name, preset

    def __init__(
        self,
        f0_ratio: float,
        formant_ratios: dict[str, float],
        formant_link: bool,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize preset dialog.

        Args:
            f0_ratio: Current F0 ratio.
            formant_ratios: Current formant ratios.
            formant_link: Current formant link state.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.f0_ratio = f0_ratio
        self.formant_ratios = formant_ratios
        self.formant_link = formant_link

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up user interface."""
        self.setWindowTitle("プリセットを保存")
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Preset info group
        info_group = QGroupBox("プリセット情報")
        info_layout = QFormLayout(info_group)

        # Name input
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例: カワイイボイス")
        info_layout.addRow("名前:", self.name_edit)

        # Description input
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("プリセットの説明を入力...")
        self.desc_edit.setMaximumHeight(80)
        info_layout.addRow("説明:", self.desc_edit)

        layout.addWidget(info_group)

        # Current parameters group
        params_group = QGroupBox("現在のパラメータ")
        params_layout = QVBoxLayout(params_group)

        # F0 ratio
        f0_label = QLabel(f"基本周波数 (F0): {self.f0_ratio:.2f}")
        params_layout.addWidget(f0_label)

        # Formant ratios
        formant_text = "フォルマント: "
        if self.formant_link:
            formant_text += f"連動モード (全て {self.formant_ratios['f1']:.2f})"
        else:
            formant_text += "独立モード\n"
            for name, ratio in self.formant_ratios.items():
                formant_text += f"  {name.upper()}: {ratio:.2f}\n"
        formant_label = QLabel(formant_text)
        params_layout.addWidget(formant_label)

        layout.addWidget(params_group)

        # Dialog buttons
        button_layout = QHBoxLayout()
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self._on_save)
        self.buttons.rejected.connect(self.reject)
        button_layout.addWidget(self.buttons)

        layout.addLayout(button_layout)

        # Focus on name field
        self.name_edit.setFocus()

    def _on_save(self) -> None:
        """Handle save button click."""
        name = self.name_edit.text().strip()

        if not name:
            QMessageBox.warning(
                self,
                "入力エラー",
                "プリセット名を入力してください。",
            )
            self.name_edit.setFocus()
            return

        # Create preset
        preset = Preset(
            name=name,
            description=self.desc_edit.toPlainText().strip(),
            f0_ratio=self.f0_ratio,
            formant_ratios=self.formant_ratios.copy(),
            formant_link=self.formant_link,
        )

        # Emit signal and close
        self.preset_saved.emit(name, preset)
        self.accept()

    def get_preset(self) -> tuple[str, Preset] | None:
        """Get the created preset.

        Returns:
            Tuple of (name, preset) if saved, None if cancelled.
        """
        if self.exec() == QDialog.DialogCode.Accepted:
            name = self.name_edit.text().strip()
            preset = Preset(
                name=name,
                description=self.desc_edit.toPlainText().strip(),
                f0_ratio=self.f0_ratio,
                formant_ratios=self.formant_ratios.copy(),
                formant_link=self.formant_link,
            )
            return name, preset
        return None
