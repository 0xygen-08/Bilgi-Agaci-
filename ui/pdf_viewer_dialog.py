import os
import subprocess
import tempfile
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .components import BrutalButton, BrutalIconButton
from .theme import Borders, Colors, Metrics, Radii, Shadows, Spacing, Typography


class PDFViewerDialog(QDialog):
    """
    Neo-Brutalist PDF Page Viewer Dialog.
    Renders high-resolution PDF pages on-the-fly and allows navigating between pages.
    """

    def __init__(self, pdf_path: str, initial_page: int = 1, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.current_page = max(1, initial_page)
        self.total_pages = 1
        self._temp_files = []

        self.setWindowTitle(f"PDF Görüntüleyici — {os.path.basename(pdf_path)}")
        self.resize(900, 850)
        self.setStyleSheet(f"background-color: {Colors.WINDOW};")

        self._read_total_pages()
        self._init_ui()
        self._render_current_page()

    def _read_total_pages(self):
        try:
            from pypdf import PdfReader
            reader = PdfReader(self.pdf_path)
            self.total_pages = max(1, len(reader.pages))
        except Exception:
            self.total_pages = 1

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        # Header with navigation controls
        header = QWidget(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(Spacing.MD)

        self.lbl_file = QLabel(os.path.basename(self.pdf_path))
        self.lbl_file.setFont(Typography.heading(13))
        self.lbl_file.setStyleSheet(f"color: {Colors.TEXT};")
        header_layout.addWidget(self.lbl_file)

        header_layout.addStretch()

        self.btn_prev = BrutalIconButton("‹", variant="surface", size=30)
        self.btn_prev.clicked.connect(self._prev_page)
        header_layout.addWidget(self.btn_prev)

        self.lbl_page = QLabel(f"Sayfa {self.current_page} / {self.total_pages}")
        self.lbl_page.setFont(Typography.label(11))
        self.lbl_page.setStyleSheet(
            f"""
            background-color: {Colors.SURFACE};
            color: {Colors.TEXT};
            border: 1px solid {Colors.BORDER};
            border-radius: 4px;
            padding: 3px 10px;
            """
        )
        header_layout.addWidget(self.lbl_page)

        self.btn_next = BrutalIconButton("›", variant="surface", size=30)
        self.btn_next.clicked.connect(self._next_page)
        header_layout.addWidget(self.btn_next)

        self.btn_close = BrutalIconButton("✕", variant="surface", size=30)
        self.btn_close.clicked.connect(self.close)
        header_layout.addWidget(self.btn_close)

        layout.addWidget(header)

        # Scroll Area for rendering the page
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setStyleSheet(
            f"""
            QScrollArea {{
                background-color: {Colors.CANVAS};
                border: 1px solid {Colors.BORDER};
                border-radius: {Radii.MD}px;
            }}
            """
        )

        self.page_label = QLabel()
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setStyleSheet("background: transparent; padding: 12px;")
        self.scroll_area.setWidget(self.page_label)

        layout.addWidget(self.scroll_area, 1)

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._render_current_page()

    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._render_current_page()

    def _render_current_page(self):
        self.lbl_page.setText(f"Sayfa {self.current_page} / {self.total_pages}")
        self.btn_prev.setEnabled(self.current_page > 1)
        self.btn_next.setEnabled(self.current_page < self.total_pages)

        # Render page using pdftoppm for crisp 150 DPI rendering
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_out:
                out_base = tmp_out.name.replace(".png", "")
            self._temp_files.append(out_base)

            # pdftoppm -png -f <page> -l <page> -r 150 <pdf> <out_base>
            cmd = [
                "pdftoppm",
                "-png",
                "-f", str(self.current_page),
                "-l", str(self.current_page),
                "-r", "150",
                self.pdf_path,
                out_base,
            ]
            subprocess.run(cmd, check=True, capture_output=True, timeout=10)

            # pdftoppm produces files like <out_base>-1.png or <out_base>-01.png
            img_path = None
            for fname in os.listdir(os.path.dirname(out_base)):
                if fname.startswith(os.path.basename(out_base)) and fname.endswith(".png"):
                    img_path = os.path.join(os.path.dirname(out_base), fname)
                    self._temp_files.append(img_path)
                    break

            if img_path and os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                # Scale nicely to fit dialog width while keeping aspect ratio
                max_w = self.scroll_area.width() - 40
                if pixmap.width() > max_w:
                    scaled = pixmap.scaledToWidth(max(600, max_w), Qt.TransformationMode.SmoothTransformation)
                    self.page_label.setPixmap(scaled)
                else:
                    self.page_label.setPixmap(pixmap)
            else:
                self.page_label.setText(f"Sayfa {self.current_page} yüklenemedi.")
        except Exception as e:
            self.page_label.setText(f"Sayfa işlenirken hata oluştu:\n{e}")

    def closeEvent(self, event):
        for f in self._temp_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass
        super().closeEvent(event)

