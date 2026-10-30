"""
Reusable Neo-Brutalist UI Component Library for Knowledge Tree.

Every component consumes tokens exclusively from `ui.theme` and implements
authentic Neo-Brutalist visuals:
- 2-3px solid #000000 borders
- Zero-blur hard offset #000000 shadows (3px / 4px / 6px)
- Saturated flat pastel fills (#FE90E8, #C0F7FE, #99E885, #F7CB46, #FFDC8B)
- Snappy 110ms physical hover (-2px, -2px) & press (+shadow, +shadow -> 0 shadow) animations
- Optional sticker rotation (-2.5 deg) and Figma-like selection frame motifs
"""

from PyQt6.QtCore import (
    QEasingCurve,
    QPointF,
    QRectF,
    QSize,
    Qt,
    QVariantAnimation,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFontMetrics,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

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
)


# ---------------------------------------------------------------------------
# Vector Drawing Helpers (Decorative Neo-Brutalist Motifs)
# ---------------------------------------------------------------------------

def draw_sparkle_star(painter: QPainter, cx: float, cy: float, radius: float, color: str = Colors.BLACK):
    """Draw a crisp 4-point Neo-Brutalist sparkle star (✦)."""
    painter.save()
    path = QPainterPath()
    inner = radius * 0.22
    path.moveTo(cx, cy - radius)
    path.quadTo(cx + inner * 0.5, cy - inner * 0.5, cx + radius, cy)
    path.quadTo(cx + inner * 0.5, cy + inner * 0.5, cx, cy + radius)
    path.quadTo(cx - inner * 0.5, cy + inner * 0.5, cx - radius, cy)
    path.quadTo(cx - inner * 0.5, cy - inner * 0.5, cx, cy - radius)
    path.closeSubpath()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(color)))
    painter.drawPath(path)
    painter.restore()


def draw_striped_circle_motif(
    painter: QPainter,
    cx: float,
    cy: float,
    radius: float,
    fill_hex: str = Colors.GREEN,
):
    """
    Draw the signature circle from the reference image: pastel circle with
    offset black outline arc + triple diagonal black stripes across it.
    """
    painter.save()
    # Offset black circle behind
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(Colors.BLACK)))
    painter.drawEllipse(QPointF(cx - 2.5, cy + 3.0), radius, radius)

    # Pastel circle
    painter.setPen(QPen(QColor(Colors.BLACK), Borders.THIN))
    painter.setBrush(QBrush(QColor(fill_hex)))
    painter.drawEllipse(QPointF(cx, cy), radius, radius)

    # Triple diagonal black stripes
    stripe_pen = QPen(
        QColor(Colors.BLACK),
        max(2.5, radius * 0.16),
        Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.SquareCap,
    )
    painter.setPen(stripe_pen)
    span = radius * 1.32
    gap = radius * 0.30
    for offset in (-gap, 0.0, gap):
        perp_x = offset * 0.7071
        perp_y = -offset * 0.7071
        painter.drawLine(
            QPointF(cx - span + perp_x, cy - span + perp_y),
            QPointF(cx + span + perp_x, cy + span + perp_y),
        )
    painter.restore()


def draw_crosshair_motif(painter: QPainter, origin_x: float, origin_y: float, cell: float = 26.0):
    """
    Draw the 2x2 intersection crosshair grid with black dots and overlapping
    pink & tilted yellow mini sticker cards from the reference image.
    """
    painter.save()
    line_pen = QPen(QColor(Colors.BLACK), 1.6)
    painter.setPen(line_pen)

    x1 = origin_x + cell
    x2 = origin_x + cell * 2.1
    y1 = origin_y + cell
    y2 = origin_y + cell * 2.1
    total = cell * 3.1

    painter.drawLine(QPointF(x1, origin_y), QPointF(x1, origin_y + total))
    painter.drawLine(QPointF(x2, origin_y), QPointF(x2, origin_y + total))
    painter.drawLine(QPointF(origin_x, y1), QPointF(origin_x + total, y1))
    painter.drawLine(QPointF(origin_x, y2), QPointF(origin_x + total, y2))

    # Intersection black dots
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(Colors.BLACK)))
    painter.drawEllipse(QPointF(x1, y1), 5.0, 5.0)
    painter.drawEllipse(QPointF(x1, y2), 3.2, 3.2)
    painter.drawEllipse(QPointF(x2, y2), 5.0, 5.0)

    # Overlapping Pink + rotated Yellow mini sticker squares at top-right intersection
    card_sz = cell * 1.15
    pink_rect = QRectF(x2 - card_sz * 0.35, origin_y + 2, card_sz, card_sz)
    painter.setBrush(QBrush(QColor(Colors.BLACK)))
    painter.drawRoundedRect(pink_rect.translated(3, 3), 6, 6)
    painter.setPen(QPen(QColor(Colors.BLACK), Borders.THIN))
    painter.setBrush(QBrush(QColor(Colors.PINK)))
    painter.drawRoundedRect(pink_rect, 6, 6)

    painter.translate(pink_rect.center().x() + 10, pink_rect.center().y() - 3)
    painter.rotate(14.0)
    yellow_rect = QRectF(-card_sz * 0.5, -card_sz * 0.5, card_sz, card_sz)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(Colors.BLACK)))
    painter.drawRoundedRect(yellow_rect.translated(3, 3), 6, 6)
    painter.setPen(QPen(QColor(Colors.BLACK), Borders.THIN))
    painter.setBrush(QBrush(QColor(Colors.YELLOW)))
    painter.drawRoundedRect(yellow_rect, 6, 6)
    painter.restore()


