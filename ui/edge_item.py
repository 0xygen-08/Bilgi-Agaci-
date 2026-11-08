from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainterPath, QPainterPathStroker, QPen
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsPathItem

from .theme import Borders, Colors


class EdgeItem(QGraphicsPathItem):
    """Clean minimal Bezier connection line between two nodes."""

    def __init__(self, source_node, target_node):
        super().__init__()
        self.source_node = source_node
        self.target_node = target_node
        self.setZValue(-1)  # Render behind NodeItems
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.update_position()

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(12)
        return stroker.createStroke(self.path())

    def update_position(self):
        source_pos = self.source_node.pos() + self.source_node.boundingRect().center()
        target_pos = self.target_node.pos() + self.target_node.boundingRect().center()

        dx = target_pos.x() - source_pos.x()
        dy = target_pos.y() - source_pos.y()
        path = QPainterPath(source_pos)

        if abs(dx) >= abs(dy):
            offset = max(30.0, min(100.0, abs(dx) * 0.45))
            sign = 1.0 if dx >= 0 else -1.0
            path.cubicTo(
                source_pos.x() + offset * sign,
                source_pos.y(),
                target_pos.x() - offset * sign,
                target_pos.y(),
                target_pos.x(),
                target_pos.y(),
            )
        else:
            offset = max(30.0, min(100.0, abs(dy) * 0.45))
            sign = 1.0 if dy >= 0 else -1.0
            path.cubicTo(
                source_pos.x(),
                source_pos.y() + offset * sign,
                target_pos.x(),
                target_pos.y() - offset * sign,
                target_pos.x(),
                target_pos.y(),
            )
        self.setPath(path)

    def paint(self, painter, option, widget):
        if self.isSelected():
            pen = QPen(
                QColor(Colors.PRIMARY),
                2.0,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        else:
            pen = QPen(
                QColor(Colors.EDGE),
                1.5,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        painter.setPen(pen)
        painter.drawPath(self.path())
