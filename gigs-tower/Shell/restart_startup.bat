@echo off
setlocal

REM ==========================
REM start-enter.bat 경로
REM ==========================
set "PROJECT_DIR=%~dp0"
set "BAT_FILE=%PROJECT_DIR%start-enter.bat"

REM ==========================
REM Startup 폴더 경로
REM ==========================
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

REM ==========================
REM 바로가기 파일 경로
REM ==========================
set "LINK_FILE=%STARTUP_FOLDER%\start-enter.lnk"

REM ==========================
REM 기존 바로가기 제거 (있으면)
REM ==========================
if exist "%LINK_FILE%" (
    del "%LINK_FILE%"
)

REM ==========================
REM 바로가기 생성
REM ==========================
powershell -command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%LINK_FILE%'); $Shortcut.TargetPath = '%BAT_FILE%'; $Shortcut.WorkingDirectory = '%PROJECT_DIR%'; $Shortcut.WindowStyle = 1; $Shortcut.Save()"

echo Startup 등록 완료: "%LINK_FILE%"
pause
