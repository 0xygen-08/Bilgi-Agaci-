import os
import json
import uuid
import tempfile
import re
import shutil

class DataManager:
    def __init__(self, workspace_path):
        self.workspace_path = workspace_path
        self.notes_dir = os.path.join(workspace_path, "notes")
        self.images_dir = os.path.join(workspace_path, "images")
        self.settings_file = os.path.join(workspace_path, "settings.json")
        
        self._tree_cache = {}  # tab_id -> data mapping
        
        self.ensure_workspace()
        
        settings = self.load_settings()
        self.active_tab_id = settings.get("active_tab", "default")

    def ensure_workspace(self):
        if not os.path.exists(self.workspace_path):
            os.makedirs(self.workspace_path)
        if not os.path.exists(self.notes_dir):
            os.makedirs(self.notes_dir)
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
            
        if not os.path.exists(self.settings_file):
            self.save_settings({
                "language": "tr",
                "auto_save": True,
                "offline_mode": True,
                "tabs": [{"id": "default", "name": "Ana Ağaç"}],
                "active_tab": "default",
                "bg_type": "dot", # dot, grid, blank
                "bg_color": "#4a4455"
            })
            
        # Migrate old tree_data.json if exists
        old_tree_file = os.path.join(self.workspace_path, "tree_data.json")
        default_tab_file = self.get_tree_file_path("default")
        if os.path.exists(old_tree_file) and not os.path.exists(default_tab_file):
            os.rename(old_tree_file, default_tab_file)
        elif not os.path.exists(default_tab_file):
            self.save_tree({"nodes": [], "edges": []}, "default")

    def _validate_tab_id(self, tab_id):
        if not tab_id or not re.match(r'^[a-zA-Z0-9\-]+$', tab_id):
            raise ValueError(f"Geçersiz sekme ID: {tab_id}")

    def get_tree_file_path(self, tab_id=None):
        if tab_id is None:
            tab_id = getattr(self, 'active_tab_id', "default")
        self._validate_tab_id(tab_id)
        return os.path.join(self.workspace_path, f"tree_{tab_id}.json")

    def load_settings(self):
        if not os.path.exists(self.settings_file):
            return {"language": "tr", "auto_save": True, "offline_mode": True, "tabs": [{"id": "default", "name": "Ana Ağaç"}], "active_tab": "default"}
        with open(self.settings_file, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"language": "tr", "auto_save": True, "offline_mode": True, "tabs": [{"id": "default", "name": "Ana Ağaç"}], "active_tab": "default"}

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
        settings = self.load_settings()
        settings["active_tab"] = tab_id
        self.save_settings(settings)
        self.active_tab_id = tab_id

    def delete_tab(self, tab_id):
        settings = self.load_settings()
        tabs = settings.get("tabs", [])
        if len(tabs) <= 1:
            return False # En az 1 sekme kalmalı
            
        tabs = [t for t in tabs if t["id"] != tab_id]
        settings["tabs"] = tabs
        if settings.get("active_tab") == tab_id:
            settings["active_tab"] = tabs[0]["id"]
            self.active_tab_id = tabs[0]["id"]
            
        self.save_settings(settings)
        
        # Dosyasını sil
        file_path = self.get_tree_file_path(tab_id)
        if os.path.exists(file_path):
            os.remove(file_path)
            
        if tab_id in self._tree_cache:
            del self._tree_cache[tab_id]
        return True

    def save_tree(self, tree_data, tab_id=None):
        if tab_id is None:
            tab_id = getattr(self, 'active_tab_id', "default")
        self._tree_cache[tab_id] = tree_data
        self._atomic_write_json(self.get_tree_file_path(tab_id), tree_data)

    def load_tree(self, tab_id=None):
        if tab_id is None:
            tab_id = getattr(self, 'active_tab_id', "default")
            
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
        if not note_id or not re.match(r'^[a-zA-Z0-9\-]+$', note_id):
            raise ValueError(f"Geçersiz not ID: {note_id}")

    def save_note_content(self, note_id, content, tab_id=None):
        self._validate_note_id(note_id)
        file_path = os.path.join(self.notes_dir, f"{note_id}.txt")
        dir_name = os.path.dirname(file_path)
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(content)
            os.replace(tmp_path, file_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

        clean_text = re.sub(r'<[^>]+>', '', content).replace('\n', ' ').strip()
        preview = clean_text[:100] + ('...' if len(clean_text) > 100 else '')
        
        # Sadece ilgili sekmedeki ağacı güncelle (optimizasyon)
        tid = tab_id if tab_id else getattr(self, 'active_tab_id', "default")
        tree_data = self.load_tree(tid)
        updated = False
        for node in tree_data.get("nodes", []):
            if node.get("id") == note_id:
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
        return "İçeriği buraya yazın..."
        
    def save_image(self, source_path):
        """Kullanıcının seçtiği resmi workspace içine kopyalar ve yeni yolunu döner."""
        if not os.path.exists(source_path):
            return None
        ext = os.path.splitext(source_path)[1].lower()
        if not ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
            return None
            
        new_filename = f"{self.generate_id()}{ext}"
        dest_path = os.path.join(self.images_dir, new_filename)
        shutil.copy2(source_path, dest_path)
        return dest_path

    def delete_note(self, note_id):
        self._validate_note_id(note_id)
        file_path = os.path.join(self.notes_dir, f"{note_id}.txt")
        if os.path.exists(file_path):
            os.remove(file_path)

    def generate_id(self):
        return str(uuid.uuid4())
        
    def create_backup(self, zip_filepath):
        base_name = zip_filepath.replace(".zip", "")
        shutil.make_archive(base_name, 'zip', self.workspace_path)
        return base_name + ".zip"
        
    def import_backup(self, zip_filepath):
        import zipfile
        if not zipfile.is_zipfile(zip_filepath):
            raise ValueError("Seçilen dosya geçerli bir ZIP arşivi değil.")
        
        safety_backup_dir = tempfile.mkdtemp(prefix="bilgi_agaci_safety_")
        safety_backup_path = os.path.join(safety_backup_dir, "safety_backup")
        try:
            shutil.make_archive(safety_backup_path, 'zip', self.workspace_path)
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
            
            with zipfile.ZipFile(zip_filepath, 'r') as zf:
                for member in zf.infolist():
                    total_extracted_size += member.file_size
                    if total_extracted_size > MAX_TOTAL_SIZE:
                        raise ValueError("Güvenlik İhlali: Zip dosyası çok büyük.")
                        
                    target_path = os.path.abspath(os.path.join(self.workspace_path, member.filename))
                    workspace_abs = os.path.abspath(self.workspace_path)
                    
                    if not target_path.startswith(workspace_abs + os.sep) and target_path != workspace_abs:
                        raise ValueError(f"Güvenlik İhlali: Güvensiz dosya yolu tespit edildi.")
                        
                    zf.extract(member, self.workspace_path)
                    
        except Exception as e:
            safety_zip = safety_backup_path + ".zip"
            if os.path.exists(safety_zip):
                shutil.unpack_archive(safety_zip, self.workspace_path, 'zip')
            raise RuntimeError(f"Yedek yüklenemedi. Eski verileriniz geri yüklendi.\nHata: {str(e)}")
        finally:
            if os.path.exists(safety_backup_dir):
                shutil.rmtree(safety_backup_dir, ignore_errors=True)
        
        self._tree_cache = {}
        self.ensure_workspace()

    def _atomic_write_json(self, file_path, data):
        dir_name = os.path.dirname(file_path)
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            os.replace(tmp_path, file_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
