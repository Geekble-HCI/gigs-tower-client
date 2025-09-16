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
REM ==========================
set DEVICE_ID=6
set GAME_TYPE=6

echo ======================================== >> %LOG_FILE%
echo %date% %time% : Starting GIGS Enter Screen... >> %LOG_FILE%

REM 프로젝트 디렉토리로 이동
cd /d %PROJECT_DIR%

REM 가상환경 활성화
call venv\Scripts\activate

REM ==========================
REM 무한 재시작 루프
REM ==========================
:loop
echo %date% %time% : Starting Enter screen (Device ID: %DEVICE_ID%) >> %LOG_FILE%

python pop-client.py --type $GAME_TYPE --device_id %DEVICE_ID% >> LOG_FILE% 2>&1

echo %date% %time% : Enter screen stopped. Restarting in 10 seconds... >> %LOG_FILE%
timeout /t 10
goto loop