import re
import urllib.parse

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor, QFont, QTextBlockFormat, QTextCharFormat, QTextListFormat
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

from core.i18n import t

from .all_notes_page import AllNotesPage
from .canvas import CanvasView, KnowledgeScene
from .components import (
    BrutalButton,
    BrutalCard,
    BrutalFAB,
    BrutalIconButton,
    BrutalInput,
    BrutalTag,
    DottedCreamFrame,
    SelectionFrameHero,
    SidebarDecoWidget,
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


class CustomTextEdit(QTextEdit):
    """Rich-text note editor supporting drag-and-drop images and heading enter reset."""

    def __init__(self, data_manager=None, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.setObjectName("note_text_edit")
        self.setFont(Typography.canvas_font(Typography.PT_EDITOR_BODY, QFont.Weight.Medium))

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
                    if file_path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")):
                        saved_path = self.data_manager.save_image(file_path)
                        if saved_path:
                            uri = "file:///" + urllib.parse.quote(saved_path.replace("\\", "/"))
                            img_html = f'<br><img src="{uri}" width="100%"><br>'
                            self.textCursor().insertHtml(img_html)
                        return
        super().insertFromMimeData(source)

    def keyPressEvent(self, event):
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

    def set_empty_visible(self, is_empty: bool):
        self.empty_hero.setVisible(is_empty)
        if is_empty:
            self._reposition_overlays()
            self.empty_hero.raise_()
        self.fab.raise_()

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_overlays()


class MainWindow(QMainWindow):
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.setWindowTitle("Knowledge Tree v3.0 — Neo-Brutalist Edition")
        self.resize(1280, 840)

        Typography.load_fonts()
        self.setStyleSheet(build_global_qss())

        self._is_updating_tabs = False
        self.init_ui()
        self.refresh_tabs()

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
            fill_color=Colors.WHITE,
            shadow_px=Shadows.MD,
            radius=Radii.MD,
            padding=Spacing.MD,
        )
        brand_layout = QHBoxLayout(brand_card)
        brand_layout.setSpacing(Spacing.MD)

        brand_mark = QLabel("✦")
        brand_mark.setFixedSize(36, 36)
        brand_mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_mark.setFont(Typography.display(18))
        brand_mark.setStyleSheet(
            f"""
            background-color: {Colors.YELLOW};
            color: {Colors.BLACK};
            border: {Borders.THIN}px solid {Colors.BLACK};
            border-radius: {Radii.SM}px;
            """
        )

        profile_col = QVBoxLayout()
        profile_col.setSpacing(2)
        name_lbl = QLabel("HARUN")
        name_lbl.setFont(Typography.heading(Typography.SIZE_BODY))
        name_lbl.setStyleSheet(f"color: {Colors.BLACK}; background: transparent;")

        plan_lbl = QLabel(t("free_plan").upper())
        plan_lbl.setFont(Typography.label(10))
        plan_lbl.setStyleSheet(
            f"""
            background-color: {Colors.GREEN};
            color: {Colors.BLACK};
            border: 1.5px solid {Colors.BLACK};
            border-radius: 6px;
            padding: 1px 6px;
            """
        )
        profile_col.addWidget(name_lbl)
        profile_col.addWidget(plan_lbl, 0, Qt.AlignmentFlag.AlignLeft)

        brand_layout.addWidget(brand_mark)
        brand_layout.addLayout(profile_col)
        brand_layout.addStretch()
        sidebar_layout.addWidget(brand_card)

        sidebar_layout.addSpacing(Spacing.XS)

        # Primary Add Node Button (Green #99E885)
        self.btn_new_node = BrutalButton(
            t("new_node_btn"),
            variant="add",
            shadow_px=Shadows.MD,
        )
        self.btn_new_node.setObjectName("new_node_btn")
        self.btn_new_node.clicked.connect(self.create_new_node)
        sidebar_layout.addWidget(self.btn_new_node)

        sidebar_layout.addSpacing(Spacing.SM)

        # Workspace Navigation Section
        nav_label = QLabel(t("workspace").upper())
        nav_label.setFont(Typography.label(Typography.SIZE_CAPTION, letter_spacing_pct=106.0))
        nav_label.setStyleSheet(f"color: {Colors.BLACK}; margin: 0px {Spacing.XS}px;")
        sidebar_layout.addWidget(nav_label)

        self.btn_all_notes = BrutalButton(t("all_notes"), variant="nav", align_left=True)
        self.btn_all_notes.setCheckable(True)
        self.btn_all_notes.clicked.connect(self.switch_to_all_notes)
        sidebar_layout.addWidget(self.btn_all_notes)

        self.btn_tree_view = BrutalButton(t("tree_view"), variant="nav", align_left=True)
        self.btn_tree_view.setCheckable(True)
        self.btn_tree_view.setChecked(True)
        self.btn_tree_view.clicked.connect(self.switch_to_tree_view)
        sidebar_layout.addWidget(self.btn_tree_view)

        self.btn_favorites = BrutalButton(t("favorites"), variant="nav", align_left=True)
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

        tabs_label = QLabel(t("tabs").upper())
        tabs_label.setFont(Typography.label(Typography.SIZE_CAPTION, letter_spacing_pct=106.0))
        tabs_label.setStyleSheet(f"color: {Colors.BLACK};")

        btn_add_tab = BrutalIconButton("＋", variant="add", size=34)
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

        # Decorative Neo-Brutalist geometric footer card
        sidebar_layout.addWidget(SidebarDecoWidget())

        # Settings Button
        self.btn_settings = BrutalButton(t("settings"), variant="nav", align_left=True)
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

        self.btn_toggle = BrutalIconButton("☰", variant="surface", size=Metrics.ICON_BTN_SIZE)
        self.btn_toggle.clicked.connect(self.toggle_sidebar)
        top_layout.addWidget(self.btn_toggle)

        self.search_bar = BrutalInput(
            placeholder=t("search_placeholder"),
            fill_color=Colors.WHITE,
            shadow_px=Shadows.MD,
        )
        self.search_bar.setObjectName("search_bar")
        self.search_bar.setFixedWidth(Metrics.SEARCH_WIDTH)
        self.search_bar.textChanged.connect(self.on_search_text_changed)
        top_layout.addWidget(self.search_bar)

        self.top_tabs = QTabBar()
        self.top_tabs.setDocumentMode(False)
        self.top_tabs.setDrawBase(False)
        self.top_tabs.setExpanding(False)
        self.top_tabs.setTabsClosable(True)
        self.top_tabs.setCursor(Qt.CursorShape.PointingHandCursor)
        self.top_tabs.tabCloseRequested.connect(self.close_tab_by_index)
        self.top_tabs.currentChanged.connect(self.on_top_tab_changed)
        top_layout.addWidget(self.top_tabs, 1)

        top_layout.addWidget(SparkleWidget(20))
        top_layout.addWidget(BrutalTag("NEO v3", fill_color=Colors.PINK, tilt_deg=2.5))

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

        # Editor Header Bar (Rotated Sticker + Sparkle + Close Button)
        editor_header = QHBoxLayout()
        editor_header.setSpacing(Spacing.SM)
        editor_header.addWidget(
            BrutalTag(t("edit_node"), fill_color=Colors.SOFT_ORANGE, tilt_deg=Motion.STICKER_TILT_DEG)
        )
        editor_header.addWidget(SparkleWidget(18))
        editor_header.addStretch()

        self.btn_close_editor = BrutalIconButton("✕", variant="danger", size=40)
        self.btn_close_editor.setToolTip(t("close_editor_tooltip"))
        self.btn_close_editor.clicked.connect(self._close_editor_panel)
        editor_header.addWidget(self.btn_close_editor)
        editor_layout.addLayout(editor_header)

        # Huge Bold Title Input
        self.editor_title = BrutalInput(
            fill_color=Colors.WHITE,
            shadow_px=Shadows.MD,
            face_height=50,
            is_heading=True,
        )
        self.editor_title.textChanged.connect(self.update_node_title)
        editor_layout.addWidget(self.editor_title)

        # Chunky Bordered Formatting Toolbar
        self.editor_toolbar = EditorToolbar()
        self.editor_toolbar.format_bold_signal.connect(self.format_bold)
        self.editor_toolbar.format_italic_signal.connect(self.format_italic)
        self.editor_toolbar.format_h1_signal.connect(self.format_h1)
        self.editor_toolbar.format_h2_signal.connect(self.format_h2)
        self.editor_toolbar.format_bullet_list_signal.connect(self.format_bullet_list)
        self.editor_toolbar.insert_image_signal.connect(self.insert_image)
        self.editor_toolbar.format_color_signal.connect(self.format_color)
        editor_layout.addWidget(self.editor_toolbar)

        # Clean Readable Body framed with Figma-like Selection Corner Handles
        body_frame = BrutalCard(
            fill_color=Colors.WHITE,
            shadow_px=Shadows.MD,
            radius=Radii.MD,
            padding=Spacing.XS,
            selection_handles=True,
        )
        body_frame_layout = QVBoxLayout(body_frame)
        body_frame_layout.setContentsMargins(0, 0, 0, 0)

        self.text_edit = CustomTextEdit(self.data_manager)
        self.text_edit.document().setDefaultStyleSheet("body, p, li { line-height: 155%; }")
        self.text_edit.cursorPositionChanged.connect(self.update_editor_toolbar_state)
        body_frame_layout.addWidget(self.text_edit)
        editor_layout.addWidget(body_frame, 1)

        # Yellow / Green Save CTA Button
        self.btn_save_note = BrutalButton(
            f"✓  {t('save_changes')}",
            variant="primary",
            shadow_px=Shadows.MD,
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

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(lambda: self.perform_search(self.search_bar.text()))

    def _close_editor_panel(self):
        if self.current_editing_node_id:
            self.save_current_note()
        self.editor_panel.hide()
        self.current_editing_node_id = None

    def _position_search_results(self):
        global_pos = self.search_bar.mapTo(self, self.search_bar.rect().bottomLeft())
        self.search_results.setGeometry(
            global_pos.x(),
            global_pos.y() + Spacing.XS,
            self.search_bar.width(),
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

        markers = ("◆", "●", "▲", "■", "✦")
        active_idx = 0
        for i, tab_info in enumerate(tabs):
            marker = markers[i % len(markers)]
            item = QListWidgetItem(f"{marker}  {tab_info['name'].upper()}")
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
            action_close = menu.addAction(f"✕  {t('close_tab').upper()}")
            action = menu.exec(self.sidebar_tabs_list.mapToGlobal(pos))
            if action == action_close:
                tab_id = item.data(Qt.ItemDataRole.UserRole)
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
            success = self.data_manager.delete_tab(tab_id)
            if not success:
                QMessageBox.warning(self, t("error"), t("at_least_one_tab"))
            else:
                self.refresh_tabs()

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
        self.current_editing_node_id = node_id
        self.editor_title.setText(title)
        content = self.data_manager.load_note_content(node_id)
        if "<" not in content and ">" not in content:
            self.text_edit.setPlainText(content)
        else:
            # Normalize legacy dark-theme default light body colors to crisp #000000 ink
            display_html = re.sub(
                r"color:\s*#(?:cbd6e5|e8edf6|dce7f5|d9e2ee|ffffff)\b",
                f"color:{Colors.BLACK}",
                content,
                flags=re.IGNORECASE,
            )
            self.text_edit.setHtml(display_html)
        self.text_edit.document().setModified(False)
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

    def _auto_save(self):
        if self.current_editing_node_id and self.editor_panel.isVisible():
            if not self.text_edit.document().isModified():
                return
            node = self.scene.nodes.get(self.current_editing_node_id)
            if node:
                content = self.text_edit.toHtml()
                self.data_manager.save_note_content(self.current_editing_node_id, content)
                self.text_edit.document().setModified(False)

    def save_current_note(self):
        if self.current_editing_node_id:
            new_title = self.editor_title.text()
            content = self.text_edit.toHtml()
            node = self.scene.nodes.get(self.current_editing_node_id)
            if node:
                node.title = new_title
                node.title_item.setPlainText(new_title)
                node._adjust_title_font()
                self.scene.save_data()
            self.data_manager.save_note_content(self.current_editing_node_id, content)
            self.text_edit.document().setModified(False)

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
                uri = "file:///" + urllib.parse.quote(saved_path.replace("\\", "/"))
                img_html = f'<br><img src="{uri}" width="100%"><br>'
                cursor = self.text_edit.textCursor()
                cursor.insertHtml(img_html)
                self.text_edit.setFocus()

    def format_color(self):
        color = QColorDialog.getColor(QColor(Colors.BLACK), self, t("color_tooltip"))
        if color.isValid():
            fmt = self.text_edit.currentCharFormat()
            fmt.setForeground(color)
            self.text_edit.mergeCurrentCharFormat(fmt)
            self.text_edit.setFocus()

    def on_search_text_changed(self, text):
        self.search_timer.start(300)

    def perform_search(self, text):
        if not text:
            self.search_results.hide()
            return
        self._position_search_results()
        choices = {node_id: node.title for node_id, node in self.scene.nodes.items()}
        self.search_results.clear()
        if not choices:
            self.search_results.show()
            self.search_results.addItem(QListWidgetItem(t("no_results")))
            return
        results = process.extract(text, choices, limit=5)
        if results:
            self.search_results.show()
            for title, score, node_id in results:
                if score >= 40:
                    item = QListWidgetItem(f"{title} ({t('match_score', score=score)})")
                    item.setData(Qt.ItemDataRole.UserRole, node_id)
                    self.search_results.addItem(item)
            if self.search_results.count() == 0:
                self.search_results.addItem(QListWidgetItem(t("no_results")))
        else:
            self.search_results.show()
            self.search_results.addItem(QListWidgetItem(t("no_results")))

    def go_to_search_result(self, item):
        node_id = item.data(Qt.ItemDataRole.UserRole)
        if node_id:
            node = self.scene.nodes.get(node_id)
            if node:
                self.switch_to_tree_view()
                self.canvas_view.resetTransform()
                self.canvas_view.centerOn(node)
                self.canvas_view.scene().clearSelection()
                node.setSelected(True)
                self.search_results.hide()
                self.search_bar.clear()
