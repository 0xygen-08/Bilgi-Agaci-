import os

from PyQt6.QtCore import QStandardPaths, QTimer, Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.i18n import set_language, t

from .components import (
    BrutalButton,
    BrutalCard,
    BrutalComboBox,
    BrutalInput,
    BrutalTag,
    BrutalToggle,
)
from .theme import (
    Colors,
    Metrics,
    Radii,
    Spacing,
    Typography,
)


def _desktop_dir() -> str:
    desktop = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DesktopLocation)
    if desktop and os.path.isdir(desktop):
        return desktop
    return os.path.expanduser("~")


class SettingsPage(QWidget):
    """
    Obsidian-Style Clean Settings & Storage Screen:
    - Clean card rows with 1px borders
    - Modern toggle switches
    - Backup & restore management
    """

    def __init__(self, data_manager, main_window):
        super().__init__()
        self.data_manager = data_manager
        self.main_window = main_window

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.MD)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Header ---
        header_row = QHBoxLayout()
        header_row.setSpacing(Spacing.MD)

        title = QLabel(t("settings_title"))
        title.setFont(Typography.display(Typography.SIZE_PAGE_TITLE))
        title.setStyleSheet(f"color: {Colors.TEXT}; background: transparent;")
        header_row.addWidget(title)

        header_row.addWidget(
            BrutalTag(t("local_safe_badge"), fill_color=Colors.SURFACE_HOVER, pill=True)
        )
        header_row.addStretch()
        layout.addLayout(header_row)

        subtitle = QLabel(t("settings_subtitle"))
        subtitle.setFont(Typography.body(Typography.SIZE_BODY))
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"color: {Colors.TEXT_MUTED}; background: transparent;")
        layout.addWidget(subtitle)

        layout.addSpacing(Spacing.SM)

        # --- Section 1: Database Management Card ---
        db_card = BrutalCard(
            fill_color=Colors.SURFACE,
            padding=Spacing.LG,
        )
        db_card.setMaximumWidth(720)
        db_layout = QVBoxLayout(db_card)
        db_layout.setSpacing(Spacing.MD)

        db_header = QHBoxLayout()
        db_title = QLabel(t("db_management"))
        db_title.setFont(Typography.heading(Typography.SIZE_CARD_TITLE))
        db_title.setStyleSheet(f"color: {Colors.TEXT}; background: transparent;")
        db_header.addWidget(db_title)
        db_header.addStretch()
        db_header.addWidget(BrutalTag(".zip", fill_color=Colors.SURFACE_HOVER, pill=True))
        db_layout.addLayout(db_header)

        db_btns_row = QHBoxLayout()
        db_btns_row.setSpacing(Spacing.MD)

        btn_backup = BrutalButton(t('create_backup'), variant="primary")
        btn_backup.clicked.connect(self.create_backup)

        btn_import = BrutalButton(t('import_backup'), variant="danger")
        btn_import.clicked.connect(self.import_backup)

        db_btns_row.addWidget(btn_backup, 1)
        db_btns_row.addWidget(btn_import, 1)
        db_layout.addLayout(db_btns_row)

        layout.addWidget(db_card)

        # --- Section 2: Application Preferences ---
        self.settings = self.data_manager.load_settings()
        self.initial_lang = self.settings.get("language", "tr")

        layout.addSpacing(Spacing.SM)

        prefs_section_lbl = QLabel(t("app_preferences"))
        prefs_section_lbl.setFont(Typography.heading(Typography.SIZE_CARD_TITLE))
        prefs_section_lbl.setStyleSheet(f"color: {Colors.TEXT}; background: transparent;")
        layout.addWidget(prefs_section_lbl)

        # Row 0: User / Profile Name
        profile_card = BrutalCard(fill_color=Colors.SURFACE, padding=Spacing.MD)
        profile_card.setMaximumWidth(720)
        profile_row = QHBoxLayout(profile_card)
        profile_row.setSpacing(Spacing.MD)

        profile_lbl = QLabel(t("user_name_label"))
        profile_lbl.setFont(Typography.label(Typography.SIZE_BODY))
        profile_lbl.setStyleSheet(f"color: {Colors.TEXT}; background: transparent;")

        self.user_name_input = BrutalInput(
            text=self.settings.get("user_name", "Harun"),
            placeholder=t("user_name_placeholder"),
            fill_color=Colors.SURFACE,
            face_height=32,
        )
        self.user_name_input.setFixedWidth(200)
        self.user_name_input.textChanged.connect(self.save_preferences)

        profile_row.addWidget(profile_lbl)
        profile_row.addStretch()
        profile_row.addWidget(self.user_name_input)
        layout.addWidget(profile_card)

        # Row 1: Application Language
        lang_card = BrutalCard(fill_color=Colors.SURFACE, padding=Spacing.MD)
        lang_card.setMaximumWidth(720)
        lang_row = QHBoxLayout(lang_card)
        lang_row.setSpacing(Spacing.MD)

        lang_label = QLabel(t("app_language"))
        lang_label.setFont(Typography.label(Typography.SIZE_BODY))
        lang_label.setStyleSheet(f"color: {Colors.TEXT}; background: transparent;")

        self.lang_combo = BrutalComboBox()
        self.lang_combo.setFont(Typography.label(Typography.SIZE_BUTTON))
        self.lang_combo.setMinimumHeight(32)
        self.lang_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lang_combo.addItem("Türkçe", "tr")
        self.lang_combo.addItem("English", "en")

        idx = self.lang_combo.findData(self.initial_lang)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.currentIndexChanged.connect(self.save_preferences)

        lang_row.addWidget(lang_label)
        lang_row.addStretch()
        lang_row.addWidget(self.lang_combo)
        layout.addWidget(lang_card)

        # Row 2: Canvas Background Pattern
        bg_card = BrutalCard(fill_color=Colors.SURFACE, padding=Spacing.MD)
        bg_card.setMaximumWidth(720)
        bg_row = QHBoxLayout(bg_card)
        bg_row.setSpacing(Spacing.MD)

        bg_label = QLabel(t("canvas_bg_pattern"))
        bg_label.setFont(Typography.label(Typography.SIZE_BODY))
        bg_label.setStyleSheet(f"color: {Colors.TEXT}; background: transparent;")

        self.bg_combo = BrutalComboBox()
        self.bg_combo.setFont(Typography.label(Typography.SIZE_BUTTON))
        self.bg_combo.setMinimumHeight(32)
        self.bg_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bg_combo.addItem(t("bg_dot"), "dot")
        self.bg_combo.addItem(t("bg_grid"), "grid")
        self.bg_combo.addItem(t("bg_blank"), "blank")

        bg_idx = self.bg_combo.findData(self.settings.get("bg_type", "dot"))
        if bg_idx >= 0:
            self.bg_combo.setCurrentIndex(bg_idx)
        self.bg_combo.currentIndexChanged.connect(self.save_preferences)

        bg_row.addWidget(bg_label)
        bg_row.addStretch()
        bg_row.addWidget(self.bg_combo)
        layout.addWidget(bg_card)

        # Row 3: Auto-save Notes
        autosave_card = BrutalCard(fill_color=Colors.SURFACE, padding=Spacing.MD)
        autosave_card.setMaximumWidth(720)
        autosave_row = QHBoxLayout(autosave_card)
        autosave_lbl = QLabel(t("auto_save_notes"))
        autosave_lbl.setFont(Typography.label(Typography.SIZE_BODY))
        autosave_lbl.setStyleSheet(f"color: {Colors.TEXT}; background: transparent;")

        self.autosave_check = BrutalToggle("")
        self.autosave_check.setChecked(self.settings.get("auto_save", True))
        self.autosave_check.stateChanged.connect(self.save_preferences)

        autosave_row.addWidget(autosave_lbl)
        autosave_row.addStretch()
        autosave_row.addWidget(self.autosave_check)
        layout.addWidget(autosave_card)

        # Row 4: Strict Offline Mode
        offline_card = BrutalCard(fill_color=Colors.SURFACE, padding=Spacing.MD)
        offline_card.setMaximumWidth(720)
        offline_row = QHBoxLayout(offline_card)
        offline_lbl = QLabel(t("strict_offline_mode"))
        offline_lbl.setFont(Typography.label(Typography.SIZE_BODY))
        offline_lbl.setStyleSheet(f"color: {Colors.TEXT}; background: transparent;")

        self.offline_check = BrutalToggle("")
        self.offline_check.setChecked(self.settings.get("offline_mode", True))
        self.offline_check.stateChanged.connect(self.save_preferences)

        offline_row.addWidget(offline_lbl)
        offline_row.addStretch()
        offline_row.addWidget(self.offline_check)
        layout.addWidget(offline_card)

        layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(Colors.WINDOW))
        painter.end()

    def save_preferences(self, *args):
        user_name = self.user_name_input.text().strip() or "Harun"
        new_lang = self.lang_combo.currentData()
        bg_type = self.bg_combo.currentData()
        auto_save = self.autosave_check.isChecked()
        offline = self.offline_check.isChecked()

        if new_lang != self.initial_lang:
            set_language(new_lang)
            QMessageBox.information(self, t("info_title"), t("language_restart_msg"))
            self.initial_lang = new_lang

        if auto_save:
            if not hasattr(self.main_window, "auto_save_timer") or not self.main_window.auto_save_timer.isActive():
                self.main_window.auto_save_timer = QTimer(self.main_window)
                self.main_window.auto_save_timer.timeout.connect(self.main_window._auto_save)
                self.main_window.auto_save_timer.start(5000)
        else:
            if hasattr(self.main_window, "auto_save_timer") and self.main_window.auto_save_timer.isActive():
                self.main_window.auto_save_timer.stop()

        self.settings = self.data_manager.load_settings()
        self.settings["user_name"] = user_name
        self.settings["language"] = new_lang
        self.settings["bg_type"] = bg_type
        self.settings["auto_save"] = auto_save
        self.settings["offline_mode"] = offline
        self.data_manager.save_settings(self.settings)

        if hasattr(self.main_window, "update_profile_name"):
            self.main_window.update_profile_name(user_name)
        if hasattr(self.main_window, "scene"):
            self.main_window.scene.update()
        if hasattr(self.main_window, "canvas_view"):
            self.main_window.canvas_view.viewport().update()

    def create_backup(self):
        if hasattr(self.main_window, "current_editing_node_id") and self.main_window.current_editing_node_id:
            self.main_window.save_current_note()
        if hasattr(self.main_window, "scene"):
            self.main_window.scene.save_data()

        default_zip = os.path.join(_desktop_dir(), "KnowledgeTree_Backup.zip")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            t("save_backup"),
            default_zip,
            "ZIP Files (*.zip)",
        )
        if file_path:
            try:
                final_path = self.data_manager.create_backup(file_path)
                QMessageBox.information(self, t("success"), f"{t('backup_success')}:\n{final_path}")
            except Exception as e:
                QMessageBox.critical(self, t("error"), f"{t('backup_error')}:\n{str(e)}")

    def import_backup(self):
        reply = QMessageBox.warning(
            self,
            t("warning"),
            t("import_warning"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                t("select_backup"),
                _desktop_dir(),
                "ZIP Files (*.zip)",
            )
            if file_path:
                try:
                    if hasattr(self.main_window, "editor_panel"):
                        self.main_window.editor_panel.hide()
                        self.main_window.current_editing_node_id = None
                    self.data_manager.import_backup(file_path)
                    self.settings = self.data_manager.load_settings()
                    if hasattr(self.main_window, "update_profile_name"):
                        self.main_window.update_profile_name(self.settings.get("user_name", "Harun"))
                    self.main_window.tab_camera_states.clear()
                    self.main_window.refresh_tabs()
                    self.main_window.all_notes_page.refresh_notes()
                    self.main_window.favorites_page.refresh_notes()
                    QMessageBox.information(self, t("success"), t("import_success"))
                except Exception as e:
                    QMessageBox.critical(self, t("error"), f"{t('import_error')}:\n{str(e)}")
