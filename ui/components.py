"""
Reusable Minimalist Modern UI Component Library for Knowledge Tree (Obsidian Aesthetic).

Features a custom mathematical vector iconography engine:
- Pure vector geometric icons drawn via QPainterPath (zero raster images, zero emojis, zero fragile font glyphs)
- 1px hairline borders
- Flat surfaces with clean hover and active states
- Soft, distraction-free elevation
- Clean typography and professional branding
"""

import math
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
    relative_luminance,
)


# ---------------------------------------------------------------------------
# Custom Vector Iconography Engine (Unique Geometric Language)
# ---------------------------------------------------------------------------

def draw_vector_icon(
    painter: QPainter,
    rect: QRectF,
    icon_name: str,
    color: QColor,
    stroke_width: float = 1.5,
):
    """
    Renders signature mathematical vector icons with pixel-perfect clarity.
    No emojis or unicode symbol dependencies.
    """
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    pen = QPen(color, stroke_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    cx = rect.center().x()
    cy = rect.center().y()

    name = (icon_name or "").lower().strip()

    if name in ("tree", "brand", "knowledge_tree"):
        # Signature Knowledge Tree emblem: Root trunk branching to 3 concept nodes
        r = 2.2
        # Center trunk
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QPointF(cx, cy + 5.0), r, r)
        # Left branch node
        painter.drawEllipse(QPointF(cx - 5.5, cy - 3.5), r, r)
        # Right branch node
        painter.drawEllipse(QPointF(cx + 5.5, cy - 3.5), r, r)
        # Top crown node
        painter.drawEllipse(QPointF(cx, cy - 5.5), 1.8, 1.8)

        # Connecting branches
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(QPointF(cx, cy + 3.0), QPointF(cx - 4.0, cy - 2.0))
        painter.drawLine(QPointF(cx, cy + 3.0), QPointF(cx + 4.0, cy - 2.0))
        painter.drawLine(QPointF(cx, cy + 3.0), QPointF(cx, cy - 3.5))

    elif name in ("menu", "hamburger"):
        # 3 crisp horizontal parallel lines
        w = 6.0
        painter.drawLine(QPointF(cx - w, cy - 4.0), QPointF(cx + w, cy - 4.0))
        painter.drawLine(QPointF(cx - w, cy), QPointF(cx + w, cy))
        painter.drawLine(QPointF(cx - w, cy + 4.0), QPointF(cx + w, cy + 4.0))

    elif name == "undo":
        # Curved counter-clockwise return arrow
        path = QPainterPath()
        path.moveTo(cx + 4.5, cy + 4.0)
        path.cubicTo(cx + 4.5, cy - 3.5, cx - 1.0, cy - 4.5, cx - 4.5, cy - 2.0)
        painter.drawPath(path)
        # Arrowhead pointing left
        painter.drawLine(QPointF(cx - 5.5, cy - 2.0), QPointF(cx - 2.5, cy - 5.0))
        painter.drawLine(QPointF(cx - 5.5, cy - 2.0), QPointF(cx - 2.0, cy + 0.5))

    elif name == "redo":
        # Curved clockwise return arrow
        path = QPainterPath()
        path.moveTo(cx - 4.5, cy + 4.0)
        path.cubicTo(cx - 4.5, cy - 3.5, cx + 1.0, cy - 4.5, cx + 4.5, cy - 2.0)
        painter.drawPath(path)
        # Arrowhead pointing right
        painter.drawLine(QPointF(cx + 5.5, cy - 2.0), QPointF(cx + 2.5, cy - 5.0))
        painter.drawLine(QPointF(cx + 5.5, cy - 2.0), QPointF(cx + 2.0, cy + 0.5))

    elif name in ("export", "download"):
        # Tray at bottom
        painter.drawLine(QPointF(cx - 5.5, cy + 1.5), QPointF(cx - 5.5, cy + 5.0))
        painter.drawLine(QPointF(cx - 5.5, cy + 5.0), QPointF(cx + 5.5, cy + 5.0))
        painter.drawLine(QPointF(cx + 5.5, cy + 5.0), QPointF(cx + 5.5, cy + 1.5))
        # Arrow pointing down
        painter.drawLine(QPointF(cx, cy - 5.5), QPointF(cx, cy + 1.5))
        painter.drawLine(QPointF(cx - 3.0, cy - 1.5), QPointF(cx, cy + 1.5))
        painter.drawLine(QPointF(cx + 3.0, cy - 1.5), QPointF(cx, cy + 1.5))

    elif name in ("all_notes", "document", "notes"):
        # Document outline with subtle folded corner
        path = QPainterPath()
        path.moveTo(cx - 4.5, cy - 6.0)
        path.lineTo(cx + 1.5, cy - 6.0)
        path.lineTo(cx + 4.5, cy - 3.0)
        path.lineTo(cx + 4.5, cy + 6.0)
        path.lineTo(cx - 4.5, cy + 6.0)
        path.closeSubpath()
        painter.drawPath(path)
        # Horizontal text lines
        painter.drawLine(QPointF(cx - 2.5, cy - 0.5), QPointF(cx + 2.5, cy - 0.5))
        painter.drawLine(QPointF(cx - 2.5, cy + 2.5), QPointF(cx + 1.5, cy + 2.5))

    elif name in ("tree_view", "hierarchy"):
        # Hierarchy tree nodes
        r = 1.8
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QPointF(cx, cy - 4.5), r, r)
        painter.drawEllipse(QPointF(cx - 4.5, cy + 4.5), r, r)
        painter.drawEllipse(QPointF(cx + 4.5, cy + 4.5), r, r)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(QPointF(cx, cy - 2.5), QPointF(cx - 3.5, cy + 3.0))
        painter.drawLine(QPointF(cx, cy - 2.5), QPointF(cx + 3.5, cy + 3.0))

    elif name in ("favorites", "star"):
        # Geometric 5-point star
        star_path = QPainterPath()
        outer_r = 5.8
        inner_r = 2.6
        for i in range(10):
            r = outer_r if i % 2 == 0 else inner_r
            angle = -math.pi / 2.0 + i * math.pi / 5.0
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)
            if i == 0:
                star_path.moveTo(px, py)
            else:
                star_path.lineTo(px, py)
        star_path.closeSubpath()
        painter.drawPath(star_path)

    elif name in ("settings", "sliders"):
        # Clean modern configuration sliders
        # Track 1
        painter.drawLine(QPointF(cx - 5.5, cy - 3.0), QPointF(cx + 5.5, cy - 3.0))
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QPointF(cx - 1.5, cy - 3.0), 1.8, 1.8)
        # Track 2
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(QPointF(cx - 5.5, cy + 3.0), QPointF(cx + 5.5, cy + 3.0))
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QPointF(cx + 2.0, cy + 3.0), 1.8, 1.8)

    elif name in ("plus", "add", "new"):
        # Mathematical plus
        arm = 5.0
        painter.drawLine(QPointF(cx - arm, cy), QPointF(cx + arm, cy))
        painter.drawLine(QPointF(cx, cy - arm), QPointF(cx, cy + arm))

    elif name in ("minus", "zoom_out"):
        # Mathematical minus
        arm = 5.0
        painter.drawLine(QPointF(cx - arm, cy), QPointF(cx + arm, cy))

    elif name in ("zoom_fit", "fit", "target"):
        # Focus frame target [ ]
        arm = 5.0
        tick = 2.5
        # Top-left
        painter.drawLine(QPointF(cx - arm, cy - arm + tick), QPointF(cx - arm, cy - arm))
        painter.drawLine(QPointF(cx - arm, cy - arm), QPointF(cx - arm + tick, cy - arm))
        # Top-right
        painter.drawLine(QPointF(cx + arm - tick, cy - arm), QPointF(cx + arm, cy - arm))
        painter.drawLine(QPointF(cx + arm, cy - arm), QPointF(cx + arm, cy - arm + tick))
        # Bottom-left
        painter.drawLine(QPointF(cx - arm, cy + arm - tick), QPointF(cx - arm, cy + arm))
        painter.drawLine(QPointF(cx - arm, cy + arm), QPointF(cx - arm + tick, cy + arm))
        # Bottom-right
        painter.drawLine(QPointF(cx + arm - tick, cy + arm), QPointF(cx + arm, cy + arm))
        painter.drawLine(QPointF(cx + arm, cy + arm), QPointF(cx + arm, cy + arm - tick))

    elif name in ("graph", "force_layout", "network"):
        # 3 connected network nodes
        r = 2.0
        p1 = QPointF(cx - 4.5, cy + 3.0)
        p2 = QPointF(cx + 4.5, cy + 3.0)
        p3 = QPointF(cx, cy - 4.0)
        painter.drawLine(p1, p2)
        painter.drawLine(p1, p3)
        painter.drawLine(p2, p3)
        painter.setBrush(QBrush(color))
        painter.drawEllipse(p1, r, r)
        painter.drawEllipse(p2, r, r)
        painter.drawEllipse(p3, r, r)

    elif name in ("close", "x"):
        # Diagonal clean cross
        arm = 4.0
        painter.drawLine(QPointF(cx - arm, cy - arm), QPointF(cx + arm, cy + arm))
        painter.drawLine(QPointF(cx + arm, cy - arm), QPointF(cx - arm, cy + arm))

    elif name in ("chevron_left", "prev", "back"):
        painter.drawLine(QPointF(cx + 2.0, cy - 4.5), QPointF(cx - 2.5, cy))
        painter.drawLine(QPointF(cx - 2.5, cy), QPointF(cx + 2.0, cy + 4.5))

    elif name in ("chevron_right", "next", "forward"):
        painter.drawLine(QPointF(cx - 2.0, cy - 4.5), QPointF(cx + 2.5, cy))
        painter.drawLine(QPointF(cx + 2.5, cy), QPointF(cx - 2.0, cy + 4.5))

    elif name == "search":
        # Magnifying glass
        r = 3.5
        painter.drawEllipse(QPointF(cx - 1.5, cy - 1.5), r, r)
        painter.drawLine(QPointF(cx + 1.2, cy + 1.2), QPointF(cx + 5.0, cy + 5.0))

    painter.restore()