def draw_selection_frame(painter: QPainter, rect: QRectF, handle_size: float = Metrics.SELECTION_HANDLE):
    """
    Draw a Figma-like thin black selection rectangle with small white square
    handles at all four corners.
    """
    painter.save()
    painter.setPen(QPen(QColor(Colors.BLACK), Borders.THIN))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRect(rect)

    half = handle_size / 2.0
    painter.setBrush(QBrush(QColor(Colors.WHITE)))
    painter.setPen(QPen(QColor(Colors.BLACK), Borders.THIN))
    corners = (
        rect.topLeft(),
        rect.topRight(),
        rect.bottomLeft(),
        rect.bottomRight(),
    )
    for pt in corners:
        painter.drawRect(QRectF(pt.x() - half, pt.y() - half, handle_size, handle_size))
    painter.restore()


# ---------------------------------------------------------------------------
# Animated Interactive Mixin Helper
# ---------------------------------------------------------------------------

class _PressHoverAnimator:
    """Manages snappy 110ms hover (-2,-2) and press (+shadow,+shadow) offsets."""

    def __init__(self, widget: QWidget, shadow_px: int = Shadows.MD, hover_px: int = Shadows.HOVER_SHIFT):
        self._widget = widget
        self.shadow_px = float(shadow_px)
        self.hover_px = float(hover_px)
        self.dx = 0.0
        self.dy = 0.0
        self._hovered = False
        self._pressed = False

        self._anim = QVariantAnimation(widget)
        self._anim.setDuration(Motion.FAST_MS)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_step)
        self._start_dx = 0.0
        self._start_dy = 0.0
        self._target_dx = 0.0
        self._target_dy = 0.0

    def _on_step(self, progress):
        p = float(progress)
        self.dx = self._start_dx + (self._target_dx - self._start_dx) * p
        self.dy = self._start_dy + (self._target_dy - self._start_dy) * p
        self._widget.update()

    def _animate_to(self, tx: float, ty: float):
        if abs(self._target_dx - tx) < 0.01 and abs(self._target_dy - ty) < 0.01:
            return
        self._anim.stop()
        self._start_dx = self.dx
        self._start_dy = self.dy
        self._target_dx = tx
        self._target_dy = ty
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()

    def set_hovered(self, hovered: bool):
        self._hovered = hovered
        self._sync()

    def set_pressed(self, pressed: bool):
        self._pressed = pressed
        self._sync()

    def _sync(self):
        if self._pressed:
            self._animate_to(self.shadow_px, self.shadow_px)
        elif self._hovered:
            self._animate_to(-self.hover_px, -self.hover_px)
        else:
            self._animate_to(0.0, 0.0)


# ---------------------------------------------------------------------------
# 1. BrutalButton
# ---------------------------------------------------------------------------

VARIANT_FILLS = {
    "primary": (Colors.YELLOW, Colors.SOFT_ORANGE),
    "add": (Colors.GREEN, Colors.YELLOW),
    "success": (Colors.GREEN, Colors.YELLOW),
    "danger": (Colors.PINK, Colors.SOFT_ORANGE),
    "accent": (Colors.PINK, Colors.SOFT_ORANGE),
    "secondary": (Colors.SOFT_ORANGE, Colors.YELLOW),
    "surface": (Colors.WHITE, Colors.SOFT_ORANGE),
    "info": (Colors.LIGHT_BLUE, Colors.WHITE),
    "nav": (Colors.WHITE, Colors.SOFT_ORANGE),
}


