import re
from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QFont, QKeySequence, QShortcut, QSyntaxHighlighter, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.i18n import t
from .theme import Borders, Colors, Shadows, Spacing, Typography


class WikiLinkHighlighter(QSyntaxHighlighter):
    """
    Highlights [[Note Name]] references in purple bold with an underline,
    and #hashtag labels with a warm pink accent.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.link_format = QTextCharFormat()
        self.link_format.setForeground(QColor("#7c3aed"))
        self.link_format.setFontWeight(QFont.Weight.Bold)
        self.link_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
        self.link_format.setUnderlineColor(QColor("#7c3aed"))

        self.tag_format = QTextCharFormat()
        self.tag_format.setForeground(QColor(Colors.PINK))
        self.tag_format.setFontWeight(QFont.Weight.Bold)

        self.link_regex = re.compile(r"\[\[(.*?)\]\]")
        self.tag_regex = re.compile(r"(?<!\w)#[a-zA-Z0-9çğıöşüÇĞİÖŞÜ_-]+")

    def highlightBlock(self, text: str):
        # Highlight [[wikilinks]]
        for match in self.link_regex.finditer(text):
            start = match.start()
            length = match.end() - start
            self.setFormat(start, length, self.link_format)

        # Highlight #tags
        for match in self.tag_regex.finditer(text):
            start = match.start()
            length = match.end() - start
            self.setFormat(start, length, self.tag_format)


class WikiLinkPopup(QFrame):
    """
    Neo-Brutalist floating autocomplete popup shown when the user types '[['.
    Allows keyboard navigation (Up/Down/Enter/Tab/Esc) and mouse clicking.
    """

    note_selected = pyqtSignal(str)  # Emits selected note title

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setObjectName("wikilink_popup")

        self.setStyleSheet(
            f"""
            QFrame#wikilink_popup {{
                background-color: {Colors.WHITE};
                border: {Borders.DEFAULT}px solid {Colors.BLACK};
                border-radius: 8px;
            }}
            QListWidget {{
                background-color: {Colors.WHITE};
                border: none;
                outline: none;
                font-family: {Typography.family()};
                font-size: 13px;
                color: {Colors.BLACK};
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 6px 10px;
                border-radius: 4px;
                border: 1.5px solid transparent;
                margin-bottom: 2px;
            }}
            QListWidget::item:selected {{
                background-color: {Colors.YELLOW};
                color: {Colors.BLACK};
                font-weight: bold;
                border: 1.5px solid {Colors.BLACK};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {Colors.LIGHT_BLUE};
                color: {Colors.BLACK};
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        header = QLabel(t('refer_node_header', default='NOT BAĞLANTISI SEÇ'))
        header.setFont(Typography.display(10))
        header.setStyleSheet("color: #64748b; padding: 2px 6px; font-weight: bold;")
        layout.addWidget(header)

        self.list_widget = QListWidget(self)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

        self.resize(260, 220)

    def populate(self, notes_list: list[dict], filter_query: str = ""):
        self.list_widget.clear()
        q = filter_query.strip().lower()

        filtered = []
        for n in notes_list:
            title = n.get("title", "").strip()
            if not title:
                continue
            if not q or q in title.lower():
                filtered.append(title)

        if not filtered:
            if q:
                # Option to create a new note directly with query name
                item = QListWidgetItem(f"+ '{q}' olarak yeni not oluştur")
                item.setData(Qt.ItemDataRole.UserRole, q)
                self.list_widget.addItem(item)
            else:
                item = QListWidgetItem(t("no_results"))
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.list_widget.addItem(item)
        else:
            for title in filtered:
                item = QListWidgetItem(title)
                item.setData(Qt.ItemDataRole.UserRole, title)
                self.list_widget.addItem(item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _on_item_clicked(self, item: QListWidgetItem):
        title = item.data(Qt.ItemDataRole.UserRole)
        if title:
            self.note_selected.emit(title)
            self.hide()

    def select_current(self) -> bool:
        item = self.list_widget.currentItem()
        if item and (item.flags() & Qt.ItemFlag.ItemIsEnabled):
            title = item.data(Qt.ItemDataRole.UserRole)
            if title:
                self.note_selected.emit(title)
                self.hide()
                return True
        return False

    def move_selection(self, delta: int):
        cur = self.list_widget.currentRow()
        count = self.list_widget.count()
        if count == 0:
            return
        nxt = (cur + delta) % count
        self.list_widget.setCurrentRow(nxt)