# ---------------------------------------------------------------------------
# BrandLogoWidget (Signature Knowledge Tree Emblem Logo)
# ---------------------------------------------------------------------------

class BrandLogoWidget(QWidget):
    """Clean Knowledge Tree emblem logo box."""

    def __init__(self, size: int = 28, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(0, 0, self.width(), self.height())
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(Colors.PRIMARY)))
        painter.drawRoundedRect(rect, Radii.SM, Radii.SM)

        draw_vector_icon(painter, rect, "tree", QColor("#ffffff"), stroke_width=1.8)
        painter.end()


# ---------------------------------------------------------------------------
# Interaction Mixin
# ---------------------------------------------------------------------------

class _PressHoverAnimator:
    def __init__(self, widget: QWidget, shadow_px: int = 0, hover_px: int = 0):
        self._widget = widget
        self.dx = 0.0
        self.dy = 0.0
        self._hovered = False
        self._pressed = False

    def set_hovered(self, hovered: bool):
        self._hovered = hovered
        self._widget.update()

    def set_pressed(self, pressed: bool):
        self._pressed = pressed
        self._widget.update()


# ---------------------------------------------------------------------------
# 1. BrutalButton (Modern Sleek Button with Optional Vector Icon)
# ---------------------------------------------------------------------------

class BrutalButton(QPushButton):
    """
    Sleek, modern button with 1px border, smooth background hover,
    clean typography, and optional mathematical vector icon.
    """

    def __init__(
        self,
        text: str = "",
        variant: str = "primary",
        parent: QWidget | None = None,
        *,
        icon_name: str = "",
        uppercase: bool = False,
        align_left: bool = False,
        show_nav_dot: bool | None = None,
        pad_x: int = Spacing.MD,
        shadow_px: int = 0,
        min_face_height: int = Metrics.TOUCH_MIN,
        tilt_deg: float = 0.0,
    ):
        super().__init__(text, parent)
        self.variant = variant
        self.icon_name = icon_name
        self.uppercase = uppercase
        self.align_left = align_left
        self.show_nav_dot = align_left if show_nav_dot is None else show_nav_dot
        self.pad_x = pad_x
        self.shadow_px = 0
        self.hover_px = 0
        self.min_face_height = min_face_height
        self.tilt_deg = 0.0
        self._custom_fill: str | None = None

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(Typography.label(Typography.SIZE_BUTTON))
        self._motion = _PressHoverAnimator(self)

        self.setMinimumHeight(self.min_face_height)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def set_custom_fill(self, hex_color: str | None):
        self._custom_fill = hex_color
        self.update()

    def enterEvent(self, event):
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

    def _resolve_colors(self) -> tuple[str, str, str]:
        if self._custom_fill:
            return (self._custom_fill, Colors.BORDER, Colors.TEXT)

        is_hover = self._motion._hovered
        is_pressed = self._motion._pressed
        is_checked = self.isCheckable() and self.isChecked()

        if self.variant in ("primary", "add"):
            fill = Colors.PRIMARY_ACTIVE if is_pressed else (Colors.PRIMARY_HOVER if is_hover else Colors.PRIMARY)
            return (fill, fill, "#ffffff")

        if self.variant == "danger":
            fill = "#dc2626" if is_hover else "#ef4444"
            return (fill, fill, "#ffffff")

        if self.variant == "nav":
            if is_checked:
                fill = Colors.SURFACE_ACTIVE
                text = Colors.TEXT
            elif is_hover:
                fill = Colors.SURFACE_HOVER
                text = Colors.TEXT
            else:
                fill = "transparent"
                text = Colors.TEXT_MUTED
            return (fill, "transparent", text)

        if is_hover:
            fill = Colors.SURFACE_HOVER
        else:
            fill = Colors.SURFACE
        return (fill, Colors.BORDER, Colors.TEXT)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = QRectF(1.0, 1.0, float(self.width()) - 2.0, float(self.height()) - 2.0)
        fill_hex, border_hex, text_hex = self._resolve_colors()

        # Face
        if fill_hex != "transparent":
            painter.setBrush(QBrush(QColor(fill_hex)))
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)

        if border_hex != "transparent":
            painter.setPen(QPen(QColor(border_hex), 1.0))
        else:
            painter.setPen(Qt.PenStyle.NoPen)

        radius = Radii.SM if self.variant == "nav" else Radii.MD
        painter.drawRoundedRect(rect, radius, radius)

        # Active indicator for sidebar nav item (Left vertical pill)
        is_checked = self.isCheckable() and self.isChecked()
        if self.variant == "nav" and is_checked:
            indicator_rect = QRectF(rect.left() + 2.0, rect.top() + 6.0, 3.0, rect.height() - 12.0)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(Colors.PRIMARY)))
            painter.drawRoundedRect(indicator_rect, 1.5, 1.5)

        # Draw icon if present
        text_left_pad = self.pad_x + (6 if (self.variant == "nav" and is_checked) else 0)
        if self.icon_name:
            icon_sz = 16.0
            icon_x = rect.left() + text_left_pad
            icon_y = rect.top() + (rect.height() - icon_sz) / 2.0
            icon_rect = QRectF(icon_x, icon_y, icon_sz, icon_sz)
            draw_vector_icon(painter, icon_rect, self.icon_name, QColor(text_hex), stroke_width=1.5)
            text_left_pad += int(icon_sz + 6.0)

        # Text label
        display_text = self.text().upper() if self.uppercase else self.text()
        if display_text:
            painter.setFont(self.font())
            painter.setPen(QPen(QColor(text_hex)))
            text_rect = rect.adjusted(text_left_pad, 0, -self.pad_x, 0)
            align = (Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter) if self.align_left else Qt.AlignmentFlag.AlignCenter
            painter.drawText(text_rect, align, display_text)

        painter.end()


