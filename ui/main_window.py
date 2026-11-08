import html
import os
import re
import urllib.parse

from PyQt6.QtCore import QEvent, QPoint, QStandardPaths, QTimer, QUrl, Qt, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QFont,
    QKeySequence,
    QShortcut,
    QTextBlockFormat,
    QTextCharFormat,
    QTextListFormat,
)
from PyQt6.QtWidgets import (
    QColorDialog,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QTabBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from thefuzz import process

from core.data_manager import extract_plain_preview
from core.i18n import t
from core.text_extractor import (
    extract_pdf_pages_structured,
    extract_text_from_file,
    extract_text_from_image,
    extract_text_from_pdf,
)

from .all_notes_page import AllNotesPage
from .backlinks_panel import BacklinksPanel
from .canvas import CanvasView, KnowledgeScene
from .graph_simulator import ForceLayoutSimulator
from .hover_preview import HoverPreviewWidget
from .pdf_viewer_dialog import PDFViewerDialog
from .components import (
    BrutalButton,
    BrutalCard,
    BrutalFAB,
    BrutalIconButton,
    BrutalInput,
    BrutalTag,
    DottedCreamFrame,
    SelectionFrameHero,
    SparkleWidget,
)
from .editor_toolbar import EditorToolbar
from .settings_page import SettingsPage
from .theme import (
    Borders,
    Colors,
    Metrics,
    Motion,
    Radii,
    Shadows,
    Spacing,
    Typography,
    build_global_qss,
    build_menu_qss,
)
from .wikilink_manager import WikiLinkHighlighter, WikiLinkPopup


class CustomTextEdit(QTextEdit):
    """Rich-text note editor supporting drag-and-drop images, heading enter reset, and [[wikilinks]]."""

    wikilink_clicked = pyqtSignal(str)  # Target note title to navigate to

    def __init__(self, data_manager=None, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.setObjectName("note_text_edit")
        self.setFont(Typography.canvas_font(Typography.PT_EDITOR_BODY, QFont.Weight.Medium))
        self.setMouseTracking(True)

        # Autocomplete Popup for [[
        self.wikilink_popup = WikiLinkPopup(self)
        self.wikilink_popup.note_selected.connect(self._insert_selected_wikilink)
        self._wikilink_start_pos = -1

        # Syntax Highlighter for [[wikilinks]] and #tags
        self.highlighter = WikiLinkHighlighter(self.document())

    def mouseMoveEvent(self, event):
        pos = event.pos()
        target = self._get_wikilink_at_pos(pos)
        if target:
            self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
            self.setToolTip(f"[[{target}]] (Düğüme gitmek için tıkla)")
        else:
            self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
            self.setToolTip("")
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            anchor = self.anchorAt(event.pos())
            if anchor and anchor.startswith("pdfpage:"):
                # Format: pdfpage:docs/filename.pdf?page=1
                import urllib.parse
                parsed = urllib.parse.urlparse(anchor)
                doc_rel = parsed.path
                qs = urllib.parse.parse_qs(parsed.query)
                page_num = int(qs.get("page", ["1"])[0])
                win = self.window()
                if hasattr(win, "data_manager") and hasattr(win, "open_pdf_viewer"):
                    full_path = os.path.join(win.data_manager.workspace_path, doc_rel)
                    if os.path.exists(full_path):
                        win.open_pdf_viewer(full_path, page_num)
                        event.accept()
                        return

            target = self._get_wikilink_at_pos(event.pos())
            if target:
                self.wikilink_clicked.emit(target)
                event.accept()
                return
        super().mouseReleaseEvent(event)

    def _get_wikilink_at_pos(self, pos: QPoint) -> str | None:
        cursor = self.cursorForPosition(pos)
        block = cursor.block()
        block_text = block.text()
        pos_in_block = cursor.positionInBlock()
        for m in re.finditer(r"\[\[(.*?)\]\]", block_text):
            if m.start() <= pos_in_block <= m.end():
                return m.group(1).strip()
        return None

    def _check_wikilink_trigger(self):
        cursor = self.textCursor()
        pos = cursor.position()
        text_before = cursor.block().text()[: cursor.positionInBlock()]
        match = re.search(r"\[\[([^\]]*)$", text_before)
        if match:
            query = match.group(1)
            self._wikilink_start_pos = pos - len(query) - 2
            win = self.window()
            all_nodes = []
            if hasattr(win, "data_manager") and win.data_manager:
                tree = win.data_manager.load_tree()
                all_nodes = tree.get("nodes", [])

            self.wikilink_popup.populate(all_nodes, filter_query=query)
            cr = self.cursorRect()
            global_pos = self.viewport().mapToGlobal(cr.bottomLeft())
            self.wikilink_popup.move(global_pos.x(), global_pos.y() + 4)
            self.wikilink_popup.show()
        else:
            if self.wikilink_popup.isVisible():
                self.wikilink_popup.hide()
            self._wikilink_start_pos = -1

    def _insert_selected_wikilink(self, target_title: str):
        cursor = self.textCursor()
        curr_pos = cursor.position()
        if self._wikilink_start_pos >= 0 and curr_pos >= self._wikilink_start_pos:
            cursor.setPosition(self._wikilink_start_pos)
            cursor.setPosition(curr_pos, QTextCursor.MoveMode.KeepAnchor)
            cursor.insertText(f"[[{target_title}]] ")
            self.setTextCursor(cursor)
        self.wikilink_popup.hide()
        self._wikilink_start_pos = -1

    def canInsertFromMimeData(self, source):
        if source.hasUrls():
            return True
        return super().canInsertFromMimeData(source)

    def insertFromMimeData(self, source):
        if source.hasUrls() and self.data_manager:
            urls = source.urls()
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    lower_p = file_path.lower()
                    if lower_p.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")):
                        saved_path = self.data_manager.save_image(file_path)
                        if saved_path:
                            uri = QUrl.fromLocalFile(saved_path).toString()
                            img_html = f'<br><img src="{uri}" width="100%"><br>'
                            self.textCursor().insertHtml(img_html)
                            win = self.window()
                            if hasattr(win, "_append_ocr_text_to_current_node"):
                                ocr_txt = extract_text_from_image(saved_path)
                                if ocr_txt:
                                    win._append_ocr_text_to_current_node(ocr_txt)
                            if hasattr(win, "save_current_note"):
                                win.save_current_note()
                        return
                    elif lower_p.endswith(".pdf"):
                        win = self.window()
                        if hasattr(win, "attach_pdf_to_current_node"):
                            win.attach_pdf_to_current_node(file_path)
                        return
        super().insertFromMimeData(source)

    def keyPressEvent(self, event):
        # Handle popup navigation if autocomplete is visible
        if self.wikilink_popup.isVisible():
            if event.key() == Qt.Key.Key_Down:
                self.wikilink_popup.move_selection(1)
                event.accept()
                return
            elif event.key() == Qt.Key.Key_Up:
                self.wikilink_popup.move_selection(-1)
                event.accept()
                return
            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab):
                if self.wikilink_popup.select_current():
                    event.accept()
                    return
            elif event.key() == Qt.Key.Key_Escape:
                self.wikilink_popup.hide()
                event.accept()
                return

        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_B:
                win = self.window()
                if hasattr(win, "format_bold"):
                    win.format_bold()
                    event.accept()
                    return
            elif event.key() == Qt.Key.Key_I:
                win = self.window()
                if hasattr(win, "format_italic"):
                    win.format_italic()
                    event.accept()
                    return
            elif event.key() == Qt.Key.Key_S:
                win = self.window()
                if hasattr(win, "save_current_note"):
                    win.save_current_note()
                    event.accept()
                    return

        if event.key() == Qt.Key.Key_Return and not event.modifiers():
            cursor = self.textCursor()
            fmt = cursor.blockFormat()
            if fmt.headingLevel() > 0:
                super().keyPressEvent(event)
                new_cursor = self.textCursor()
                new_fmt = new_cursor.blockFormat()
                new_fmt.setHeadingLevel(0)
                new_cursor.setBlockFormat(new_fmt)
                char_fmt = new_cursor.charFormat()
                char_fmt.setFontFamilies([Typography.family()])
                char_fmt.setFontPointSize(Typography.PT_EDITOR_BODY)
                char_fmt.setFontWeight(QFont.Weight.Medium)
                new_cursor.mergeCharFormat(char_fmt)
                self.setTextCursor(new_cursor)
                self.setCurrentCharFormat(char_fmt)
                return

        super().keyPressEvent(event)
        self._check_wikilink_trigger()


class _CanvasStageWidget(QWidget):
    """
    Hosts the Mind-Map CanvasView along with:
    1) A non-blocking Neo-Brutalist SelectionFrameHero empty-state overlay when 0 nodes exist
    2) A bottom-right Yellow Floating Action Button (BrutalFAB)
    """

    def __init__(self, canvas_view: CanvasView, on_create_node, parent=None):
        super().__init__(parent)
        self.canvas_view = canvas_view

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.canvas_view)

        self.empty_hero = SelectionFrameHero(
            badge_text=t("empty_canvas_badge"),
            headline_text=t("empty_canvas_title"),
            desc_text=t("empty_canvas_desc"),
            cta_text=t("new_node_btn"),
            parent=self,
        )
        self.empty_hero.resize(520, 320)
        self.empty_hero.action_clicked.connect(on_create_node)

        self.fab = BrutalFAB(self, tooltip=t("new_node_btn"))
        self.fab.clicked.connect(on_create_node)

        # Bottom-Left Zoom Controls Bar (－ / ⊡ / ＋)
        self.zoom_bar = QWidget(self)
        self.zoom_bar.setStyleSheet("background: transparent;")
        zoom_layout = QHBoxLayout(self.zoom_bar)
        zoom_layout.setContentsMargins(0, 0, 0, 0)
        zoom_layout.setSpacing(Spacing.XS + 2)

        self.btn_zoom_out = BrutalIconButton("－", variant="surface", size=28)
        self.btn_zoom_out.setToolTip(t("zoom_out_tooltip"))
        self.btn_zoom_out.clicked.connect(self.canvas_view.zoom_out)

        self.btn_zoom_fit = BrutalIconButton("1:1", variant="surface", size=28, min_width=36)
        self.btn_zoom_fit.setToolTip(t("zoom_reset_tooltip"))
        self.btn_zoom_fit.clicked.connect(self.canvas_view.fit_all_nodes)

        self.btn_zoom_in = BrutalIconButton("+", variant="surface", size=28)
        self.btn_zoom_in.setToolTip(t("zoom_in_tooltip"))
        self.btn_zoom_in.clicked.connect(self.canvas_view.zoom_in)

        self.btn_force_layout = BrutalIconButton("Ağ", variant="surface", size=28, min_width=38)
        self.btn_force_layout.setToolTip(t("force_layout_tooltip", default="Ağ Düzeni (Organize Et)"))

        zoom_layout.addWidget(self.btn_zoom_out)
        zoom_layout.addWidget(self.btn_zoom_fit)
        zoom_layout.addWidget(self.btn_zoom_in)
        zoom_layout.addWidget(self.btn_force_layout)
        self.zoom_bar.adjustSize()

    def set_empty_visible(self, is_empty: bool):
        self.empty_hero.setVisible(is_empty)
        if is_empty:
            self._reposition_overlays()
            self.empty_hero.raise_()
        self.fab.raise_()
        self.zoom_bar.raise_()

    def _reposition_overlays(self):
        # Center empty-state hero card
        hw = min(540, max(360, self.width() - Spacing.XXL * 2))
        hh = 320
        self.empty_hero.setGeometry(
            max(Spacing.MD, (self.width() - hw) // 2),
            max(Spacing.MD, (self.height() - hh) // 2),
            hw,
            hh,
        )
        # Anchor FAB at bottom-right
        margin = Spacing.XL + 4
        fx = max(Spacing.MD, self.width() - self.fab.width() - margin)
        fy = max(Spacing.MD, self.height() - self.fab.height() - margin)
        self.fab.move(fx, fy)
        self.fab.raise_()

        # Anchor Zoom Bar at bottom-left
        zx = Spacing.XL
        zy = max(Spacing.MD, self.height() - self.zoom_bar.height() - margin)
        self.zoom_bar.move(zx, zy)
        self.zoom_bar.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_overlays()


class MainWindow(QMainWindow):
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.setWindowTitle("Knowledge Tree")
        self.resize(1280, 840)

        Typography.load_fonts()
        self.setStyleSheet(build_global_qss())

        self._is_updating_tabs = False
        self.init_ui()
        self.refresh_tabs()

    def apply_system_theme(self):
        """Update stylesheets, patterns, and views when OS dark/light mode changes."""
        self.setStyleSheet(build_global_qss())
        if hasattr(self, "search_bar"):
            self.search_bar.fill_color = Colors.SURFACE
            self.search_bar.update()
        if hasattr(self, "editor_title"):
            self.editor_title.fill_color = Colors.SURFACE
            self.editor_title.update()
        if hasattr(self, "canvas_view") and hasattr(self.canvas_view, "canvas"):
            pattern = self.data_manager.load_settings().get("canvas_bg_pattern", "dot")
            self.canvas_view.canvas.set_background_pattern(pattern)
            self.canvas_view.canvas.update()
            self.scene.update()
        if hasattr(self, "sidebar_tabs_list"):
            self.refresh_tabs()
        if hasattr(self, "all_notes_page"):
            self.all_notes_page.refresh_notes()
        if hasattr(self, "favorites_page"):
            self.favorites_page.refresh_notes()
        self.update()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- SIDEBAR (Light Blue #C0F7FE + 3px Black Divider) ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(Metrics.SIDEBAR_WIDTH)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(Spacing.LG, Spacing.XL, Spacing.LG, Spacing.LG)
        sidebar_layout.setSpacing(Spacing.SM + 2)

        # Brand & Profile Card
        brand_card = BrutalCard(
            fill_color=Colors.SURFACE,
            radius=Radii.MD,
            padding=Spacing.MD,
        )
        brand_layout = QHBoxLayout(brand_card)
        brand_layout.setSpacing(Spacing.MD)

        brand_mark = QLabel("✦")
        brand_mark.setFixedSize(28, 28)
        brand_mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_mark.setFont(Typography.display(13))
        brand_mark.setStyleSheet(
            f"""
            background-color: {Colors.PRIMARY};
            color: #ffffff;
            border-radius: {Radii.SM}px;
            """
        )

        profile_col = QVBoxLayout()
        profile_col.setSpacing(1)
        initial_user = self.data_manager.load_settings().get("user_name") or "Harun"
        self.profile_name_lbl = QLabel(initial_user)
        self.profile_name_lbl.setFont(Typography.heading(Typography.SIZE_BODY))
        self.profile_name_lbl.setStyleSheet(f"color: {Colors.TEXT}; background: transparent;")
        profile_col.addWidget(self.profile_name_lbl)

        brand_layout.addWidget(brand_mark)
        brand_layout.addLayout(profile_col)
        brand_layout.addStretch()
        sidebar_layout.addWidget(brand_card)

        sidebar_layout.addSpacing(Spacing.XS)

        # Primary Add Node Button (Obsidian Violet)
        self.btn_new_node = BrutalButton(
            t("new_node_btn"),
            variant="add",
            icon_name="plus",
            min_face_height=34,
        )
        self.btn_new_node.setObjectName("new_node_btn")
        self.btn_new_node.clicked.connect(self.create_new_node)
        sidebar_layout.addWidget(self.btn_new_node)

        sidebar_layout.addSpacing(Spacing.SM)

        # Workspace Navigation Section
        nav_label = QLabel(t("workspace"))
        nav_label.setFont(Typography.label(Typography.SIZE_CAPTION))
        nav_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; margin: 0px {Spacing.XS}px;")
        sidebar_layout.addWidget(nav_label)

        self.btn_all_notes = BrutalButton(t("all_notes"), variant="nav", icon_name="all_notes", align_left=True, min_face_height=32)
        self.btn_all_notes.setCheckable(True)
        self.btn_all_notes.clicked.connect(self.switch_to_all_notes)
        sidebar_layout.addWidget(self.btn_all_notes)

        self.btn_tree_view = BrutalButton(t("tree_view"), variant="nav", icon_name="tree_view", align_left=True, min_face_height=32)
        self.btn_tree_view.setCheckable(True)
        self.btn_tree_view.setChecked(True)
        self.btn_tree_view.clicked.connect(self.switch_to_tree_view)
        sidebar_layout.addWidget(self.btn_tree_view)

        self.btn_favorites = BrutalButton(t("favorites"), variant="nav", icon_name="favorites", align_left=True, min_face_height=32)
        self.btn_favorites.setCheckable(True)
        self.btn_favorites.clicked.connect(self.switch_to_favorites)
        sidebar_layout.addWidget(self.btn_favorites)

        sidebar_layout.addSpacing(Spacing.SM)

        # Per-tab camera memory dictionary
        self.tab_camera_states = {}

        # Workspace Tabs Header
        tabs_header = QWidget()
        tabs_h_layout = QHBoxLayout(tabs_header)
        tabs_h_layout.setContentsMargins(Spacing.XS, 0, Spacing.XS, 0)
        tabs_h_layout.setSpacing(Spacing.SM)

        tabs_label = QLabel(t("tabs"))
        tabs_label.setFont(Typography.label(Typography.SIZE_CAPTION))
        tabs_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")

        btn_add_tab = BrutalIconButton("＋", variant="surface", size=26)
        btn_add_tab.setToolTip(t("new_tab"))
        btn_add_tab.clicked.connect(self.add_new_tab)

        tabs_h_layout.addWidget(tabs_label)
        tabs_h_layout.addStretch()
        tabs_h_layout.addWidget(btn_add_tab)
        sidebar_layout.addWidget(tabs_header)

        self.sidebar_tabs_list = QListWidget()
        self.sidebar_tabs_list.setObjectName("sidebar_tabs_list")
        self.sidebar_tabs_list.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sidebar_tabs_list.itemClicked.connect(self.on_sidebar_tab_clicked)
        self.sidebar_tabs_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sidebar_tabs_list.customContextMenuRequested.connect(self.show_tab_context_menu)
        sidebar_layout.addWidget(self.sidebar_tabs_list, 1)

        # Settings Button
        self.btn_settings = BrutalButton(t("settings"), variant="nav", icon_name="settings", align_left=True, min_face_height=32)
        self.btn_settings.setCheckable(True)
        self.btn_settings.clicked.connect(self.switch_to_storage)
        sidebar_layout.addWidget(self.btn_settings)

        # Auto Save Timer
        self.settings = self.data_manager.load_settings()
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self._auto_save)
        if self.settings.get("auto_save", True):
            self.auto_save_timer.start(5000)

        # --- RIGHT MAIN AREA ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Topbar (Light Blue #C0F7FE + 3px Black Bottom Border)
        topbar = QWidget()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(Metrics.TOPBAR_HEIGHT)
        top_layout = QHBoxLayout(topbar)
        top_layout.setContentsMargins(Spacing.XL, 0, Spacing.XL, 0)
        top_layout.setSpacing(Spacing.MD)

        self.btn_toggle = BrutalIconButton("Menü", variant="surface", size=Metrics.ICON_BTN_SIZE, min_width=36)
        self.btn_toggle.setToolTip("Menü")
        self.btn_toggle.clicked.connect(self.toggle_sidebar)
        top_layout.addWidget(self.btn_toggle)

        self.search_bar = BrutalInput(
            placeholder=t("search_placeholder"),
            fill_color=Colors.SURFACE,
            face_height=32,
        )
        self.search_bar.setObjectName("search_bar")
        self.search_bar.setFixedWidth(Metrics.SEARCH_WIDTH)
        self.search_bar.textChanged.connect(self.on_search_text_changed)
        top_layout.addWidget(self.search_bar)

        self.top_tabs = QTabBar()
        self.top_tabs.setDocumentMode(False)
        self.top_tabs.setDrawBase(False)
        self.top_tabs.setExpanding(False)
        self.top_tabs.setUsesScrollButtons(False)
        self.top_tabs.setTabsClosable(True)
        self.top_tabs.setCursor(Qt.CursorShape.PointingHandCursor)
        self.top_tabs.tabCloseRequested.connect(self.close_tab_by_index)
        self.top_tabs.tabBarDoubleClicked.connect(self.rename_tab_by_index)
        self.top_tabs.currentChanged.connect(self.on_top_tab_changed)
        top_layout.addWidget(self.top_tabs, 1)

        # Undo / Redo / Export Controls
        self.btn_undo = BrutalIconButton("↶", variant="surface", size=Metrics.ICON_BTN_SIZE)
        self.btn_undo.setToolTip(t("undo_tooltip"))
        self.btn_undo.clicked.connect(self._handle_undo)
        top_layout.addWidget(self.btn_undo)

        self.btn_redo = BrutalIconButton("↷", variant="surface", size=Metrics.ICON_BTN_SIZE)
        self.btn_redo.setToolTip(t("redo_tooltip"))
        self.btn_redo.clicked.connect(self._handle_redo)
        top_layout.addWidget(self.btn_redo)

        self.btn_export = BrutalButton(
            t("export_btn"),
            variant="surface",
            icon_name="export",
            min_face_height=Metrics.ICON_BTN_SIZE,
            pad_x=Spacing.SM,
        )
        self.btn_export.setToolTip(t("export_tooltip"))
        self.btn_export.clicked.connect(self.show_export_menu)
        top_layout.addWidget(self.btn_export)

        # Content Pages Stack
        self.stacked_widget = QStackedWidget()

        # Page 0: Tree View + Note Editor Split Pane
        self.tree_page = QWidget()
        tree_layout = QVBoxLayout(self.tree_page)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        tree_layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(Borders.DEFAULT)

        # Canvas + Empty State Hero + Floating FAB
        self.scene = KnowledgeScene(self.data_manager)
        self.scene.node_double_clicked_signal.connect(self.open_editor)
        self.canvas_view = CanvasView(self.scene)
        self.canvas_stage = _CanvasStageWidget(self.canvas_view, self.create_new_node)
        self.hover_preview = HoverPreviewWidget(self.canvas_stage)
        self.scene.node_hovered_signal.connect(self._on_node_hover_enter)
        self.scene.node_unhovered_signal.connect(self._on_node_hover_leave)
        self.force_simulator = ForceLayoutSimulator(self.scene, self)
        self.canvas_stage.btn_force_layout.clicked.connect(self._toggle_force_layout)
        self.scene.nodes_count_changed.connect(
            lambda count: self.canvas_stage.set_empty_visible(count == 0)
        )
        self.canvas_stage.set_empty_visible(len(self.scene.nodes) == 0)

        # Note Editor Panel (Cream #FBFAE8 Dotted-Grid Canvas)
        self.editor_panel = DottedCreamFrame(left_border=True)
        self.editor_panel.setObjectName("editor_panel")
        self.editor_panel.setMinimumWidth(Metrics.EDITOR_MIN_WIDTH)
        self.editor_panel.hide()
        editor_layout = QVBoxLayout(self.editor_panel)
        editor_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.XL)
        editor_layout.setSpacing(Spacing.MD)

        # Editor Header Bar
        editor_header = QHBoxLayout()
        editor_header.setSpacing(Spacing.SM)
        editor_title_lbl = QLabel(t("edit_node"))
        editor_title_lbl.setFont(Typography.heading(Typography.SIZE_BODY))
        editor_title_lbl.setStyleSheet(f"color: {Colors.TEXT};")
        editor_header.addWidget(editor_title_lbl)
        editor_header.addStretch()

        self.btn_close_editor = BrutalIconButton("✕", variant="surface", size=26)
        self.btn_close_editor.setToolTip(t("close_editor_tooltip"))
        self.btn_close_editor.clicked.connect(self._close_editor_panel)
        editor_header.addWidget(self.btn_close_editor)
        editor_layout.addLayout(editor_header)

        # Title Input
        self.editor_title = BrutalInput(
            fill_color=Colors.SURFACE,
            face_height=38,
            is_heading=True,
        )
        self.editor_title.textChanged.connect(self.update_node_title)
        editor_layout.addWidget(self.editor_title)

        # Formatting Toolbar
        self.editor_toolbar = EditorToolbar()
        self.editor_toolbar.format_bold_signal.connect(self.format_bold)
        self.editor_toolbar.format_italic_signal.connect(self.format_italic)
        self.editor_toolbar.format_h1_signal.connect(self.format_h1)
        self.editor_toolbar.format_h2_signal.connect(self.format_h2)
        self.editor_toolbar.format_bullet_list_signal.connect(self.format_bullet_list)
        self.editor_toolbar.insert_image_signal.connect(self.insert_image)
        self.editor_toolbar.format_color_signal.connect(self.format_color)
        editor_layout.addWidget(self.editor_toolbar)

        # Clean Note Body Frame
        body_frame = BrutalCard(
            fill_color=Colors.SURFACE,
            radius=Radii.MD,
            padding=Spacing.XS,
        )
        body_frame_layout = QVBoxLayout(body_frame)
        body_frame_layout.setContentsMargins(0, 0, 0, 0)

        self.text_edit = CustomTextEdit(self.data_manager)
        self.text_edit.document().setDefaultStyleSheet("body, p, li { line-height: 155%; }")
        self.text_edit.cursorPositionChanged.connect(self.update_editor_toolbar_state)
        self.text_edit.wikilink_clicked.connect(self._handle_wikilink_navigation)
        body_frame_layout.addWidget(self.text_edit)
        editor_layout.addWidget(body_frame, 1)

        # Obsidian-style Backlinks Panel
        self.backlinks_panel = BacklinksPanel(self.data_manager, self.editor_panel)
        self.backlinks_panel.backlink_clicked.connect(self._navigate_to_backlink_node)
        editor_layout.addWidget(self.backlinks_panel)

        # Clean Save Note CTA Button
        self.btn_save_note = BrutalButton(
            t('save_changes'),
            variant="primary",
            min_face_height=34,
        )
        self.btn_save_note.setObjectName("primary_btn")
        self.btn_save_note.clicked.connect(self.save_current_note)
        editor_layout.addWidget(self.btn_save_note)

        self.splitter.addWidget(self.canvas_stage)
        self.splitter.addWidget(self.editor_panel)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)

        tree_layout.addWidget(self.splitter)

        # Page 1: All Notes
        self.all_notes_page = AllNotesPage(self.data_manager, self, favorites_only=False)
        # Page 2: Storage & Settings
        self.settings_page = SettingsPage(self.data_manager, self)
        # Page 3: Favorites
        self.favorites_page = AllNotesPage(self.data_manager, self, favorites_only=True)

        self.stacked_widget.addWidget(self.tree_page)
        self.stacked_widget.addWidget(self.all_notes_page)
        self.stacked_widget.addWidget(self.settings_page)
        self.stacked_widget.addWidget(self.favorites_page)

        # Search Results Overlay Popup
        self.search_results = QListWidget(self)
        self.search_results.setObjectName("search_results")
        self.search_results.hide()
        self.search_results.itemClicked.connect(self.go_to_search_result)

        right_layout.addWidget(topbar)
        right_layout.addWidget(self.stacked_widget)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(right_panel)

        self.current_editing_node_id = None
        self._title_modified = False

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(lambda: self.perform_search(self.search_bar.text()))

        # Global Keyboard Shortcuts
        self._save_shortcut = QShortcut(QKeySequence.StandardKey.Save, self)
        self._save_shortcut.activated.connect(self.save_current_note)

        self._undo_shortcut = QShortcut(QKeySequence.StandardKey.Undo, self)
        self._undo_shortcut.activated.connect(self._handle_undo)

        self._redo_shortcut = QShortcut(QKeySequence.StandardKey.Redo, self)
        self._redo_shortcut.activated.connect(self._handle_redo)

        self._redo_ctrl_y = QShortcut(QKeySequence("Ctrl+Y"), self)
        self._redo_ctrl_y.activated.connect(self._handle_redo)

        self._zoom_in_shortcut = QShortcut(QKeySequence.StandardKey.ZoomIn, self)
        self._zoom_in_shortcut.activated.connect(self.canvas_view.zoom_in)

        self._zoom_out_shortcut = QShortcut(QKeySequence.StandardKey.ZoomOut, self)
        self._zoom_out_shortcut.activated.connect(self.canvas_view.zoom_out)

        self._zoom_reset_shortcut = QShortcut(QKeySequence("Ctrl+0"), self)
        self._zoom_reset_shortcut.activated.connect(self.canvas_view.fit_all_nodes)

        self._esc_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self._esc_shortcut.activated.connect(self._dismiss_search_results)

    def _handle_undo(self):
        if self.text_edit.hasFocus():
            self.text_edit.undo()
            return
        self.scene.undo()

    def _handle_redo(self):
        if self.text_edit.hasFocus():
            self.text_edit.redo()
            return
        self.scene.redo()

    def _toggle_force_layout(self):
        if self.force_simulator.is_running():
            self.force_simulator.stop()
        else:
            self.force_simulator.start()

    def _on_node_hover_enter(self, node, screen_pos):
        # Don't show preview if node is currently open in editor
        if getattr(self, "current_editing_node_id", None) == node.node_id and self.editor_panel.isVisible():
            self.hover_preview.hide()
            return
        preview_text = getattr(node, "preview", "")
        if not preview_text:
            content = self.data_manager.load_note_content(node.node_id)
            preview_text = extract_plain_preview(content, title=node.title, max_len=140)

        # Map screen position to canvas_stage coordinate space
        stage_pos = self.canvas_stage.mapFromGlobal(screen_pos.toPoint() if hasattr(screen_pos, "toPoint") else screen_pos)
        self.hover_preview.show_preview(node.title, preview_text, getattr(node, "tag", ""), stage_pos)

    def _on_node_hover_leave(self, node):
        self.hover_preview.hide()

    def _dismiss_search_results(self):
        if self.search_results.isVisible():
            self.search_results.hide()

    def mousePressEvent(self, event):
        if self.search_results.isVisible() and not self.search_results.geometry().contains(event.pos()):
            self.search_results.hide()
        super().mousePressEvent(event)

    def closeEvent(self, event):
        if self.current_editing_node_id:
            self.save_current_note()
        self.scene.save_data()
        super().closeEvent(event)

    def _close_editor_panel(self):
        if self.current_editing_node_id:
            self.save_current_note()
        self.editor_panel.hide()
        self.current_editing_node_id = None
        self._title_modified = False

    def _position_search_results(self):
        global_pos = self.search_bar.mapTo(self, self.search_bar.rect().bottomLeft())
        dropdown_w = max(420, self.search_bar.width())
        self.search_results.setGeometry(
            global_pos.x(),
            global_pos.y() + Spacing.XS,
            dropdown_w,
            Metrics.SEARCH_DROPDOWN_HEIGHT,
        )
        self.search_results.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_search_results()

    def refresh_tabs(self):
        self._is_updating_tabs = True
        self.sidebar_tabs_list.clear()

        self.top_tabs.blockSignals(True)
        while self.top_tabs.count() > 0:
            self.top_tabs.removeTab(0)

        tabs = self.data_manager.get_tabs()
        active = self.data_manager.active_tab_id

        active_idx = 0
        for i, tab_info in enumerate(tabs):
            item = QListWidgetItem(tab_info['name'].upper())
            item.setData(Qt.ItemDataRole.UserRole, tab_info["id"])
            item.setForeground(QColor(Colors.BLACK))
            self.sidebar_tabs_list.addItem(item)

            self.top_tabs.addTab(tab_info["name"].upper())
            self.top_tabs.setTabData(i, tab_info["id"])

            if tab_info["id"] == active:
                active_idx = i

        self.sidebar_tabs_list.setCurrentRow(active_idx)
        self.top_tabs.setCurrentIndex(active_idx)
        self.top_tabs.blockSignals(False)
        self._is_updating_tabs = False

        self.scene.clear_scene()
        self.scene.reset_history()
        self.scene.load_data()
        self.canvas_stage.set_empty_visible(len(self.scene.nodes) == 0)
        self.canvas_view.viewport().update()

    def on_top_tab_changed(self, index):
        if self._is_updating_tabs or index < 0:
            return
        tab_id = self.top_tabs.tabData(index)
        if tab_id and tab_id != self.data_manager.active_tab_id:
            if self.current_editing_node_id:
                self.save_current_note()
            self.scene.save_data()

            self.save_camera_state(self.data_manager.active_tab_id)
            self.data_manager.switch_tab(tab_id)
            self.refresh_tabs()
            self.restore_camera_state(tab_id)

            self.editor_panel.hide()
            self.current_editing_node_id = None

            current_idx = self.stacked_widget.currentIndex()
            if current_idx == 1:
                self.all_notes_page.refresh_notes()
            elif current_idx == 3:
                self.favorites_page.refresh_notes()

    def update_profile_name(self, name: str):
        clean = (name or "HARUN").strip().upper()
        self.profile_name_lbl.setText(clean)

    def rename_tab_by_index(self, index):
        if index < 0:
            return
        tab_id = self.top_tabs.tabData(index)
        if tab_id:
            self.rename_tab_by_id(tab_id)

    def rename_tab_by_id(self, tab_id):
        current_name = ""
        for tab in self.data_manager.get_tabs():
            if tab.get("id") == tab_id:
                current_name = tab.get("name", "")
                break
        new_name, ok = QInputDialog.getText(
            self,
            t("rename_tab"),
            t("enter_new_tab_name"),
            text=current_name,
        )
        if ok and new_name.strip():
            if self.current_editing_node_id:
                self.save_current_note()
            self.scene.save_data()
            if self.data_manager.rename_tab(tab_id, new_name.strip()):
                self.refresh_tabs()

    def close_tab_by_index(self, index):
        tab_id = self.top_tabs.tabData(index)
        if tab_id:
            self.close_tab_by_id(tab_id)

    def show_tab_context_menu(self, pos):
        item = self.sidebar_tabs_list.itemAt(pos)
        if item:
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
            action_rename = menu.addAction(t('rename_tab').upper())
            menu.addSeparator()
            action_close = menu.addAction(t('close_tab').upper())
            action = menu.exec(self.sidebar_tabs_list.mapToGlobal(pos))
            tab_id = item.data(Qt.ItemDataRole.UserRole)
            if action == action_rename and tab_id:
                self.rename_tab_by_id(tab_id)
            elif action == action_close and tab_id:
                self.close_tab_by_id(tab_id)

    def close_tab_by_id(self, tab_id):
        reply = QMessageBox.question(
            self,
            t("close_tab"),
            t("confirm_delete_tab"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            was_active = tab_id == self.data_manager.active_tab_id
            if not was_active and self.current_editing_node_id:
                self.save_current_note()
                self.scene.save_data()
            success = self.data_manager.delete_tab(tab_id)
            if not success:
                QMessageBox.warning(self, t("error"), t("at_least_one_tab"))
            else:
                if was_active:
                    self.editor_panel.hide()
                    self.current_editing_node_id = None
                    self._title_modified = False
                self.tab_camera_states.pop(tab_id, None)
                self.refresh_tabs()
                current_idx = self.stacked_widget.currentIndex()
                if current_idx == 1:
                    self.all_notes_page.refresh_notes()
                elif current_idx == 3:
                    self.favorites_page.refresh_notes()

    def on_sidebar_tab_clicked(self, item):
        tab_id = item.data(Qt.ItemDataRole.UserRole)
        if tab_id and tab_id != self.data_manager.active_tab_id:
            if self.current_editing_node_id:
                self.save_current_note()
            self.scene.save_data()

            self.save_camera_state(self.data_manager.active_tab_id)
            self.data_manager.switch_tab(tab_id)
            self.refresh_tabs()
            self.restore_camera_state(tab_id)
            self.editor_panel.hide()
            self.current_editing_node_id = None

            current_idx = self.stacked_widget.currentIndex()
            if current_idx == 1:
                self.all_notes_page.refresh_notes()
            elif current_idx == 3:
                self.favorites_page.refresh_notes()

    def add_new_tab(self):
        name, ok = QInputDialog.getText(self, t("new_tab"), t("enter_tab_name"))
        if ok and name.strip():
            if self.current_editing_node_id:
                self.save_current_note()
            self.scene.save_data()

            self.save_camera_state(self.data_manager.active_tab_id)
            self.data_manager.add_tab(name.strip())
            self.refresh_tabs()
            self.restore_camera_state(self.data_manager.active_tab_id)

            self.switch_to_tree_view()

    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def _sync_nav_checks(self, active_page: int):
        self.btn_tree_view.setChecked(active_page == 0)
        self.btn_all_notes.setChecked(active_page == 1)
        self.btn_settings.setChecked(active_page == 2)
        self.btn_favorites.setChecked(active_page == 3)
        for btn in (self.btn_tree_view, self.btn_all_notes, self.btn_settings, self.btn_favorites):
            btn.update()

    def switch_to_tree_view(self):
        self.stacked_widget.setCurrentIndex(0)
        self._sync_nav_checks(0)

    def switch_to_all_notes(self):
        self.stacked_widget.setCurrentIndex(1)
        self._sync_nav_checks(1)
        self.all_notes_page.refresh_notes()

    def save_camera_state(self, tab_id):
        if not tab_id:
            return
        self.tab_camera_states[tab_id] = {
            "transform": self.canvas_view.transform(),
            "h_scroll": self.canvas_view.horizontalScrollBar().value(),
            "v_scroll": self.canvas_view.verticalScrollBar().value(),
        }

    def restore_camera_state(self, tab_id):
        state = self.tab_camera_states.get(tab_id)
        if state:
            self.canvas_view.setTransform(state["transform"])
            self.canvas_view.horizontalScrollBar().setValue(state["h_scroll"])
            self.canvas_view.verticalScrollBar().setValue(state["v_scroll"])
        else:
            self.canvas_view.resetTransform()
            self.canvas_view.centerOn(0, 0)

    def switch_to_favorites(self):
        self.stacked_widget.setCurrentIndex(3)
        self._sync_nav_checks(3)
        self.favorites_page.refresh_notes()

    def switch_to_storage(self):
        self.stacked_widget.setCurrentIndex(2)
        self._sync_nav_checks(2)

    def create_new_node(self):
        view_center = self.canvas_view.mapToScene(self.canvas_view.viewport().rect().center())
        node = self.scene.add_node(t("new_node"), view_center.x(), view_center.y())
        self.open_editor(node.node_id, node.title)
        self.switch_to_tree_view()

    def open_editor(self, node_id, title):
        if self.current_editing_node_id and self.current_editing_node_id != node_id:
            self.save_current_note()

        self.current_editing_node_id = None  # block update_node_title during initial setText
        self.editor_title.setText(title)
        self.current_editing_node_id = node_id
        self._title_modified = False

        content = self.data_manager.load_note_content(node_id)
        is_html = bool(
            re.search(
                r"<(?:!doctype|html|body|p|div|span|h[1-6]|ul|ol|li|br|img|b|i|strong|em)\b",
                content,
                re.IGNORECASE,
            )
        )
        if not is_html:
            self.text_edit.setPlainText(content)
        else:
            # Normalize legacy dark-theme default light body colors to crisp #000000 ink
            display_html = re.sub(
                r"color:\s*#(?:cbd6e5|e8edf6|dce7f5|d9e2ee|ffffff)\b",
                f"color:{Colors.BLACK}",
                content,
                flags=re.IGNORECASE,
            )
            # Rewrite image paths to current workspace images_dir for cross-machine portability
            def _fix_img_src(match):
                fname = urllib.parse.unquote(match.group(1))
                local_img = os.path.join(self.data_manager.images_dir, fname)
                if os.path.exists(local_img):
                    return f'src="{QUrl.fromLocalFile(local_img).toString()}"'
                return match.group(0)

            display_html = re.sub(
                r'src=["\']file:///[^"\']*?/images/([^"\'/\\]+)["\']',
                _fix_img_src,
                display_html,
            )
            self.text_edit.setHtml(display_html)
        self.text_edit.document().setModified(False)

        # Refresh Obsidian-style Backlinks for this node
        self.backlinks_panel.refresh_backlinks(node_id, title)

        if not self.editor_panel.isVisible():
            self.editor_panel.show()
            total_w = max(800, self.splitter.width())
            editor_w = max(Metrics.EDITOR_MIN_WIDTH, int(total_w * 0.40))
            self.splitter.setSizes([total_w - editor_w, editor_w])

    def update_node_title(self, new_title):
        if self.current_editing_node_id:
            node = self.scene.nodes.get(self.current_editing_node_id)
            if node:
                node.title = new_title
                node.title_item.setPlainText(new_title)
                node._adjust_title_font()
                self._title_modified = True
                self.scene.save_data()

    def _auto_save(self):
        if self.current_editing_node_id and self.editor_panel.isVisible():
            if not self.text_edit.document().isModified() and not self._title_modified:
                return
            node = self.scene.nodes.get(self.current_editing_node_id)
            if node:
                content = self.text_edit.toHtml()
                node.preview = extract_plain_preview(content, title=node.title, max_len=100)
                self.scene.save_data()
                self.data_manager.save_note_content(self.current_editing_node_id, content)
                self.text_edit.document().setModified(False)
                self._title_modified = False
                # Keep mind-map edges in sync on auto-save
                self._sync_wikilink_edges(node, self.text_edit.toPlainText())

    def save_current_note(self):
        if self.current_editing_node_id:
            new_title = self.editor_title.text()
            content = self.text_edit.toHtml()
            node = self.scene.nodes.get(self.current_editing_node_id)
            if node:
                node.title = new_title
                node.title_item.setPlainText(new_title)
                node._adjust_title_font()
                node.preview = extract_plain_preview(content, title=new_title, max_len=100)
                self.scene.save_data()
            self.data_manager.save_note_content(self.current_editing_node_id, content)
            self.text_edit.document().setModified(False)
            self._title_modified = False

            # Automatically establish mind-map edges for [[wikilink]] references
            self._sync_wikilink_edges(node, self.text_edit.toPlainText())

    def _sync_wikilink_edges(self, source_node, plain_text: str):
        if not source_node or not plain_text:
            return
        # Find all [[Target Title]] in note text
        matches = re.findall(r"\[\[(.*?)\]\]", plain_text)
        if not matches:
            return

        title_to_node = {
            n.title.strip().lower(): n
            for n in self.scene.nodes.values()
            if n != source_node
        }

        for target_title in set(matches):
            t_clean = target_title.strip().lower()
            target_node = title_to_node.get(t_clean)
            if target_node:
                self.scene.add_edge(source_node, target_node, record_undo=False)

    def _handle_wikilink_navigation(self, target_title: str):
        """Navigate to or create the referenced wikilink node."""
        if not target_title:
            return
        # Save current note before moving
        self.save_current_note()

        # Check if node exists in current scene
        target_clean = target_title.strip().lower()
        found_node = None
        for node in self.scene.nodes.values():
            if node.title.strip().lower() == target_clean:
                found_node = node
                break

        if found_node:
            self.switch_to_tree_view()
            self.canvas_view.centerOn(found_node.pos())
            self.open_editor(found_node.node_id, found_node.title)
        else:
            # Ask to create new node
            reply = QMessageBox.question(
                self,
                t("create_node_prompt_title"),
                t("create_node_prompt_msg", title=target_title),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Yes:
                curr_node = self.scene.nodes.get(self.current_editing_node_id)
                if curr_node:
                    x = curr_node.pos().x() + 320
                    y = curr_node.pos().y()
                else:
                    center = self.canvas_view.mapToScene(self.canvas_view.viewport().rect().center())
                    x, y = center.x(), center.y()

                new_node = self.scene.add_node(target_title, x, y)
                if curr_node:
                    self.scene.add_edge(curr_node, new_node, record_undo=False)
                self.switch_to_tree_view()
                self.canvas_view.centerOn(new_node.pos())
                self.open_editor(new_node.node_id, new_node.title)

    def _navigate_to_backlink_node(self, node_id: str):
        """Navigate to a backlink node when clicked in the BacklinksPanel."""
        if not node_id:
            return
        node = self.scene.nodes.get(node_id)
        if node:
            self.save_current_note()
            self.switch_to_tree_view()
            self.canvas_view.centerOn(node.pos())
            self.open_editor(node.node_id, node.title)

    def update_editor_toolbar_state(self):
        if not self.text_edit.hasFocus():
            return
        fmt = self.text_edit.currentCharFormat()
        is_bold = fmt.fontWeight() >= QFont.Weight.Bold
        is_italic = fmt.fontItalic()
        cursor = self.text_edit.textCursor()
        block_fmt = cursor.blockFormat()
        is_h1 = block_fmt.headingLevel() == 1
        is_h2 = block_fmt.headingLevel() == 2
        is_list = cursor.currentList() is not None
        self.editor_toolbar.update_states(is_bold, is_italic, is_h1, is_h2, is_list)

    def format_bold(self):
        fmt = self.text_edit.currentCharFormat()
        weight = (
            QFont.Weight.Bold
            if fmt.fontWeight() < QFont.Weight.Bold
            else QFont.Weight.Medium
        )
        fmt.setFontWeight(weight)
        self.text_edit.mergeCurrentCharFormat(fmt)
        self.text_edit.setFocus()
        self.update_editor_toolbar_state()

    def format_italic(self):
        fmt = self.text_edit.currentCharFormat()
        fmt.setFontItalic(not fmt.fontItalic())
        self.text_edit.mergeCurrentCharFormat(fmt)
        self.text_edit.setFocus()
        self.update_editor_toolbar_state()

    def format_h1(self):
        cursor = self.text_edit.textCursor()
        cursor.select(cursor.SelectionType.BlockUnderCursor)
        block_fmt = cursor.blockFormat()
        new_level = 0 if block_fmt.headingLevel() == 1 else 1
        block_fmt.setHeadingLevel(new_level)
        cursor.setBlockFormat(block_fmt)
        char_fmt = QTextCharFormat()
        char_fmt.setFontFamilies([Typography.family()])
        if new_level == 1:
            char_fmt.setFontPointSize(Typography.PT_EDITOR_H1)
            char_fmt.setFontWeight(QFont.Weight.ExtraBold)
        else:
            char_fmt.setFontPointSize(Typography.PT_EDITOR_BODY)
            char_fmt.setFontWeight(QFont.Weight.Medium)
        cursor.mergeCharFormat(char_fmt)
        cursor.clearSelection()
        self.text_edit.setCurrentCharFormat(char_fmt)
        self.text_edit.setFocus()
        self.update_editor_toolbar_state()

    def format_h2(self):
        cursor = self.text_edit.textCursor()
        cursor.select(cursor.SelectionType.BlockUnderCursor)
        block_fmt = cursor.blockFormat()
        new_level = 0 if block_fmt.headingLevel() == 2 else 2
        block_fmt.setHeadingLevel(new_level)
        cursor.setBlockFormat(block_fmt)
        char_fmt = QTextCharFormat()
        char_fmt.setFontFamilies([Typography.family()])
        if new_level == 2:
            char_fmt.setFontPointSize(Typography.PT_EDITOR_H2)
            char_fmt.setFontWeight(QFont.Weight.Bold)
        else:
            char_fmt.setFontPointSize(Typography.PT_EDITOR_BODY)
            char_fmt.setFontWeight(QFont.Weight.Medium)
        cursor.mergeCharFormat(char_fmt)
        cursor.clearSelection()
        self.text_edit.setCurrentCharFormat(char_fmt)
        self.text_edit.setFocus()
        self.update_editor_toolbar_state()

    def format_bullet_list(self):
        cursor = self.text_edit.textCursor()
        if cursor.currentList() is not None:
            fmt = QTextBlockFormat(cursor.blockFormat())
            fmt.setObjectIndex(-1)
            cursor.setBlockFormat(fmt)
        else:
            cursor.createList(QTextListFormat.Style.ListDisc)
        self.text_edit.setFocus()
        self.update_editor_toolbar_state()

    def _append_ocr_text_to_current_node(self, extracted_txt: str):
        if not extracted_txt or not self.current_editing_node_id:
            return
        node = self.scene.nodes.get(self.current_editing_node_id)
        if not node:
            return
        clean = extracted_txt.strip()
        existing = getattr(node, "ocr_text", "") or ""
        if clean and clean not in existing:
            node.ocr_text = (existing + "\n" + clean).strip() if existing else clean
            self.scene.save_data()

    def insert_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t("image_tooltip"),
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp)",
        )
        if file_path:
            saved_path = self.data_manager.save_image(file_path)
            if saved_path:
                uri = QUrl.fromLocalFile(saved_path).toString()
                img_html = f'<br><img src="{uri}" width="100%"><br>'
                cursor = self.text_edit.textCursor()
                cursor.insertHtml(img_html)
                ocr_txt = extract_text_from_image(saved_path)
                if ocr_txt:
                    self._append_ocr_text_to_current_node(ocr_txt)
                self.save_current_note()
                self.text_edit.setFocus()

    def extract_text_from_media(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t("extract_select_file"),
            "",
            "Images & PDF (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.pdf)",
        )
        if not file_path:
            return

        # If no node is currently open, create a new node automatically!
        if not self.current_editing_node_id:
            fname = os.path.basename(file_path)
            node_title, _ = os.path.splitext(fname)
            view_center = self.canvas_view.mapToScene(self.canvas_view.viewport().rect().center())
            new_node = self.scene.add_node(node_title, view_center.x(), view_center.y())
            self.switch_to_tree_view()
            self.open_editor(new_node.node_id, new_node.title)

        if file_path.lower().endswith(".pdf"):
            self.attach_pdf_to_current_node(file_path)
            return

        extracted = extract_text_from_file(file_path)
        if not extracted:
            QMessageBox.information(self, t("info_title"), t("extract_empty_msg"))
            return
        fname = os.path.basename(file_path)
        header = html.escape(t("extracted_from_header", filename=fname))
        body = html.escape(extracted).replace("\n", "<br>")
        block_html = f"<br><p><b>{header}</b><br>{body}</p><br>"
        cursor = self.text_edit.textCursor()
        cursor.insertHtml(block_html)
        self._append_ocr_text_to_current_node(extracted)
        self.save_current_note()
        self.text_edit.setFocus()

    def attach_pdf_to_current_node(self, file_path: str):
        """Attaches a PDF document to the current note with per-page index and direct page viewer link."""
        if not file_path or not os.path.exists(file_path) or not self.current_editing_node_id:
            return

        saved_doc = self.data_manager.save_document(file_path)
        if not saved_doc:
            return

        fname = os.path.basename(file_path)
        doc_rel = os.path.relpath(saved_doc, self.data_manager.workspace_path)
        import core.text_extractor
        pages = core.text_extractor.extract_pdf_pages_structured(saved_doc)

        # Store indexed page text into node's metadata
        node = self.scene.nodes.get(self.current_editing_node_id)
        if node:
            if not hasattr(node, "pdf_attachments") or not isinstance(node.pdf_attachments, list):
                node.pdf_attachments = []
            node.pdf_attachments.append({
                "filename": fname,
                "doc_rel": doc_rel,
                "pages": pages,
            })
            # Combine all page text into node.ocr_text for fast cross-indexing
            combined_txt = "\n\n".join(
                [f"[{fname} Sayfa {p['page_num']}]\n{p['text']}" for p in pages if p['text']]
            )
            existing_ocr = getattr(node, "ocr_text", "") or ""
            node.ocr_text = (existing_ocr + "\n\n" + combined_txt).strip() if existing_ocr else combined_txt
            self.scene.save_data()

        # Insert rich clickable badge into note content
        doc_uri = f"pdfpage:{doc_rel}?page=1"
        badge_html = (
            f'<div style="background-color: #FE90E8; border: 2.5px solid #000000; border-radius: 8px; padding: 10px 14px; margin: 10px 0;">'
            f'<b>[PDF]:</b> <a href="{doc_uri}" style="color: #000000; font-weight: bold; text-decoration: underline;">{html.escape(fname)} ({len(pages)} sayfa - Görüntülemek için tıkla)</a>'
            f'</div><br>'
        )
        cursor = self.text_edit.textCursor()
        cursor.insertHtml(badge_html)
        self.save_current_note()
        self.text_edit.setFocus()

    def show_export_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(build_menu_qss())
        act_png = menu.addAction(t("export_png"))
        act_pdf = menu.addAction(t("export_pdf"))
        menu.addSeparator()
        act_md = menu.addAction(t("export_md"))

        pos = self.btn_export.mapToGlobal(self.btn_export.rect().bottomLeft())
        chosen = menu.exec(pos)
        if chosen == act_png:
            self.export_mindmap_png()
        elif chosen == act_pdf:
            self.export_mindmap_pdf()
        elif chosen == act_md:
            self.export_notes_markdown()

    @staticmethod
    def _default_export_dir() -> str:
        desktop = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DesktopLocation)
        if desktop and os.path.isdir(desktop):
            return desktop
        return os.path.expanduser("~")

    def export_mindmap_png(self):
        if self.current_editing_node_id:
            self.save_current_note()
        default_path = os.path.join(self._default_export_dir(), "BilgiAgaci_Harita.png")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            t("export_png"),
            default_path,
            "PNG Image (*.png)",
        )
        if file_path:
            try:
                saved = self.scene.export_to_png(file_path)
                QMessageBox.information(self, t("success"), t("export_success", path=saved))
            except Exception as e:
                QMessageBox.critical(self, t("error"), t("export_error", error=str(e)))

    def export_mindmap_pdf(self):
        if self.current_editing_node_id:
            self.save_current_note()
        default_path = os.path.join(self._default_export_dir(), "BilgiAgaci_Harita.pdf")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            t("export_pdf"),
            default_path,
            "PDF Document (*.pdf)",
        )
        if file_path:
            try:
                saved = self.scene.export_to_pdf(file_path)
                QMessageBox.information(self, t("success"), t("export_success", path=saved))
            except Exception as e:
                QMessageBox.critical(self, t("error"), t("export_error", error=str(e)))

    def export_notes_markdown(self):
        if self.current_editing_node_id:
            self.save_current_note()
        self.scene.save_data()
        default_path = os.path.join(self._default_export_dir(), "BilgiAgaci_Notlar.md")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            t("export_md"),
            default_path,
            "Markdown (*.md)",
        )
        if not file_path:
            return
        final_path = file_path if file_path.lower().endswith(".md") else file_path + ".md"
        try:
            tree = self.data_manager.load_tree()
            nodes = tree.get("nodes", [])
            edges = tree.get("edges", [])
            id_to_title = {n["id"]: n.get("title", "") for n in nodes}

            tab_name = "Ana Ağaç"
            for tab in self.data_manager.get_tabs():
                if tab.get("id") == self.data_manager.active_tab_id:
                    tab_name = tab.get("name", tab_name)
                    break

            lines = [f"# {tab_name}\n"]
            for idx, n in enumerate(nodes, start=1):
                nid = n["id"]
                title = n.get("title", f"Düğüm {idx}")
                tag = (n.get("tag") or "").strip()
                fav = " [Favori]" if n.get("is_favorite") else ""
                tag_str = f" `[{tag}]`" if tag else ""
                lines.append(f"## {idx}. {title}{fav}{tag_str}\n")

                connected = [
                    id_to_title.get(e["target"], e["target"])
                    for e in edges
                    if e.get("source") == nid and e.get("target") in id_to_title
                ] + [
                    id_to_title.get(e["source"], e["source"])
                    for e in edges
                    if e.get("target") == nid and e.get("source") in id_to_title
                ]
                if connected:
                    lines.append(f"**Bağlantılar:** {', '.join(connected)}\n")

                raw = self.data_manager.load_note_content(nid)
                body = extract_plain_preview(raw, title=title, max_len=50000)
                if body:
                    lines.append(f"{body}\n")

                ocr_txt = (n.get("ocr_text") or "").strip()
                if ocr_txt and ocr_txt not in body:
                    lines.append(f"> **Fotoğraf / PDF Metni:**\n> {ocr_txt}\n")
                lines.append("---\n")

            with open(final_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            QMessageBox.information(self, t("success"), t("export_success", path=final_path))
        except Exception as e:
            QMessageBox.critical(self, t("error"), t("export_error", error=str(e)))

    def format_color(self):
        color = QColorDialog.getColor(QColor(Colors.BLACK), self, t("color_tooltip"))
        if color.isValid():
            fmt = self.text_edit.currentCharFormat()
            fmt.setForeground(color)
            self.text_edit.mergeCurrentCharFormat(fmt)
            self.text_edit.setFocus()

    def on_search_text_changed(self, text):
        self.search_timer.start(250)

    def perform_search(self, text):
        query = (text or "").strip()
        if not query:
            self.search_results.hide()
            self.scene.set_active_tag_filter(None)
            return

        # If user types #tag, trigger dynamic canvas highlight clustering
        if query.startswith("#"):
            self.scene.set_active_tag_filter(query)
        else:
            self.scene.set_active_tag_filter(None)

        self._position_search_results()
        self.search_results.clear()

        if self.current_editing_node_id:
            self.save_current_note()
        self.scene.save_data()

        q_lower = query.lower()
        scored_matches = []  # (score, display_label, (tab_id, node_id))
        tabs = self.data_manager.get_tabs()
        multi_tabs = len(tabs) > 1

        # Segregate matches: Direct Node Matches vs OCR / Document Text Matches
        node_matches = []  # Title, Tags, Content
        ocr_doc_matches = []  # Attached PDFs, Extracted OCR in Images

        for tab in tabs:
            tab_id = tab.get("id")
            tab_name = tab.get("name", "")
            tree = self.data_manager.load_tree(tab_id)
            for n in tree.get("nodes", []):
                nid = n.get("id")
                title = n.get("title", "")
                tag = n.get("tag", "")
                ocr_txt = n.get("ocr_text", "") or ""
                preview = n.get("preview", "") or ""
                raw_note = ""
                try:
                    raw_note = extract_plain_preview(
                        self.data_manager.load_note_content(nid), title=title, max_len=10000
                    )
                except Exception:
                    pass

                # Check inside attached PDFs per-page index
                pdf_target_match = None
                pdf_list = n.get("pdf_attachments", [])
                for pdf_entry in pdf_list:
                    p_name = pdf_entry.get("filename", "PDF")
                    p_rel = pdf_entry.get("doc_rel", "")
                    for p_info in pdf_entry.get("pages", []):
                        p_txt = p_info.get("text", "")
                        p_num = p_info.get("page_num", 1)
                        if p_txt and q_lower in p_txt.lower():
                            pdf_target_match = (p_rel, p_num, p_name)
                            break
                    if pdf_target_match:
                        break

                prefix = f"[{tab_name}] " if multi_tabs else ""

                # 1. Attached PDF match -> OCR / Document section
                if pdf_target_match:
                    p_rel, p_num, p_name = pdf_target_match
                    lbl = f"  [PDF] {p_name} (Sayfa {p_num})  →  {prefix}{title}"
                    ocr_doc_matches.append((99, lbl, (tab_id, nid, pdf_target_match)))
                    continue

                # 2. Image OCR match -> OCR / Document section
                if ocr_txt and q_lower in ocr_txt.lower():
                    # Extract snippet around match
                    snippet = ""
                    idx = ocr_txt.lower().find(q_lower)
                    if idx >= 0:
                        start = max(0, idx - 20)
                        end = min(len(ocr_txt), idx + len(query) + 30)
                        snippet = f"  \"{ocr_txt[start:end].strip()}...\""
                    lbl = f"  [OCR] {snippet}  →  {prefix}{title}"
                    ocr_doc_matches.append((95, lbl, (tab_id, nid, None)))
                    continue

                # 3. Direct Node Match (Title / Tag / Note Content)
                best_score = 0
                if q_lower in title.lower() or (tag and q_lower in tag.lower()):
                    best_score = 98
                elif q_lower in raw_note.lower() or q_lower in preview.lower():
                    best_score = 90
                else:
                    title_res = process.extractOne(query, [title]) if title else None
                    t_score = title_res[1] if title_res else 0
                    note_res = process.extractOne(query, [raw_note]) if raw_note else None
                    n_score = note_res[1] if note_res else 0
                    best_score = max(t_score, n_score)

                if best_score >= 45:
                    lbl = f"  {prefix}{title}"
                    if tag:
                        lbl += f"  [{tag.upper()}]"
                    node_matches.append((best_score, lbl, (tab_id, nid, None)))

        node_matches.sort(key=lambda x: x[0], reverse=True)
        ocr_doc_matches.sort(key=lambda x: x[0], reverse=True)

        self.search_results.show()
        has_items = False

        if node_matches:
            has_items = True
            hdr = QListWidgetItem("─── DÜĞÜMLER ───")
            hdr.setFlags(Qt.ItemFlag.NoItemFlags)
            hdr.setForeground(QColor("#71849b"))
            hdr.setFont(Typography.label(10))
            self.search_results.addItem(hdr)
            for _, label, payload in node_matches[:5]:
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, payload)
                item.setFont(Typography.body(12))
                self.search_results.addItem(item)

        if ocr_doc_matches:
            has_items = True
            hdr = QListWidgetItem("─── DOKÜMAN VE OCR METİNLERİ ───")
            hdr.setFlags(Qt.ItemFlag.NoItemFlags)
            hdr.setForeground(QColor("#71849b"))
            hdr.setFont(Typography.label(10))
            self.search_results.addItem(hdr)
            for _, label, payload in ocr_doc_matches[:6]:
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, payload)
                item.setFont(Typography.body(12))
                self.search_results.addItem(item)

        if not has_items:
            self.search_results.addItem(QListWidgetItem(t("no_results")))

    def go_to_search_result(self, item):
        payload = item.data(Qt.ItemDataRole.UserRole)
        if payload:
            pdf_target_match = None
            if isinstance(payload, tuple) and len(payload) == 3:
                tab_id, node_id, pdf_target_match = payload
            elif isinstance(payload, tuple) and len(payload) == 2:
                tab_id, node_id = payload
            else:
                tab_id, node_id = self.data_manager.active_tab_id, payload

            if tab_id and tab_id != self.data_manager.active_tab_id:
                if self.current_editing_node_id:
                    self.save_current_note()
                self.scene.save_data()
                self.save_camera_state(self.data_manager.active_tab_id)
                self.data_manager.switch_tab(tab_id)
                self.refresh_tabs()

            node = self.scene.nodes.get(node_id)
            if node:
                self.switch_to_tree_view()
                self.canvas_view.resetTransform()
                self.canvas_view.centerOn(node)
                self.canvas_view.scene().clearSelection()
                node.setSelected(True)
                self.open_editor(node.node_id, node.title)

                # If the search matched a specific page inside an attached PDF, open the PDF page viewer!
                if pdf_target_match:
                    doc_rel, page_num, _ = pdf_target_match
                    full_pdf_path = os.path.join(self.data_manager.workspace_path, doc_rel)
                    if os.path.exists(full_pdf_path):
                        QTimer.singleShot(150, lambda: self.open_pdf_viewer(full_pdf_path, page_num))

        self.search_results.hide()
        self.search_bar.clear()

    def open_pdf_viewer(self, pdf_path: str, page_num: int = 1):
        """Opens the interactive PDF viewer directly at the specified page."""
        dlg = PDFViewerDialog(pdf_path, initial_page=page_num, parent=self)
        dlg.exec()
