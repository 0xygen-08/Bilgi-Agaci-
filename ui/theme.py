"""
Obsidian-Style Design System & Theme Tokens for Knowledge Tree.

A clean, modern, professional, distraction-free interface inspired by Obsidian.
Features:
- Refined Obsidian dark/light palette with deep charcoal surfaces and violet accents
- Hairline 1px borders (#2e2e34 / #e5e7eb)
- Minimalist flat surfaces with optional subtle elevation (zero cartoon offset shadows)
- Sleek 4-8px rounded corners
- Refined typography with proper sentence casing
- Clean, responsive canvas node cards
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
    QPalette,
    QPen,
    QPixmap,
)
from PyQt6.QtWidgets import QApplication


def is_system_dark_mode() -> bool:
    """Detect whether the OS / system theme is currently in Dark Mode."""
    app = QApplication.instance()
    if not app:
        return True  # Default to modern dark theme like Obsidian
    try:
        hints = app.styleHints()
        if hints and hasattr(hints, "colorScheme"):
            scheme = hints.colorScheme()
            if scheme == Qt.ColorScheme.Dark:
                return True
            elif scheme == Qt.ColorScheme.Light:
                return False
    except Exception:
        pass
    try:
        window_col = app.palette().color(QPalette.ColorRole.Window)
        return window_col.lightness() < 128
    except Exception:
        return True


class Colors:
    """
    Obsidian Minimalist Color Palette with dynamic System Theme tracking.
    Dark Mode: deep charcoal canvas (#141416), sleek surfaces (#202024), Obsidian violet (#7c3aed).
    Light Mode: crisp off-white canvas (#ffffff), light gray surfaces (#f8f9fa), subtle borders (#e5e7eb).
    """

    IS_DARK: bool = True

    # Primary brand accent (Obsidian Royal Violet)
    PRIMARY = "#7c3aed"
    PRIMARY_HOVER = "#8b5cf6"
    PRIMARY_ACTIVE = "#6d28d9"

    # Status & Utility accents (Refined, not neon)
    SUCCESS = "#10b981"
    WARNING = "#f59e0b"
    DANGER = "#ef4444"
    INFO = "#38bdf8"

    # Core Dynamic Tokens (Dark Theme Defaults)
    WINDOW = "#18181b"          # Topbar & main frame
    SIDEBAR = "#121214"         # Side navigation tree
    CANVAS = "#141416"          # Graph canvas background
    CREAM = "#141416"           # Canvas alias
    SURFACE = "#202024"         # Cards, panels, elevated widgets
    SURFACE_HOVER = "#2a2a32"   # Hover state for cards/items
    SURFACE_ACTIVE = "#32323e"  # Selected state for cards/items
    WHITE = "#202024"           # Surface alias
    TEXT = "#f4f4f5"            # Primary text (zinc-100)
    TEXT_MUTED = "#9ca3af"      # Secondary / description text (zinc-400)
    BORDER = "#2e2e34"          # Clean 1px hairline border
    BORDER_MUTED = "#242429"    # Very subtle divider
    SHADOW = "#000000"          # Shadow token
    EDGE = "#52525b"            # Mind-map connection line

    # Semantic compatibility aliases
    YELLOW = "#7c3aed"          # Legacy primary mappings now use Obsidian violet
    PINK = "#a855f7"
    GREEN = "#10b981"
    LIGHT_BLUE = "#18181b"
    SOFT_ORANGE = "#2a2a32"
    BLACK = "#000000"

    # Minimalist palette for nodes (clean dark slate cards with subtle colored accents)
    NODE_SURFACE = "#202024"
    NODE_SURFACE_HOVER = "#26262c"

    # Tag subtle pill palette
    TAG_ROTATION = (
        "#2e263d",  # Subtle violet
        "#1e2d3d",  # Subtle blue
        "#1a332a",  # Subtle emerald
        "#382c20",  # Subtle amber
        "#33222a",  # Subtle rose
        "#25252b",  # Subtle slate
    )

    PASTEL_ROTATION = (
        "#202024",
        "#222226",
        "#1f1f23",
        "#242428",
        "#212125",
    )

    CARD_ON_BLUE_ROTATION = PASTEL_ROTATION

    @classmethod
    def set_theme_mode(cls, is_dark: bool):
        """Switch palette tokens dynamically to follow OS/system theme."""
        cls.IS_DARK = is_dark
        if is_dark:
            # Obsidian Dark
            cls.PRIMARY = "#7c3aed"
            cls.PRIMARY_HOVER = "#8b5cf6"
            cls.PRIMARY_ACTIVE = "#6d28d9"

            cls.WINDOW = "#18181b"
            cls.SIDEBAR = "#121214"
            cls.CANVAS = "#141416"
            cls.CREAM = "#141416"
            cls.SURFACE = "#202024"
            cls.SURFACE_HOVER = "#2a2a32"
            cls.SURFACE_ACTIVE = "#32323e"
            cls.WHITE = "#202024"
            cls.TEXT = "#f4f4f5"
            cls.TEXT_MUTED = "#9ca3af"
            cls.BORDER = "#2e2e34"
            cls.BORDER_MUTED = "#242429"
            cls.SHADOW = "#000000"
            cls.EDGE = "#52525b"

            cls.YELLOW = "#7c3aed"
            cls.PINK = "#a855f7"
            cls.GREEN = "#10b981"
            cls.LIGHT_BLUE = "#18181b"
            cls.SOFT_ORANGE = "#2a2a32"
            cls.BLACK = "#000000"

            cls.NODE_SURFACE = "#202024"
            cls.NODE_SURFACE_HOVER = "#26262c"

            cls.TAG_ROTATION = (
                "#2e263d",
                "#1e2d3d",
                "#1a332a",
                "#382c20",
                "#33222a",
                "#25252b",
            )
            cls.PASTEL_ROTATION = (
                "#202024",
                "#222226",
                "#1f1f23",
                "#242428",
                "#212125",
            )
            cls.CARD_ON_BLUE_ROTATION = cls.PASTEL_ROTATION
        else:
            # Obsidian Light
            cls.PRIMARY = "#7c3aed"
            cls.PRIMARY_HOVER = "#6d28d9"
            cls.PRIMARY_ACTIVE = "#5b21b6"

            cls.WINDOW = "#f8f9fa"
            cls.SIDEBAR = "#f1f3f5"
            cls.CANVAS = "#ffffff"
            cls.CREAM = "#ffffff"
            cls.SURFACE = "#ffffff"
            cls.SURFACE_HOVER = "#f1f3f5"
            cls.SURFACE_ACTIVE = "#e9ecef"
            cls.WHITE = "#ffffff"
            cls.TEXT = "#18181b"
            cls.TEXT_MUTED = "#6b7280"
            cls.BORDER = "#e5e7eb"
            cls.BORDER_MUTED = "#f3f4f6"
            cls.SHADOW = "#000000"
            cls.EDGE = "#9ca3af"

            cls.YELLOW = "#7c3aed"
            cls.PINK = "#9333ea"
            cls.GREEN = "#059669"
            cls.LIGHT_BLUE = "#f8f9fa"
            cls.SOFT_ORANGE = "#f1f3f5"
            cls.BLACK = "#000000"

            cls.NODE_SURFACE = "#ffffff"
            cls.NODE_SURFACE_HOVER = "#f8f9fa"

            cls.TAG_ROTATION = (
                "#f3e8ff",
                "#e0e7ff",
                "#dcfce7",
                "#fef3c7",
                "#ffe4e6",
                "#f1f5f9",
            )
            cls.PASTEL_ROTATION = (
                "#ffffff",
                "#fafafa",
                "#f8f9fa",
            )
            cls.CARD_ON_BLUE_ROTATION = cls.PASTEL_ROTATION

        # Clear pattern cache on mode switch
        _PATTERN_CACHE.clear()

    # Legacy background/accent mapping to keep saved data looking elegant
    LEGACY_DARK_BGS = frozenset({
        "#1f2335", "#12263a", "#16161e", "#1a1b26", "#0a1929",
        "#0d1d2e", "#081726", "#282b4a", "#07121f", "#0b1a2a",
        "#c0f7fe", "#fbfae8", "#fe90e8", "#f7cb46", "#ffdc8b", "#99e885",
        "",
    })

    LEGACY_DARK_ACCENTS = frozenset({
        "#7aa2f7", "#a88dff", "#bb9fff", "#b9a5ff", "#d2bbff",
        "#68b4dc", "#e1ac63", "#9ece6a", "#f7768e", "#e0af68",
        "#bb9af7", "#1abc9c", "#ff9e64", "#c0caf5",
        "",
    })


class Spacing:
    """Consistent 4 / 8 / 12 / 16 / 20 / 24 spacing scale."""
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 20
    XXL = 24


class Borders:
    """Obsidian hairline 1px borders."""
    THIN = 1
    DEFAULT = 1


class Shadows:
    """Minimalist flat design: no comic offset shadows."""
    NONE = 0
    SM = 0
    MD = 0
    LG = 0
    HOVER_SHIFT = 0
    BLUR_RADIUS = 0


class Radii:
    """Subtle, modern rounded corners (4-8px)."""
    SM = 4
    MD = 6
    LG = 8
    XL = 10
    PILL = 999


class Motion:
    """Subtle, professional transitions."""
    FAST_MS = 90
    TOGGLE_MS = 100
    STICKER_TILT_DEG = 0.0  # Zero tilt: straight, organized, clean


class Metrics:
    """Shared layout dimensions matching professional desktop note apps."""
    TOUCH_MIN = 34
    ICON_BTN_SIZE = 32
    TOOLBAR_BTN_HEIGHT = 30
    TOOLBAR_BTN_MIN_WIDTH = 32
    FAB_SIZE = 46
    SIDEBAR_WIDTH = 240
    TOPBAR_HEIGHT = 48
    SEARCH_WIDTH = 260
    SEARCH_DROPDOWN_HEIGHT = 260
    EDITOR_MIN_WIDTH = 420

    # Canvas & subtle dotted-grid settings (~22px spacing, very faint dots)
    GRID_DOT_SPACING = 22
    GRID_DOT_DIAMETER = 1.8
    GRID_DOT_ALPHA = 18
    GRID_LINE_ALPHA = 14

    SELECTION_HANDLE = 7

    # Note cards in All Notes / Favorites
    NOTE_CARD_WIDTH = 280
    NOTE_CARD_HEIGHT = 160
    NOTE_LIST_HEIGHT = 80

    # Toggle switch dimensions
    TOGGLE_TRACK_W = 44
    TOGGLE_TRACK_H = 24
    TOGGLE_THUMB = 18


class Typography:
    """Font family registry and clean semantic QFont builders."""
    PRIMARY_FAMILY = "Poppins"
    FALLBACK_FAMILIES = ("Inter", "Segoe UI", "Roboto", "Noto Sans", "Cantarell", "Sans Serif")
    _loaded_family = None

    SIZE_HERO = 24
    SIZE_PAGE_TITLE = 20
    SIZE_EDITOR_TITLE = 18
    SIZE_SECTION = 14
    SIZE_CARD_TITLE = 14
    SIZE_BODY = 13
    SIZE_BUTTON = 12
    SIZE_LABEL = 11
    SIZE_CAPTION = 10

    PT_NODE_BASE = 11
    PT_NODE_MIN = 9
    PT_NODE_TAG = 9
    PT_EDITOR_BODY = 11
    PT_EDITOR_H1 = 20
    PT_EDITOR_H2 = 16

    @classmethod
    def resolve_base_path(cls) -> str:
        if hasattr(sys, "_MEIPASS"):
            return sys._MEIPASS
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @classmethod
    def load_fonts(cls) -> str:
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
        font = QFont(cls.family())
        font.setPixelSize(px_size)
        font.setWeight(QFont.Weight.DemiBold)
        return font

    @classmethod
    def heading(cls, px_size: int = SIZE_CARD_TITLE) -> QFont:
        font = QFont(cls.family())
        font.setPixelSize(px_size)
        font.setWeight(QFont.Weight.DemiBold)
        return font

    @classmethod
    def label(cls, px_size: int = SIZE_LABEL, letter_spacing_pct: float = 102.0) -> QFont:
        font = QFont(cls.family())
        font.setPixelSize(px_size)
        font.setWeight(QFont.Weight.Medium)
        font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, letter_spacing_pct)
        return font

    @classmethod
    def body(cls, px_size: int = SIZE_BODY) -> QFont:
        font = QFont(cls.family())
        font.setPixelSize(px_size)
        font.setWeight(QFont.Weight.Normal)
        return font

    @classmethod
    def canvas_font(cls, point_size: int = PT_NODE_BASE, weight: QFont.Weight = QFont.Weight.Medium) -> QFont:
        font = QFont(cls.family(), point_size, weight)
        return font


def _stable_index(seed: str, modulo: int) -> int:
    if not seed or modulo <= 0:
        return 0
    total = sum((idx + 1) * ord(ch) for idx, ch in enumerate(seed))
    return total % modulo


def relative_luminance(hex_color: str) -> float:
    c = QColor(hex_color)
    if not c.isValid():
        return 0.1
    def _chan(val: float) -> float:
        return val / 12.92 if val <= 0.03928 else ((val + 0.055) / 1.055) ** 2.4
    r = _chan(c.redF())
    g = _chan(c.greenF())
    b = _chan(c.blueF())
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def resolve_node_bg(raw_bg: str, seed: str = "", on_light_blue: bool = False) -> str:
    """Return sleek dark surface in dark mode or clean white in light mode."""
    return Colors.NODE_SURFACE


def resolve_accent_color(raw_color: str, seed: str = "", avoid_bg: str = "") -> str:
    """Return a refined accent color for tags and highlights."""
    norm = (raw_color or "").strip().lower()
    palette = Colors.TAG_ROTATION
    if norm in Colors.LEGACY_DARK_ACCENTS or not norm:
        return palette[_stable_index(seed, len(palette))]
    return raw_color


def readable_ink(bg_hex: str, muted: bool = False) -> QColor:
    """Return high-contrast legible text color."""
    if relative_luminance(bg_hex) < 0.35:
        ink = QColor("#f4f4f5")
        if muted:
            ink.setAlpha(180)
        return ink
    ink = QColor("#18181b")
    if muted:
        ink.setAlpha(160)
    return ink


# ---------------------------------------------------------------------------
# Canvas Grid Pattern Tile Cache
# ---------------------------------------------------------------------------

_PATTERN_CACHE: dict[str, QPixmap] = {}


def get_pattern_pixmap(
    bg_hex: str = None,
    pattern_type: str = "dot",
    spacing: int = Metrics.GRID_DOT_SPACING,
) -> QPixmap:
    if bg_hex is None:
        bg_hex = Colors.CANVAS

    key = f"{bg_hex}_{pattern_type}_{spacing}_{Colors.IS_DARK}"
    if key in _PATTERN_CACHE:
        return _PATTERN_CACHE[key]

    pixmap = QPixmap(spacing, spacing)
    pixmap.fill(QColor(bg_hex))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    dot_base = QColor("#ffffff" if Colors.IS_DARK else "#000000")

    if pattern_type == "grid":
        line_color = QColor(dot_base)
        line_color.setAlpha(Metrics.GRID_LINE_ALPHA)
        painter.setPen(QPen(line_color, 1))
        painter.drawLine(0, 0, spacing, 0)
        painter.drawLine(0, 0, 0, spacing)
    elif pattern_type == "dot":
        dot_color = QColor(dot_base)
        dot_color.setAlpha(Metrics.GRID_DOT_ALPHA)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(dot_color))
        center = spacing / 2.0
        r = Metrics.GRID_DOT_DIAMETER / 2.0
        painter.drawEllipse(
            int(round(center - r)),
            int(round(center - r)),
            max(1, int(round(Metrics.GRID_DOT_DIAMETER))),
            max(1, int(round(Metrics.GRID_DOT_DIAMETER))),
        )

    painter.end()
    _PATTERN_CACHE[key] = pixmap
    return pixmap


# ---------------------------------------------------------------------------
# Global QSS Builder (Obsidian Desktop Theme)
# ---------------------------------------------------------------------------

def build_menu_qss() -> str:
    fam = Typography.family()
    return f"""
        QMenu {{
            background-color: {Colors.SURFACE};
            color: {Colors.TEXT};
            border: 1px solid {Colors.BORDER};
            border-radius: {Radii.MD}px;
            padding: 4px;
            font-family: '{fam}', sans-serif;
            font-size: {Typography.SIZE_BODY}px;
        }}
        QMenu::item {{
            padding: 6px 14px;
            border-radius: {Radii.SM}px;
            color: {Colors.TEXT};
            margin: 1px 0px;
        }}
        QMenu::item:selected {{
            background-color: {Colors.PRIMARY};
            color: #ffffff;
        }}
        QMenu::separator {{
            height: 1px;
            background: {Colors.BORDER};
            margin: 4px 6px;
        }}
    """


def build_global_qss() -> str:
    fam = Typography.family()
    return f"""/* Knowledge Tree - Obsidian Minimalist Theme */
QMainWindow {{
    background-color: {Colors.WINDOW};
}}

QWidget {{
    color: {Colors.TEXT};
    font-family: '{fam}', 'Inter', 'Segoe UI', sans-serif;
    font-size: {Typography.SIZE_BODY}px;
}}

/* Sidebar */
#sidebar {{
    background-color: {Colors.SIDEBAR};
    border-right: 1px solid {Colors.BORDER};
}}

