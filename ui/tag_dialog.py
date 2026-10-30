from PyQt6.QtCore import QRectF, QSize, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
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
    SparkleWidget,
    _PressHoverAnimator,
)
from .node_item import NodeItem
from .theme import (
    Borders,
    Colors,
    Metrics,
    Motion,
    Radii,
    Shadows,
    Spacing,
    Typography,
    get_pattern_pixmap,
    readable_ink,
    resolve_accent_color,
    resolve_node_bg,
)


class _ColorSwatchButton(QPushButton):
    """Chunky Neo-Brutalist color swatch square with black border & checkmark."""

    def __init__(self, hex_code: str, tooltip: str = "", parent=None):
        super().__init__("", parent)
        self.hex_code = hex_code
        self.is_active_swatch = False
        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(Metrics.TOUCH_MIN, Metrics.TOUCH_MIN)
        self._motion = _PressHoverAnimator(self, shadow_px=Shadows.SM, hover_px=Shadows.HOVER_SHIFT)

    def set_active_swatch(self, active: bool):
        self.is_active_swatch = active
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(Metrics.TOUCH_MIN, Metrics.TOUCH_MIN)

    def enterEvent(self, event):
        self._motion.set_hovered(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._motion.set_hovered(False)
        self._motion.set_pressed(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._motion.set_pressed(True)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._motion.set_pressed(False)
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        sz = float(self.width()) - Shadows.SM - 4.0
        base = QRectF(2.0, 2.0, sz, sz)
        shadow = base.translated(float(Shadows.SM), float(Shadows.SM))
        face = base.translated(self._motion.dx, self._motion.dy)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(Colors.BLACK)))
        painter.drawRoundedRect(shadow, Radii.SM + 2, Radii.SM + 2)

        border_w = Borders.DEFAULT if self.is_active_swatch else Borders.THIN
        painter.setPen(QPen(QColor(Colors.BLACK), border_w))
        painter.setBrush(QBrush(QColor(self.hex_code)))
        painter.drawRoundedRect(face, Radii.SM + 2, Radii.SM + 2)

        if self.is_active_swatch:
            painter.setFont(Typography.heading(Typography.SIZE_BODY + 2))
            painter.setPen(QPen(readable_ink(self.hex_code)))
            painter.drawText(face, Qt.AlignmentFlag.AlignCenter, "✓")

        painter.end()


