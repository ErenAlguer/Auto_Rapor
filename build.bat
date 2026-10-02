@echo off
chcp 65001 > nul
echo ============================================================
echo   Oto Servis Takip - PyInstaller EXE Derleme Araci
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/3] Python kontrol ediliyor...
where pyinstaller >nul 2>nul
if %errorlevel% neq 0 (
    echo [BILGI] pyinstaller komutu dogrudan bulunamadi, Python modul olarak calistirilacak...
    py -3.11 -m PyInstaller --noconsole --onefile --name "OtoServisTakip" --clean main.py || (
        "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" -m PyInstaller --noconsole --onefile --name "OtoServisTakip" --clean main.py
    )
) else (
    echo [2/3] PyInstaller calistiriliyor: pyinstaller --noconsole --onefile main.py
    pyinstaller --noconsole --onefile --name "OtoServisTakip" --clean main.py
)

if %errorlevel% equ 0 (
    echo.
    echo ============================================================
    echo [BASARILI] Program basariyla derlendi!
    echo Calistirilabilir dosya: dist\OtoServisTakip.exe
    echo ============================================================
) else (
    echo.
    echo [HATA] Derleme sirasinda hata olustu.
)

pause