/* Topbar */
#topbar {{
    background-color: {Colors.WINDOW};
    border-bottom: 1px solid {Colors.BORDER};
}}

/* Workspace Top TabBar */
QTabBar {{
    background: transparent;
    qproperty-drawBase: 0;
}}
QTabBar::scroller {{
    width: 0px;
    height: 0px;
}}
QTabBar QToolButton {{
    background-color: {Colors.SURFACE};
    border: 1px solid {Colors.BORDER};
    border-radius: {Radii.SM}px;
    margin: 2px;
}}
QTabBar QToolButton:hover {{
    background-color: {Colors.SURFACE_HOVER};
}}
QTabBar::tab {{
    background-color: transparent;
    color: {Colors.TEXT_MUTED};
    border: 1px solid transparent;
    border-radius: {Radii.SM}px;
    padding: 6px 12px;
    margin-right: 4px;
    font-weight: 500;
    font-size: {Typography.SIZE_BUTTON}px;
    min-height: 22px;
}}
QTabBar::tab:hover {{
    background-color: {Colors.SURFACE_HOVER};
    color: {Colors.TEXT};
}}
QTabBar::tab:selected {{
    background-color: {Colors.SURFACE};
    color: {Colors.TEXT};
    border: 1px solid {Colors.BORDER};
    font-weight: 600;
}}
QTabBar::close-button {{
    subcontrol-position: right;
    margin: 2px 2px 2px 6px;
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
    background-color: transparent;
    color: {Colors.TEXT_MUTED};
    border: 1px solid transparent;
    border-radius: {Radii.SM}px;
    padding: 6px 10px;
    margin: 1px 2px;
    font-weight: 500;
    font-size: {Typography.SIZE_BODY}px;
}}
QListWidget#sidebar_tabs_list::item:hover {{
    background-color: {Colors.SURFACE_HOVER};
    color: {Colors.TEXT};
}}
QListWidget#sidebar_tabs_list::item:selected {{
    background-color: {Colors.SURFACE};
    color: {Colors.TEXT};
    border: 1px solid {Colors.BORDER};
    font-weight: 600;
}}

