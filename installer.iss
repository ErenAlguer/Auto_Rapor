; ===============================================================================
; Araç Bakım ve Servis Takip Otomasyonu - Profesyonel Windows Kurulum Betiği
; Araç: Inno Setup 6+
; Çıktı: Setup.exe (Müşteri Bilgisayarları İçin Tek Tıkla Kurulum Paketi)
; ===============================================================================

#define MyAppName "Araç Servis & Bakım Takip"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Oto Servis Otomasyon Yazılımları"
#define MyAppExeName "OtoServisTakip.exe"

[Setup]
; --- 1. UYGULAMA KİMLİĞİ VE BİLGİLERİ ---
; Her kurulumda uygulamanın aynı olduğunu tespit eden benzersiz GUID
AppId={{A79D3B24-8149-4F57-9A1F-30B1C4B598F1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppVerName={#MyAppName} v{#MyAppVersion}

; --- 2. PROGRAM FILES KURULUMU (AÇIKLAMA) ---
; {autopf} (Auto Program Files) makrosu:
; 64-bit Windows işletim sistemlerinde doğrudan "C:\Program Files\AracServisTakip" dizinine kurulur.
; 32-bit Windows sistemlerde ise otomatik olarak "C:\Program Files (x86)\AracServisTakip" yolunu seçer.
DefaultDirName={autopf}\AracServisTakip
DefaultGroupName=Araç Servis Takip Otomasyonu

; Program Files dizinine yazabilmek ve kısayolları tüm kullanıcılara kaydedebilmek için Yönetici İzni şarttır
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible

; --- 3. ÇIKTI (SETUP.EXE) VE SIKIŞTIRMA AYARLARI ---
OutputDir=installer_output
OutputBaseFilename=AracServis_Setup_v{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Kaldırma simgesi olarak ana .exe dosyasının simgesini kullan
UninstallDisplayIcon={app}\{#MyAppExeName}

; Kurulum sırasında çalışan eski bir sürüm varsa otomatik tespit edip kapatılmasını ister
CloseApplications=yes

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
; Kullanıcının isteğine bağlı masaüstü kısayolu oluşturma seçeneği
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; PyInstaller ile derlenmiş ana çalıştırılabilir dosyamızı Program Files altına ({app}) kopyalar
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; ===============================================================================
; 4. VERİTABANI KLASÖRÜ VE İZİN AYARLARI (PERMISSIONS) (AÇIKLAMA)
; ===============================================================================
; NEDEN PROGRAM FILES'A YAZILMAZ?
; Windows UAC (Kullanıcı Hesabı Denetimi) ilkelerine göre, Program Files klasörü
; salt-okunurdur; standart kullanıcı haklarıyla çalışan uygulamalar bu klasör içine
; SQLite veritabanı yazamaz veya güncelleyemez (Access Denied / Yetki hatası alınır).
;
; ÇÖZÜM:
; Veritabanı "AppData\Roaming\AracServis" altına yerleştirilmiştir.
; Kurulum sırasında bu klasör önceden oluşturulur ve "Permissions: users-full"
; direktifi ile Windows'taki tüm standart kullanıcılara (Users grubuna) tam okuma,
; yazma ve dosya oluşturma hakkı verilir.
; Böylece programı kısıtlı yetkili bir kullanıcı dahi açsa veritabanına sorunsuz yazar.
; "uninsneveruninstall" bayrağı ile program bilgisayardan kaldırılsa dahi müşterinin
; geçmiş araç bakım kayıtlarının KAZARA SİLİNMESİ KESİNLİKLE ENGELLENİR.
; ===============================================================================
Name: "{userappdata}\AracServis"; Permissions: users-full; Flags: uninsneveruninstall

[Icons]
; Başlat Menüsü Kısayolları
Name: "{autoprograms}\{groupname}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autoprograms}\{groupname}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Masaüstü Kısayolu (Kullanıcı onay kutusunu işaretlediyse oluşturulur)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Kurulum bittiğinde kullanıcının programı hemen başlatabilmesi için son ekranda onay kutusu sunar
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
