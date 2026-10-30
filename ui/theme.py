"""
Central Neo-Brutalist Design System & Theme Tokens for Knowledge Tree.

All colors, borders, zero-blur hard shadows, corner radii, spacing scale,
typography factories, pattern tiles, and global Qt Style Sheets live here.
Components and screens MUST import tokens from this module instead of
using hard-coded colors or magic numbers.
"""

import os
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontDatabase,
    QPainter,
    QPen,
    QPixmap,
)


class Colors:
    """Exact Neo-Brutalist color palette from the design specification."""

    PINK = "#FE90E8"         # Accent, highlights, tags, destructive/special cards
    LIGHT_BLUE = "#C0F7FE"   # Main app/section background, sidebar, header areas
    GREEN = "#99E885"        # Success states, "new/add" actions, positive tags, toggle ON
    YELLOW = "#F7CB46"       # Primary buttons / CTA, FAB, active nav, important cards
    SOFT_ORANGE = "#FFDC8B"  # Secondary cards, hover states, note card variants
    BLACK = "#000000"        # ALL borders, hard offset shadows, text, icons
    CREAM = "#FBFAE8"        # Main mind-map canvas & note editor dotted-grid surface
    WHITE = "#FFFFFF"        # Clean inputs, base modals/menus, corner handles, toggle OFF

    # Playful pastel rotation across mind-map nodes (on Cream canvas)
    PASTEL_ROTATION = (
        YELLOW,
        PINK,
        LIGHT_BLUE,
        GREEN,
        SOFT_ORANGE,
    )

    # Playful pastel rotation across cards sitting on Light Blue (#C0F7FE) pages
    CARD_ON_BLUE_ROTATION = (
        YELLOW,
        PINK,
        GREEN,
        SOFT_ORANGE,
        WHITE,
    )

    # Pill tag/chip pastel rotation
    TAG_ROTATION = (
        PINK,
        GREEN,
        YELLOW,
        SOFT_ORANGE,
        LIGHT_BLUE,
    )

    # Legacy dark-mode defaults from previous app versions (mapped in UI layer only)
    LEGACY_DARK_BGS = frozenset({
        "#1f2335",
        "#12263a",
        "#16161e",
        "#1a1b26",
        "#0a1929",
        "#0d1d2e",
        "#081726",
        "#282b4a",
        "#07121f",
        "#0b1a2a",
        "",
    })

    LEGACY_DARK_ACCENTS = frozenset({
        "#7aa2f7",
        "#a88dff",
        "#bb9fff",
        "#b9a5ff",
        "#d2bbff",
        "#68b4dc",
        "#e1ac63",
        "#9ece6a",
        "#f7768e",
        "#e0af68",
        "#bb9af7",
        "#1abc9c",
        "#ff9e64",
        "#c0caf5",
        "",
    })


class Spacing:
    """Consistent 4 / 8 / 12 / 16 / 24 / 32 spacing scale."""

    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32


class Borders:
    """Solid black border thicknesses (2-3px)."""

    THIN = 2
    DEFAULT = 3


class Shadows:
    """Zero-blur hard offset shadow distances in pixels."""

    NONE = 0
    SM = 3
    MD = 4
    LG = 6
    HOVER_SHIFT = 2
    BLUR_RADIUS = 0


class Radii:
    """Medium rounded corner radii matching the Neo-Brutalist reference."""

    SM = 8
    MD = 12
    LG = 16
    XL = 18
    PILL = 999


class Motion:
    """Snappy physical transition timings (100-150ms)."""

    FAST_MS = 110
    TOGGLE_MS = 130
    STICKER_TILT_DEG = -2.5


class Metrics:
    """Shared layout and touch-target dimensions."""

    TOUCH_MIN = 44
    ICON_BTN_SIZE = 44
    TOOLBAR_BTN_HEIGHT = 40
    TOOLBAR_BTN_MIN_WIDTH = 42
    FAB_SIZE = 60
    SIDEBAR_WIDTH = 268
    TOPBAR_HEIGHT = 82
    SEARCH_WIDTH = 330
    SEARCH_DROPDOWN_HEIGHT = 240
    EDITOR_MIN_WIDTH = 480

    # Canvas & dotted-grid settings (~20px spacing, subtle black dots)
    GRID_DOT_SPACING = 20
    GRID_DOT_DIAMETER = 2.4
    GRID_DOT_ALPHA = 50
    GRID_LINE_ALPHA = 34

    # Figma-like selection frame corner handle size
    SELECTION_HANDLE = 9

    # Note cards in All Notes / Favorites
    NOTE_CARD_WIDTH = 292
    NOTE_CARD_HEIGHT = 204
    NOTE_LIST_HEIGHT = 112

    # Toggle switch dimensions
    TOGGLE_TRACK_W = 56
    TOGGLE_TRACK_H = 30
    TOGGLE_THUMB = 20


