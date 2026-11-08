import math
import re

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFontMetrics, QPainter, QPainterPath, QPen, QTextOption
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.data_manager import extract_plain_preview
from core.i18n import t

from .components import (
    BrutalChip,
    BrutalFAB,
    BrutalIconButton,
    BrutalInput,
    BrutalTag,
    SelectionFrameHero,
    _PressHoverAnimator,
)
from .theme import (
    Borders,
    Colors,
    Metrics,
    Radii,
    Spacing,
    Typography,
    readable_ink,
    relative_luminance,
    resolve_accent_color,
    resolve_node_bg,
)


class NoteCard(QFrame):
    """
    Obsidian-Style Clean Note Card:
    - Sleek 1px border with surface hover highlighting
    - Natural casing for title & preview
    - Subtle index, clean tag badge & gold star
    """

    def __init__(
        self,
        node_id: str,
        title: str,
        preview_text: str,
        parent_page: "AllNotesPage",
        color: str = "",
        tag: str = "",
        bg_color: str = "",
        is_favorite: bool = False,
        card_index: int = 1,
        list_mode: bool = False,
    ):
        super().__init__()
        self.node_id = node_id
        self.title = title
        self.preview_text = preview_text
        self.parent_page = parent_page
        self.color = color
        self.tag = tag
        self.bg_color = bg_color
        self.is_favorite = is_favorite
        self.card_index = card_index
        self.list_mode = list_mode

        self.setObjectName("NoteCard")
        self._motion = _PressHoverAnimator(self)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_mode_dimensions()

    def _apply_mode_dimensions(self):
        if self.list_mode:
            self.setMinimumHeight(Metrics.NOTE_LIST_HEIGHT)
            self.setMaximumHeight(Metrics.NOTE_LIST_HEIGHT)
            self.setMinimumWidth(320)
            self.setMaximumWidth(16777215)
        else:
            self.setFixedSize(Metrics.NOTE_CARD_WIDTH, Metrics.NOTE_CARD_HEIGHT)

    def set_list_mode(self, list_mode: bool):
        if self.list_mode != list_mode:
            self.list_mode = list_mode
            self._apply_mode_dimensions()
            self.update()

    def enterEvent(self, event):
        self._motion.set_hovered(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._motion.set_hovered(False)
        self._motion.set_pressed(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._motion.set_pressed(True)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        was_pressed = self._motion._pressed
        self._motion.set_pressed(False)
        if was_pressed and event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.pos()):
            self.parent_page.open_note_signal(self.node_id)
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = QRectF(1.0, 1.0, float(self.width()) - 2.0, float(self.height()) - 2.0)

        # 1. Background Surface
        fill_col = Colors.SURFACE_HOVER if self._motion._hovered else Colors.SURFACE
        border_col = Colors.PRIMARY if self._motion._hovered else Colors.BORDER

        painter.setPen(QPen(QColor(border_col), 1.0))
        painter.setBrush(QBrush(QColor(fill_col)))
        painter.drawRoundedRect(rect, Radii.MD, Radii.MD)

        pad = float(Spacing.MD)
        cur_x = rect.left() + pad
        top_y = rect.top() + pad

        # 2. Metadata Header: Index + Tag + Star
        idx_font = Typography.label(Typography.SIZE_CAPTION)
        painter.setFont(idx_font)
        idx_str = f"#{self.card_index:02d}"
        idx_fm = QFontMetrics(idx_font)
        idx_w = float(idx_fm.horizontalAdvance(idx_str) + 8)

        painter.setPen(QPen(QColor(Colors.TEXT_MUTED)))
        painter.drawText(QRectF(cur_x, top_y, idx_w, 20.0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, idx_str)
        cur_x += idx_w + float(Spacing.SM)

        if self.tag:
            tag_text = self.tag
            tag_w = min(
                float(idx_fm.horizontalAdvance(tag_text) + Spacing.MD * 2),
                max(48.0, rect.width() - (cur_x - rect.left()) - 36.0),
            )
            tag_rect = QRectF(cur_x, top_y, tag_w, 20.0)

            painter.setPen(QPen(QColor(Colors.BORDER), 1.0))
            painter.setBrush(QBrush(QColor(Colors.SURFACE_ACTIVE)))
            painter.drawRoundedRect(tag_rect, Radii.SM, Radii.SM)

            elided_tag = idx_fm.elidedText(tag_text, Qt.TextElideMode.ElideRight, int(tag_w - 6))
            painter.setPen(QPen(QColor(Colors.TEXT_MUTED)))
            painter.drawText(tag_rect, Qt.AlignmentFlag.AlignCenter, elided_tag)

        if self.is_favorite:
            star_sz = 14.0
            cx = rect.right() - pad - star_sz / 2.0
            cy = top_y + 10.0

            star_path = QPainterPath()
            outer_r = 5.5
            inner_r = 2.5
            for i in range(10):
                r = outer_r if i % 2 == 0 else inner_r
                angle = -math.pi / 2.0 + i * math.pi / 5.0
                px = cx + r * math.cos(angle)
                py = cy + r * math.sin(angle)
                if i == 0:
                    star_path.moveTo(px, py)
                else:
                    star_path.lineTo(px, py)
            star_path.closeSubpath()

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#f59e0b")))
            painter.drawPath(star_path)

        # 3. Clean Card Title
        title_font = Typography.heading(Typography.SIZE_CARD_TITLE)
        painter.setFont(title_font)
        painter.setPen(QPen(QColor(Colors.TEXT)))
        title_fm = QFontMetrics(title_font)
        title_top = top_y + 26.0
        content_w = rect.width() - pad * 2.0

        if self.list_mode:
            elided_title = title_fm.elidedText(self.title, Qt.TextElideMode.ElideRight, int(content_w))
            title_rect = QRectF(rect.left() + pad, title_top, content_w, 22.0)
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_title)
            preview_top = title_top + 24.0
        else:
            title_h = float(title_fm.lineSpacing() + 4)
            title_rect = QRectF(rect.left() + pad, title_top, content_w, title_h)
            elided_title = title_fm.elidedText(self.title, Qt.TextElideMode.ElideRight, int(content_w))
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_title)
            preview_top = title_top + title_h + 4.0

        # 4. Subtle Divider
        painter.setPen(QPen(QColor(Colors.BORDER), 1.0))
        painter.drawLine(
            int(rect.left() + pad),
            int(preview_top),
            int(rect.right() - pad),
            int(preview_top),
        )

        # 5. Preview Body
        body_font = Typography.body(Typography.SIZE_LABEL)
        painter.setFont(body_font)
        painter.setPen(QPen(QColor(Colors.TEXT_MUTED)))
        body_fm = QFontMetrics(body_font)

        avail_h = max(16.0, rect.bottom() - float(Spacing.SM) - (preview_top + 6.0))
        max_lines = max(1, int(avail_h // max(1, body_fm.lineSpacing())))
        preview_str = self.preview_text.strip()
        if body_fm.horizontalAdvance(preview_str) > content_w * max_lines * 0.95:
            preview_str = body_fm.elidedText(
                preview_str,
                Qt.TextElideMode.ElideRight,
                int(content_w * max_lines * 0.92),
            )
        body_rect = QRectF(rect.left() + pad, preview_top + 6.0, content_w, avail_h)
        body_opt = QTextOption(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        body_opt.setWrapMode(QTextOption.WrapMode.WordWrap)
        painter.drawText(body_rect, preview_str, body_opt)

        painter.end()


class AllNotesPage(QWidget):
    def __init__(self, data_manager, main_window, favorites_only=False):
        super().__init__()
        self.data_manager = data_manager
        self.main_window = main_window
        self.favorites_only = favorites_only

        self.list_mode = False
        self.active_tag_filter = None
        self.filter_query = ""
        self.note_widgets: list[NoteCard] = []
        self.tag_chips: list[BrutalChip] = []
        self.current_col_count = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        # --- HEADER BAR ---
        header_row = QHBoxLayout()
        header_row.setSpacing(Spacing.MD)

        raw_title = t("favorite_notes_title") if favorites_only else t("all_notes_title")
        self.title_lbl = QLabel(raw_title)
        self.title_lbl.setFont(Typography.display(Typography.SIZE_PAGE_TITLE))
        self.title_lbl.setStyleSheet(f"color: {Colors.TEXT}; background: transparent;")
        header_row.addWidget(self.title_lbl)

        self.count_badge = BrutalTag("0", fill_color=Colors.SURFACE_HOVER, pill=True)
        header_row.addWidget(self.count_badge)

        header_row.addStretch()

        # Search Input
        self.filter_input = BrutalInput(
            placeholder=t("filter_notes_placeholder"),
            fill_color=Colors.SURFACE,
            face_height=32,
        )
        self.filter_input.setFixedWidth(220)
        self.filter_input.textChanged.connect(self._on_filter_text_changed)
        header_row.addWidget(self.filter_input)

        # Grid / List Toggle
        self.btn_grid_mode = BrutalIconButton("Izgara", variant="surface", size=32, min_width=54)
        self.btn_grid_mode.setCheckable(True)
        self.btn_grid_mode.setChecked(True)
        self.btn_grid_mode.clicked.connect(lambda: self._set_view_mode(list_mode=False))

        self.btn_list_mode = BrutalIconButton("Liste", variant="surface", size=32, min_width=54)
        self.btn_list_mode.setCheckable(True)
        self.btn_list_mode.setChecked(False)
        self.btn_list_mode.clicked.connect(lambda: self._set_view_mode(list_mode=True))

        header_row.addWidget(self.btn_grid_mode)
        header_row.addWidget(self.btn_list_mode)
        layout.addLayout(header_row)

        # --- TAG FILTER CHIPS BAR ---
        self.chips_container = QWidget()
        self.chips_layout = QHBoxLayout(self.chips_container)
        self.chips_layout.setContentsMargins(0, 0, 0, 0)
        self.chips_layout.setSpacing(Spacing.SM)
        layout.addWidget(self.chips_container)

        # --- CONTENT STACK ---
        self.content_stack = QStackedWidget()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid_layout.setContentsMargins(0, Spacing.XS, Spacing.SM, Spacing.XL)
        self.grid_layout.setSpacing(Spacing.MD)

        self.scroll_area.setWidget(self.grid_widget)
        self.content_stack.addWidget(self.scroll_area)

        # Empty State
        empty_badge = t("favorites_empty_badge") if favorites_only else t("all_notes_empty_badge")
        empty_title = t("favorites_empty_title") if favorites_only else t("all_notes_empty_title")
        empty_desc = t("favorites_empty_desc") if favorites_only else t("all_notes_empty_desc")
        empty_cta = "" if favorites_only else t("new_node_btn")

        self.empty_hero = SelectionFrameHero(
            badge_text=empty_badge,
            headline_text=empty_title,
            desc_text=empty_desc,
            cta_text=empty_cta,
            parent=self,
        )
        if empty_cta:
            self.empty_hero.action_clicked.connect(self._create_new_note)

        empty_wrapper = QWidget()
        empty_layout = QVBoxLayout(empty_wrapper)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(self.empty_hero)
        self.content_stack.addWidget(empty_wrapper)

        layout.addWidget(self.content_stack, 1)

        # Floating Action Button
        self.fab = BrutalFAB(self, tooltip=t("new_node_btn"))
        self.fab.clicked.connect(self._create_new_note)

        self.refresh_notes()

    def _set_view_mode(self, list_mode: bool):
        self.list_mode = list_mode
        self.btn_grid_mode.setChecked(not list_mode)
        self.btn_list_mode.setChecked(list_mode)
        for card in self.note_widgets:
            card.set_list_mode(list_mode)
        self._rebuild_grid_layout()

    def _on_filter_text_changed(self, text: str):
        self.filter_query = text.strip().lower()
        self.apply_filters()

    def _on_tag_filter_clicked(self, tag_name: str | None):
        self.active_tag_filter = tag_name
        for chip in self.tag_chips:
            is_active = (chip.property("tag_value") == tag_name)
            chip.blockSignals(True)
            chip.setChecked(is_active)
            chip.blockSignals(False)
            chip.update()
        self.apply_filters()

    def _create_new_note(self):
        if hasattr(self.main_window, "create_new_node"):
            self.main_window.create_new_node()

    def open_note_signal(self, node_id: str):
        if hasattr(self.main_window, "open_editor_for_node_id"):
            self.main_window.open_editor_for_node_id(node_id)
        elif hasattr(self.main_window, "open_editor"):
            title = ""
            for card in self.note_widgets:
                if card.node_id == node_id:
                    title = card.title
                    break
            self.main_window.open_editor(node_id, title)

    def refresh_notes(self):
        data = self.data_manager.load_tree()
        all_nodes = data.get("nodes", [])

        if self.favorites_only:
            nodes_to_show = [n for n in all_nodes if n.get("is_favorite", False)]
        else:
            nodes_to_show = all_nodes

        self._clear_grid()
        self.note_widgets.clear()

        all_tags = set()
        for idx, node in enumerate(nodes_to_show, 1):
            tag = node.get("tag", "").strip()
            if tag:
                all_tags.add(tag)

            raw_preview = node.get("preview") or ""
            if not raw_preview:
                raw_preview = self.data_manager.load_note_content(node.get("id"))
            clean_preview = extract_plain_preview(raw_preview, max_len=140)

            card = NoteCard(
                node_id=node.get("id"),
                title=node.get("title", t("untitled")),
                preview_text=clean_preview,
                parent_page=self,
                color=node.get("color", ""),
                tag=tag,
                bg_color=node.get("bg_color", ""),
                is_favorite=node.get("is_favorite", False),
                card_index=idx,
                list_mode=self.list_mode,
            )
            self.note_widgets.append(card)

        self.count_badge.setText(str(len(nodes_to_show)))
        self._populate_tag_chips(sorted(all_tags))
        self.apply_filters()

    def _populate_tag_chips(self, sorted_tags: list[str]):
        while self.chips_layout.count():
            item = self.chips_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.tag_chips.clear()

        if not sorted_tags:
            self.chips_container.hide()
            return
        self.chips_container.show()

        all_chip = BrutalChip(t("all_notes_chip"), pastel_color=Colors.PRIMARY)
        all_chip.setProperty("tag_value", None)
        all_chip.setChecked(self.active_tag_filter is None)
        all_chip.clicked.connect(lambda: self._on_tag_filter_clicked(None))
        self.chips_layout.addWidget(all_chip)
        self.tag_chips.append(all_chip)

        for tag_str in sorted_tags:
            accent_col = resolve_accent_color("", seed=tag_str)
            chip = BrutalChip(tag_str, pastel_color=accent_col)
            chip.setProperty("tag_value", tag_str)
            chip.setChecked(self.active_tag_filter == tag_str)
            t_val = tag_str
            chip.clicked.connect(lambda _, val=t_val: self._on_tag_filter_clicked(val))
            self.chips_layout.addWidget(chip)
            self.tag_chips.append(chip)

        self.chips_layout.addStretch()

    def apply_filters(self):
        visible_cards = []
        q = self.filter_query
        active_tag = self.active_tag_filter

        for card in self.note_widgets:
            match_text = True
            if q:
                match_text = (q in card.title.lower()) or (q in card.preview_text.lower()) or (q in card.tag.lower())

            match_tag = True
            if active_tag is not None:
                match_tag = (card.tag.lower() == active_tag.lower())

            visible = match_text and match_tag
            card.setVisible(visible)
            if visible:
                visible_cards.append(card)

        if not visible_cards:
            self.content_stack.setCurrentIndex(1)
            self.fab.hide()
        else:
            self.content_stack.setCurrentIndex(0)
            self._rebuild_grid_layout(visible_cards)
            self.fab.show()
            self.fab.raise_()

    def _clear_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

    def _rebuild_grid_layout(self, cards: list[NoteCard] | None = None):
        self._clear_grid()
        if cards is None:
            cards = [c for c in self.note_widgets if c.isVisible()]

        if self.list_mode:
            for row_idx, card in enumerate(cards):
                self.grid_layout.addWidget(card, row_idx, 0)
        else:
            col_width = Metrics.NOTE_CARD_WIDTH + Spacing.MD
            avail_w = max(col_width, self.scroll_area.viewport().width() - Spacing.MD * 2)
            cols = max(1, avail_w // col_width)
            for idx, card in enumerate(cards):
                r = idx // cols
                c = idx % cols
                self.grid_layout.addWidget(card, r, c)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        margin = Spacing.XL
        fx = max(Spacing.MD, self.width() - self.fab.width() - margin)
        fy = max(Spacing.MD, self.height() - self.fab.height() - margin)
        self.fab.move(fx, fy)
        self.fab.raise_()
        if not self.list_mode:
            self._rebuild_grid_layout()