/* Search Results Popup */
QListWidget#search_results {{
    background-color: {Colors.SURFACE};
    color: {Colors.TEXT};
    border: 1px solid {Colors.BORDER};
    border-radius: {Radii.MD}px;
    padding: 4px;
    outline: none;
}}
QListWidget#search_results::item {{
    padding: 6px 10px;
    border-radius: {Radii.SM}px;
    color: {Colors.TEXT};
    margin: 1px 0px;
}}
QListWidget#search_results::item:hover {{
    background-color: {Colors.SURFACE_HOVER};
}}
QListWidget#search_results::item:selected {{
    background-color: {Colors.PRIMARY};
    color: #ffffff;
}}

/* Rich Text Note Editor Area */
QTextEdit#note_text_edit {{
    background-color: {Colors.SURFACE};
    color: {Colors.TEXT};
    border: 1px solid {Colors.BORDER};
    border-radius: {Radii.MD}px;
    padding: 14px;
    font-size: {Typography.SIZE_BODY}px;
    selection-background-color: {Colors.PRIMARY};
    selection-color: #ffffff;
}}

/* Splitter Handle between Canvas and Note Editor */
QSplitter::handle:horizontal {{
    background-color: {Colors.BORDER};
    width: 1px;
}}
QSplitter::handle:horizontal:hover {{
    background-color: {Colors.PRIMARY};
}}

