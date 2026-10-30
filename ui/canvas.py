from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QFrame, QGraphicsScene, QGraphicsView, QMenu, QMessageBox

from core.i18n import t

from .edge_item import EdgeItem
from .node_item import NodeItem
from .tag_dialog import TagDialog
from .theme import (
    Borders,
    Colors,
    Metrics,
    build_menu_qss,
    get_pattern_pixmap,
    resolve_accent_color,
    resolve_node_bg,
)


class KnowledgeScene(QGraphicsScene):
    node_double_clicked_signal = pyqtSignal(str, str)  # node_id, title
    nodes_count_changed = pyqtSignal(int)

    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.setSceneRect(-5000, -5000, 10000, 10000)
        self.nodes = {}
        self.edges = []

        # Persistent temporary connection line during right-click drag
        self.temp_edge_item = self.addPath(
            QPainterPath(),
            QPen(QColor(Colors.BLACK), Borders.DEFAULT, Qt.PenStyle.DashLine),
        )
        self.temp_edge_item.setZValue(100)
        self.temp_edge_item.hide()
        self.drawing_edge = False
        self.edge_source_node = None
        self._trash = []

        self.load_data()

    def _empty_trash(self):
        self._trash.clear()

    def _get_view(self):
        """Return first attached QGraphicsView safely (or None)."""
        views = self.views()
        return views[0] if views else None

    def drawBackground(self, painter, rect):
        settings = self.data_manager.load_settings()
        bg_type = settings.get("bg_type", "dot")  # "grid", "dot", "blank"

        if bg_type == "blank":
            painter.fillRect(rect, QColor(Colors.CREAM))
            return

        pixmap = get_pattern_pixmap(Colors.CREAM, bg_type, Metrics.GRID_DOT_SPACING)
        # fillRect with QBrush aligns tiling to scene (0, 0) to prevent pan/zoom moiré
        painter.fillRect(rect, QBrush(pixmap))

    def load_data(self):
        data = self.data_manager.load_tree()

        for n in data.get("nodes", []):
            nid = n["id"]
            node = NodeItem(
                nid,
                n["title"],
                n["x"],
                n["y"],
                self,
                color=n.get("color", resolve_accent_color("", seed=f"{nid}_accent")),
                tag=n.get("tag", ""),
                width=n.get("width", 220),
                height=n.get("height", 110),
                bg_color=n.get("bg_color", resolve_node_bg("", seed=nid)),
                is_favorite=n.get("is_favorite", False),
            )
            self.addItem(node)
            self.nodes[nid] = node

        for e in data.get("edges", []):
            source = self.nodes.get(e["source"])
            target = self.nodes.get(e["target"])
            if source and target:
                edge = EdgeItem(source, target)
                self.addItem(edge)
                self.edges.append(edge)

        self.nodes_count_changed.emit(len(self.nodes))

    def clear_scene(self):
        for edge in self.edges:
            edge.hide()
            self.removeItem(edge)
            self._trash.append(edge)
        for node in self.nodes.values():
            node.setGraphicsEffect(None)
            node.hide()
            self.removeItem(node)
            self._trash.append(node)
        self.edges.clear()
        self.nodes.clear()
        self.nodes_count_changed.emit(0)
        QTimer.singleShot(5000, self._empty_trash)

    def save_data(self):
        nodes_data = []
        for node_id, node in self.nodes.items():
            nodes_data.append(
                {
                    "id": node_id,
                    "title": node.title,
                    "x": node.x(),
                    "y": node.y(),
                    "color": node.color,
                    "tag": node.tag,
                    "width": node.width,
                    "height": node.height,
                    "bg_color": node.bg_color,
                    "is_favorite": node.is_favorite,
                }
            )

        edges_data = []
        for edge in self.edges:
            edges_data.append(
                {
                    "source": edge.source_node.node_id,
                    "target": edge.target_node.node_id,
                }
            )

        self.data_manager.save_tree({"nodes": nodes_data, "edges": edges_data})

    def add_node(self, title, x, y):
        node_id = self.data_manager.generate_id()
        pastel_bg = resolve_node_bg("", seed=node_id, on_light_blue=False)
        pastel_accent = resolve_accent_color("", seed=f"{node_id}_tag", avoid_bg=pastel_bg)
        node = NodeItem(
            node_id,
            title,
            x,
            y,
            self,
            color=pastel_accent,
            bg_color=pastel_bg,
            width=210,
            height=104,
        )
        self.addItem(node)
        self.nodes[node_id] = node
        self.save_data()

        self.data_manager.save_note_content(node_id, f"#{title}\n\nİçeriği buraya yazın...")
        self.nodes_count_changed.emit(len(self.nodes))
        return node

    def add_edge(self, source_node, target_node):
        for existing_edge in self.edges:
            if (existing_edge.source_node == source_node and existing_edge.target_node == target_node) or (
                existing_edge.source_node == target_node and existing_edge.target_node == source_node
            ):
                return
        edge = EdgeItem(source_node, target_node)
        self.addItem(edge)
        self.edges.append(edge)
        self.save_data()

    def update_edges(self):
        for edge in self.edges:
            edge.update_position()

    def update_edges_for_node(self, node):
        for edge in self.edges:
            if edge.source_node == node or edge.target_node == node:
                edge.update_position()

    def node_double_clicked(self, node):
        self.node_double_clicked_signal.emit(node.node_id, node.title)

    def mousePressEvent(self, event):
        view = self._get_view()
        if not view:
            super().mousePressEvent(event)
            return

        item = self.itemAt(event.scenePos(), view.transform())

        while item and not isinstance(item, NodeItem) and not isinstance(item, EdgeItem):
            item = item.parentItem()

        if event.button() == Qt.MouseButton.RightButton and isinstance(item, NodeItem):
            self.drawing_edge = True
            self.edge_source_node = item

            start_pos = item.pos() + item.boundingRect().center()
            path = QPainterPath(start_pos)
            path.lineTo(event.scenePos())

            self.temp_edge_item.setPath(path)
            self.temp_edge_item.show()
            event.accept()
        else:
            self.drawing_edge = False
            self.temp_edge_item.hide()
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drawing_edge and self.edge_source_node:
            start_pos = self.edge_source_node.pos() + self.edge_source_node.boundingRect().center()
            path = QPainterPath(start_pos)
            path.lineTo(event.scenePos())
            self.temp_edge_item.setPath(path)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        view = self._get_view()
        if self.drawing_edge:
            self.drawing_edge = False
            self.temp_edge_item.hide()

            if not view or not self.edge_source_node:
                event.accept()
                return

            item = self.itemAt(event.scenePos(), view.transform())
            while item and not isinstance(item, NodeItem):
                item = item.parentItem()

            if isinstance(item, NodeItem) and item != self.edge_source_node:
                self.add_edge(self.edge_source_node, item)
            elif isinstance(item, NodeItem) and item == self.edge_source_node:
                screen_pos = event.screenPos()
                node_ref = item
                QTimer.singleShot(50, lambda: self.show_node_context_menu(node_ref, screen_pos))
            self.edge_source_node = None
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton and view:
            item = self.itemAt(event.scenePos(), view.transform())
            if isinstance(item, EdgeItem):
                screen_pos = event.screenPos()
                edge_ref = item
                QTimer.singleShot(50, lambda: self.show_edge_context_menu(edge_ref, screen_pos))
                event.accept()
                return
            super().mouseReleaseEvent(event)
        else:
            super().mouseReleaseEvent(event)

    def show_edge_context_menu(self, edge, screen_pos):
        menu = QMenu()
        menu.setStyleSheet(
            build_menu_qss()
            + f"""
            QMenu::item:selected {{
                background-color: {Colors.PINK};
                color: {Colors.BLACK};
            }}
            """
        )
        action_delete = menu.addAction(f"✕  {t('disconnect').upper()}")
        action = menu.exec(screen_pos)

        if action == action_delete:
            QTimer.singleShot(0, lambda: self.delete_edge(edge))

    def delete_edge(self, edge):
        if edge in self.edges:
            self.edges.remove(edge)
            self._trash.append(edge)
        edge.hide()
        if edge.scene() == self:
            self.removeItem(edge)
        self.save_data()
        QTimer.singleShot(5000, self._empty_trash)

    def show_node_context_menu(self, node, screen_pos):
        menu = QMenu()
        menu.setStyleSheet(build_menu_qss())

        action_add_child = menu.addAction(f"＋  {t('create_child_note')}")
        action_appearance = menu.addAction(f"✦  {t('box_appearance')}")
        action_fav_text = (
            f"★  {t('remove_favorite')}"
            if getattr(node, "is_favorite", False)
            else f"☆  {t('add_favorite')}"
        )
        action_fav = menu.addAction(action_fav_text)
        menu.addSeparator()
        action_delete = menu.addAction(f"✕  {t('delete_note')}")

        action = menu.exec(screen_pos)

        if action == action_add_child:
            new_node = self.add_node(t("new_child_note"), node.pos().x() + 300, node.pos().y())
            self.add_edge(node, new_node)
        elif action == action_appearance:
            view = self._get_view()
            dialog = TagDialog(node.color, node.tag, node._effective_bg(), view)
            if dialog.exec():
                color, tag, bg_color = dialog.get_result()
                node.set_color_and_tag(color, tag)
                node.set_bg_color(bg_color)
                self.save_data()
                if view and view.window():
                    view.window().all_notes_page.refresh_notes()
        elif action == action_fav:
            node.set_favorite(not getattr(node, "is_favorite", False))
            self.save_data()
            view = self._get_view()
            if view and view.window():
                view.window().favorites_page.refresh_notes()
        elif action == action_delete:
            parent_win = self._get_view().window() if self._get_view() else None
            reply = QMessageBox.question(
                parent_win,
                t("confirm_delete"),
                t("confirm_delete_note", title=node.title),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                QTimer.singleShot(50, lambda: self.delete_node(node))

    def delete_node(self, node):
        view = self._get_view()
        if view and view.window():
            main_window = view.window()
            if getattr(main_window, "current_editing_node_id", None) == node.node_id:
                main_window.editor_panel.hide()
                main_window.current_editing_node_id = None

        edges_to_remove = [e for e in self.edges if e.source_node == node or e.target_node == node]
        for e in edges_to_remove:
            if e in self.edges:
                self.edges.remove(e)
                self._trash.append(e)
            e.hide()
            if e.scene() == self:
                self.removeItem(e)

        if node.node_id in self.nodes:
            self._trash.append(self.nodes.pop(node.node_id))

        if node.isSelected():
            node.setSelected(False)

        node.setGraphicsEffect(None)
        node.hide()
        if node.scene() == self:
            self.removeItem(node)

        self.data_manager.delete_note(node.node_id)
        self.save_data()
        self.nodes_count_changed.emit(len(self.nodes))
        QTimer.singleShot(5000, self._empty_trash)


class CanvasView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Optimizations preventing ghosting trails and zoom moiré
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)

    def wheelEvent(self, event):
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        self.scale(zoom_factor, zoom_factor)
