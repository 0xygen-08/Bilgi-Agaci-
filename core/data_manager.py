import html
import json
import os
import re
import shutil
import tempfile
import urllib.parse
import uuid

from core.i18n import t


def extract_plain_preview(content: str, title: str = "", max_len: int = 120) -> str:
    """Strip HTML <head>/<style> blocks and tags cleanly to produce a readable note preview."""
    if not content:
        return ""
    cleaned = re.sub(r"<(style|head|script)[^>]*>.*?</\1>", " ", content, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<br\s*/?>|</p>|</li>|</h[1-6]>|</div>", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = html.unescape(cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Remove default heading/placeholder prefixes if unmodified
    if title:
        prefix = f"#{title}".strip()
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :].strip()
    for placeholder in ("İçeriği buraya yazın...", "Write your content here...", t("default_note_placeholder")):
        if cleaned == placeholder:
            cleaned = ""

    if not cleaned:
        return ""
    return cleaned[:max_len] + ("..." if len(cleaned) > max_len else "")


class DataManager:
    def __init__(self, workspace_path):
        self.workspace_path = workspace_path
        self.notes_dir = os.path.join(workspace_path, "notes")
        self.images_dir = os.path.join(workspace_path, "images")
        self.docs_dir = os.path.join(workspace_path, "docs")
        self.settings_file = os.path.join(workspace_path, "settings.json")

        self._tree_cache = {}  # tab_id -> data mapping

        self.ensure_workspace()

        settings = self.load_settings()
        tabs = settings.get("tabs", [])
        valid_ids = {tab.get("id") for tab in tabs if isinstance(tab, dict)}
        active = settings.get("active_tab", "default")
        if active not in valid_ids and tabs:
            active = tabs[0].get("id", "default")
        self.active_tab_id = active

    @staticmethod
    def _default_settings():
        return {
            "language": "tr",
            "user_name": "HARUN",
            "auto_save": True,
            "offline_mode": True,
            "tabs": [{"id": "default", "name": "Ana Ağaç"}],
            "active_tab": "default",
            "bg_type": "dot",  # dot, grid, blank
            "bg_color": "#FBFAE8",
        }

    def ensure_workspace(self):
        if not os.path.exists(self.workspace_path):
            os.makedirs(self.workspace_path)
        if not os.path.exists(self.notes_dir):
            os.makedirs(self.notes_dir)
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
        if not os.path.exists(self.docs_dir):
            os.makedirs(self.docs_dir)

        if not os.path.exists(self.settings_file):
            self.save_settings(self._default_settings())

        # Migrate old tree_data.json if exists
        old_tree_file = os.path.join(self.workspace_path, "tree_data.json")
        default_tab_file = self.get_tree_file_path("default")
        if os.path.exists(old_tree_file) and not os.path.exists(default_tab_file):
            os.rename(old_tree_file, default_tab_file)
        elif not os.path.exists(default_tab_file):
            self.save_tree({"nodes": [], "edges": []}, "default")

    def _validate_tab_id(self, tab_id):
        if not tab_id or not re.match(r"^[a-zA-Z0-9\-]+$", str(tab_id)):
            raise ValueError(f"Geçersiz sekme ID: {tab_id}")

    def get_tree_file_path(self, tab_id=None):
        if tab_id is None:
            tab_id = getattr(self, "active_tab_id", "default")
        self._validate_tab_id(tab_id)
        return os.path.join(self.workspace_path, f"tree_{tab_id}.json")

    def load_settings(self):
        defaults = self._default_settings()
        if not os.path.exists(self.settings_file):
            return defaults
        with open(self.settings_file, "r", encoding="utf-8") as f:
            try:
                loaded = json.load(f)
                if not isinstance(loaded, dict):
                    return defaults
                merged = {**defaults, **loaded}
                if not merged.get("tabs"):
                    merged["tabs"] = defaults["tabs"]
                return merged
            except json.JSONDecodeError:
                return defaults

    def save_settings(self, settings_data):
        self._atomic_write_json(self.settings_file, settings_data)

    def get_tabs(self):
        settings = self.load_settings()
        return settings.get("tabs", [{"id": "default", "name": "Ana Ağaç"}])

    def add_tab(self, name):
        settings = self.load_settings()
        tabs = settings.get("tabs", [])
        new_tab_id = self.generate_id()
        tabs.append({"id": new_tab_id, "name": name})
        settings["tabs"] = tabs
        settings["active_tab"] = new_tab_id
        self.save_settings(settings)
        self.active_tab_id = new_tab_id
        self.save_tree({"nodes": [], "edges": []}, new_tab_id)
        return new_tab_id

    def switch_tab(self, tab_id):
        self._validate_tab_id(tab_id)
        settings = self.load_settings()
        settings["active_tab"] = tab_id
        self.save_settings(settings)
        self.active_tab_id = tab_id

    def rename_tab(self, tab_id, new_name):
        self._validate_tab_id(tab_id)
        clean_name = (new_name or "").strip()
        if not clean_name:
            return False
        settings = self.load_settings()
        tabs = settings.get("tabs", [])
        updated = False
        for tab in tabs:
            if tab.get("id") == tab_id:
                tab["name"] = clean_name
                updated = True
                break
        if updated:
            settings["tabs"] = tabs
            self.save_settings(settings)
        return updated

    def delete_tab(self, tab_id):
        settings = self.load_settings()
        tabs = settings.get("tabs", [])
        if len(tabs) <= 1:
            return False  # En az 1 sekme kalmalı

        # Sekmeye ait tüm not dosyalarını sil (yetim dosya kalmasın)
        try:
            tree_data = self.load_tree(tab_id)
            for node in tree_data.get("nodes", []):
                nid = node.get("id")
                if nid:
                    self.delete_note(nid)
        except Exception:
            pass

        tabs = [tab for tab in tabs if tab["id"] != tab_id]
        settings["tabs"] = tabs
        if settings.get("active_tab") == tab_id:
            settings["active_tab"] = tabs[0]["id"]
            self.active_tab_id = tabs[0]["id"]

        self.save_settings(settings)

        # Ağaç JSON dosyasını sil
        file_path = self.get_tree_file_path(tab_id)
        if os.path.exists(file_path):
            os.remove(file_path)

        if tab_id in self._tree_cache:
            del self._tree_cache[tab_id]
        self.cleanup_unused_assets()
        return True

    def save_tree(self, tree_data, tab_id=None):
        if tab_id is None:
            tab_id = getattr(self, "active_tab_id", "default")
        self._tree_cache[tab_id] = tree_data
        self._atomic_write_json(self.get_tree_file_path(tab_id), tree_data)

    def load_tree(self, tab_id=None):
        if tab_id is None:
            tab_id = getattr(self, "active_tab_id", "default")

        if tab_id in self._tree_cache:
            return self._tree_cache[tab_id]

        file_path = self.get_tree_file_path(tab_id)
        if not os.path.exists(file_path):
            self._tree_cache[tab_id] = {"nodes": [], "edges": []}
            return self._tree_cache[tab_id]

        with open(file_path, "r", encoding="utf-8") as f:
            try:
                self._tree_cache[tab_id] = json.load(f)
                return self._tree_cache[tab_id]
            except json.JSONDecodeError:
                self._tree_cache[tab_id] = {"nodes": [], "edges": []}
                return self._tree_cache[tab_id]

    def _validate_note_id(self, note_id):
        if not note_id or not re.match(r"^[a-zA-Z0-9\-]+$", str(note_id)):
            raise ValueError(f"Geçersiz not ID: {note_id}")

    def save_note_content(self, note_id, content, tab_id=None):
        self._validate_note_id(note_id)
        file_path = os.path.join(self.notes_dir, f"{note_id}.txt")
        dir_name = os.path.dirname(file_path)
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            os.replace(tmp_path, file_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

        # İlgili sekmedeki ağacın preview alanını temiz metin olarak güncelle
        tid = tab_id if tab_id else getattr(self, "active_tab_id", "default")
        tree_data = self.load_tree(tid)
        updated = False
        for node in tree_data.get("nodes", []):
            if node.get("id") == note_id:
                preview = extract_plain_preview(content, title=node.get("title", ""), max_len=100)
                node["preview"] = preview
                updated = True
        if updated:
            self.save_tree(tree_data, tid)

    def load_note_content(self, note_id):
        self._validate_note_id(note_id)
        file_path = os.path.join(self.notes_dir, f"{note_id}.txt")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        return t("default_note_placeholder")

    def save_image(self, source_path):
        """Kullanıcının seçtiği resmi workspace içine kopyalar ve yeni yolunu döner."""
        if not os.path.exists(source_path):
            return None
        ext = os.path.splitext(source_path)[1].lower()
        if ext not in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"]:
            return None

        new_filename = f"{self.generate_id()}{ext}"
        dest_path = os.path.join(self.images_dir, new_filename)
        shutil.copy2(source_path, dest_path)
        return dest_path

    def save_document(self, source_path):
        """Kullanıcının seçtiği PDF veya dokümanı workspace içine kopyalar ve yeni yolunu döner."""
        if not os.path.exists(source_path):
            return None
        ext = os.path.splitext(source_path)[1].lower()
        orig_name = os.path.basename(source_path)
        base_name, _ = os.path.splitext(orig_name)
        # Keep clean recognizable filename prefix with unique id
        safe_base = re.sub(r"[^\w\-_.]", "_", base_name)[:30]
        new_filename = f"{safe_base}_{self.generate_id()[:8]}{ext}"
        dest_path = os.path.join(self.docs_dir, new_filename)
        shutil.copy2(source_path, dest_path)
        return dest_path

    def delete_note(self, note_id):
        self._validate_note_id(note_id)
        file_path = os.path.join(self.notes_dir, f"{note_id}.txt")
        if os.path.exists(file_path):
            os.remove(file_path)
        self.cleanup_unused_assets()

    def cleanup_unused_assets(self):
        """Hiçbir sekmedeki düğüme bağlı olmayan yetim notları ve hiçbir notta kullanılmayan görselleri temizler."""
        try:
            active_node_ids = set()
            all_tabs_ok = True
            for tab in self.get_tabs():
                tid = tab.get("id")
                if not tid:
                    continue
                try:
                    tree = self.load_tree(tid)
                    for node in tree.get("nodes", []):
                        nid = node.get("id")
                        if nid:
                            active_node_ids.add(nid)
                except Exception:
                    all_tabs_ok = False

            # 1. Yetim not dosyalarını temizle
            referenced_images = set()
            if os.path.isdir(self.notes_dir):
                for fname in os.listdir(self.notes_dir):
                    if not fname.endswith(".txt"):
                        continue
                    nid = fname[:-4]
                    fpath = os.path.join(self.notes_dir, fname)
                    if all_tabs_ok and nid not in active_node_ids:
                        try:
                            os.remove(fpath)
                            continue
                        except Exception:
                            pass
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            content = f.read()
                        for match in re.finditer(r"images[/\\]([^\"'\s>\\]+)", content):
                            referenced_images.add(urllib.parse.unquote(match.group(1)))
                    except Exception:
                        pass

            # 2. Hiçbir notta referansı kalmayan görselleri temizle
            if os.path.isdir(self.images_dir):
                for img_name in os.listdir(self.images_dir):
                    if img_name not in referenced_images:
                        try:
                            os.remove(os.path.join(self.images_dir, img_name))
                        except Exception:
                            pass
        except Exception:
            pass

    def generate_id(self):
        return str(uuid.uuid4())

    def create_backup(self, zip_filepath):
        self.cleanup_unused_assets()
        final_path = zip_filepath if zip_filepath.lower().endswith(".zip") else zip_filepath + ".zip"
        tmp_dir = tempfile.mkdtemp(prefix="bilgi_agaci_export_")
        try:
            tmp_base = os.path.join(tmp_dir, "archive")
            archive_file = shutil.make_archive(tmp_base, "zip", self.workspace_path)
            shutil.move(archive_file, final_path)
            return final_path
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def import_backup(self, zip_filepath):
        import zipfile

        if not zipfile.is_zipfile(zip_filepath):
            raise ValueError("Seçilen dosya geçerli bir ZIP arşivi değil.")

        safety_backup_dir = tempfile.mkdtemp(prefix="bilgi_agaci_safety_")
        safety_backup_path = os.path.join(safety_backup_dir, "safety_backup")
        incoming_zip_copy = os.path.join(safety_backup_dir, "incoming_backup.zip")
        try:
            shutil.copy2(zip_filepath, incoming_zip_copy)
            shutil.make_archive(safety_backup_path, "zip", self.workspace_path)
        except Exception:
            pass

        for item in os.listdir(self.workspace_path):
            item_path = os.path.join(self.workspace_path, item)
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception:
                pass

        try:
            MAX_TOTAL_SIZE = 500 * 1024 * 1024
            total_extracted_size = 0

            with zipfile.ZipFile(incoming_zip_copy, "r") as zf:
                for member in zf.infolist():
                    total_extracted_size += member.file_size
                    if total_extracted_size > MAX_TOTAL_SIZE:
                        raise ValueError("Güvenlik İhlali: Zip dosyası çok büyük.")

                    target_path = os.path.abspath(os.path.join(self.workspace_path, member.filename))
                    workspace_abs = os.path.abspath(self.workspace_path)

                    if not target_path.startswith(workspace_abs + os.sep) and target_path != workspace_abs:
                        raise ValueError("Güvenlik İhlali: Güvensiz dosya yolu tespit edildi.")

                    zf.extract(member, self.workspace_path)

        except Exception as e:
            safety_zip = safety_backup_path + ".zip"
            if os.path.exists(safety_zip):
                shutil.unpack_archive(safety_zip, self.workspace_path, "zip")
            raise RuntimeError(f"Yedek yüklenemedi. Eski verileriniz geri yüklendi.\nHata: {str(e)}")
        finally:
            if os.path.exists(safety_backup_dir):
                shutil.rmtree(safety_backup_dir, ignore_errors=True)

        self._tree_cache = {}
        self.ensure_workspace()
        settings = self.load_settings()
        tabs = settings.get("tabs", [])
        valid_ids = {tab.get("id") for tab in tabs if isinstance(tab, dict)}
        active = settings.get("active_tab", "default")
        if active not in valid_ids and tabs:
            active = tabs[0].get("id", "default")
        self.active_tab_id = active

    def _atomic_write_json(self, file_path, data):
        dir_name = os.path.dirname(file_path)
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            os.replace(tmp_path, file_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