class BrutalButton(QPushButton):
    """
    Reusable Neo-Brutalist button with thick black border, zero-blur hard shadow,
    snappy hover lift (-2px, -2px), and physical press animation.
    """

    def __init__(
        self,
        text: str = "",
        variant: str = "primary",
        parent: QWidget | None = None,
        *,
        uppercase: bool = True,
        align_left: bool = False,
        show_nav_dot: bool | None = None,
        pad_x: int = Spacing.LG,
        shadow_px: int = Shadows.MD,
        min_face_height: int = Metrics.TOUCH_MIN,
        tilt_deg: float = 0.0,
    ):
        super().__init__(text, parent)
        self.variant = variant
        self.uppercase = uppercase
        self.align_left = align_left
        self.show_nav_dot = align_left if show_nav_dot is None else show_nav_dot
        self.pad_x = pad_x
        self.shadow_px = shadow_px
        self.hover_px = Shadows.HOVER_SHIFT
        self.min_face_height = min_face_height
        self.tilt_deg = tilt_deg
        self._custom_fill: str | None = None

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(Typography.label(Typography.SIZE_BUTTON))
        self._motion = _PressHoverAnimator(self, shadow_px=shadow_px, hover_px=self.hover_px)

        total_h = self.min_face_height + self.hover_px + self.shadow_px + 2
        self.setMinimumHeight(total_h)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def set_custom_fill(self, hex_color: str | None):
        self._custom_fill = hex_color
        self.update()

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        label = self.text().upper() if self.uppercase else self.text()
        text_w = fm.horizontalAdvance(label)
        extra_x = self.pad_x * 2 + self.hover_px + self.shadow_px + 8
        total_h = self.min_face_height + self.hover_px + self.shadow_px + 2
        return QSize(max(Metrics.TOUCH_MIN, text_w + extra_x), total_h)

    def enterEvent(self, event):
        if self.isEnabled():
            self._motion.set_hovered(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._motion.set_hovered(False)
        self._motion.set_pressed(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.isEnabled():
            self._motion.set_pressed(True)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._motion.set_pressed(False)
        super().mouseReleaseEvent(event)

    def _resolve_fill(self) -> str:
        if self._custom_fill:
            return self._custom_fill
        base_fill, hover_fill = VARIANT_FILLS.get(self.variant, VARIANT_FILLS["primary"])
        if self.isCheckable() and self.isChecked():
            return Colors.YELLOW if self.variant == "nav" else Colors.PINK
        if self._motion._hovered and not self._motion._pressed:
            return hover_fill
        return base_fill

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        top_pad = float(self.hover_px + 1)
        left_pad = float(self.hover_px + 1)
        face_w = max(10.0, float(self.width()) - left_pad - self.shadow_px - 2.0)
        face_h = max(10.0, float(self.height()) - top_pad - self.shadow_px - 2.0)

        base_rect = QRectF(left_pad, top_pad, face_w, face_h)
        shadow_rect = base_rect.translated(float(self.shadow_px), float(self.shadow_px))

        dx = self._motion.dx
        dy = self._motion.dy
        if self.isCheckable() and self.isChecked() and not self._motion._pressed and not self._motion._hovered:
            # Subtle active prominence for checked navigation buttons
            dx, dy = -1.0, -1.0
        face_rect = base_rect.translated(dx, dy)

        if abs(self.tilt_deg) > 0.05:
            center = base_rect.center()
            painter.translate(center)
            painter.rotate(self.tilt_deg)
            painter.translate(-center)

        # 1. Hard zero-blur black offset shadow
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(Colors.BLACK)))
        painter.drawRoundedRect(shadow_rect, Radii.MD, Radii.MD)

        # 2. Saturated pastel face + thick solid black border
        fill_hex = self._resolve_fill()
        painter.setPen(QPen(QColor(Colors.BLACK), Borders.DEFAULT))
        painter.setBrush(QBrush(QColor(fill_hex)))
        painter.drawRoundedRect(face_rect, Radii.MD, Radii.MD)

        # 3. Active pill dot indicator for checked sidebar navigation
        text_rect = face_rect.adjusted(self.pad_x, 0, -self.pad_x, 0)
        if self.show_nav_dot and self.variant == "nav" and self.isCheckable() and self.isChecked():
            dot_r = 4.5
            dot_cx = face_rect.right() - Spacing.LG
            dot_cy = face_rect.center().y()
            painter.setPen(QPen(QColor(Colors.BLACK), 1.5))
            painter.setBrush(QBrush(QColor(Colors.PINK)))
            painter.drawEllipse(QPointF(dot_cx, dot_cy), dot_r, dot_r)
            text_rect = face_rect.adjusted(self.pad_x, 0, -(Spacing.XL + 4), 0)

        # 4. Crisp black Poppins typography
        painter.setFont(self.font())
        painter.setPen(QPen(readable_ink(fill_hex)))
        display_text = self.text().upper() if self.uppercase else self.text()
        align = (
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            if self.align_left
            else Qt.AlignmentFlag.AlignCenter
        )
        painter.drawText(text_rect, align, display_text)
        painter.end()


# ---------------------------------------------------------------------------
# 2. BrutalIconButton & BrutalComboBox
# ---------------------------------------------------------------------------

class BrutalIconButton(BrutalButton):
    """Chunky bordered icon/toolbar button built from shared tokens."""

    def __init__(
        self,
        label: str,
        variant: str = "surface",
        parent: QWidget | None = None,
        *,
        size: int = Metrics.ICON_BTN_SIZE,
        min_width: int | None = None,
        uppercase: bool = False,
    ):
        super().__init__(
            label,
            variant=variant,
            parent=parent,
            uppercase=uppercase,
            show_nav_dot=False,
            pad_x=Spacing.XS + 2,
            shadow_px=Shadows.SM,
            min_face_height=max(26, size - Shadows.SM - Shadows.HOVER_SHIFT - 2),
        )
        self._box_h = size
        self._min_w = min_width if min_width is not None else size
        self.setMinimumHeight(self._box_h)
        self.setMaximumHeight(self._box_h)
        self.setMinimumWidth(self._min_w)

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        label = self.text().upper() if self.uppercase else self.text()
        txt_w = fm.horizontalAdvance(label)
        needed_w = max(self._min_w, txt_w + Spacing.MD * 2 + self.shadow_px + self.hover_px + 4)
        return QSize(needed_w, self._box_h)


