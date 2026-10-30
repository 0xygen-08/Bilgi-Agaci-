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

    # Bundled Neo-Brutalist Poppins font ailesini yükle
    Typography.load_fonts()
    app.setFont(Typography.body())

    window = MainWindow(data_manager)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