# ---------------------------------------------------------------------------
# 2. BrutalIconButton (Clean Sleek Vector Icon Button)
# ---------------------------------------------------------------------------

class BrutalIconButton(BrutalButton):
    def __init__(
        self,
        symbol: str = "",
        icon_name: str = "",
        variant: str = "surface",
        parent: QWidget | None = None,
        size: int = Metrics.ICON_BTN_SIZE,
        min_width: int | None = None,
        uppercase: bool = False,
    ):
        detected_icon = icon_name
        if not detected_icon and symbol:
            norm = symbol.strip().lower()
            mapping = {
                "menü": "menu",
                "menu": "menu",
                "↶": "undo",
                "undo": "undo",
                "↷": "redo",
                "redo": "redo",
                "x": "close",
                "✕": "close",
                "close": "close",
                "＋": "plus",
                "+": "plus",
                "add": "plus",
                "－": "minus",
                "-": "minus",
                "1:1": "zoom_fit",
                "reset": "zoom_fit",
                "ağ": "graph",
                "ag": "graph",
                "graph": "graph",
                "<": "chevron_left",
                "‹": "chevron_left",
                ">": "chevron_right",
                "›": "chevron_right",
            }
            detected_icon = mapping.get(norm, "")

        super().__init__(
            symbol if not detected_icon else "",
            variant=variant,
            parent=parent,
            icon_name=detected_icon,
            uppercase=uppercase,
            pad_x=Spacing.SM,
            shadow_px=0,
            min_face_height=size,
        )
        self._box_h = size
        self._min_w = min_width if min_width is not None else size
        self.setFixedHeight(self._box_h)
        self.setMinimumWidth(self._min_w)

    def paintEvent(self, event):
        if self.icon_name and not self.text():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            rect = QRectF(1.0, 1.0, float(self.width()) - 2.0, float(self.height()) - 2.0)
            fill_hex, border_hex, text_hex = self._resolve_colors()

            if fill_hex != "transparent":
                painter.setBrush(QBrush(QColor(fill_hex)))
            else:
                painter.setBrush(Qt.BrushStyle.NoBrush)

            if border_hex != "transparent":
                painter.setPen(QPen(QColor(border_hex), 1.0))
            else:
                painter.setPen(Qt.PenStyle.NoPen)

            painter.drawRoundedRect(rect, Radii.SM, Radii.SM)

            icon_sz = min(16.0, float(self.height()) - 10.0)
            icon_rect = QRectF(
                rect.center().x() - icon_sz / 2.0,
                rect.center().y() - icon_sz / 2.0,
                icon_sz,
                icon_sz,
            )
            draw_vector_icon(painter, icon_rect, self.icon_name, QColor(text_hex), stroke_width=1.5)
            painter.end()
        else:
            super().paintEvent(event)

    def sizeHint(self) -> QSize:
        if self.icon_name and not self.text():
            return QSize(self._min_w, self._box_h)
        fm = QFontMetrics(self.font())
        txt_w = fm.horizontalAdvance(self.text())
        needed_w = max(self._min_w, txt_w + Spacing.SM * 2 + 8)
        return QSize(needed_w, self._box_h)


