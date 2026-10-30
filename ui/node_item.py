from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainterPath, QPen
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsTextItem

from .theme import (
    Borders,
    Colors,
    Metrics,
    Radii,
    Shadows,
    Spacing,
    Typography,
    readable_ink,
    resolve_accent_color,
    resolve_node_bg,
)


class NodeItem(QGraphicsItem):
    """Neo-Brutalist Mind-Map Node Card on QGraphicsScene."""

    def __init__(
        self,
        node_id,
        title,
        x,
        y,
        parent_scene,
        color=None,
        tag="",
        width=180,
        height=92,
        bg_color=None,
        is_favorite=False,
    ):
        super().__init__()
        self.node_id = node_id
        self.title = title
        self.parent_scene = parent_scene
        self.color = resolve_accent_color(color or "", seed=f"{node_id}_accent")
        self.tag = tag
        self.width = width
        self.height = height
        self.bg_color = resolve_node_bg(bg_color or "", seed=node_id, on_light_blue=False)
        self.is_favorite = is_favorite

        self._hovered = False
        self._is_resizing = False

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
        return resolve_node_bg(self.bg_color, seed=self.node_id, on_light_blue=False)

    def _sync_ink_color(self):
        self.title_item.setDefaultTextColor(readable_ink(self._effective_bg()))

    def _adjust_title_pos(self):
        top_y = float(Spacing.MD) if not self.tag else 38.0
        right_reserve = 38.0 if self.is_favorite and not self.tag else float(Spacing.LG * 2)
        self.title_item.setPos(float(Spacing.LG), top_y)
        self.title_item.setTextWidth(max(60.0, float(self.width) - right_reserve))
        self._adjust_title_font()

    def _adjust_title_font(self):
        # Proportional font scaling when user resizes the node box
        scale_factor = min(self.width / 160.0, self.height / 84.0)
        current_size = max(Typography.PT_NODE_BASE, int(Typography.PT_NODE_BASE * scale_factor))

        font = Typography.canvas_font(current_size, QFont.Weight.ExtraBold)
        font.setCapitalization(QFont.Capitalization.AllUppercase)
        self.title_item.setFont(font)

        max_height = max(22.0, float(self.height - (50 if self.tag else 26)))
        while current_size > Typography.PT_NODE_MIN and self.title_item.boundingRect().height() > max_height:
            current_size -= 1
            font.setPointSize(current_size)
            self.title_item.setFont(font)

    def boundingRect(self):
        # Symmetric margin covers hover lift, 3px border, 6px hard shadow, and corner handles
        # while keeping boundingRect().center() == (width/2, height/2).
        margin = 10.0
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
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def paint(self, painter, option, widget):
        fill_hex = self._effective_bg()
        self._sync_ink_color()

        lift = -1.5 if (self._hovered and not self._is_resizing) else 0.0
        box_rect = QRectF(lift, lift, float(self.width), float(self.height))
        shadow_offset = float(Shadows.LG if (self.isSelected() or self._hovered) else Shadows.MD)
        shadow_rect = QRectF(
            shadow_offset,
            shadow_offset,
            float(self.width),
            float(self.height),
        )

        # 1. Zero-blur solid black offset shadow
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(Colors.BLACK)))
        painter.drawRoundedRect(shadow_rect, float(Radii.MD + 2), float(Radii.MD + 2))

        # 2. Saturated pastel card face + thick black border
        painter.setPen(QPen(QColor(Colors.BLACK), Borders.DEFAULT))
        painter.setBrush(QBrush(QColor(fill_hex)))
        painter.drawRoundedRect(box_rect, float(Radii.MD + 2), float(Radii.MD + 2))

        # 3. Neo-Brutalist Tag Pill
        if self.tag:
            tag_font = Typography.canvas_font(Typography.PT_NODE_TAG, QFont.Weight.Bold)
            painter.setFont(tag_font)
            fm = painter.fontMetrics()
            tag_upper = self.tag.upper()
            text_width = fm.horizontalAdvance(tag_upper)
            max_pill_w = max(44.0, float(self.width) - (56.0 if self.is_favorite else 28.0))
            pill_w = min(float(text_width + Spacing.LG + 4), max_pill_w)

            pill_rect = QRectF(
                box_rect.left() + float(Spacing.LG),
                box_rect.top() + float(Spacing.MD),
                pill_w,
                22.0,
            )
            pill_fill = resolve_accent_color(self.color, seed=self.tag, avoid_bg=fill_hex)

            # Mini hard shadow behind pill
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(Colors.BLACK)))
            painter.drawRoundedRect(pill_rect.translated(2.0, 2.0), 11.0, 11.0)

            painter.setPen(QPen(QColor(Colors.BLACK), Borders.THIN))
            painter.setBrush(QBrush(QColor(pill_fill)))
            painter.drawRoundedRect(pill_rect, 11.0, 11.0)

            elided_tag = fm.elidedText(tag_upper, Qt.TextElideMode.ElideRight, int(pill_w - 10))
            painter.setPen(QPen(readable_ink(pill_fill)))
            painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, elided_tag)

        # 4. Favorite Star Sticker (Top Right)
        if self.is_favorite:
            badge_sz = 24.0
            star_rect = QRectF(
                box_rect.right() - badge_sz - float(Spacing.MD),
                box_rect.top() + float(Spacing.MD - 2),
                badge_sz,
                badge_sz,
            )
            star_bg = Colors.PINK if fill_hex.lower() == Colors.YELLOW.lower() else Colors.YELLOW
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(Colors.BLACK)))
            painter.drawRoundedRect(star_rect.translated(2.0, 2.0), 7.0, 7.0)

            painter.setPen(QPen(QColor(Colors.BLACK), Borders.THIN))
            painter.setBrush(QBrush(QColor(star_bg)))
            painter.drawRoundedRect(star_rect, 7.0, 7.0)

            star_font = Typography.canvas_font(11, QFont.Weight.Black)
            painter.setFont(star_font)
            painter.setPen(QPen(QColor(Colors.BLACK)))
            painter.drawText(star_rect, Qt.AlignmentFlag.AlignCenter, "★")

        # 5. Tactile diagonal resize grip lines (Bottom Right)
        grip_pen = QPen(readable_ink(fill_hex), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(grip_pen)
        bx = box_rect.right() - 6.0
        by = box_rect.bottom() - 6.0
        painter.drawLine(QPointF(bx - 9.0, by), QPointF(bx, by - 9.0))
        painter.drawLine(QPointF(bx - 4.0, by), QPointF(bx, by - 4.0))

        # 6. Figma-like corner selection handles when selected
        if self.isSelected():
            h_sz = float(Metrics.SELECTION_HANDLE)
            half = h_sz / 2.0
            painter.setPen(QPen(QColor(Colors.BLACK), Borders.THIN))
            painter.setBrush(QBrush(QColor(Colors.WHITE)))
            for pt in (
                box_rect.topLeft(),
                box_rect.topRight(),
                box_rect.bottomLeft(),
                box_rect.bottomRight(),
            ):
                painter.drawRect(QRectF(pt.x() - half, pt.y() - half, h_sz, h_sz))

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            if hasattr(self.parent_scene, "update_edges_for_node"):
                self.parent_scene.update_edges_for_node(self)
            else:
                self.parent_scene.update_edges()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        pos = event.pos()
        if pos.x() >= self.width - 22 and pos.y() >= self.height - 22:
            self._is_resizing = True
            event.accept()
        else:
            self._is_resizing = False
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_resizing:
            new_w = max(150, int(event.pos().x()))
            new_h = max(84, int(event.pos().y()))
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
            self.parent_scene.save_data()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if not self._is_resizing:
            self.parent_scene.node_double_clicked(self)
        super().mouseDoubleClickEvent(event)
