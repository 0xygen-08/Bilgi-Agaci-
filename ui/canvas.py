import copy

from PyQt6.QtCore import QMarginsF, QRectF, QSizeF, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QImage,
    QPageLayout,
    QPageSize,
    QPainter,
    QPainterPath,
    QPdfWriter,
    QPen,
)
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
    history_changed = pyqtSignal(bool, bool)  # can_undo, can_redo
    node_hovered_signal = pyqtSignal(object, object)  # node_item, screen_pos
    node_unhovered_signal = pyqtSignal(object)        # node_item
    MAX_HISTORY = 40

    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.setSceneRect(-5000, -5000, 10000, 10000)
        self.nodes = {}
        self.edges = []
        self.undo_stack = []
        self.redo_stack = []

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

    def reset_history(self):
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.history_changed.emit(False, False)

    def capture_snapshot(self) -> dict:
        """Capture complete state of nodes, edges, and note contents for Undo/Redo."""
        nodes_data = []
        notes_map = {}
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
                    "preview": getattr(node, "preview", ""),
                    "ocr_text": getattr(node, "ocr_text", ""),
                    "pdf_attachments": getattr(node, "pdf_attachments", []),
                }
            )
            try:
                notes_map[node_id] = self.data_manager.load_note_content(node_id)
            except Exception:
                pass

        edges_data = [
            {
                "source": edge.source_node.node_id,
                "target": edge.target_node.node_id,
            }
            for edge in self.edges
        ]
        return {
            "tree": copy.deepcopy({"nodes": nodes_data, "edges": edges_data}),
            "notes": notes_map,
        }

    def push_undo_snapshot(self, snapshot: dict):
        if not snapshot:
            return
        self.undo_stack.append(snapshot)
        if len(self.undo_stack) > self.MAX_HISTORY:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        self.history_changed.emit(bool(self.undo_stack), bool(self.redo_stack))

    def push_undo_state(self):
        self.push_undo_snapshot(self.capture_snapshot())

    def _restore_snapshot(self, snapshot: dict):
        tree = snapshot.get("tree", {"nodes": [], "edges": []})
        notes_map = snapshot.get("notes", {})
        for nid, content in notes_map.items():
            try:
                self.data_manager.save_note_content(nid, content)
            except Exception:
                pass
        self.data_manager.save_tree(copy.deepcopy(tree))
        self.clear_scene()
        self.load_data()
        view = self._get_view()
        if view and view.window():
            win = view.window()
            if getattr(win, "current_editing_node_id", None) not in self.nodes:
                win.editor_panel.hide()
                win.current_editing_node_id = None

    def undo(self) -> bool:
        if not self.undo_stack:
            return False
        current = self.capture_snapshot()
        self.redo_stack.append(current)
        prev = self.undo_stack.pop()
        self._restore_snapshot(prev)
        self.history_changed.emit(bool(self.undo_stack), bool(self.redo_stack))
        return True

    def redo(self) -> bool:
        if not self.redo_stack:
            return False
        current = self.capture_snapshot()
        self.undo_stack.append(current)
        nxt = self.redo_stack.pop()
        self._restore_snapshot(nxt)
        self.history_changed.emit(bool(self.undo_stack), bool(self.redo_stack))
        return True

    def set_active_tag_filter(self, tag_filter: str | None):
        """Highlights nodes containing the tag and dims unmatching nodes and edges."""
        clean_tag = tag_filter.strip().lower() if tag_filter else None
        if clean_tag and clean_tag.startswith("#"):
            clean_tag = clean_tag[1:]

        for node_id, node in self.nodes.items():
            if not clean_tag:
                node.setOpacity(1.0)
                continue

            node_tag = (node.tag or "").strip().lower()
            # Also check if note content contains the #tag
            content_tags = []
            try:
                cnt = self.data_manager.load_note_content(node_id)
                import re
                content_tags = [t.lower() for t in re.findall(r"#([a-zA-Z0-9çğıöşüÇĞİÖŞÜ_-]+)", cnt)]
            except Exception:
                pass

            matches = (clean_tag in node_tag) or (clean_tag in content_tags)
            node.setOpacity(1.0 if matches else 0.22)

        for edge in self.edges:
            if not clean_tag:
                edge.setOpacity(1.0)
            else:
                s_op = edge.source_node.opacity() if edge.source_node else 1.0
                t_op = edge.target_node.opacity() if edge.target_node else 1.0
                edge.setOpacity(1.0 if (s_op > 0.5 and t_op > 0.5) else 0.15)

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
                preview=n.get("preview", ""),
                ocr_text=n.get("ocr_text", ""),
            )
            node.pdf_attachments = n.get("pdf_attachments", [])
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
                    "preview": getattr(node, "preview", ""),
                    "ocr_text": getattr(node, "ocr_text", ""),
                    "pdf_attachments": getattr(node, "pdf_attachments", []),
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

    def add_node(self, title, x, y, record_undo=True):
        if record_undo:
            self.push_undo_state()
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
            preview="",
            ocr_text="",
        )
        self.addItem(node)
        self.nodes[node_id] = node
        self.save_data()

        self.data_manager.save_note_content(
            node_id, f"#{title}\n\n{t('default_note_placeholder')}"
        )
        self.nodes_count_changed.emit(len(self.nodes))
        return node

    def add_edge(self, source_node, target_node, record_undo=True):
        for existing_edge in self.edges:
            if (existing_edge.source_node == source_node and existing_edge.target_node == target_node) or (
                existing_edge.source_node == target_node and existing_edge.target_node == source_node
            ):
                return
        if record_undo:
            self.push_undo_state()
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

    def node_hover_enter(self, node, screen_pos):
        self.node_hovered_signal.emit(node, screen_pos)

    def node_hover_leave(self, node):
        self.node_unhovered_signal.emit(node)

    def _compute_export_bounds(self) -> QRectF:
        if not self.nodes:
            return QRectF(-400, -300, 800, 600)
        rect = QRectF()
        for node in self.nodes.values():
            node_rect = node.sceneBoundingRect()
            rect = rect.united(node_rect) if not rect.isNull() else node_rect
        for edge in self.edges:
            rect = rect.united(edge.sceneBoundingRect())
        pad = 64.0
        return rect.adjusted(-pad, -pad, pad, pad)

    def export_to_png(self, file_path: str) -> str:
        final_path = file_path if file_path.lower().endswith(".png") else file_path + ".png"
        bounds = self._compute_export_bounds()
        scale = 2.0
        img_w = max(400, min(8000, int(bounds.width() * scale)))
        img_h = max(300, min(8000, int(bounds.height() * scale)))

        image = QImage(img_w, img_h, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(QColor(Colors.CREAM))

        was_selected = [item for item in self.selectedItems()]
        self.clearSelection()

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.render(painter, QRectF(0, 0, img_w, img_h), bounds)
        painter.end()

        for item in was_selected:
            item.setSelected(True)

        image.save(final_path, "PNG")
        return final_path

    def export_to_pdf(self, file_path: str) -> str:
        final_path = file_path if file_path.lower().endswith(".pdf") else file_path + ".pdf"
        bounds = self._compute_export_bounds()

        writer = QPdfWriter(final_path)
        writer.setResolution(150)
        page_size = QPageSize(QSizeF(max(200.0, bounds.width() * 0.5), max(150.0, bounds.height() * 0.5)), QPageSize.Unit.Point)
        writer.setPageLayout(
            QPageLayout(page_size, QPageLayout.Orientation.Portrait, QMarginsF(0, 0, 0, 0))
        )

        was_selected = [item for item in self.selectedItems()]
        self.clearSelection()

        painter = QPainter(writer)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.render(painter, QRectF(0, 0, writer.width(), writer.height()), bounds)
        painter.end()

        for item in was_selected:
            item.setSelected(True)

        return final_path

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
        menu.setStyleSheet(build_menu_qss())
        action_delete = menu.addAction(t('disconnect'))
        action = menu.exec(screen_pos)

        if action == action_delete:
            QTimer.singleShot(0, lambda: self.delete_edge(edge))

    def delete_edge(self, edge, record_undo=True):
        if record_undo:
            self.push_undo_state()
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

        action_add_child = menu.addAction(f"+ {t('create_child_note')}")
        action_appearance = menu.addAction(t('box_appearance'))
        action_fav_text = (
            t('remove_favorite')
            if getattr(node, "is_favorite", False)
            else t('add_favorite')
        )
        action_fav = menu.addAction(action_fav_text)
        menu.addSeparator()
        action_delete = menu.addAction(t('delete_note'))

        action = menu.exec(screen_pos)

        if action == action_add_child:
            self.push_undo_state()
            new_node = self.add_node(
                t("new_child_note"), node.pos().x() + 300, node.pos().y(), record_undo=False
            )
            self.add_edge(node, new_node, record_undo=False)
        elif action == action_appearance:
            view = self._get_view()
            dialog = TagDialog(node.color, node.tag, node._effective_bg(), view)
            if dialog.exec():
                self.push_undo_state()
                color, tag, bg_color = dialog.get_result()
                node.set_color_and_tag(color, tag)
                node.set_bg_color(bg_color)
                self.save_data()
                if view and view.window():
                    view.window().all_notes_page.refresh_notes()
        elif action == action_fav:
            self.push_undo_state()
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

    def delete_node(self, node, record_undo=True):
        if record_undo:
            self.push_undo_state()
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

        self.save_data()
        self.data_manager.delete_note(node.node_id)
        self.nodes_count_changed.emit(len(self.nodes))
        QTimer.singleShot(5000, self._empty_trash)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            selected = self.selectedItems()
            selected_edges = [item for item in selected if isinstance(item, EdgeItem)]
            selected_nodes = [item for item in selected if isinstance(item, NodeItem)]
            for edge in selected_edges:
                self.delete_edge(edge)
            if selected_nodes:
                node = selected_nodes[0]
                parent_win = self._get_view().window() if self._get_view() else None
                reply = QMessageBox.question(
                    parent_win,
                    t("confirm_delete"),
                    t("confirm_delete_note", title=node.title),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.delete_node(node)
            event.accept()
            return
        super().keyPressEvent(event)


class CanvasView(QGraphicsView):
    MIN_ZOOM = 0.15
    MAX_ZOOM = 4.0

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

    def zoom_in(self):
        if self.transform().m11() * 1.2 <= self.MAX_ZOOM:
            self.scale(1.2, 1.2)

    def zoom_out(self):
        if self.transform().m11() / 1.2 >= self.MIN_ZOOM:
            self.scale(1.0 / 1.2, 1.0 / 1.2)

    def fit_all_nodes(self):
        sc = self.scene()
        if not sc or not getattr(sc, "nodes", None):
            self.resetTransform()
            self.centerOn(0, 0)
            return
        bounds = sc._compute_export_bounds()
        self.fitInView(bounds, Qt.AspectRatioMode.KeepAspectRatio)
        current_scale = self.transform().m11()
        if current_scale > 1.2:
            self.resetTransform()
            self.centerOn(bounds.center())
        elif current_scale < self.MIN_ZOOM:
            self.resetTransform()
            self.scale(self.MIN_ZOOM, self.MIN_ZOOM)
            self.centerOn(bounds.center())

    def wheelEvent(self, event):
        delta_y = event.angleDelta().y()
        if delta_y == 0:
            return

        zoom_in_factor = 1.15
        zoom_out_factor = 1.0 / zoom_in_factor
        zoom_factor = zoom_in_factor if delta_y > 0 else zoom_out_factor

        current_scale = self.transform().m11()
        new_scale = current_scale * zoom_factor
        if new_scale < self.MIN_ZOOM or new_scale > self.MAX_ZOOM:
            return

        self.scale(zoom_factor, zoom_factor)
