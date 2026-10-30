from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainterPath, QPainterPathStroker, QPen
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsPathItem

from .theme import Borders, Colors


class EdgeItem(QGraphicsPathItem):
    """Neo-Brutalist solid black Bezier connection line between two nodes."""

    def __init__(self, source_node, target_node):
        super().__init__()
        self.source_node = source_node
        self.target_node = target_node
        self.setZValue(-1)  # Render behind NodeItems
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.update_position()

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(16)
        return stroker.createStroke(self.path())

    def update_position(self):
        source_pos = self.source_node.pos() + self.source_node.boundingRect().center()
        target_pos = self.target_node.pos() + self.target_node.boundingRect().center()

        path = QPainterPath(source_pos)
        control_point_offset = 60
        path.cubicTo(
            source_pos.x(),
            source_pos.y() + control_point_offset,
            target_pos.x(),
            target_pos.y() - control_point_offset,
            target_pos.x(),
            target_pos.y(),
        )
        self.setPath(path)

    def paint(self, painter, option, widget):
        if self.isSelected():
            # Selected state: bold black casing with vibrant Pink inner core
            outer_pen = QPen(
                QColor(Colors.BLACK),
                Borders.DEFAULT * 2 + 1,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
            painter.setPen(outer_pen)
            painter.drawPath(self.path())

            inner_pen = QPen(
                QColor(Colors.PINK),
                Borders.DEFAULT,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
            painter.setPen(inner_pen)
            painter.drawPath(self.path())
        else:
            pen = QPen(
                QColor(Colors.BLACK),
                Borders.DEFAULT,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
            painter.setPen(pen)
            painter.drawPath(self.path())
