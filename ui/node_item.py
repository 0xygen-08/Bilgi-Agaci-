import math
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainterPath,
    QPen,
)
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsTextItem

from .theme import (
    Borders,
    Colors,
    Metrics,
    Radii,
    Spacing,
    Typography,
    readable_ink,
    relative_luminance,
    resolve_accent_color,
    resolve_node_bg,
)


class NodeItem(QGraphicsItem):
    """
    Obsidian Canvas Node Item:
    - Minimalist rectangular card with 1px hairline border
    - Deep dark slate surface (#202024) in dark mode, crisp white in light mode
    - Optional colored left accent indicator
    - Clean typography with natural sentence casing
    - Clean tag badge & subtle gold favorite star
    """

    def __init__(
        self,
        node_id,
        title,
        x,
        y,
        parent_scene=None,
        color="",
        tag="",
        width=180,
        height=100,
        bg_color="",
        is_favorite=False,
        preview="",
        ocr_text="",
    ):
        super().__init__()
        self.node_id = node_id
        self.title = title
        self.parent_scene = parent_scene
        self.color = color or ""
        self.tag = tag or ""
        self.width = width
        self.height = height
        self.bg_color = bg_color or ""
        self.is_favorite = is_favorite
        self.preview = preview
        self.ocr_text = ocr_text

        self._hovered = False
        self._is_resizing = False
        self._drag_start_pos = QPointF(x, y)
        self._pre_action_snapshot = None

        self.setPos(x, y)
        self.setAcceptHoverEvents(True)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

        self.title_item = QGraphicsTextItem(self.title, self)
        self._sync_ink_color()
        self._adjust_title_pos()

    def _effective_bg(self) -> str:
        return Colors.NODE_SURFACE

    def _sync_ink_color(self):
        self.title_item.setDefaultTextColor(QColor(Colors.TEXT))

    def _adjust_title_pos(self):
        top_y = float(Spacing.MD) if not self.tag else 30.0
        right_reserve = 32.0 if self.is_favorite and not self.tag else float(Spacing.MD * 2)
        left_pad = float(Spacing.MD + (6 if self.color else 0))
        self.title_item.setPos(left_pad, top_y)
        self.title_item.setTextWidth(max(60.0, float(self.width) - right_reserve - left_pad))
        self._adjust_title_font()

    def _adjust_title_font(self):
        scale_factor = min(self.width / 160.0, self.height / 84.0)
        current_size = max(Typography.PT_NODE_BASE, int(Typography.PT_NODE_BASE * scale_factor))

        font = Typography.canvas_font(current_size, QFont.Weight.DemiBold)
        self.title_item.setFont(font)

        max_height = max(20.0, float(self.height - (42 if self.tag else 20)))
        while current_size > Typography.PT_NODE_MIN and self.title_item.boundingRect().height() > max_height:
            current_size -= 1
            font.setPointSize(current_size)
            self.title_item.setFont(font)

    def boundingRect(self):
        margin = 4.0
        return QRectF(
            -margin,
            -margin,
            float(self.width) + margin * 2.0,
            float(self.height) + margin * 2.0,
        )

    def set_color_and_tag(self, color, tag):
        self.color = color
        self.tag = tag
        self._adjust_title_pos()
        self.update()

    def set_bg_color(self, bg_color):
        self.bg_color = bg_color
        self._sync_ink_color()
        self.update()

    def set_favorite(self, is_favorite):
        self.is_favorite = is_favorite
        self._adjust_title_pos()
        self.update()

    def hoverEnterEvent(self, event):
        self._hovered = True
        self.update()
        if hasattr(self.parent_scene, "node_hover_enter"):
            screen_pt = event.screenPos()
            self.parent_scene.node_hover_enter(self, screen_pt)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.update()
        if hasattr(self.parent_scene, "node_hover_leave"):
            self.parent_scene.node_hover_leave(self)
        super().hoverLeaveEvent(event)

    def paint(self, painter, option, widget):
        self._sync_ink_color()

        box_rect = QRectF(0.0, 0.0, float(self.width), float(self.height))

        # 1. Background Surface
        fill_col = Colors.NODE_SURFACE_HOVER if self._hovered else Colors.NODE_SURFACE
        painter.setBrush(QBrush(QColor(fill_col)))

        # 2. Border
        if self.isSelected():
            border_pen = QPen(QColor(Colors.PRIMARY), 1.5)
        elif self._hovered:
            border_pen = QPen(QColor(Colors.PRIMARY_HOVER), 1.0)
        else:
            border_pen = QPen(QColor(Colors.BORDER), 1.0)

        painter.setPen(border_pen)
        painter.drawRoundedRect(box_rect, float(Radii.MD), float(Radii.MD))

        # 3. Optional Left Accent Color Strip
        accent_col = self.color
        if accent_col and accent_col.lower() not in ("#000000", "#ffffff", Colors.SURFACE.lower()):
            strip_rect = QRectF(box_rect.left() + 1.0, box_rect.top() + 4.0, 3.5, box_rect.height() - 8.0)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(accent_col)))
            painter.drawRoundedRect(strip_rect, 1.5, 1.5)

        # 4. Minimalist Tag Badge (Top Left)
        if self.tag:
            tag_font = Typography.canvas_font(Typography.PT_NODE_TAG, QFont.Weight.Medium)
            painter.setFont(tag_font)
            fm = painter.fontMetrics()
            tag_text = self.tag
            text_width = fm.horizontalAdvance(tag_text)
            max_pill_w = max(40.0, float(self.width) - (48.0 if self.is_favorite else 24.0))
            pill_w = min(float(text_width + Spacing.MD * 2), max_pill_w)

            left_x = box_rect.left() + float(Spacing.MD + (6 if self.color else 0))
            pill_rect = QRectF(left_x, box_rect.top() + 6.0, pill_w, 18.0)

            painter.setPen(QPen(QColor(Colors.BORDER), 1.0))
            painter.setBrush(QBrush(QColor(Colors.SURFACE_HOVER)))
            painter.drawRoundedRect(pill_rect, float(Radii.SM), float(Radii.SM))

            elided_tag = fm.elidedText(tag_text, Qt.TextElideMode.ElideRight, int(pill_w - 8))
            painter.setPen(QPen(QColor(Colors.TEXT_MUTED)))
            painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, elided_tag)

        # 5. Clean Gold Favorite Star Icon (Top Right)
        if self.is_favorite:
            star_sz = 14.0
            cx = box_rect.right() - star_sz / 2.0 - 8.0
            cy = box_rect.top() + star_sz / 2.0 + 8.0

            star_path = QPainterPath()
            outer_r = 6.0
            inner_r = 2.8
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

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#f59e0b")))
            painter.drawPath(star_path)

        # 6. Subtle Corner Resize Grip (Bottom Right)
        if self._hovered or self.isSelected():
            grip_pen = QPen(QColor(Colors.BORDER), 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(grip_pen)
            bx = box_rect.right() - 5.0
            by = box_rect.bottom() - 5.0
            painter.drawLine(QPointF(bx - 6.0, by), QPointF(bx, by - 6.0))
            painter.drawLine(QPointF(bx - 3.0, by), QPointF(bx, by - 3.0))

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            if hasattr(self.parent_scene, "update_edges_for_node"):
                self.parent_scene.update_edges_for_node(self)
            else:
                self.parent_scene.update_edges()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        pos = event.pos()
        self._drag_start_pos = self.pos()
        if event.button() == Qt.MouseButton.LeftButton and hasattr(self.parent_scene, "capture_snapshot"):
            self._pre_action_snapshot = self.parent_scene.capture_snapshot()
        if (
            event.button() == Qt.MouseButton.LeftButton
            and pos.x() >= self.width - 18
            and pos.y() >= self.height - 18
        ):
            self._is_resizing = True
            event.accept()
        else:
            self._is_resizing = False
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_resizing:
            new_w = max(140, int(event.pos().x()))
            new_h = max(70, int(event.pos().y()))
            self.prepareGeometryChange()
            self.width = new_w
            self.height = new_h
            self._adjust_title_pos()
            if hasattr(self.parent_scene, "update_edges_for_node"):
                self.parent_scene.update_edges_for_node(self)
            else:
                self.parent_scene.update_edges()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._is_resizing:
            self._is_resizing = False
            if self._pre_action_snapshot and hasattr(self.parent_scene, "push_undo_snapshot"):
                self.parent_scene.push_undo_snapshot(self._pre_action_snapshot)
            self._pre_action_snapshot = None
            if hasattr(self.parent_scene, "save_data"):
                self.parent_scene.save_data()
            event.accept()
        else:
            super().mouseReleaseEvent(event)
            if (
                event.button() == Qt.MouseButton.LeftButton
                and self.pos() != self._drag_start_pos
                and hasattr(self.parent_scene, "save_data")
            ):
                if self._pre_action_snapshot and hasattr(self.parent_scene, "push_undo_snapshot"):
                    self.parent_scene.push_undo_snapshot(self._pre_action_snapshot)
                self.parent_scene.save_data()
            self._pre_action_snapshot = None

    def mouseDoubleClickEvent(self, event):
        if not self._is_resizing:
            self.parent_scene.node_double_clicked(self)
        super().mouseDoubleClickEvent(event)