class BrutalComboBox(QComboBox):
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        cx = float(self.width()) - 14.0
        cy = float(self.height()) / 2.0
        tri = QPainterPath()
        tri.moveTo(cx - 3.5, cy - 2.0)
        tri.lineTo(cx + 3.5, cy - 2.0)
        tri.lineTo(cx, cy + 2.5)
        tri.closeSubpath()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(Colors.TEXT_MUTED)))
        painter.drawPath(tri)
        painter.end()


# ---------------------------------------------------------------------------
# 3. BrutalCard (Clean Minimal Card Container)
# ---------------------------------------------------------------------------

class BrutalCard(QFrame):
    def __init__(
        self,
        fill_color: str = Colors.SURFACE,
        parent: QWidget | None = None,
        *,
        shadow_px: int = 0,
        radius: int = Radii.MD,
        padding: int = Spacing.LG,
        selection_handles: bool = False,
    ):
        super().__init__(parent)
        self.fill_color = fill_color
        self.radius = radius
        self.selection_handles = False
        self.setContentsMargins(padding, padding, padding, padding)

    def set_fill_color(self, hex_color: str):
        self.fill_color = hex_color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(1.0, 1.0, float(self.width()) - 2.0, float(self.height()) - 2.0)
        painter.setPen(QPen(QColor(Colors.BORDER), 1.0))
        painter.setBrush(QBrush(QColor(Colors.SURFACE)))
        painter.drawRoundedRect(rect, self.radius, self.radius)
        painter.end()


