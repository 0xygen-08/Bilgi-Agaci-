# Bilgi Ağacı (Knowledge Tree)

**Bilgi Ağacı (Knowledge Tree)**, zihin haritaları (mind maps) üzerinden görsel bir şekilde not almanızı, düşüncelerinizi organize etmenizi ve bağlantılar kurmanızı sağlayan Obsidian tarzı modern, minimalist ve kurumsal tasarımlı bir masaüstü uygulamasıdır.

## Özellikler

- **Görsel Zihin Haritası**: Notlarınızı sonsuz bir tuval üzerinde kutucuklar halinde oluşturun, boyutlandırın ve sağ tık sürükleme ile birbirine bağlayın.
- **Obsidian Minimalist Tasarım Sistemi**: Dikkat dağıtmayan zarif koyu/açık tema, 1px zarif çerçeveler, düz ve modern yüzeyler, mor vurgular (`#7c3aed`), temiz tipografi ve geometrik vektör simgeler.
- **Gelişmiş Zengin Metin Editörü (Rich Text)**: Başlıklar (`H1`, `H2`), listeler, kalın/italik yazılar (`Ctrl+B`, `Ctrl+I`), metin rengi ve sürükle-bırak görsel/PDF desteği.
- **Fotoğraf (OCR) ve PDF Metin Çıkarma & Arama**: Nota eklenen veya sürüklenen fotoğraflardaki ve PDF belgelerindeki yazıları Türkçe/İngilizce OCR (`Tesseract` + `pypdf`) ile okur, nota aktarır ve arama indeksine kaydeder.
- **Tüm Sekmeler, İçerik ve Fotoğraf/PDF Genel Araması**: Üst arama çubuğundan tüm sekmelerdeki düğüm başlıklarını, etiketleri, not içeriklerini ve fotoğraf/PDF içindeki yazıları arayın (`[OCR]` ve `[PDF]` etiketleriyle).
- **Geri Al / Yinele (Undo / Redo)**: Tuval üzerindeki düğüm ve bağlantı işlemleri için `Ctrl+Z` / `Ctrl+Y` ve üst bar kontrolleri.
- **Çoklu Dışa Aktarma (Export)**: Zihin haritasını yüksek çözünürlüklü **PNG** veya vektörel **PDF** olarak, notlarınızı ise bağlantılarıyla birlikte **Markdown (`.md`)** olarak dışa aktarın.
- **Tüm Notlar & Favoriler (Izgara / Liste Görünümü)**: Etiket (tag) filtreleme hapları, anlık kart/içerik/OCR arama ve duyarlı ızgara/liste görünümü.
- **Çoklu Çalışma Alanı (Sekmeler)**: Farklı projeleriniz için bağımsız sekmeler açın, yeniden adlandırın; her sekme kendi kamera ve yakınlaştırma (zoom) konumunu hafızasında tutar.
- **Çoklu Dil & Özelleştirilebilir Profil**: Türkçe ve İngilizce arayüz desteği, özelleştirilebilir profil adı ve tuval arka plan deseni (`Noktalı`, `Izgara`, `Düz`).
- **Güvenli Yerel Depolama, Otomatik Temizlik & Yedekleme**: Verileriniz yerel diskinizde (`~/KnowledgeTree`) saklanır; kullanılmayan yetim görseller otomatik temizlenir, tek tıkla `.zip` yedeği alabilir ve güvenle geri yükleyebilirsiniz.

## Kurulum (Geliştiriciler İçin)

Python 3.10+ yüklü sisteminizde aşağıdaki adımları izleyerek projeyi çalıştırabilirsiniz:

```bash
# 1. Depoyu klonlayın
git clone https://github.com/0xygen-08/Bilgi-Agaci-.git
cd Bilgi-Agaci-

# 2. Gerekli kütüphaneleri yükleyin
pip install -r requirements.txt

# 3. Uygulamayı başlatın
python3 app.py
```

## Dağıtım (Tek Dosya Paketleme)

Projeyi Python yüklü olmayan bilgisayarlarda çalıştırılabilir tek bir dosya haline getirmek için (`PyInstaller` ile):

```bash
pyinstaller --clean -y KnowledgeTree.spec
```

Oluşan çalıştırılabilir dosya `dist/KnowledgeTree` dizininde yer alacaktır.

## Katkıda Bulunma

1. Bu depoyu **Fork** edin veya klonlayın.
2. Yeni bir özellik dalı oluşturun (`git checkout -b yeni-ozellik`).
3. Değişikliklerinizi kaydedip **Pull Request** gönderin.
   - Tasarım token'ları ve tema sistemi: `ui/theme.py`
   - Yeniden kullanılabilir modern bileşenler: `ui/components.py`
   - Çekirdek veri yöneticisi: `core/data_manager.py`

## Lisans
MIT License
