#!/bin/bash

# GIGS Game Client - Sleep Auto Start Script
# 꿀잠 방해꾼 OUT! 자동 시작 스크립트

GAME_NAME="Sleep"
GAME_TYPE=2
DEVICE_ID=2
PROJECT_DIR="/home/pi/samyang-pop-client/gigs-tower"
LOG_FILE="/home/pi/gigs-sleep.log"

echo "========================================" >> $LOG_FILE
echo "$(date): Starting GIGS Game $GAME_NAME Client..." >> $LOG_FILE

# 30초 대기 (시스템 완전 부팅 대기)
echo "$(date): Waiting for system boot completion..." >> $LOG_FILE
sleep 30

# 네트워크 연결 대기
echo "$(date): Waiting for network connection..." >> $LOG_FILE
while ! ping -c 1 8.8.8.8 >/dev/null 2>&1; do
    echo "$(date): Network not ready, waiting 5 seconds..." >> $LOG_FILE
    sleep 5
done
echo "$(date): Network connected!" >> $LOG_FILE

# 프로젝트 디렉토리 존재 확인
if [ ! -d "$PROJECT_DIR" ]; then
    echo "$(date): ERROR - Project directory not found: $PROJECT_DIR" >> $LOG_FILE
    exit 1
fi

# 프로젝트 디렉토리로 이동
cd $PROJECT_DIR

# 가상환경 존재 확인 및 활성화
if [ ! -d "venv" ]; then
    echo "$(date): ERROR - Virtual environment not found" >> $LOG_FILE
    exit 1
fi

source venv/bin/activate
echo "$(date): Virtual environment activated" >> $LOG_FILE

# 게임 실행 (무한 재시작)
while true; do
    echo "$(date): Starting $GAME_NAME game client (Type: $GAME_TYPE, Device ID: $DEVICE_ID)..." >> $LOG_FILE
    python3 pop-client.py --tcp --type $GAME_TYPE --device_id $DEVICE_ID >> $LOG_FILE 2>&1
    echo "$(date): Game client stopped. Restarting in 10 seconds..." >> $LOG_FILE
    sleep 10
done