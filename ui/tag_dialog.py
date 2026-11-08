from PyQt6.QtCore import QRectF, QSize, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QColorDialog,
    QFrame,
    QGraphicsItem,
    QGraphicsScene,
    QGraphicsView,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from core.i18n import t

from .components import (
    BrutalButton,
    BrutalCard,
    BrutalInput,
    BrutalModal,
    BrutalTag,
    _PressHoverAnimator,
)
from .node_item import NodeItem
from .theme import (
    Borders,
    Colors,
    Metrics,
    Radii,
    Spacing,
    Typography,
    get_pattern_pixmap,
    readable_ink,
    resolve_accent_color,
    resolve_node_bg,
)


class _ColorSwatchButton(QPushButton):
    """Clean color swatch button with subtle border and checkmark."""

    def __init__(self, hex_code: str, tooltip: str = "", parent=None):
        super().__init__("", parent)
        self.hex_code = hex_code
        self.is_active_swatch = False
        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(30, 30)
        self._motion = _PressHoverAnimator(self)

    def set_active_swatch(self, active: bool):
        self.is_active_swatch = active
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(30, 30)

    def enterEvent(self, event):
        self._motion.set_hovered(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._motion.set_hovered(False)
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = QRectF(1.0, 1.0, float(self.width()) - 2.0, float(self.height()) - 2.0)
        border_col = Colors.PRIMARY if self.is_active_swatch else Colors.BORDER
        border_w = 2.0 if self.is_active_swatch else 1.0

        painter.setPen(QPen(QColor(border_col), border_w))
        painter.setBrush(QBrush(QColor(self.hex_code)))
        painter.drawRoundedRect(rect, Radii.SM, Radii.SM)

        if self.is_active_swatch:
            ink = readable_ink(self.hex_code)
            check_pen = QPen(ink, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(check_pen)
            cx, cy = rect.center().x(), rect.center().y()
            check_path = QPainterPath()
            check_path.moveTo(cx - 4, cy)
            check_path.lineTo(cx - 1, cy + 3)
            check_path.lineTo(cx + 5, cy - 3)
            painter.drawPath(check_path)

        painter.end()


class TagDialog(BrutalModal):
    """Clean Appearance Modal matching Obsidian style."""

    def __init__(self, current_color, current_tag, current_bg_color, parent=None):
        super().__init__(t("box_appearance"), parent)
        self.setFixedSize(700, 480)

        self.selected_bg_color = resolve_node_bg(current_bg_color or "", seed="preview")
        self.selected_color = resolve_accent_color(
            current_color or "",
            seed=current_tag or "tag",
            avoid_bg=self.selected_bg_color,
        )
        self.selected_tag = current_tag if current_tag else ""

        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.XL)
        root.setSpacing(Spacing.MD)

        # Header
        header_row = QHBoxLayout()
        header_row.setSpacing(Spacing.MD)

        title_lbl = QLabel(t("box_appearance"))
        title_lbl.setFont(Typography.display(Typography.SIZE_PAGE_TITLE))
        title_lbl.setStyleSheet(f"color: {Colors.TEXT}; background: transparent;")
        header_row.addWidget(title_lbl)
        header_row.addStretch()
        root.addLayout(header_row)

        # Body
        body_layout = QHBoxLayout()
        body_layout.setSpacing(Spacing.MD)

        # Left Controls Card
        left_card = BrutalCard(fill_color=Colors.SURFACE, padding=Spacing.MD)
        left_layout = QVBoxLayout(left_card)
        left_layout.setSpacing(Spacing.SM + 2)

        tag_lbl = QLabel(t("tag_label_text"))
        tag_lbl.setFont(Typography.label(Typography.SIZE_LABEL))
        tag_lbl.setStyleSheet(f"color: {Colors.TEXT}; background: transparent;")
        left_layout.addWidget(tag_lbl)

        self.tag_input = BrutalInput(
            text=self.selected_tag,
            placeholder=t("tag_placeholder"),
            fill_color=Colors.SURFACE,
            face_height=32,
        )
        self.tag_input.textChanged.connect(self.update_preview)
        left_layout.addWidget(self.tag_input)

        accent_lbl = QLabel(t("theme_color"))
        accent_lbl.setFont(Typography.label(Typography.SIZE_LABEL))
        accent_lbl.setStyleSheet(f"color: {Colors.TEXT}; background: transparent;")
        left_layout.addWidget(accent_lbl)

        palette_options = [
            ("#7c3aed", "Violet"),
            ("#3b82f6", "Blue"),
            ("#10b981", "Emerald"),
            ("#f59e0b", "Amber"),
            ("#ef4444", "Rose"),
            ("#64748b", "Slate"),
        ]

        self._accent_swatches: list[_ColorSwatchButton] = []
        accent_grid = QGridLayout()
        accent_grid.setSpacing(Spacing.SM)
        for idx, (hex_code, name) in enumerate(palette_options):
            sw = _ColorSwatchButton(hex_code, tooltip=name)
            sw.clicked.connect(lambda checked, c=hex_code: self.select_color(c))
            accent_grid.addWidget(sw, 0, idx)
            self._accent_swatches.append(sw)
        left_layout.addLayout(accent_grid)

        # Custom color button
        custom_bg_row = QHBoxLayout()
        custom_bg_row.setSpacing(Spacing.SM)
        self.btn_bg_color = BrutalButton(
            t("select_color"),
            variant="surface",
            min_face_height=30,
        )
        self.btn_bg_color.clicked.connect(self.select_bg_color)
        custom_bg_row.addWidget(self.btn_bg_color)
        custom_bg_row.addStretch()
        left_layout.addLayout(custom_bg_row)

        left_layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(Spacing.SM)
        self.btn_cancel = BrutalButton(t("cancel"), variant="surface", min_face_height=32)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_apply = BrutalButton(t("apply"), variant="primary", min_face_height=32)
        self.btn_apply.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_apply)
        left_layout.addLayout(btn_layout)

        body_layout.addWidget(left_card, 3)

        # Right Live Preview Card
        right_card = BrutalCard(
            fill_color=Colors.CANVAS,
            padding=Spacing.MD,
        )
        right_layout = QVBoxLayout(right_card)
        right_layout.setSpacing(Spacing.SM)

        preview_lbl = QLabel(t("live_preview"))
        preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_lbl.setFont(Typography.label(Typography.SIZE_LABEL))
        preview_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; background: transparent;")
        right_layout.addWidget(preview_lbl)

        self.preview_scene = QGraphicsScene()
        self.preview_scene.setBackgroundBrush(
            QBrush(get_pattern_pixmap(Colors.CANVAS, "dot", Metrics.GRID_DOT_SPACING))
        )

        self.preview_view = QGraphicsView(self.preview_scene)
        self.preview_view.setFrameShape(QFrame.Shape.NoFrame)
        self.preview_view.setStyleSheet(
            f"border: 1px solid {Colors.BORDER}; border-radius: {Radii.MD}px; background: {Colors.CANVAS};"
        )
        self.preview_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        class MockScene:
            def update_edges(self):
                pass
            def update_edges_for_node(self, node):
                pass

        self.preview_node = NodeItem(
            "mock_id",
            t("sample_note_title"),
            0,
            0,
            color=self.selected_color,
            tag=self.selected_tag,
            parent_scene=MockScene(),
            width=200,
            height=100,
            bg_color=self.selected_bg_color,
            is_favorite=True,
        )
        self.preview_node.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.preview_node.setSelected(True)
        self.preview_scene.addItem(self.preview_node)

        right_layout.addWidget(self.preview_view, 1)
        body_layout.addWidget(right_card, 3)

        root.addLayout(body_layout, 1)

        self._sync_swatch_indicators()
        self.update_preview()

    def _sync_swatch_indicators(self):
        for sw in self._accent_swatches:
            sw.set_active_swatch(sw.hex_code.lower() == self.selected_color.lower())

    def select_color(self, hex_code):
        self.selected_color = hex_code
        self._sync_swatch_indicators()
        self.update_preview()

    def select_bg_color(self):
        color = QColorDialog.getColor(QColor(self.selected_color), self, t("box_bg_color"))
        if color.isValid():
            self.selected_color = color.name()
            self._sync_swatch_indicators()
            self.update_preview()

    def update_preview(self, text=None):
        if text is not None:
            self.selected_tag = text
        self.preview_node.set_color_and_tag(self.selected_color, self.selected_tag)
        self.preview_node.set_bg_color(self.selected_bg_color)
        self.preview_scene.update()

    def get_result(self):
        return self.selected_color, self.selected_tag, self.selected_bg_color
