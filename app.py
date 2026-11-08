import os
import sys

from PyQt6.QtWidgets import QApplication

from core.data_manager import DataManager
from ui.main_window import MainWindow
from ui.theme import Typography


def main():
    # Workspace Yolu
    workspace_path = os.path.expanduser("~/KnowledgeTree")

    # Veri Yöneticisi
    data_manager = DataManager(workspace_path)

    # Çoklu dil ayarı
    from core.i18n import set_language
    settings = data_manager.load_settings()
    set_language(settings.get("language", "tr"))

    # Uygulama Başlatma
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Sistem Teması (Aydınlık / Karanlık) Algılama ve Uygulama
    from PyQt6.QtCore import Qt
    from ui.theme import Colors, Typography, is_system_dark_mode
    Colors.set_theme_mode(is_system_dark_mode())

    # Bundled Neo-Brutalist Poppins font ailesini yükle
    Typography.load_fonts()
    app.setFont(Typography.body())

    window = MainWindow(data_manager)

    # Sistem teması canlı değişirse anlık uygula
    def on_color_scheme_changed(scheme):
        is_dark = (scheme == Qt.ColorScheme.Dark)
        Colors.set_theme_mode(is_dark)
        if hasattr(window, "apply_system_theme"):
            window.apply_system_theme()

    if hasattr(app.styleHints(), "colorSchemeChanged"):
        app.styleHints().colorSchemeChanged.connect(on_color_scheme_changed)

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
