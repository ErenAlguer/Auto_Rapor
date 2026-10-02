"""
Araç Servis Takip Otomasyonu - Windows Tek Dosya (.exe) Derleme Betiği
PyInstaller kullanarak projeyi harici konsol penceresi olmadan tek bir çalıştırılabilir dosya haline getirir.
"""

import os
import sys
import shutil
import subprocess

def build():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    print("==================================================")
    print("  Oto Servis Takip - Tek Dosya .EXE Üretimi")
    print("==================================================")
    print(f"Çalışma Dizini: {base_dir}")

    # Eğer çalışan bir OtoServisTakip.exe varsa dosya kilitlenmesini önlemek için kapat
    try:
        subprocess.run(["taskkill", "/f", "/im", "OtoServisTakip.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # Mevcut veritabanı dosyalarını derleme öncesi güvene al
    dist_db = os.path.join(base_dir, "dist", "servis_takip.db")
    backup_db = os.path.join(base_dir, "servis_takip.db")
    if os.path.exists(dist_db) and not os.path.exists(backup_db):
        shutil.copy2(dist_db, backup_db)
        print("Mevcut veritabanı proje kök dizinine güvenle yedeklendi.")

    # Önceki build / dist kalıntılarını temizle (db hariç)
    build_dir = os.path.join(base_dir, "build")
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir, ignore_errors=True)

    dist_dir = os.path.join(base_dir, "dist")
    if os.path.exists(dist_dir):
        for item in os.listdir(dist_dir):
            if not item.endswith(".db"):
                item_path = os.path.join(dist_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                else:
                    try:
                        os.remove(item_path)
                    except Exception:
                        pass

    # PyInstaller komut parametreleri
    # Kullanıcı gereksinimi: pyinstaller --noconsole --onefile main.py
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconsole",
        "--onefile",
        "--name", "OtoServisTakip",
        "--clean",
        "main.py"
    ]

    print("\nPyInstaller çalıştırılıyor...")
    print("Komut: " + " ".join(cmd))
    
    result = subprocess.run(cmd)

    if result.returncode == 0:
        exe_path = os.path.join(base_dir, "dist", "OtoServisTakip.exe")
        print("\n" + "="*50)
        print(" [BAŞARILI] .EXE Dosyası Üretildi!")
        print(f" Konum: {exe_path}")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f" Boyut: {size_mb:.2f} MB")
        print("="*50 + "\n")
    else:
        print("\n[HATA] Derleme işlemi başarısız oldu!")
        sys.exit(result.returncode)

if __name__ == "__main__":
    build()