/* ComboBox (Settings Language Selector) */
QComboBox {{
    background-color: {Colors.SURFACE};
    color: {Colors.TEXT};
    border: 1px solid {Colors.BORDER};
    border-radius: {Radii.SM}px;
    padding: 4px 10px;
    min-height: 24px;
    min-width: 120px;
    font-weight: 500;
}}
QComboBox:hover {{
    background-color: {Colors.SURFACE_HOVER};
    border-color: {Colors.PRIMARY};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
    background-color: transparent;
}}
QComboBox QAbstractItemView {{
    background-color: {Colors.SURFACE};
    color: {Colors.TEXT};
    border: 1px solid {Colors.BORDER};
    selection-background-color: {Colors.PRIMARY};
    selection-color: #ffffff;
    padding: 4px;
    border-radius: {Radii.SM}px;
}}

/* Scrollbars */
QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: 8px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {Colors.BORDER};
    min-height: 24px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background: {Colors.TEXT_MUTED};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    border: none;
    background: transparent;
    height: 8px;
    margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: {Colors.BORDER};
    min-width: 24px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {Colors.TEXT_MUTED};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Tooltips */
QToolTip {{
    background-color: {Colors.SURFACE};
    color: {Colors.TEXT};
    border: 1px solid {Colors.BORDER};
    padding: 4px 8px;
    border-radius: {Radii.SM}px;
    font-size: {Typography.SIZE_CAPTION}px;
}}

/* Dialogs & MessageBoxes (Modals) */
QMessageBox, QInputDialog, QDialog {{
    background-color: {Colors.WINDOW};
    color: {Colors.TEXT};
}}
QMessageBox QLabel, QInputDialog QLabel {{
    color: {Colors.TEXT};
    font-size: {Typography.SIZE_BODY}px;
}}
QMessageBox QPushButton, QInputDialog QPushButton {{
    background-color: {Colors.PRIMARY};
    color: #ffffff;
    border: 1px solid {Colors.PRIMARY};
    border-radius: {Radii.SM}px;
    padding: 6px 14px;
    min-height: 24px;
    font-weight: 500;
}}
QMessageBox QPushButton:hover, QInputDialog QPushButton:hover {{
    background-color: {Colors.PRIMARY_HOVER};
}}
QInputDialog QLineEdit {{
    background-color: {Colors.SURFACE};
    color: {Colors.TEXT};
    border: 1px solid {Colors.BORDER};
    border-radius: {Radii.SM}px;
    padding: 6px 10px;
    min-height: 24px;
}}
{build_menu_qss()}
"""