# ---------------------------------------------------------------------------
# 4. BrutalInput (Clean Modern Input Field)
# ---------------------------------------------------------------------------

class BrutalInput(QFrame):
    textChanged = pyqtSignal(str)
    returnPressed = pyqtSignal()

    def __init__(
        self,
        text: str = "",
        placeholder: str = "",
        parent: QWidget | None = None,
        *,
        fill_color: str = Colors.SURFACE,
        shadow_px: int = 0,
        face_height: int = 34,
        is_heading: bool = False,
    ):
        super().__init__(parent)
        self.fill_color = fill_color
        self._focused = False

        self.setFixedHeight(face_height)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.SM + 2, 2, Spacing.SM + 2, 2)
        layout.setSpacing(Spacing.XS)

        self.line_edit = QLineEdit(text, self)
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.setFrame(False)

        font = (
            Typography.heading(Typography.SIZE_CARD_TITLE + 1)
            if is_heading
            else Typography.body(Typography.SIZE_BODY)
        )
        self.line_edit.setFont(font)
        self.line_edit.setStyleSheet(
            f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {Colors.TEXT};
                selection-background-color: {Colors.PRIMARY};
                selection-color: #ffffff;
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
        rect = QRectF(1.0, 1.0, float(self.width()) - 2.0, float(self.height()) - 2.0)
        border_col = Colors.PRIMARY if self._focused else Colors.BORDER
        painter.setPen(QPen(QColor(border_col), 1.0))
        painter.setBrush(QBrush(QColor(Colors.SURFACE)))
        painter.drawRoundedRect(rect, Radii.SM, Radii.SM)
        painter.end()


# ---------------------------------------------------------------------------
# 5. BrutalChip & 6. BrutalTag (Clean Modern Badges)
# ---------------------------------------------------------------------------

class BrutalChip(QPushButton):
    def __init__(self, text: str, pastel_color: str = Colors.PRIMARY, parent: QWidget | None = None):
        super().__init__(text, parent)
        self.pastel_color = pastel_color
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(Typography.label(Typography.SIZE_CAPTION))
        self._motion = _PressHoverAnimator(self)
        self.setFixedHeight(28)

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        w = fm.horizontalAdvance(self.text()) + Spacing.MD * 2 + 8
        return QSize(max(50, w), 28)

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
        pill_r = rect.height() / 2.0

        if self.isChecked():
            painter.setPen(QPen(QColor(Colors.PRIMARY), 1.0))
            painter.setBrush(QBrush(QColor(Colors.PRIMARY)))
            text_col = "#ffffff"
        elif self._motion._hovered:
            painter.setPen(QPen(QColor(Colors.PRIMARY), 1.0))
            painter.setBrush(QBrush(QColor(Colors.SURFACE_HOVER)))
            text_col = Colors.TEXT
        else:
            painter.setPen(QPen(QColor(Colors.BORDER), 1.0))
            painter.setBrush(QBrush(QColor(Colors.SURFACE)))
            text_col = Colors.TEXT_MUTED

        painter.drawRoundedRect(rect, pill_r, pill_r)
        painter.setFont(self.font())
        painter.setPen(QPen(QColor(text_col)))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())
        painter.end()


