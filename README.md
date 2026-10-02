# Oto Servis & Periyodik Bakım Takip Otomasyonu

Araç bakım servisleri ve oto tamir atölyeleri için plaka bazlı araç geçmişi takibi, bakım/onarım kayıtları, servis fişi yazdırma ve PDF aktarımı sağlayan masaüstü uygulaması.

---

## 🚀 Özellikler

- **İlişkisel Veritabanı (SQLite)**:
  - `Araclar` ve `Bakimlar` tabloları (Foreign Key ilişkili).
  - Plaka bazında tam veri tutarlılığı.
  - Sık kullanılan işlemler hazır liste (Yağ bakımı, fren balatası, disk değişimi, triger, buji vb.).
  - Hem açılır menüden hızlı seçim hem de klavye ile serbest metin ("Sağ ön disk değişimi" gibi) girişi.
- **Kullanıcı Arayüzü (PyQt6)**:
  - Türkçe karakter ve büyük harf duyarlı, otomatik tamamlama (`QCompleter`) destekli hızlı plaka arama.
  - Seçilen araca ait tüm geçmiş işlemleri kronolojik (tarihe göre sıralı) listeleyen dinamik tablo.
  - Araç künyesi: Marka, model, yıl, sahip, telefon, toplam bakım sayısı, son km, son bakım tarihi ve toplam servis harcaması.
  - Yeni araç ekleme, araç düzenleme, bakım ekleme/düzenleme/silme.
- **Yazdırma ve PDF Entegrasyonu**:
  - Şık servis fişi şablonu.
  - Windows varsayılan yazıcısına doğrudan yazdırma.
  - Yazdırma öncesi canlı sayfa önizleme.
  - Tek tıkla resmi servis dökümünü `.pdf` formatında kaydetme.
- **Windows Paketleme (PyInstaller)**:
  - Konsol penceresiz tek dosya (`--noconsole --onefile`) Windows `.exe` çıktısı.

---

## 📦 Kurulum ve Çalıştırma

### 1. Gereksinimleri Yükleme
```powershell
pip install -r requirements.txt
```

### 2. Uygulamayı Başlatma
```powershell
python main.py
```

### 3. Tek Dosya .EXE Olarak Derleme (PyInstaller)
Projeyi bağımsız Windows `.exe` dosyası haline getirmek için:
```powershell
python build_exe.py
```
veya doğrudan komut satırından:
```powershell
pyinstaller --noconsole --onefile --name "OtoServisTakip" main.py
```
veya `build.bat` dosyasına çift tıklayabilirsiniz.

Derlenen `.exe` dosyası `dist/` klasörü içerisinde yer alacaktır.
