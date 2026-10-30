import os

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.i18n import t

from .components import (
    BrutalButton,
    BrutalCard,
    BrutalComboBox,
    BrutalTag,
    BrutalToggle,
    SparkleWidget,
)
from .theme import (
    Colors,
    Metrics,
    Motion,
    Shadows,
    Spacing,
    Typography,
)


class SettingsPage(QWidget):
    """
    Neo-Brutalist Settings & Storage Screen:
    - Light Blue (#C0F7FE) surface
    - Bold UPPERCASE page title + rotated sticker badge + ✦ sparkle star
    - Bordered row cards with chunky BrutalToggle switches (Green = ON, White = OFF)
    - Database backup (Yellow primary) & destructive restore (Pink) action buttons
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
        layout.setContentsMargins(Spacing.XXL, Spacing.XL, Spacing.XXL, Spacing.XXL)
        layout.setSpacing(Spacing.LG)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Header ---
        header_row = QHBoxLayout()
        header_row.setSpacing(Spacing.MD)
        header_row.addWidget(SparkleWidget(26))

        title = QLabel(t("settings_title").upper())
        title.setFont(Typography.display(Typography.SIZE_PAGE_TITLE))
        title.setStyleSheet(f"color: {Colors.BLACK}; background: transparent;")
        header_row.addWidget(title)

        header_row.addWidget(
            BrutalTag("LOCAL & SAFE", fill_color=Colors.GREEN, tilt_deg=Motion.STICKER_TILT_DEG)
        )
        header_row.addStretch()
        layout.addLayout(header_row)

        subtitle = QLabel(t("settings_subtitle"))
        subtitle.setFont(Typography.body(Typography.SIZE_BODY))
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"color: {Colors.BLACK}; background: transparent;")
        layout.addWidget(subtitle)

        layout.addSpacing(Spacing.SM)

        # --- Section 1: Database Management Card ---
        db_card = BrutalCard(
            fill_color=Colors.CREAM,
            shadow_px=Shadows.LG,
            padding=Spacing.XL,
        )
        db_card.setMaximumWidth(780)
        db_layout = QVBoxLayout(db_card)
        db_layout.setSpacing(Spacing.MD)

        db_header = QHBoxLayout()
        db_title = QLabel(t("db_management").upper())
        db_title.setFont(Typography.heading(Typography.SIZE_SECTION))
        db_title.setStyleSheet(f"color: {Colors.BLACK}; background: transparent;")
        db_header.addWidget(db_title)
        db_header.addStretch()
        db_header.addWidget(BrutalTag(".ZIP", fill_color=Colors.SOFT_ORANGE, tilt_deg=2.0))
        db_layout.addLayout(db_header)

        db_btns_row = QHBoxLayout()
        db_btns_row.setSpacing(Spacing.LG)

        btn_backup = BrutalButton(f"⬇  {t('create_backup')}", variant="primary")
        btn_backup.clicked.connect(self.create_backup)

        # Import overwrites current data -> styled in Pink (destructive/caution action)
        btn_import = BrutalButton(f"⬆  {t('import_backup')}", variant="danger")
        btn_import.clicked.connect(self.import_backup)

        db_btns_row.addWidget(btn_backup, 1)
        db_btns_row.addWidget(btn_import, 1)
        db_layout.addLayout(db_btns_row)

        layout.addWidget(db_card)

        # --- Section 2: Application Preferences (Individual Bordered Row Cards) ---
        self.settings = self.data_manager.load_settings()
        self.initial_lang = self.settings.get("language", "tr")

        layout.addSpacing(Spacing.SM)

        prefs_section_lbl = QLabel(t("app_preferences").upper())
        prefs_section_lbl.setFont(Typography.heading(Typography.SIZE_SECTION))
        prefs_section_lbl.setStyleSheet(f"color: {Colors.BLACK}; background: transparent;")
        layout.addWidget(prefs_section_lbl)

        # Row Card 1: Application Language
        lang_card = BrutalCard(fill_color=Colors.WHITE, shadow_px=Shadows.MD, padding=Spacing.LG)
        lang_card.setMaximumWidth(780)
        lang_row = QHBoxLayout(lang_card)
        lang_row.setSpacing(Spacing.LG)

        lang_label = QLabel(t("app_language"))
        lang_label.setFont(Typography.label(Typography.SIZE_BODY, letter_spacing_pct=101.0))
        lang_label.setStyleSheet(f"color: {Colors.BLACK}; background: transparent;")

        self.lang_combo = BrutalComboBox()
        self.lang_combo.setFont(Typography.label(Typography.SIZE_BUTTON))
        self.lang_combo.setMinimumHeight(Metrics.TOUCH_MIN)
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

        # Row Card 2: Auto-save Notes (Chunky Toggle: Green = ON, White = OFF)
        autosave_card = BrutalCard(fill_color=Colors.WHITE, shadow_px=Shadows.MD, padding=Spacing.LG)
        autosave_card.setMaximumWidth(780)
        autosave_row = QHBoxLayout(autosave_card)
        autosave_lbl = QLabel(t("auto_save_notes"))
        autosave_lbl.setFont(Typography.label(Typography.SIZE_BODY, letter_spacing_pct=101.0))
        autosave_lbl.setStyleSheet(f"color: {Colors.BLACK}; background: transparent;")

        self.autosave_check = BrutalToggle("")
        self.autosave_check.setChecked(self.settings.get("auto_save", True))
        self.autosave_check.stateChanged.connect(self.save_preferences)

        autosave_row.addWidget(autosave_lbl)
        autosave_row.addStretch()
        autosave_row.addWidget(self.autosave_check)
        layout.addWidget(autosave_card)

        # Row Card 3: Strict Offline Mode (Chunky Toggle: Green = ON, White = OFF)
        offline_card = BrutalCard(fill_color=Colors.WHITE, shadow_px=Shadows.MD, padding=Spacing.LG)
        offline_card.setMaximumWidth(780)
        offline_row = QHBoxLayout(offline_card)
        offline_lbl = QLabel(t("strict_offline_mode"))
        offline_lbl.setFont(Typography.label(Typography.SIZE_BODY, letter_spacing_pct=101.0))
        offline_lbl.setStyleSheet(f"color: {Colors.BLACK}; background: transparent;")

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
        painter.fillRect(self.rect(), QColor(Colors.LIGHT_BLUE))
        painter.end()

    def save_preferences(self, *args):
        new_lang = self.lang_combo.currentData()
        auto_save = self.autosave_check.isChecked()
        offline = self.offline_check.isChecked()

        if new_lang != self.initial_lang:
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

        self.settings["language"] = new_lang
        self.settings["auto_save"] = auto_save
        self.settings["offline_mode"] = offline
        self.data_manager.save_settings(self.settings)

    def create_backup(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            t("save_backup"),
            os.path.expanduser("~/Desktop/KnowledgeTree_Backup.zip"),
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
                os.path.expanduser("~/Desktop"),
                "ZIP Files (*.zip)",
            )
            if file_path:
                try:
                    self.data_manager.import_backup(file_path)
                    self.main_window.scene.clear_scene()
                    self.main_window.scene.load_data()
                    self.main_window.all_notes_page.refresh_notes()
                    QMessageBox.information(self, t("success"), t("import_success"))
                except Exception as e:
                    QMessageBox.critical(self, t("error"), f"{t('import_error')}:\n{str(e)}")