class Typography:
    """Font family registry and semantic QFont builders."""

    PRIMARY_FAMILY = "Poppins"
    FALLBACK_FAMILIES = ("Poppins", "Noto Sans", "Cantarell", "Sans Serif")
    _loaded_family = None

    # Pixel sizes for UI widgets
    SIZE_HERO = 28
    SIZE_PAGE_TITLE = 26
    SIZE_EDITOR_TITLE = 22
    SIZE_SECTION = 17
    SIZE_CARD_TITLE = 15
    SIZE_BODY = 14
    SIZE_BUTTON = 13
    SIZE_LABEL = 12
    SIZE_CAPTION = 11

    # Point sizes for rich-text & zoomable QGraphicsScene items
    PT_NODE_BASE = 12
    PT_NODE_MIN = 9
    PT_NODE_TAG = 9
    PT_EDITOR_BODY = 12
    PT_EDITOR_H1 = 24
    PT_EDITOR_H2 = 18

    @classmethod
    def resolve_base_path(cls) -> str:
        if hasattr(sys, "_MEIPASS"):
            return sys._MEIPASS
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @classmethod
    def load_fonts(cls) -> str:
        """Load bundled Poppins .ttf files into QFontDatabase for offline fidelity."""
        if cls._loaded_family:
            return cls._loaded_family

        fonts_dir = os.path.join(cls.resolve_base_path(), "assets", "fonts")
        registered_families = []
        if os.path.isdir(fonts_dir):
            for fname in sorted(os.listdir(fonts_dir)):
                if fname.lower().endswith((".ttf", ".otf")):
                    font_id = QFontDatabase.addApplicationFont(os.path.join(fonts_dir, fname))
                    if font_id >= 0:
                        registered_families.extend(QFontDatabase.applicationFontFamilies(font_id))

        available = set(QFontDatabase.families())
        if cls.PRIMARY_FAMILY in registered_families or cls.PRIMARY_FAMILY in available:
            cls._loaded_family = cls.PRIMARY_FAMILY
        else:
            for candidate in cls.FALLBACK_FAMILIES:
                if candidate in available:
                    cls._loaded_family = candidate
                    break
            else:
                cls._loaded_family = "Sans Serif"

        return cls._loaded_family

    @classmethod
    def family(cls) -> str:
        return cls._loaded_family or cls.load_fonts()

    @classmethod
    def display(cls, px_size: int = SIZE_PAGE_TITLE) -> QFont:
        """Poppins Black/ExtraBold (900), tight tracking for UPPERCASE hero/page headings."""
        font = QFont(cls.family())
        font.setPixelSize(px_size)
        font.setWeight(QFont.Weight.Black)
        font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 99.0)
        return font

    @classmethod
    def heading(cls, px_size: int = SIZE_CARD_TITLE) -> QFont:
        """Poppins ExtraBold (800) for card titles, modal headers, and editor headings."""
        font = QFont(cls.family())
        font.setPixelSize(px_size)
        font.setWeight(QFont.Weight.ExtraBold)
        return font

    @classmethod
    def label(cls, px_size: int = SIZE_LABEL, letter_spacing_pct: float = 104.0) -> QFont:
        """Poppins Bold (700) with slight letter-spacing for uppercase labels, buttons & chips."""
        font = QFont(cls.family())
        font.setPixelSize(px_size)
        font.setWeight(QFont.Weight.Bold)
        font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, letter_spacing_pct)
        return font

    @classmethod
    def body(cls, px_size: int = SIZE_BODY) -> QFont:
        """Poppins Medium (500) for comfortable sentence-case body text and inputs."""
        font = QFont(cls.family())
        font.setPixelSize(px_size)
        font.setWeight(QFont.Weight.Medium)
        return font

    @classmethod
    def canvas_font(cls, point_size: int = PT_NODE_BASE, weight: QFont.Weight = QFont.Weight.ExtraBold) -> QFont:
        """Point-sized Poppins font for zoomable QGraphicsScene items."""
        font = QFont(cls.family(), point_size, weight)
        return font


