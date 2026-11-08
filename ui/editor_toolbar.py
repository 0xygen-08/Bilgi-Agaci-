from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QWidget

from core.i18n import t

from .components import BrutalIconButton
from .theme import Metrics, Spacing, Typography


class EditorToolbar(QWidget):
    """Sleek minimalist formatting toolbar matching Obsidian."""

    format_bold_signal = pyqtSignal()
    format_italic_signal = pyqtSignal()
    format_h1_signal = pyqtSignal()
    format_h2_signal = pyqtSignal()
    format_bullet_list_signal = pyqtSignal()
    insert_image_signal = pyqtSignal()
    format_color_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        btn_h = 28

        self.btn_bold = BrutalIconButton("B", variant="surface", size=btn_h, min_width=28)
        self.btn_bold.setFont(Typography.display(11))
        self.btn_bold.setToolTip(t("bold_tooltip"))
        self.btn_bold.setCheckable(True)
        self.btn_bold.clicked.connect(self.format_bold_signal.emit)

        self.btn_italic = BrutalIconButton("I", variant="surface", size=btn_h, min_width=28)
        italic_font = Typography.heading(11)
        italic_font.setItalic(True)
        self.btn_italic.setFont(italic_font)
        self.btn_italic.setToolTip(t("italic_tooltip"))
        self.btn_italic.setCheckable(True)
        self.btn_italic.clicked.connect(self.format_italic_signal.emit)

        self.btn_h1 = BrutalIconButton("H1", variant="surface", size=btn_h, min_width=32)
        self.btn_h1.setToolTip(t("h1_tooltip"))
        self.btn_h1.setCheckable(True)
        self.btn_h1.clicked.connect(self.format_h1_signal.emit)

        self.btn_h2 = BrutalIconButton("H2", variant="surface", size=btn_h, min_width=32)
        self.btn_h2.setToolTip(t("h2_tooltip"))
        self.btn_h2.setCheckable(True)
        self.btn_h2.clicked.connect(self.format_h2_signal.emit)

        self.btn_list = BrutalIconButton(t("list_btn"), variant="surface", size=btn_h, min_width=44)
        self.btn_list.setToolTip(t("list_tooltip"))
        self.btn_list.setCheckable(True)
        self.btn_list.clicked.connect(self.format_bullet_list_signal.emit)

        self.btn_image = BrutalIconButton(t("image_btn"), variant="surface", size=btn_h, min_width=48)
        self.btn_image.setToolTip(t("image_tooltip"))
        self.btn_image.clicked.connect(self.insert_image_signal.emit)

        self.btn_color = BrutalIconButton(t("color_btn"), variant="surface", size=btn_h, min_width=44)
        self.btn_color.setToolTip(t("color_tooltip"))
        self.btn_color.clicked.connect(self.format_color_signal.emit)

        layout.addWidget(self.btn_bold)
        layout.addWidget(self.btn_italic)
        layout.addWidget(self.btn_h1)
        layout.addWidget(self.btn_h2)
        layout.addWidget(self.btn_list)
        layout.addWidget(self.btn_image)
        layout.addWidget(self.btn_color)
        layout.addStretch()

    def update_states(self, is_bold, is_italic, is_h1, is_h2, is_list):
        for btn, state in (
            (self.btn_bold, is_bold),
            (self.btn_italic, is_italic),
            (self.btn_h1, is_h1),
            (self.btn_h2, is_h2),
            (self.btn_list, is_list),
        ):
            btn.blockSignals(True)
            btn.setChecked(state)
            btn.blockSignals(False)
            btn.update()
