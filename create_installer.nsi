!include "MUI2.nsh"

; Configuración básica
Name "Sistema Hospitalario"
OutFile "Instalador_Hospitalario.exe"
InstallDir "$PROGRAMFILES\Sistema Hospitalario"
InstallDirRegKey HKCU "Software\SistemaHospitalario" ""

; Variables
Var StartMenuFolder

; Interfaz moderna
!define MUI_ABORTWARNING
!define MUI_ICON "resources\hospital.ico"
!define MUI_UNICON "resources\hospital.ico"

; Páginas del instalador
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Páginas del desinstalador
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Idiomas
!insertmacro MUI_LANGUAGE "Spanish"

Section "Instalar Aplicación" SecMain
    SectionIn RO
    
    ; Establecer directorio de salida
    SetOutPath "$INSTDIR"
    
    ; Copiar archivos principales
    File /r "dist\HospitalSystem\*.*"
    
    ; Crear acceso directo en el escritorio
    CreateShortCut "$DESKTOP\Sistema Hospitalario.lnk" "$INSTDIR\HospitalSystem.exe" "" "$INSTDIR\resources\hospital.ico"
    
    ; Crear entrada en el menú Inicio
    !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
        CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
        CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Sistema Hospitalario.lnk" "$INSTDIR\HospitalSystem.exe"
        CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Desinstalar.lnk" "$INSTDIR\Uninstall.exe"
    !insertmacro MUI_STARTMENU_WRITE_END
    
    ; Crear desinstalador
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    ; Registrar en el registro
    WriteRegStr HKCU "Software\SistemaHospitalario" "" $INSTDIR
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SistemaHospitalario" \
        "DisplayName" "Sistema Hospitalario"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SistemaHospitalario" \
        "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SistemaHospitalario" \
        "DisplayIcon" "$INSTDIR\resources\hospital.ico"
    WriteReg