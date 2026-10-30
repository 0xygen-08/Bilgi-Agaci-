# Bilgi Ağacı (Knowledge Tree) v3.0 — Neo-Brutalist Edition

**Bilgi Ağacı (Knowledge Tree)**, zihin haritaları (mind maps) üzerinden görsel bir şekilde not almanızı, düşüncelerinizi organize etmenizi ve bağlantılar kurmanızı sağlayan **Neo-Brutalist** tasarımlı modern bir masaüstü uygulamasıdır.

## ✨ Özellikler

- 🌟 **Görsel Zihin Haritası**: Notlarınızı sonsuz bir tuval üzerinde kutucuklar halinde oluşturun, boyutlandırın ve sağ tık sürükleme ile birbirine bağlayın.
- 🎨 **Neo-Brutalist Tasarım Sistemi**: Yüksek kontrastlı pastel kartlar (`#FE90E8`, `#C0F7FE`, `#99E885`, `#F7CB46`, `#FFDC8B`), kalın siyah çerçeveler, sıfır bulanıklıklı sert gölgeler, fiziksel basılma/hover animasyonları ve gömülü `Poppins` tipografisi.
- 📝 **Gelişmiş Zengin Metin Editörü (Rich Text)**: Başlıklar (`H1`, `H2`), listeler, kalın/italik yazılar, metin rengi ve sürükle-bırak görsel desteği.
- 🗂️ **Tüm Notlar & Favoriler (Izgara / Liste Görünümü)**: Etiket (tag) filtreleme hapları, anlık kart arama ve duyarlı ızgara/liste görünümü.
- 📁 **Çoklu Çalışma Alanı (Sekmeler)**: Farklı projeleriniz için tamamen bağımsız sekmeler açın; her sekme kendi kamera ve yakınlaştırma (zoom) konumunu hafızasında tutar.
- 🌍 **Çoklu Dil Desteği**: Türkçe ve İngilizce arayüz desteği.
- 🛡️ **Güvenli Yerel Depolama & Yedekleme**: Verileriniz yerel diskinizde (`~/KnowledgeTree`) saklanır; tek tıkla `.zip` yedeği alabilir ve güvenle geri yükleyebilirsiniz.

## 🚀 Kurulum (Geliştiriciler İçin)

Python 3.10+ yüklü sisteminizde aşağıdaki adımları izleyerek projeyi çalıştırabilirsiniz:

```bash
# 1. Depoyu klonlayın
git clone https://github.com/0xygen-08/Bilgi-Agaci.git
cd Bilgi-Agaci

# 2. Gerekli kütüphaneleri yükleyin
pip install -r requirements.txt

# 3. Uygulamayı başlatın
python3 app.py
```

## 📦 Dağıtım (Tek Dosya Paketleme)

Projeyi Python yüklü olmayan bilgisayarlarda çalıştırılabilir tek bir dosya haline getirmek için (`PyInstaller` ile):

```bash
pip install pyinstaller
pyinstaller --clean -y KnowledgeTree.spec
```

Oluşan çalıştırılabilir dosya `dist/KnowledgeTree` dizininde yer alacaktır.

## 🤝 Katkıda Bulunma

1. Bu depoyu **Fork** edin veya klonlayın.
2. Yeni bir özellik dalı oluşturun (`git checkout -b yeni-ozellik`).
3. Değişikliklerinizi kaydedip **Pull Request** gönderin.
   - Tasarım token'ları ve tema sistemi: `ui/theme.py`
   - Tekrar kullanılabilir Neo-Brutalist bileşenler: `ui/components.py`
   - Çekirdek veri yöneticisi: `core/data_manager.py`

## 📄 Lisans
MIT License
