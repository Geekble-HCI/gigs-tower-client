@echo off
setlocal

REM ==========================
REM 프로젝트 디렉토리 (USERPROFILE 기준)
REM ==========================
set "PROJECT_DIR=%USERPROFILE%\Desktop\gigs-tower-client\gigs-tower"

REM ==========================
REM 로그 파일 경로 (프로젝트 폴더 안)
REM ==========================
set "LOG_FILE=%PROJECT_DIR%\gigs-enter.log"

REM ==========================
REM 환경 변수 
REM 1: "헬시 버거\n챌린지",
REM 2: "꿀잠 방해꾼\nOUT!",
REM 3: "불태워!\n칼로링머신",
REM 4: "볼볼볼\n영양소",
REM 5: "바이오데이터\n에어시소",
REM 6: "슛잇!\n무빙 골대",
REM 7: "입장 화면", 
REM 8: "퇴장 화면" 
REM ==========================
set DEVICE_ID=5
set GAME_TYPE=5

REM ==========================
REM 현재CMD창 최대화
REM ==========================
powershell -command "& {Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing; $sig = '[DllImport(\"user32.dll\")]public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);'; Add-Type -MemberDefinition $sig -Name NativeMethods -Namespace Win32; $hwnd = (Get-Process -Id $PID).MainWindowHandle; [Win32.NativeMethods]::ShowWindowAsync($hwnd, 3)}"

REM ==========================
REM ip값 출력 후 10초대기
REM ==========================
ipconfig
timeout /t 10

REM 프로젝트 디렉토리로 이동
cd /d %PROJECT_DIR%

REM ==========================
REM 깃 저장소 원격 HEAD 기준으로 강제 동기화
REM ==========================
echo %date% %time% : Resetting local repo to remote HEAD >> %LOG_FILE%
git fetch --all >> %LOG_FILE% 2>&1
git reset --hard origin/HEAD >> %LOG_FILE% 2>&1
git clean -fd >> %LOG_FILE% 2>&1

REM ==========================
REM 무한 재시작 루프
REM ==========================
:loop
echo %date% %time% : Starting Enter screen (Device ID: %DEVICE_ID%) >> %LOG_FILE%

REM 파이썬 파일 실행
python3 pop-client.py --type %GAME_TYPE% --device_id %DEVICE_ID% >> LOG_FILE% 2>&1

echo %date% %time% : Enter screen stopped. Restarting in 10 seconds... >> %LOG_FILE%
ipconfig
timeout /t 10
goto loop