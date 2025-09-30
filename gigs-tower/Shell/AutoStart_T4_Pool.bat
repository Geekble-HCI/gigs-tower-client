@echo off

REM ======================================
REM 현재 배치파일을 최대화된 새 CMD 창에서 실행
REM ======================================
if "%MAXIMIZED%" neq "1" (
    set "MAXIMIZED=1"
    start "" /max "%~f0"
    exit
)

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
set DEVICE_ID=4
set GAME_TYPE=4

REM ==========================
REM ip값 출력 후 10초대기
REM ==========================
ipconfig
timeout /t 10

REM 프로젝트 디렉토리로 이동
cd /d %PROJECT_DIR%

REM ==========================
REM 깃 저장소 origin/develop 기준으로 강제 동기화
REM ==========================
echo %date% %time% : Resetting local repo to origin/develop
git fetch --all
git reset --hard origin/develop
git clean -fd

timeout /t 10

REM ==========================
REM 무한 재시작 루프
REM ==========================
:loop
echo %date% %time% : Starting Enter screen (Device ID: %DEVICE_ID%)

REM 파이썬 파일 실행
python3 pop-client.py --type %GAME_TYPE% --device_id %DEVICE_ID%

echo %date% %time% : Enter screen stopped. Restarting in 10 seconds...
ipconfig
timeout /t 10
goto loop