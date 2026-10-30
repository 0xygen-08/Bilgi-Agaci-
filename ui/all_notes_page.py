import re

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFontMetrics, QPainter, QPen, QTextOption
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

from core.i18n import t

from .components import (
    BrutalChip,
    BrutalFAB,
    BrutalIconButton,
    BrutalInput,
    BrutalTag,
    SelectionFrameHero,
    SparkleWidget,
    _PressHoverAnimator,
)
from .theme import (
    Borders,
    Colors,
    Metrics,
    Motion,
    Radii,
    Shadows,
    Spacing,
    Typography,
    readable_ink,
    resolve_accent_color,
    resolve_node_bg,
)


class NoteCard(QFrame):
    """
    Playful Neo-Brutalist Note Card with thick black border, zero-blur hard shadow,
    pastel fill rotation, bold uppercase title, tag chip, and physical press/hover physics.
    """

    def __init__(
        self,
        node_id: str,
        title: str,
        preview_text: str,
        parent_page: "AllNotesPage",
        color: str = Colors.PINK,
        tag: str = "",
        bg_color: str = Colors.YELLOW,
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
        self.shadow_px = Shadows.MD
        self.hover_px = Shadows.HOVER_SHIFT
        self._motion = _PressHoverAnimator(self, shadow_px=self.shadow_px, hover_px=self.hover_px)

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

        inset = float(self.hover_px + 1)
        face_w = max(40.0, float(self.width()) - inset - self.shadow_px - 2.0)
        face_h = max(40.0, float(self.height()) - inset - self.shadow_px - 2.0)

        base_rect = QRectF(inset, inset, face_w, face_h)
        shadow_rect = base_rect.translated(float(self.shadow_px), float(self.shadow_px))
        face_rect = base_rect.translated(self._motion.dx, self._motion.dy)

        # 1. Hard zero-blur black offset shadow
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(Colors.BLACK)))
        painter.drawRoundedRect(shadow_rect, Radii.LG, Radii.LG)

        # 2. Saturated pastel face + 3px solid black border
        painter.setPen(QPen(QColor(Colors.BLACK), Borders.DEFAULT))
        painter.setBrush(QBrush(QColor(self.bg_color)))
        painter.drawRoundedRect(face_rect, Radii.LG, Radii.LG)

        ink = readable_ink(self.bg_color)
        muted_ink = readable_ink(self.bg_color, muted=True)

        pad = float(Spacing.LG)
        cur_x = face_rect.left() + pad
        top_y = face_rect.top() + float(Spacing.MD)

        # 3. Top Metadata Row: Index Chip + Tag Pill + Favorite Star
        idx_font = Typography.label(Typography.SIZE_CAPTION)
        painter.setFont(idx_font)
        idx_str = f"#{self.card_index:02d}"
        idx_fm = QFontMetrics(idx_font)
        idx_w = float(idx_fm.horizontalAdvance(idx_str) + 12)
        idx_rect = QRectF(cur_x, top_y, idx_w, 22.0)
        painter.setPen(QPen(QColor(Colors.BLACK), Borders.THIN))
        painter.setBrush(QBrush(QColor(Colors.WHITE)))
        painter.drawRoundedRect(idx_rect, 6.0, 6.0)
        painter.setPen(QPen(QColor(Colors.BLACK)))
        painter.drawText(idx_rect, Qt.AlignmentFlag.AlignCenter, idx_str)
        cur_x += idx_w + float(Spacing.SM)

        if self.tag:
            tag_upper = self.tag.upper()
            tag_w = min(
                float(idx_fm.horizontalAdvance(tag_upper) + Spacing.LG),
                max(54.0, face_rect.width() - (cur_x - face_rect.left()) - 48.0),
            )
            tag_rect = QRectF(cur_x, top_y, tag_w, 22.0)
            tag_fill = resolve_accent_color(self.color, seed=self.tag, avoid_bg=self.bg_color)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(Colors.BLACK)))
            painter.drawRoundedRect(tag_rect.translated(2.0, 2.0), 11.0, 11.0)

            painter.setPen(QPen(QColor(Colors.BLACK), Borders.THIN))
            painter.setBrush(QBrush(QColor(tag_fill)))
            painter.drawRoundedRect(tag_rect, 11.0, 11.0)

            elided_tag = idx_fm.elidedText(tag_upper, Qt.TextElideMode.ElideRight, int(tag_w - 10))
            painter.setPen(QPen(readable_ink(tag_fill)))
            painter.drawText(tag_rect, Qt.AlignmentFlag.AlignCenter, elided_tag)

        if self.is_favorite:
            star_sz = 24.0
            star_rect = QRectF(face_rect.right() - pad - star_sz, top_y - 1.0, star_sz, star_sz)
            star_bg = Colors.PINK if self.bg_color.lower() == Colors.YELLOW.lower() else Colors.YELLOW
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(Colors.BLACK)))
            painter.drawRoundedRect(star_rect.translated(2.0, 2.0), 7.0, 7.0)
            painter.setPen(QPen(QColor(Colors.BLACK), Borders.THIN))
            painter.setBrush(QBrush(QColor(star_bg)))
            painter.drawRoundedRect(star_rect, 7.0, 7.0)
            painter.setPen(QPen(QColor(Colors.BLACK)))
            painter.drawText(star_rect, Qt.AlignmentFlag.AlignCenter, "★")

        # 4. Bold UPPERCASE Card Title
        title_font = Typography.heading(Typography.SIZE_CARD_TITLE + 1)
        painter.setFont(title_font)
        painter.setPen(QPen(ink))
        title_fm = QFontMetrics(title_font)
        title_top = top_y + 32.0
        content_w = face_rect.width() - pad * 2.0

        if self.list_mode:
            elided_title = title_fm.elidedText(self.title.upper(), Qt.TextElideMode.ElideRight, int(content_w))
            title_rect = QRectF(face_rect.left() + pad, title_top, content_w, 24.0)
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_title)
            preview_top = title_top + 26.0
        else:
            title_h = float(title_fm.lineSpacing() * 2 + 2)
            title_rect = QRectF(face_rect.left() + pad, title_top, content_w, title_h)
            opt = QTextOption(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            opt.setWrapMode(QTextOption.WrapMode.WordWrap)
            # Clamp to 2 lines cleanly
            words_title = self.title.upper()
            if title_fm.horizontalAdvance(words_title) > content_w * 1.85:
                words_title = title_fm.elidedText(words_title, Qt.TextElideMode.ElideRight, int(content_w * 1.8))
            painter.drawText(title_rect, words_title, opt)
            used_h = float(title_fm.lineSpacing() * (2 if title_fm.horizontalAdvance(words_title) > content_w else 1))
            preview_top = title_top + used_h + 6.0

        # 5. Thin black divider rule + readable preview body
        painter.setPen(QPen(QColor(Colors.BLACK), 1.5))
        painter.drawLine(
            int(face_rect.left() + pad),
            int(preview_top),
            int(face_rect.right() - pad),
            int(preview_top),
        )

        body_font = Typography.body(Typography.SIZE_LABEL + 1)
        painter.setFont(body_font)
        painter.setPen(QPen(muted_ink))
        body_fm = QFontMetrics(body_font)

        avail_h = max(18.0, face_rect.bottom() - float(Spacing.MD) - (preview_top + 8.0))
        max_lines = max(1, int(avail_h // max(1, body_fm.lineSpacing())))
        preview_str = self.preview_text.strip()
        if body_fm.horizontalAdvance(preview_str) > content_w * max_lines * 0.92:
            preview_str = body_fm.elidedText(
                preview_str,
                Qt.TextElideMode.ElideRight,
                int(content_w * max_lines * 0.9),
            )
        body_rect = QRectF(face_rect.left() + pad, preview_top + 8.0, content_w, avail_h)
        body_opt = QTextOption(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        body_opt.setWrapMode(QTextOption.WrapMode.WordWrap)
        painter.drawText(body_rect, preview_str, body_opt)

        painter.end()


class AllNotesPage(QWidget):
    """
    Neo-Brutalist Notes List / Favorites Screen:
    - Light-blue (#C0F7FE) background
    - Bold uppercase page title + rotated sticker count badge + ✦ sparkle star
    - Thick-bordered white search filter + Grid/List view toggle
    - Pastel tag filter chips row
    - Responsive pastel-rotated NoteCards + Empty-state SelectionFrameHero + Floating yellow FAB
    """

    def __init__(self, data_manager, main_window, favorites_only=False):
        super().__init__()
        self.data_manager = data_manager
        self.main_window = main_window
        self.favorites_only = favorites_only

        self.list_mode = False
        self.active_tag_filter = None  # None == All
        self.filter_query = ""
        self.note_widgets: list[NoteCard] = []
        self.tag_chips: list[BrutalChip] = []
        self.current_col_count = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XXL, Spacing.XL, Spacing.XXL, Spacing.XL)
        layout.setSpacing(Spacing.LG)

        # --- HEADER BAR ---
        header_row = QHBoxLayout()
        header_row.setSpacing(Spacing.MD)

        header_row.addWidget(SparkleWidget(26))

        raw_title = t("favorite_notes_title") if favorites_only else t("all_notes_title")
        clean_title = re.sub(r"^[▤☆\s]+", "", raw_title).strip().upper()
        self.title_lbl = QLabel(clean_title)
        self.title_lbl.setFont(Typography.display(Typography.SIZE_PAGE_TITLE))
        self.title_lbl.setStyleSheet(f"color: {Colors.BLACK}; background: transparent;")
        header_row.addWidget(self.title_lbl)

        sticker_color = Colors.PINK if favorites_only else Colors.YELLOW
        self.count_sticker = BrutalTag(
            t("fav_sticker" if favorites_only else "notes_sticker", count=0),
            fill_color=sticker_color,
            tilt_deg=Motion.STICKER_TILT_DEG,
        )
        header_row.addWidget(self.count_sticker)

        header_row.addStretch()

        # Filter Search Input
        self.filter_input = BrutalInput(
            placeholder=t("filter_notes_placeholder"),
            fill_color=Colors.WHITE,
            shadow_px=Shadows.MD,
        )
        self.filter_input.setFixedWidth(250)
        self.filter_input.textChanged.connect(self._on_filter_text_changed)
        header_row.addWidget(self.filter_input)

        # Grid / List View Toggle Buttons
        self.btn_grid_mode = BrutalIconButton("▦", variant="nav", size=Metrics.ICON_BTN_SIZE)
        self.btn_grid_mode.setCheckable(True)
        self.btn_grid_mode.setChecked(True)
        self.btn_grid_mode.setToolTip(t("grid_view_tooltip"))
        self.btn_grid_mode.clicked.connect(lambda: self._set_view_mode(list_mode=False))

        self.btn_list_mode = BrutalIconButton("☰", variant="nav", size=Metrics.ICON_BTN_SIZE)
        self.btn_list_mode.setCheckable(True)
        self.btn_list_mode.setChecked(False)
        self.btn_list_mode.setToolTip(t("list_view_tooltip"))
        self.btn_list_mode.clicked.connect(lambda: self._set_view_mode(list_mode=True))

        header_row.addWidget(self.btn_grid_mode)
        header_row.addWidget(self.btn_list_mode)
        layout.addLayout(header_row)

        # Subtitle
        subtitle_str = t("favorite_notes_desc") if favorites_only else t("all_notes_desc")
        self.subtitle_lbl = QLabel(subtitle_str)
        self.subtitle_lbl.setFont(Typography.body(Typography.SIZE_BODY))
        self.subtitle_lbl.setStyleSheet(f"color: {Colors.BLACK}; background: transparent;")
        layout.addWidget(self.subtitle_lbl)

        # --- TAG FILTER CHIPS BAR ---
        self.chips_container = QWidget()
        self.chips_layout = QHBoxLayout(self.chips_container)
        self.chips_layout.setContentsMargins(0, 0, 0, 0)
        self.chips_layout.setSpacing(Spacing.SM)
        layout.addWidget(self.chips_container)

        # --- CONTENT STACK: [0] Cards Scroll Area, [1] Empty State Hero ---
        self.content_stack = QStackedWidget()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid_layout.setContentsMargins(0, Spacing.XS, Spacing.MD, Spacing.XXL * 2)
        self.grid_layout.setSpacing(Spacing.XL)

        self.scroll_area.setWidget(self.grid_widget)
        self.content_stack.addWidget(self.scroll_area)

        # Empty State Container
        empty_wrap = QWidget()
        empty_layout = QVBoxLayout(empty_wrap)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_headline = t("no_favorite_notes") if favorites_only else t("no_notes_in_tab")
        self.empty_hero = SelectionFrameHero(
            badge_text=t("empty_notes_badge"),
            headline_text=empty_headline,
            desc_text=t("empty_canvas_desc"),
            cta_text=t("add_new_note"),
        )
        self.empty_hero.action_clicked.connect(self._create_note_from_page)
        empty_layout.addWidget(self.empty_hero)
        self.content_stack.addWidget(empty_wrap)

        layout.addWidget(self.content_stack, 1)

        # --- FLOATING ACTION BUTTON (FAB) ---
        self.fab = BrutalFAB(self, tooltip=t("add_new_note"))
        self.fab.clicked.connect(self._create_note_from_page)
        self.fab.raise_()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(Colors.LIGHT_BLUE))
        painter.end()

    def _create_note_from_page(self):
        if self.main_window:
            self.main_window.create_new_node()

    def _set_view_mode(self, list_mode: bool):
        self.list_mode = list_mode
        self.btn_grid_mode.setChecked(not list_mode)
        self.btn_list_mode.setChecked(list_mode)
        for card in self.note_widgets:
            card.set_list_mode(list_mode)
        self.rearrange_grid(force=True)

    def _on_filter_text_changed(self, text: str):
        self.filter_query = text.strip().lower()
        self.refresh_notes()

    def _select_tag_filter(self, tag_val: str | None):
        self.active_tag_filter = tag_val
        self.refresh_notes()

    def _rebuild_tag_chips(self, unique_tags: list[str]):
        for chip in self.tag_chips:
            self.chips_layout.removeWidget(chip)
            chip.deleteLater()
        self.tag_chips.clear()

        # Remove trailing stretch items
        while self.chips_layout.count() > 0:
            item = self.chips_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        all_chip = BrutalChip(t("all_filter"), pastel_color=Colors.YELLOW)
        all_chip.setChecked(self.active_tag_filter is None)
        all_chip.clicked.connect(lambda: self._select_tag_filter(None))
        self.chips_layout.addWidget(all_chip)
        self.tag_chips.append(all_chip)

        for idx, tag_str in enumerate(unique_tags):
            pastel = Colors.TAG_ROTATION[idx % len(Colors.TAG_ROTATION)]
            chip = BrutalChip(tag_str, pastel_color=pastel)
            chip.setChecked(self.active_tag_filter == tag_str)
            chip.clicked.connect(lambda checked, tg=tag_str: self._select_tag_filter(tg))
            self.chips_layout.addWidget(chip)
            self.tag_chips.append(chip)

        self.chips_layout.addStretch()
        self.chips_container.setVisible(len(unique_tags) > 0)

    def _extract_preview(self, node_data: dict) -> str:
        cached = (node_data.get("preview") or "").strip()
        if cached:
            return cached
        try:
            raw = self.data_manager.load_note_content(node_data["id"])
            clean = re.sub(r"<[^>]+>", " ", raw)
            clean = re.sub(r"\s+", " ", clean).strip()
            if clean and clean != f"#{node_data.get('title', '')} İçeriği buraya yazın...":
                return clean[:120] + ("..." if len(clean) > 120 else "")
        except Exception:
            pass
        return t("click_to_view_note")

    def refresh_notes(self):
        for widget in self.note_widgets:
            self.grid_layout.removeWidget(widget)
            widget.deleteLater()
        self.note_widgets.clear()
        self.current_col_count = 0

        tree_data = self.data_manager.load_tree()
        nodes = tree_data.get("nodes", [])

        # Collect eligible nodes (respecting favorites_only) for tag chips
        base_nodes = [
            n for n in nodes if (not self.favorites_only or n.get("is_favorite", False))
        ]

        unique_tags = []
        seen_tags = set()
        for n in base_nodes:
            tg = (n.get("tag") or "").strip()
            if tg and tg not in seen_tags:
                seen_tags.add(tg)
                unique_tags.append(tg)

        if self.active_tag_filter and self.active_tag_filter not in seen_tags:
            self.active_tag_filter = None

        self._rebuild_tag_chips(unique_tags)

        # Filter by active tag & search query
        filtered_nodes = []
        for n in base_nodes:
            tg = (n.get("tag") or "").strip()
            if self.active_tag_filter and tg != self.active_tag_filter:
                continue
            preview = self._extract_preview(n)
            if self.filter_query:
                haystack = f"{n.get('title', '')} {tg} {preview}".lower()
                if self.filter_query not in haystack:
                    continue
            filtered_nodes.append((n, preview))

        # Update rotated count sticker
        sticker_key = "fav_sticker" if self.favorites_only else "notes_sticker"
        self.count_sticker.setText(t(sticker_key, count=len(filtered_nodes)))

        if not filtered_nodes:
            self.content_stack.setCurrentIndex(1)
            return

        self.content_stack.setCurrentIndex(0)

        for idx, (node_data, preview_content) in enumerate(filtered_nodes):
            nid = node_data["id"]
            raw_bg = node_data.get("bg_color", "")
            # Rotate pastel colors playfully across cards while respecting explicit pastel choices
            if not raw_bg or raw_bg.strip().lower() in Colors.LEGACY_DARK_BGS:
                card_bg = Colors.CARD_ON_BLUE_ROTATION[idx % len(Colors.CARD_ON_BLUE_ROTATION)]
            else:
                card_bg = resolve_node_bg(raw_bg, seed=nid, on_light_blue=True)

            card = NoteCard(
                nid,
                node_data["title"],
                preview_content,
                self,
                color=node_data.get("color", ""),
                tag=node_data.get("tag", ""),
                bg_color=card_bg,
                is_favorite=node_data.get("is_favorite", False),
                card_index=idx + 1,
                list_mode=self.list_mode,
            )
            self.note_widgets.append(card)

        self.rearrange_grid(force=True)

    def _position_fab(self):
        margin = Spacing.XL + 4
        x = max(Spacing.LG, self.width() - self.fab.width() - margin)
        y = max(Spacing.LG, self.height() - self.fab.height() - margin)
        self.fab.move(x, y)
        self.fab.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_fab()
        self.rearrange_grid()

    def rearrange_grid(self, force=False):
        if not hasattr(self, "grid_layout") or not hasattr(self, "note_widgets"):
            return

        if self.list_mode:
            self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.grid_layout.setColumnStretch(0, 1)
            new_col_count = 1
        else:
            self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            self.grid_layout.setColumnStretch(0, 0)
            available_width = self.scroll_area.viewport().width()
            if available_width < 50:
                available_width = self.width() - Spacing.XXL * 2

            card_width = Metrics.NOTE_CARD_WIDTH
            spacing = self.grid_layout.spacing()
            margins = self.grid_layout.contentsMargins()
            usable_width = available_width - margins.left() - margins.right()
            new_col_count = max(1, (usable_width + spacing) // (card_width + spacing))

        if new_col_count == self.current_col_count and not force:
            return

        self.current_col_count = new_col_count

        for i, widget in enumerate(self.note_widgets):
            row = i // new_col_count
            col = i % new_col_count
            self.grid_layout.addWidget(widget, row, col)

    def open_note_signal(self, node_id):
        self.main_window.switch_to_tree_view()
        node = self.main_window.scene.nodes.get(node_id)
        if node:
            self.main_window.canvas_view.resetTransform()
            self.main_window.canvas_view.centerOn(node)
            self.main_window.scene.clearSelection()
            node.setSelected(True)
            self.main_window.open_editor(node_id, node.title)
