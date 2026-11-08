from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from .theme import Borders, Colors, Radii, Typography


class HoverPreviewWidget(QFrame):
    """Clean minimal floating hover preview popup for Mind-Map nodes."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("hover_preview_card")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setFixedWidth(260)

        self.setStyleSheet(
            f"""
            QFrame#hover_preview_card {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER};
                border-radius: {Radii.MD}px;
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)

        self.title_lbl = QLabel(self)
        self.title_lbl.setFont(Typography.heading(12))
        self.title_lbl.setStyleSheet(f"color: {Colors.TEXT};")
        self.title_lbl.setWordWrap(True)
        header_layout.addWidget(self.title_lbl, 1)

        self.tag_badge = QLabel(self)
        self.tag_badge.setFont(Typography.body(9))
        self.tag_badge.setStyleSheet(
            f"""
            background-color: {Colors.SURFACE_HOVER};
            color: {Colors.TEXT_MUTED};
            border: 1px solid {Colors.BORDER};
            border-radius: 4px;
            padding: 1px 6px;
            """
        )
        self.tag_badge.hide()
        header_layout.addWidget(self.tag_badge)

        layout.addLayout(header_layout)

        # Preview content
        self.content_lbl = QLabel(self)
        self.content_lbl.setFont(Typography.body(11))
        self.content_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; line-height: 140%;")
        self.content_lbl.setWordWrap(True)
        layout.addWidget(self.content_lbl)

        self.hide()

    def show_preview(self, title: str, preview_text: str, tag: str, global_pos: QPoint):
        self.title_lbl.setText(title)
        clean_text = preview_text.strip() if preview_text else "Henüz bir içerik girilmemiş..."
        if len(clean_text) > 160:
            clean_text = clean_text[:157] + "..."
        self.content_lbl.setText(clean_text)

        if tag:
            self.tag_badge.setText(tag)
            self.tag_badge.show()
        else:
            self.tag_badge.hide()

        self.adjustSize()
        self.move(global_pos.x() + 15, global_pos.y() + 15)
        self.show()
        self.raise_()