class BrutalTag(QWidget):
    def __init__(
        self,
        text: str,
        fill_color: str = Colors.SURFACE,
        parent: QWidget | None = None,
        *,
        tilt_deg: float = 0.0,
        pill: bool = False,
    ):
        super().__init__(parent)
        self._text = text
        self.fill_color = fill_color
        self.pill = pill
        self.setFont(Typography.label(Typography.SIZE_CAPTION))
        self.setFixedHeight(24)

    def setText(self, text: str):
        self._text = text
        self.updateGeometry()
        self.update()

    def text(self) -> str:
        return self._text

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        w = fm.horizontalAdvance(self._text) + Spacing.MD * 2
        return QSize(max(40, w), 24)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = QRectF(1.0, 1.0, float(self.width()) - 2.0, float(self.height()) - 2.0)
        radius = rect.height() / 2.0 if self.pill else Radii.SM

        painter.setPen(QPen(QColor(Colors.BORDER), 1.0))
        painter.setBrush(QBrush(QColor(Colors.SURFACE_HOVER)))
        painter.drawRoundedRect(rect, radius, radius)

        painter.setFont(self.font())
        painter.setPen(QPen(QColor(Colors.TEXT_MUTED)))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._text)
        painter.end()


# ---------------------------------------------------------------------------
# 7. BrutalToggle (Sleek Modern Switch)
# ---------------------------------------------------------------------------