class TagDialog(BrutalModal):
    """
    Neo-Brutalist Box Appearance Modal:
    - Thick 3px borders, 6px zero-blur hard shadows, bold uppercase headers
    - Quick Neo-Brutalist pastel swatches for both Tag Pill and Card Fill + custom picker
    - Live NodeItem preview rendered on the Cream (#FBFAE8) dotted-grid canvas
    """

    def __init__(self, current_color, current_tag, current_bg_color, parent=None):
        super().__init__(t("box_appearance"), parent)
        self.setFixedSize(760, 540)

        self.selected_bg_color = resolve_node_bg(current_bg_color or "", seed="preview")
        self.selected_color = resolve_accent_color(
            current_color or "",
            seed=current_tag or "tag",
            avoid_bg=self.selected_bg_color,
        )
        self.selected_tag = current_tag if current_tag else ""

        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.XL)
        root.setSpacing(Spacing.LG)

        # --- Modal Header ---
        header_row = QHBoxLayout()
        header_row.setSpacing(Spacing.MD)
        header_row.addWidget(SparkleWidget(22))

        title_lbl = QLabel(t("box_appearance").upper())
        title_lbl.setFont(Typography.display(Typography.SIZE_EDITOR_TITLE))
        title_lbl.setStyleSheet(f"color: {Colors.BLACK}; background: transparent;")
        header_row.addWidget(title_lbl)

        header_row.addWidget(
            BrutalTag("NEO-STYLE", fill_color=Colors.PINK, tilt_deg=Motion.STICKER_TILT_DEG)
        )
        header_row.addStretch()
        root.addLayout(header_row)

        # --- Main Two-Column Body ---
        body_layout = QHBoxLayout()
        body_layout.setSpacing(Spacing.LG)

        # Left Controls Card
        left_card = BrutalCard(fill_color=Colors.WHITE, shadow_px=Shadows.LG, padding=Spacing.LG)
        left_layout = QVBoxLayout(left_card)
        left_layout.setSpacing(Spacing.MD)

        tag_lbl = QLabel(t("tag_label_text").upper())
        tag_lbl.setFont(Typography.label(Typography.SIZE_LABEL))
        tag_lbl.setStyleSheet(f"color: {Colors.BLACK}; background: transparent;")
        left_layout.addWidget(tag_lbl)

        self.tag_input = BrutalInput(
            text=self.selected_tag,
            placeholder=t("tag_placeholder"),
            fill_color=Colors.WHITE,
            shadow_px=Shadows.SM,
        )
        self.tag_input.textChanged.connect(self.update_preview)
        left_layout.addWidget(self.tag_input)

        # Tag / Accent Color Swatches
        accent_lbl = QLabel(t("theme_color").upper())
        accent_lbl.setFont(Typography.label(Typography.SIZE_LABEL))
        accent_lbl.setStyleSheet(f"color: {Colors.BLACK}; background: transparent;")
        left_layout.addWidget(accent_lbl)

        palette_options = [
            (Colors.PINK, t("color_pink")),
            (Colors.LIGHT_BLUE, t("color_light_blue")),
            (Colors.GREEN, t("color_green")),
            (Colors.YELLOW, t("color_yellow")),
            (Colors.SOFT_ORANGE, t("color_soft_orange")),
            (Colors.WHITE, t("color_white")),
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

        # Box Fill Color Swatches + Custom Color Picker
        bg_lbl = QLabel(t("box_bg_color").upper())
        bg_lbl.setFont(Typography.label(Typography.SIZE_LABEL))
        bg_lbl.setStyleSheet(f"color: {Colors.BLACK}; background: transparent;")
        left_layout.addWidget(bg_lbl)

        self._bg_swatches: list[_ColorSwatchButton] = []
        bg_grid = QGridLayout()
        bg_grid.setSpacing(Spacing.SM)
        for idx, (hex_code, name) in enumerate(palette_options):
            sw = _ColorSwatchButton(hex_code, tooltip=name)
            sw.clicked.connect(lambda checked, c=hex_code: self._set_bg_swatch(c))
            bg_grid.addWidget(sw, 0, idx)
            self._bg_swatches.append(sw)
        left_layout.addLayout(bg_grid)

        custom_bg_row = QHBoxLayout()
        custom_bg_row.setSpacing(Spacing.SM)
        self.btn_bg_color = BrutalButton(
            t("select_color"),
            variant="secondary",
            shadow_px=Shadows.SM,
            min_face_height=38,
        )
        self.btn_bg_color.clicked.connect(self.select_bg_color)
        custom_bg_row.addWidget(self.btn_bg_color)
        custom_bg_row.addStretch()
        left_layout.addLayout(custom_bg_row)

        left_layout.addStretch()

        # Action Buttons (Destructive/Cancel in Pink, Apply in Yellow)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(Spacing.MD)
        self.btn_cancel = BrutalButton(t("cancel"), variant="danger", shadow_px=Shadows.MD)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_apply = BrutalButton(t("apply"), variant="primary", shadow_px=Shadows.MD)
        self.btn_apply.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_apply)
        left_layout.addLayout(btn_layout)

        body_layout.addWidget(left_card, 3)

        # Right Live Preview Card (with Figma-style corner handles!)
        right_card = BrutalCard(
            fill_color=Colors.CREAM,
            shadow_px=Shadows.LG,
            padding=Spacing.LG,
            selection_handles=True,
        )
        right_layout = QVBoxLayout(right_card)
        right_layout.setSpacing(Spacing.SM)

        preview_lbl = QLabel(t("live_preview").upper())
        preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_lbl.setFont(Typography.label(Typography.SIZE_LABEL))
        preview_lbl.setStyleSheet(f"color: {Colors.BLACK}; background: transparent;")
        right_layout.addWidget(preview_lbl)

        self.preview_scene = QGraphicsScene()
        self.preview_scene.setBackgroundBrush(
            QBrush(get_pattern_pixmap(Colors.CREAM, "dot", Metrics.GRID_DOT_SPACING))
        )

        self.preview_view = QGraphicsView(self.preview_scene)
        self.preview_view.setFrameShape(QFrame.Shape.NoFrame)
        self.preview_view.setStyleSheet(
            f"border: {Borders.THIN}px solid {Colors.BLACK}; border-radius: {Radii.MD}px; background: {Colors.CREAM};"
        )
        self.preview_view.setRenderHint(
            self.preview_view.renderHints() | QPainter.RenderHint.Antialiasing
        )

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
            MockScene(),
            color=self.selected_color,
            tag=self.selected_tag,
            width=210,
            height=110,
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
        for sw in self._bg_swatches:
            sw.set_active_swatch(sw.hex_code.lower() == self.selected_bg_color.lower())

    def select_color(self, hex_code):
        self.selected_color = hex_code
        self._sync_swatch_indicators()
        self.update_preview()

    def _set_bg_swatch(self, hex_code):
        self.selected_bg_color = hex_code
        self._sync_swatch_indicators()
        self.update_preview()

    def select_bg_color(self):
        color = QColorDialog.getColor(QColor(self.selected_bg_color), self, t("box_bg_color"))
        if color.isValid():
            self.selected_bg_color = color.name()
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