class BrutalComboBox(QComboBox):
    """Neo-Brutalist dropdown selector painting a crisp vector chevron inside the right box."""

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        cx = float(self.width()) - 18.0
        cy = float(self.height()) / 2.0 + 1.0
        tri = QPainterPath()
        tri.moveTo(cx - 5.5, cy - 3.0)
        tri.lineTo(cx + 5.5, cy - 3.0)
        tri.lineTo(cx, cy + 4.0)
        tri.closeSubpath()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(Colors.BLACK)))
        painter.drawPath(tri)
        painter.end()


# ---------------------------------------------------------------------------
# 3. BrutalCard
# ---------------------------------------------------------------------------

class BrutalCard(QFrame):
    """
    Reusable Neo-Brutalist container card with thick black border, flat fill,
    and zero-blur hard offset shadow.
    """

    def __init__(
        self,
        fill_color: str = Colors.WHITE,
        parent: QWidget | None = None,
        *,
        shadow_px: int = Shadows.LG,
        radius: int = Radii.LG,
        padding: int = Spacing.XL,
        selection_handles: bool = False,
    ):
        super().__init__(parent)
        self.fill_color = fill_color
        self.shadow_px = shadow_px
        self.radius = radius
        self.selection_handles = selection_handles

        extra = Metrics.SELECTION_HANDLE // 2 + 2 if selection_handles else 2
        self.setContentsMargins(
            padding + extra,
            padding + extra,
            padding + shadow_px + extra,
            padding + shadow_px + extra,
        )

    def set_fill_color(self, hex_color: str):
        self.fill_color = hex_color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        inset = float(Metrics.SELECTION_HANDLE // 2 + 2) if self.selection_handles else 2.0
        face_w = max(10.0, float(self.width()) - inset - self.shadow_px - 2.0)
        face_h = max(10.0, float(self.height()) - inset - self.shadow_px - 2.0)
        face_rect = QRectF(inset, inset, face_w, face_h)
        shadow_rect = face_rect.translated(float(self.shadow_px), float(self.shadow_px))

        # Hard black shadow
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(Colors.BLACK)))
        painter.drawRoundedRect(shadow_rect, self.radius, self.radius)

        # Card face
        painter.setPen(QPen(QColor(Colors.BLACK), Borders.DEFAULT))
        painter.setBrush(QBrush(QColor(self.fill_color)))
        painter.drawRoundedRect(face_rect, self.radius, self.radius)

        if self.selection_handles:
            half = Metrics.SELECTION_HANDLE / 2.0
            painter.setBrush(QBrush(QColor(Colors.WHITE)))
            painter.setPen(QPen(QColor(Colors.BLACK), Borders.THIN))
            for pt in (
                face_rect.topLeft(),
                face_rect.topRight(),
                face_rect.bottomLeft(),
                face_rect.bottomRight(),
            ):
                painter.drawRect(QRectF(pt.x() - half, pt.y() - half, Metrics.SELECTION_HANDLE, Metrics.SELECTION_HANDLE))

        painter.end()


# ---------------------------------------------------------------------------
# 4. BrutalInput
# ---------------------------------------------------------------------------

