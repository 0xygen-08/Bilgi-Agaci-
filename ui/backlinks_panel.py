import re
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.i18n import t
from .theme import Borders, Colors, Radii, Spacing, Typography


class BacklinksPanel(QFrame):
    """
    Obsidian-style Backlinks panel for Knowledge Tree.
    Shows all other nodes that reference the currently edited node via [[Title]].
    """

    backlink_clicked = pyqtSignal(str)

    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.setObjectName("backlinks_panel")

        self.setStyleSheet(
            f"""
            QFrame#backlinks_panel {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER};
                border-radius: {Radii.MD}px;
                padding: 4px;
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(t('backlinks_header', default='Geri Bağlantılar (Backlinks)'))
        self.title_label.setFont(Typography.heading(11))
        self.title_label.setStyleSheet(f"color: {Colors.TEXT};")
        header_layout.addWidget(self.title_label)

        self.count_badge = QLabel("0")
        self.count_badge.setFont(Typography.label(9))
        self.count_badge.setStyleSheet(
            f"""
            background-color: {Colors.SURFACE_HOVER};
            color: {Colors.TEXT_MUTED};
            border: 1px solid {Colors.BORDER};
            border-radius: 8px;
            padding: 1px 6px;
            """
        )
        header_layout.addWidget(self.count_badge)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Chips Container inside a light horizontal scroll
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedHeight(40)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.chips_widget = QWidget()
        self.chips_widget.setStyleSheet("background: transparent;")
        self.chips_layout = QHBoxLayout(self.chips_widget)
        self.chips_layout.setContentsMargins(0, 2, 0, 2)
        self.chips_layout.setSpacing(6)
        self.chips_layout.addStretch()

        self.scroll_area.setWidget(self.chips_widget)
        layout.addWidget(self.scroll_area)

        self.empty_label = QLabel(t("no_backlinks", default="Bu nota henüz referans verilmemiş."))
        self.empty_label.setFont(Typography.body(11))
        self.empty_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-style: italic;")
        layout.addWidget(self.empty_label)

    def refresh_backlinks(self, current_node_id: str, current_node_title: str):
        if not current_node_id or not current_node_title:
            self.hide()
            return

        while self.chips_layout.count() > 1:
            item = self.chips_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tree = self.data_manager.load_tree()
        all_nodes = tree.get("nodes", [])

        target_title_clean = current_node_title.strip().lower()
        referencing_nodes = []

        for node in all_nodes:
            nid = node.get("id")
            if nid == current_node_id:
                continue
            content = self.data_manager.load_note_content(nid)
            wikilinks = re.findall(r"\[\[(.*?)\]\]", content)
            for link in wikilinks:
                if link.strip().lower() == target_title_clean:
                    referencing_nodes.append((nid, node.get("title", nid)))
                    break

        count = len(referencing_nodes)
        self.count_badge.setText(str(count))

        if count == 0:
            self.scroll_area.hide()
            self.empty_label.show()
        else:
            self.empty_label.hide()
            self.scroll_area.show()
            for nid, title in referencing_nodes:
                chip = QPushButton(f"← {title}")
                chip.setCursor(Qt.CursorShape.PointingHandCursor)
                chip.setFont(Typography.body(11))
                chip.setStyleSheet(
                    f"""
                    QPushButton {{
                        background-color: {Colors.SURFACE};
                        color: {Colors.TEXT};
                        border: 1px solid {Colors.BORDER};
                        border-radius: 4px;
                        padding: 3px 8px;
                    }}
                    QPushButton:hover {{
                        background-color: {Colors.SURFACE_HOVER};
                        border-color: {Colors.PRIMARY};
                    }}
                    """
                )
                chip.clicked.connect(lambda checked=False, target_id=nid: self.backlink_clicked.emit(target_id))
                self.chips_layout.insertWidget(self.chips_layout.count() - 1, chip)

        self.show()