class BrutalToggle(QCheckBox):
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
        return QSize(Metrics.TOGGLE_TRACK_W + gap + txt_w + 4, Metrics.TOUCH_MIN)

    def hitButton(self, pos) -> bool:
        return self.rect().contains(pos)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        track_w = float(Metrics.TOGGLE_TRACK_W)
        track_h = float(Metrics.TOGGLE_TRACK_H)
        cy = float(self.height()) / 2.0

        if self.text():
            text_rect = QRectF(0, 0, float(self.width()) - track_w - Spacing.MD, float(self.height()))
            painter.setFont(self.font())
            painter.setPen(QPen(QColor(Colors.TEXT)))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.text())
            track_x = float(self.width()) - track_w - 2.0
        else:
            track_x = 2.0

        track_y = cy - track_h / 2.0
        track_rect = QRectF(track_x, track_y, track_w, track_h)
        radius = track_h / 2.0

        track_fill = Colors.PRIMARY if self.isChecked() else Colors.BORDER
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(track_fill)))
        painter.drawRoundedRect(track_rect, radius, radius)

        # Sliding thumb
        thumb_sz = float(Metrics.TOGGLE_THUMB)
        pad = (track_h - thumb_sz) / 2.0
        min_x = track_rect.left() + pad
        max_x = track_rect.right() - pad - thumb_sz
        knob_x = min_x + (max_x - min_x) * self._knob_pos
        knob_rect = QRectF(knob_x, track_rect.top() + pad, thumb_sz, thumb_sz)

        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawEllipse(knob_rect)
        painter.end()


# ---------------------------------------------------------------------------
# 8. BrutalFAB (Modern Floating Action Button)
# ---------------------------------------------------------------------------