class BrutalInput(QFrame):
    """
    Neo-Brutalist text input (thick black border, white fill, hard shadow)
    exposing a QLineEdit-compatible API so existing signals work unchanged.
    """

    textChanged = pyqtSignal(str)
    returnPressed = pyqtSignal()

    def __init__(
        self,
        text: str = "",
        placeholder: str = "",
        parent: QWidget | None = None,
        *,
        fill_color: str = Colors.WHITE,
        shadow_px: int = Shadows.MD,
        face_height: int = Metrics.TOUCH_MIN,
        is_heading: bool = False,
    ):
        super().__init__(parent)
        self.fill_color = fill_color
        self.shadow_px = shadow_px
        self._focused = False

        total_h = face_height + shadow_px + 4
        self.setFixedHeight(total_h)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            Spacing.LG,
            4,
            Spacing.LG + shadow_px,
            4 + shadow_px,
        )
        layout.setSpacing(Spacing.SM)

        self.line_edit = QLineEdit(text, self)
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.setFrame(False)
        font = (
            Typography.heading(Typography.SIZE_EDITOR_TITLE)
            if is_heading
            else Typography.body(Typography.SIZE_BODY)
        )
        self.line_edit.setFont(font)
        self.line_edit.setStyleSheet(
            f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {Colors.BLACK};
                selection-background-color: {Colors.PINK};
                selection-color: {Colors.BLACK};
                padding: 0px;
            }}
            """
        )
        self.line_edit.textChanged.connect(self.textChanged.emit)
        self.line_edit.returnPressed.connect(self.returnPressed.emit)
        self.line_edit.installEventFilter(self)
        layout.addWidget(self.line_edit)

    def eventFilter(self, obj, event):
        if obj is self.line_edit:
            if event.type() == event.Type.FocusIn:
                self._focused = True
                self.update()
            elif event.type() == event.Type.FocusOut:
                self._focused = False
                self.update()
        return super().eventFilter(obj, event)

    # QLineEdit proxy methods
    def text(self) -> str:
        return self.line_edit.text()

    def setText(self, value: str):
        self.line_edit.setText(value)

    def clear(self):
        self.line_edit.clear()

    def setPlaceholderText(self, placeholder: str):
        self.line_edit.setPlaceholderText(placeholder)

    def setFocus(self):
        self.line_edit.setFocus()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        face_w = max(10.0, float(self.width()) - self.shadow_px - 4.0)
        face_h = max(10.0, float(self.height()) - self.shadow_px - 4.0)
        shift = -1.0 if self._focused else 0.0
        base_rect = QRectF(2.0, 2.0, face_w, face_h)
        shadow_rect = base_rect.translated(float(self.shadow_px), float(self.shadow_px))
        face_rect = base_rect.translated(shift, shift)

        # Hard black shadow
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(Colors.BLACK)))
        painter.drawRoundedRect(shadow_rect, Radii.MD, Radii.MD)

        # Input face (subtle warm highlight on focus)
        bg = Colors.CREAM if (self._focused and self.fill_color == Colors.WHITE) else self.fill_color
        painter.setPen(QPen(QColor(Colors.BLACK), Borders.DEFAULT))
        painter.setBrush(QBrush(QColor(bg)))
        painter.drawRoundedRect(face_rect, Radii.MD, Radii.MD)

        # Crisp focus accent bar on left edge
        if self._focused:
            bar_rect = QRectF(face_rect.left() + 5, face_rect.top() + 8, 4.0, max(8.0, face_rect.height() - 16))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(Colors.PINK)))
            painter.drawRoundedRect(bar_rect, 2, 2)

        painter.end()


# ---------------------------------------------------------------------------
# 5. BrutalChip & 6. BrutalTag
# ---------------------------------------------------------------------------

class BrutalChip(QPushButton):
    """
    Pill-shaped category/tag filter chip with black border.
    Unselected = white fill; Selected = saturated pastel fill + hard shadow.
    """

    def __init__(self, text: str, pastel_color: str = Colors.PINK, parent: QWidget | None = None):
        super().__init__(text, parent)
        self.pastel_color = pastel_color
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(Typography.label(Typography.SIZE_CAPTION))
        self.shadow_px = Shadows.SM
        self.hover_px = 1.5
        self._motion = _PressHoverAnimator(self, shadow_px=self.shadow_px, hover_px=int(self.hover_px))
        self.setFixedHeight(38)

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        w = fm.horizontalAdvance(self.text().upper()) + Spacing.LG * 2 + self.shadow_px + 6
        return QSize(max(64, w), 38)

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

        face_w = max(16.0, float(self.width()) - self.shadow_px - 4.0)
        face_h = max(16.0, float(self.height()) - self.shadow_px - 4.0)
        base_rect = QRectF(2.0, 2.0, face_w, face_h)
        pill_r = face_h / 2.0

        face_rect = base_rect.translated(self._motion.dx, self._motion.dy)

        if self.isChecked() or self._motion._hovered:
            shadow_rect = base_rect.translated(float(self.shadow_px), float(self.shadow_px))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(Colors.BLACK)))
            painter.drawRoundedRect(shadow_rect, pill_r, pill_r)

        fill = self.pastel_color if self.isChecked() else (Colors.SOFT_ORANGE if self._motion._hovered else Colors.WHITE)
        border_w = Borders.DEFAULT if self.isChecked() else Borders.THIN
        painter.setPen(QPen(QColor(Colors.BLACK), border_w))
        painter.setBrush(QBrush(QColor(fill)))
        painter.drawRoundedRect(face_rect, pill_r, pill_r)

        painter.setFont(self.font())
        painter.setPen(QPen(readable_ink(fill)))
        painter.drawText(face_rect, Qt.AlignmentFlag.AlignCenter, self.text().upper())
        painter.end()


class BrutalTag(QWidget):
    """
    Sticker / Tag pill label with optional rotation (-2.5° to +2.5°),
    solid black outline, pastel fill, and hard offset shadow.
    """

    def __init__(
        self,
        text: str,
        fill_color: str = Colors.YELLOW,
        parent: QWidget | None = None,
        *,
        tilt_deg: float = Motion.STICKER_TILT_DEG,
        pill: bool = False,
    ):
        super().__init__(parent)
        self._text = text
        self.fill_color = fill_color
        self.tilt_deg = tilt_deg
        self.pill = pill
        self.setFont(Typography.label(Typography.SIZE_CAPTION))
        self.setFixedHeight(38)

    def setText(self, text: str):
        self._text = text
        self.updateGeometry()
        self.update()

    def text(self) -> str:
        return self._text

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        w = fm.horizontalAdvance(self._text.upper()) + Spacing.LG * 2 + 12
        return QSize(max(68, w), 38)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        pad_x = 5.0
        pad_y = 5.0
        face_w = max(14.0, float(self.width()) - pad_x * 2 - Shadows.SM)
        face_h = max(14.0, float(self.height()) - pad_y * 2 - Shadows.SM)
        face_rect = QRectF(pad_x, pad_y, face_w, face_h)
        shadow_rect = face_rect.translated(float(Shadows.SM), float(Shadows.SM))
        radius = face_h / 2.0 if self.pill else Radii.SM

        center = face_rect.center()
        painter.translate(center)
        painter.rotate(self.tilt_deg)
        painter.translate(-center)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(Colors.BLACK)))
        painter.drawRoundedRect(shadow_rect, radius, radius)

        painter.setPen(QPen(QColor(Colors.BLACK), Borders.THIN))
        painter.setBrush(QBrush(QColor(self.fill_color)))
        painter.drawRoundedRect(face_rect, radius, radius)

        painter.setFont(self.font())
        painter.setPen(QPen(readable_ink(self.fill_color)))
        painter.drawText(face_rect, Qt.AlignmentFlag.AlignCenter, self._text.upper())
        painter.end()


# ---------------------------------------------------------------------------
# 7. BrutalToggle (Chunky Neo-Brutalist Switch: Green = ON, White = OFF)
# ---------------------------------------------------------------------------

class BrutalToggle(QCheckBox):
    """
    Chunky Neo-Brutalist switch inheriting QCheckBox for 100% signal/state
    compatibility (`isChecked`, `setChecked`, `stateChanged`).
    """

    def __init__(self, text: str = "", parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(Typography.label(Typography.SIZE_BODY, letter_spacing_pct=100.0))
        self.setMinimumHeight(Metrics.TOUCH_MIN)

        self._knob_pos = 1.0 if self.isChecked() else 0.0
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(Motion.TOGGLE_MS)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_anim)
        self.toggled.connect(self._start_slide)

    def _on_anim(self, val):
        self._knob_pos = float(val)
        self.update()

    def _start_slide(self, checked: bool):
        self._anim.stop()
        self._anim.setStartValue(self._knob_pos)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self._knob_pos = 1.0 if checked else 0.0
        self.update()

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        txt_w = fm.horizontalAdvance(self.text()) if self.text() else 0
        gap = Spacing.MD if txt_w else 0
        return QSize(Metrics.TOGGLE_TRACK_W + Shadows.SM + gap + txt_w + 8, Metrics.TOUCH_MIN)

    def hitButton(self, pos) -> bool:
        return self.rect().contains(pos)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        track_w = float(Metrics.TOGGLE_TRACK_W)
        track_h = float(Metrics.TOGGLE_TRACK_H)
        cy = float(self.height()) / 2.0

        # Draw label on left if text provided, switch on right (or switch directly if no text)
        if self.text():
            text_rect = QRectF(0, 0, float(self.width()) - track_w - Shadows.SM - Spacing.MD, float(self.height()))
            painter.setFont(self.font())
            painter.setPen(QPen(QColor(Colors.BLACK)))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.text())
            track_x = float(self.width()) - track_w - Shadows.SM - 2.0
        else:
            track_x = 2.0

        track_y = cy - track_h / 2.0 - 1.0
        track_rect = QRectF(track_x, track_y, track_w, track_h)
        shadow_rect = track_rect.translated(float(Shadows.SM), float(Shadows.SM))
        radius = track_h / 2.0

        # Hard black shadow
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(Colors.BLACK)))
        painter.drawRoundedRect(shadow_rect, radius, radius)

        # Track fill: Green (#99E885) when ON, White (#FFFFFF) when OFF
        track_fill = Colors.GREEN if self.isChecked() else Colors.WHITE
        painter.setPen(QPen(QColor(Colors.BLACK), Borders.DEFAULT))
        painter.setBrush(QBrush(QColor(track_fill)))
        painter.drawRoundedRect(track_rect, radius, radius)

        # Sliding thumb knob
        thumb_sz = float(Metrics.TOGGLE_THUMB)
        pad = (track_h - thumb_sz) / 2.0
        min_x = track_rect.left() + pad
        max_x = track_rect.right() - pad - thumb_sz
        knob_x = min_x + (max_x - min_x) * self._knob_pos
        knob_rect = QRectF(knob_x, track_rect.top() + pad, thumb_sz, thumb_sz)

        knob_fill = Colors.BLACK if not self.isChecked() else Colors.YELLOW
        painter.setPen(QPen(QColor(Colors.BLACK), Borders.THIN))
        painter.setBrush(QBrush(QColor(knob_fill)))
        painter.drawEllipse(knob_rect)

        painter.end()


# ---------------------------------------------------------------------------
# 8. BrutalFAB (Floating Action Button)
# ---------------------------------------------------------------------------

class BrutalFAB(QPushButton):
    """
    Big Yellow (#F7CB46) Floating Action Button with thick black border,
    6px hard offset shadow, '+' icon, and snappy physical press animation.
    """

    def __init__(self, parent: QWidget | None = None, tooltip: str = ""):
        super().__init__("", parent)
        self.shadow_px = Shadows.LG
        self.hover_px = Shadows.HOVER_SHIFT
        total = Metrics.FAB_SIZE + self.shadow_px + self.hover_px + 2
        self.setFixedSize(total, total)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if tooltip:
            self.setToolTip(tooltip)
        self._motion = _PressHoverAnimator(self, shadow_px=self.shadow_px, hover_px=self.hover_px)

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

        inset = float(self.hover_px + 1)
        sz = float(Metrics.FAB_SIZE)
        base_rect = QRectF(inset, inset, sz, sz)
        shadow_rect = base_rect.translated(float(self.shadow_px), float(self.shadow_px))
        face_rect = base_rect.translated(self._motion.dx, self._motion.dy)

        # Hard black shadow
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(Colors.BLACK)))
        painter.drawRoundedRect(shadow_rect, Radii.XL, Radii.XL)

        # Yellow face
        fill = Colors.GREEN if self._motion._hovered and not self._motion._pressed else Colors.YELLOW
        painter.setPen(QPen(QColor(Colors.BLACK), Borders.DEFAULT))
        painter.setBrush(QBrush(QColor(fill)))
        painter.drawRoundedRect(face_rect, Radii.XL, Radii.XL)

        # Crisp vector '+' icon
        cx = face_rect.center().x()
        cy = face_rect.center().y()
        arm = 11.0
        plus_pen = QPen(QColor(Colors.BLACK), 4.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(plus_pen)
        painter.drawLine(QPointF(cx - arm, cy), QPointF(cx + arm, cy))
        painter.drawLine(QPointF(cx, cy - arm), QPointF(cx, cy + arm))

        painter.end()


# ---------------------------------------------------------------------------
# 9. BrutalModal & DottedCreamFrame
# ---------------------------------------------------------------------------

class DottedCreamFrame(QFrame):
    """Cream (#FBFAE8) surface tiled with the 20px subtle black dotted-grid."""

    def __init__(self, parent: QWidget | None = None, left_border: bool = False):
        super().__init__(parent)
        self.left_border = left_border

    def paintEvent(self, event):
        painter = QPainter(self)
        tile = get_pattern_pixmap(Colors.CREAM, "dot", Metrics.GRID_DOT_SPACING)
        painter.fillRect(self.rect(), QBrush(tile))
        if self.left_border:
            painter.setPen(QPen(QColor(Colors.BLACK), Borders.DEFAULT))
            painter.drawLine(0, 0, 0, self.height())
        painter.end()


class BrutalModal(QDialog):
    """Reusable Neo-Brutalist modal dialog shell with Light Blue / Cream surface."""

    def __init__(self, title: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(title)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(Colors.LIGHT_BLUE))
        # Subtle sparkle star in bottom-left corner
        draw_sparkle_star(painter, 22, self.height() - 22, 9.0, Colors.BLACK)
        painter.end()


# ---------------------------------------------------------------------------
# 10. Decorative Neo-Brutalist Hero & Sidebar Widgets
# ---------------------------------------------------------------------------

class SparkleWidget(QWidget):
    """Standalone inline 4-point black sparkle star (✦) widget."""

    def __init__(self, size: int = 24, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r = min(self.width(), self.height()) * 0.44
        draw_sparkle_star(painter, self.width() / 2.0, self.height() / 2.0, r, Colors.BLACK)
        painter.end()


class SelectionFrameHero(QWidget):
    """
    Empty-state & onboarding hero card modeled directly after the attached
    Neo-Brutalism reference image:
    - Cream (#FBFAE8) dotted-grid card with thick black shadow
    - Figma-like thin black selection rectangle with 4 white square corner handles
    - Green circle (#99E885) + black offset outline + triple diagonal stripes
    - Top-right 2x2 crosshair intersection dots + pink/yellow sticker squares
    - Top-left concept banner badge & rotated yellow CTA button
    """

    action_clicked = pyqtSignal()

    def __init__(
        self,
        badge_text: str,
        headline_text: str,
        desc_text: str,
        cta_text: str = "",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.badge_text = badge_text
        self.headline_text = headline_text
        self.desc_text = desc_text

        self.setMinimumSize(460, 310)
        self.setMaximumWidth(640)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(Spacing.XXL + 12, Spacing.XXL + 12, Spacing.XXL + 18, Spacing.XXL + 18)
        outer.setSpacing(Spacing.MD)

        # Top badge chip
        top_row = QHBoxLayout()
        self.badge_lbl = BrutalTag(badge_text, fill_color=Colors.SOFT_ORANGE, tilt_deg=0.0)
        top_row.addWidget(self.badge_lbl, 0, Qt.AlignmentFlag.AlignLeft)
        top_row.addStretch()
        outer.addLayout(top_row)

        outer.addSpacing(Spacing.SM)

        self.title_lbl = QLabel(headline_text.upper())
        self.title_lbl.setFont(Typography.display(Typography.SIZE_HERO))
        self.title_lbl.setWordWrap(True)
        self.title_lbl.setStyleSheet(f"color: {Colors.BLACK}; background: transparent;")
        outer.addWidget(self.title_lbl)

        self.desc_lbl = QLabel(desc_text)
        self.desc_lbl.setFont(Typography.body(Typography.SIZE_BODY))
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setStyleSheet(f"color: {Colors.BLACK}; background: transparent;")
        outer.addWidget(self.desc_lbl)

        outer.addStretch()

        if cta_text:
            cta_row = QHBoxLayout()
            cta_row.addStretch()
            self.cta_btn = BrutalButton(
                cta_text,
                variant="primary",
                tilt_deg=Motion.STICKER_TILT_DEG,
                shadow_px=Shadows.MD,
            )
            self.cta_btn.clicked.connect(self.action_clicked.emit)
            cta_row.addWidget(self.cta_btn)
            outer.addLayout(cta_row)
        else:
            self.cta_btn = None

    def set_texts(self, badge_text: str, headline_text: str, desc_text: str, cta_text: str = ""):
        self.badge_lbl.setText(badge_text)
        self.title_lbl.setText(headline_text.upper())
        self.desc_lbl.setText(desc_text)
        if self.cta_btn and cta_text:
            self.cta_btn.setText(cta_text)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        card_rect = QRectF(
            4.0,
            4.0,
            max(40.0, float(self.width()) - Shadows.LG - 8.0),
            max(40.0, float(self.height()) - Shadows.LG - 8.0),
        )
        shadow_rect = card_rect.translated(float(Shadows.LG), float(Shadows.LG))

        # 1. Hard black offset shadow
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(Colors.BLACK)))
        painter.drawRoundedRect(shadow_rect, Radii.LG, Radii.LG)

        # 2. Cream dotted-grid surface
        clip = QPainterPath()
        clip.addRoundedRect(card_rect, Radii.LG, Radii.LG)
        painter.save()
        painter.setClipPath(clip)
        tile = get_pattern_pixmap(Colors.CREAM, "dot", Metrics.GRID_DOT_SPACING)
        painter.fillRect(card_rect, QBrush(tile))
        painter.restore()

        painter.setPen(QPen(QColor(Colors.BLACK), Borders.DEFAULT))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(card_rect, Radii.LG, Radii.LG)

        # 3. Decorative motifs inside top-right (non-blocking)
        if card_rect.width() >= 380:
            draw_striped_circle_motif(
                painter,
                card_rect.right() - 140.0,
                card_rect.top() + 58.0,
                22.0,
                Colors.GREEN,
            )
            draw_crosshair_motif(
                painter,
                card_rect.right() - 102.0,
                card_rect.top() + 22.0,
                cell=22.0,
            )

        # 4. Inner Figma-like selection frame with 4 white corner square handles
        frame_rect = card_rect.adjusted(18.0, 18.0, -18.0, -18.0)
        draw_selection_frame(painter, frame_rect, Metrics.SELECTION_HANDLE)

        # 5. Sparkle star accent near bottom-left of selection frame
        draw_sparkle_star(
            painter,
            frame_rect.left() + 26.0,
            frame_rect.bottom() - 16.0,
            11.0,
            Colors.BLACK,
        )
        painter.end()


class SidebarDecoWidget(QWidget):
    """
    Subtle decorative Neo-Brutalist footer accent in the sidebar:
    cream mini-card with green striped circle, pink dot, and 4-point sparkle star.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(64)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = QRectF(4.0, 4.0, float(self.width()) - Shadows.SM - 8.0, float(self.height()) - Shadows.SM - 8.0)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(Colors.BLACK)))
        painter.drawRoundedRect(rect.translated(Shadows.SM, Shadows.SM), Radii.MD, Radii.MD)

        clip = QPainterPath()
        clip.addRoundedRect(rect, Radii.MD, Radii.MD)
        painter.save()
        painter.setClipPath(clip)
        painter.fillRect(rect, QBrush(get_pattern_pixmap(Colors.CREAM, "dot", Metrics.GRID_DOT_SPACING)))
        painter.restore()

        painter.setPen(QPen(QColor(Colors.BLACK), Borders.THIN))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, Radii.MD, Radii.MD)

        # Decorative shapes inside
        draw_striped_circle_motif(painter, rect.left() + 28.0, rect.center().y(), 14.0, Colors.GREEN)
        draw_sparkle_star(painter, rect.right() - 24.0, rect.center().y(), 9.5, Colors.BLACK)

        # Mini rotated yellow sticker pill in center
        painter.save()
        painter.translate(rect.center().x() + 6.0, rect.center().y())
        painter.rotate(-3.0)
        pill = QRectF(-44.0, -11.0, 88.0, 22.0)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(Colors.BLACK)))
        painter.drawRoundedRect(pill.translated(2, 2), 6, 6)
        painter.setPen(QPen(QColor(Colors.BLACK), 1.8))
        painter.setBrush(QBrush(QColor(Colors.PINK)))
        painter.drawRoundedRect(pill, 6, 6)
        painter.setFont(Typography.label(10))
        painter.setPen(QPen(QColor(Colors.BLACK)))
        painter.drawText(pill, Qt.AlignmentFlag.AlignCenter, "NEO-TREE")
        painter.restore()

        painter.end()