# ---------------------------------------------------------------------------
# Color Resolution & Contrast Helpers (Presentation Layer Only)
# ---------------------------------------------------------------------------

def _stable_index(seed: str, modulo: int) -> int:
    if not seed:
        return 0
    total = 0
    for idx, ch in enumerate(str(seed)):
        total += (idx + 1) * ord(ch)
    return total % modulo


def relative_luminance(hex_color: str) -> float:
    """Compute WCAG relative luminance in [0.0, 1.0]."""
    c = QColor(hex_color)
    if not c.isValid():
        return 1.0

    def _chan(val: float) -> float:
        return val / 12.92 if val <= 0.03928 else ((val + 0.055) / 1.055) ** 2.4

    r = _chan(c.redF())
    g = _chan(c.greenF())
    b = _chan(c.blueF())
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def resolve_node_bg(raw_bg: str, seed: str = "", on_light_blue: bool = False) -> str:
    """
    Map legacy dark-theme default node backgrounds deterministically onto the
    Neo-Brutalist pastel rotation while preserving explicit pastel/custom fills.
    """
    palette = Colors.CARD_ON_BLUE_ROTATION if on_light_blue else Colors.PASTEL_ROTATION
    norm = (raw_bg or "").strip().lower()
    if norm in Colors.LEGACY_DARK_BGS or relative_luminance(norm) < 0.22:
        return palette[_stable_index(seed, len(palette))]
    if on_light_blue and norm == Colors.LIGHT_BLUE.lower():
        # Ensure card stands out crisply against the Light Blue page background
        return Colors.WHITE
    return raw_bg


def resolve_accent_color(raw_color: str, seed: str = "", avoid_bg: str = "") -> str:
    """Resolve tag/accent color to a Neo-Brutalist pastel contrasting with avoid_bg."""
    norm = (raw_color or "").strip().lower()
    palette = Colors.TAG_ROTATION
    if norm in Colors.LEGACY_DARK_ACCENTS:
        chosen = palette[_stable_index(seed, len(palette))]
    else:
        chosen = raw_color

    if avoid_bg and chosen.strip().lower() == avoid_bg.strip().lower():
        idx = (_stable_index(seed, len(palette)) + 1) % len(palette)
        alt = palette[idx]
        if alt.lower() == avoid_bg.strip().lower():
            return Colors.WHITE
        return alt
    return chosen


def readable_ink(bg_hex: str, muted: bool = False) -> QColor:
    """
    Return pure black (#000000) ink for all pastel/light backgrounds (WCAG compliant),
    falling back to white only if a user selected a very dark custom color.
    """
    if relative_luminance(bg_hex) < 0.18:
        ink = QColor(Colors.WHITE)
        if muted:
            ink.setAlpha(215)
        return ink
    ink = QColor(Colors.BLACK)
    if muted:
        ink.setAlpha(188)
    return ink


# ---------------------------------------------------------------------------
# Shared Dotted-Grid & Pattern Tile Cache
# ---------------------------------------------------------------------------

_PATTERN_CACHE: dict[str, QPixmap] = {}


def get_pattern_pixmap(
    bg_hex: str = Colors.CREAM,
    pattern_type: str = "dot",
    spacing: int = Metrics.GRID_DOT_SPACING,
) -> QPixmap:
    """
    Return a seamlessly tileable QPixmap for the Cream (#FBFAE8) dotted-grid
    (or line-grid) canvas & editor background.
    """
    key = f"{bg_hex}_{pattern_type}_{spacing}"
    if key in _PATTERN_CACHE:
        return _PATTERN_CACHE[key]

    pixmap = QPixmap(spacing, spacing)
    pixmap.fill(QColor(bg_hex))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    if pattern_type == "grid":
        line_color = QColor(Colors.BLACK)
        line_color.setAlpha(Metrics.GRID_LINE_ALPHA)
        painter.setPen(QPen(line_color, 1))
        painter.drawLine(0, 0, spacing, 0)
        painter.drawLine(0, 0, 0, spacing)
    elif pattern_type == "dot":
        dot_color = QColor(Colors.BLACK)
        dot_color.setAlpha(Metrics.GRID_DOT_ALPHA)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(dot_color))
        center = spacing / 2.0
        r = Metrics.GRID_DOT_DIAMETER / 2.0
        painter.drawEllipse(
            int(round(center - r)),
            int(round(center - r)),
            max(2, int(round(Metrics.GRID_DOT_DIAMETER))),
            max(2, int(round(Metrics.GRID_DOT_DIAMETER))),
        )

    painter.end()
    _PATTERN_CACHE[key] = pixmap
    return pixmap