class BrutalFAB(QPushButton):
    def __init__(self, parent: QWidget | None = None, tooltip: str = ""):
        super().__init__("", parent)
        self.setFixedSize(Metrics.FAB_SIZE, Metrics.FAB_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if tooltip:
            self.setToolTip(tooltip)
        self._motion = _PressHoverAnimator(self)

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

        rect = QRectF(1.0, 1.0, float(self.width()) - 2.0, float(self.height()) - 2.0)
        fill = Colors.PRIMARY_HOVER if self._motion._hovered else Colors.PRIMARY

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(fill)))
        painter.drawEllipse(rect)

        # Crisp mathematical vector plus
        draw_vector_icon(painter, rect, "plus", QColor("#ffffff"), stroke_width=2.2)
        painter.end()


# ---------------------------------------------------------------------------
# 9. Frames & Dialogs
# ---------------------------------------------------------------------------

class DottedCreamFrame(QFrame):
    def __init__(self, parent: QWidget | None = None, left_border: bool = False):
        super().__init__(parent)
        self.left_border = left_border

    def paintEvent(self, event):
        painter = QPainter(self)
        tile = get_pattern_pixmap(Colors.CANVAS, "dot", Metrics.GRID_DOT_SPACING)
        painter.fillRect(self.rect(), QBrush(tile))
        if self.left_border:
            painter.setPen(QPen(QColor(Colors.BORDER), 1.0))
            painter.drawLine(0, 0, 0, self.height())
        painter.end()


class BrutalModal(QDialog):
    def __init__(self, title: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(title)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(Colors.WINDOW))
        painter.end()


class SparkleWidget(QWidget):
    def __init__(self, size: int = 24, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(0, 0)
        self.hide()


class SelectionFrameHero(QWidget):
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

        self.setMinimumSize(420, 240)
        self.setMaximumWidth(580)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        outer.setSpacing(Spacing.MD)

        top_row = QHBoxLayout()
        self.badge_lbl = BrutalTag(badge_text, fill_color=Colors.SURFACE_HOVER)
        top_row.addWidget(self.badge_lbl, 0, Qt.AlignmentFlag.AlignLeft)
        top_row.addStretch()
        outer.addLayout(top_row)

        self.title_lbl = QLabel(headline_text)
        self.title_lbl.setFont(Typography.display(Typography.SIZE_PAGE_TITLE))
        self.title_lbl.setWordWrap(True)
        self.title_lbl.setStyleSheet(f"color: {Colors.TEXT}; background: transparent;")
        outer.addWidget(self.title_lbl)

        self.desc_lbl = QLabel(desc_text)
        self.desc_lbl.setFont(Typography.body(Typography.SIZE_BODY))
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; background: transparent;")
        outer.addWidget(self.desc_lbl)

        outer.addStretch()

        if cta_text:
            cta_row = QHBoxLayout()
            cta_row.addStretch()
            self.cta_btn = BrutalButton(cta_text, variant="primary", icon_name="plus")
            self.cta_btn.clicked.connect(self.action_clicked.emit)
            cta_row.addWidget(self.cta_btn)
            outer.addLayout(cta_row)
        else:
            self.cta_btn = None

    def set_texts(self, badge_text: str, headline_text: str, desc_text: str, cta_text: str = ""):
        self.badge_lbl.setText(badge_text)
        self.title_lbl.setText(headline_text)
        self.desc_lbl.setText(desc_text)
        if self.cta_btn and cta_text:
            self.cta_btn.setText(cta_text)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(1.0, 1.0, float(self.width()) - 2.0, float(self.height()) - 2.0)
        painter.setPen(QPen(QColor(Colors.BORDER), 1.0))
        painter.setBrush(QBrush(QColor(Colors.SURFACE)))
        painter.drawRoundedRect(rect, Radii.LG, Radii.LG)
        painter.end()


class SidebarDecoWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(0)
        self.hide()