# ---------------------------------------------------------------------------
# Global Stylesheet Builders (100% Token-Driven, Zero Magic Numbers)
# ---------------------------------------------------------------------------

def build_menu_qss() -> str:
    """Neo-Brutalist context menu stylesheet."""
    fam = Typography.family()
    return f"""
        QMenu {{
            background-color: {Colors.WHITE};
            color: {Colors.BLACK};
            border: {Borders.DEFAULT}px solid {Colors.BLACK};
            border-radius: {Radii.MD}px;
            padding: {Spacing.SM}px;
            font-family: '{fam}', 'Noto Sans', sans-serif;
            font-size: {Typography.SIZE_BUTTON}px;
            font-weight: 700;
        }}
        QMenu::item {{
            padding: {Spacing.SM + 2}px {Spacing.LG}px;
            border-radius: {Radii.SM}px;
            color: {Colors.BLACK};
            margin: 2px 0px;
        }}
        QMenu::item:selected {{
            background-color: {Colors.YELLOW};
            color: {Colors.BLACK};
        }}
        QMenu::separator {{
            height: {Borders.THIN}px;
            background: {Colors.BLACK};
            margin: {Spacing.XS + 2}px {Spacing.XS}px;
        }}
    """


def build_global_qss() -> str:
    """Generate the application-wide Neo-Brutalist QSS strictly from tokens."""
    fam = Typography.family()
    return f"""/* Knowledge Tree - Neo-Brutalist Theme (Generated from ui/theme.py tokens) */
QMainWindow {{
    background-color: {Colors.LIGHT_BLUE};
}}

QWidget {{
    color: {Colors.BLACK};
    font-family: '{fam}', 'Noto Sans', 'Cantarell', sans-serif;
    font-size: {Typography.SIZE_BODY}px;
}}

/* Sidebar */
#sidebar {{
    background-color: {Colors.LIGHT_BLUE};
    border-right: {Borders.DEFAULT}px solid {Colors.BLACK};
}}

/* Topbar */
#topbar {{
    background-color: {Colors.LIGHT_BLUE};
    border-bottom: {Borders.DEFAULT}px solid {Colors.BLACK};
}}

/* Workspace Top TabBar */
QTabBar {{
    background: transparent;
    qproperty-drawBase: 0;
}}
QTabBar::tab {{
    background-color: {Colors.WHITE};
    color: {Colors.BLACK};
    border: {Borders.THIN}px solid {Colors.BLACK};
    border-radius: {Radii.MD}px;
    padding: {Spacing.SM}px {Spacing.MD + 2}px;
    margin-right: {Spacing.SM}px;
    font-weight: 800;
    font-size: {Typography.SIZE_LABEL}px;
    min-height: 24px;
}}
QTabBar::tab:hover {{
    background-color: {Colors.SOFT_ORANGE};
}}
QTabBar::tab:selected {{
    background-color: {Colors.YELLOW};
    border: {Borders.DEFAULT}px solid {Colors.BLACK};
}}
QTabBar::close-button {{
    subcontrol-position: right;
    margin: 2px 4px 2px 6px;
}}

/* Sidebar Workspace Tabs List */
QListWidget#sidebar_tabs_list {{
    background-color: transparent;
    border: none;
    outline: none;
    padding: 0px;
    margin: 0px;
}}
QListWidget#sidebar_tabs_list::item {{
    background-color: {Colors.WHITE};
    color: {Colors.BLACK};
    border: {Borders.THIN}px solid {Colors.BLACK};
    border-radius: {Radii.MD}px;
    padding: {Spacing.SM + 2}px {Spacing.MD}px;
    margin: {Spacing.XS}px 2px;
    font-weight: 700;
}}
QListWidget#sidebar_tabs_list::item:hover {{
    background-color: {Colors.SOFT_ORANGE};
}}
QListWidget#sidebar_tabs_list::item:selected {{
    background-color: {Colors.YELLOW};
    color: {Colors.BLACK};
    border: {Borders.DEFAULT}px solid {Colors.BLACK};
}}

/* Search Results Popup */
QListWidget#search_results {{
    background-color: {Colors.WHITE};
    color: {Colors.BLACK};
    border: {Borders.DEFAULT}px solid {Colors.BLACK};
    border-radius: {Radii.MD}px;
    padding: {Spacing.SM}px;
    outline: none;
}}
QListWidget#search_results::item {{
    padding: {Spacing.SM + 2}px {Spacing.MD}px;
    border-radius: {Radii.SM}px;
    color: {Colors.BLACK};
    font-weight: 700;
    margin: 2px 0px;
}}
QListWidget#search_results::item:hover {{
    background-color: {Colors.SOFT_ORANGE};
}}
QListWidget#search_results::item:selected {{
    background-color: {Colors.YELLOW};
    color: {Colors.BLACK};
}}

/* Rich Text Note Editor Area */
QTextEdit#note_text_edit {{
    background-color: {Colors.WHITE};
    color: {Colors.BLACK};
    border: none;
    border-radius: {Radii.MD}px;
    padding: {Spacing.LG}px;
    font-size: {Typography.SIZE_BODY}px;
    selection-background-color: {Colors.PINK};
    selection-color: {Colors.BLACK};
}}

/* Splitter Handle between Canvas and Note Editor */
QSplitter::handle:horizontal {{
    background-color: {Colors.BLACK};
    width: {Borders.DEFAULT}px;
}}
QSplitter::handle:horizontal:hover {{
    background-color: {Colors.PINK};
}}

/* ComboBox (Settings Language Selector) */
QComboBox {{
    background-color: {Colors.YELLOW};
    color: {Colors.BLACK};
    border: {Borders.DEFAULT}px solid {Colors.BLACK};
    border-radius: {Radii.MD}px;
    padding: {Spacing.SM}px {Spacing.LG}px;
    min-height: 24px;
    min-width: 150px;
    font-weight: 800;
}}
QComboBox:hover {{
    background-color: {Colors.SOFT_ORANGE};
}}
QComboBox::drop-down {{
    border-left: {Borders.THIN}px solid {Colors.BLACK};
    width: 32px;
    background-color: {Colors.WHITE};
    border-top-right-radius: {Radii.SM + 2}px;
    border-bottom-right-radius: {Radii.SM + 2}px;
}}
QComboBox QAbstractItemView {{
    background-color: {Colors.WHITE};
    color: {Colors.BLACK};
    border: {Borders.DEFAULT}px solid {Colors.BLACK};
    selection-background-color: {Colors.YELLOW};
    selection-color: {Colors.BLACK};
    padding: {Spacing.XS}px;
    font-weight: 700;
}}

/* Scrollbars */
QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: 12px;
    margin: {Spacing.XS}px 2px;
}}
QScrollBar::handle:vertical {{
    background: {Colors.YELLOW};
    border: {Borders.THIN}px solid {Colors.BLACK};
    min-height: 28px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{
    background: {Colors.PINK};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    border: none;
    background: transparent;
    height: 12px;
    margin: 2px {Spacing.XS}px;
}}
QScrollBar::handle:horizontal {{
    background: {Colors.YELLOW};
    border: {Borders.THIN}px solid {Colors.BLACK};
    min-width: 28px;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {Colors.PINK};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Tooltips */
QToolTip {{
    background-color: {Colors.YELLOW};
    color: {Colors.BLACK};
    border: {Borders.THIN}px solid {Colors.BLACK};
    padding: {Spacing.XS + 2}px {Spacing.SM + 2}px;
    font-weight: 700;
}}

/* Dialogs & MessageBoxes (Modals) */
QMessageBox, QInputDialog, QDialog {{
    background-color: {Colors.CREAM};
    color: {Colors.BLACK};
}}
QMessageBox QLabel, QInputDialog QLabel {{
    color: {Colors.BLACK};
    font-weight: 700;
    font-size: {Typography.SIZE_BODY}px;
}}
QMessageBox QPushButton, QInputDialog QPushButton {{
    background-color: {Colors.YELLOW};
    color: {Colors.BLACK};
    border: {Borders.DEFAULT}px solid {Colors.BLACK};
    border-radius: {Radii.MD}px;
    padding: {Spacing.SM}px {Spacing.LG + 4}px;
    min-height: 26px;
    font-weight: 800;
}}
QMessageBox QPushButton:hover, QInputDialog QPushButton:hover {{
    background-color: {Colors.SOFT_ORANGE};
}}
QInputDialog QLineEdit {{
    background-color: {Colors.WHITE};
    color: {Colors.BLACK};
    border: {Borders.DEFAULT}px solid {Colors.BLACK};
    border-radius: {Radii.MD}px;
    padding: {Spacing.SM + 2}px {Spacing.MD}px;
    min-height: 24px;
    font-weight: 600;
}}
{build_menu_qss()}
"""
