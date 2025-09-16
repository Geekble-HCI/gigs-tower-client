#!/bin/bash

# GIGS Game Client - Basketball Auto Start Script
# 농구 게임 자동 시작 스크립트

GAME_NAME="Basketball"
GAME_TYPE=6
DEVICE_ID=6

# 스크립트 실행 위치를 기준으로 프로젝트 디렉토리 자동 탐지
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$HOME/gigs-basketball.log"

echo "========================================" >> $LOG_FILE
echo "$(date): Starting GIGS Game $GAME_NAME Client..." >> $LOG_FILE
echo "$(date): Script directory: $SCRIPT_DIR" >> $LOG_FILE
echo "$(date): Project directory: $PROJECT_DIR" >> $LOG_FILE

# 즉시 실행 (부팅 대기 제거)
echo "$(date): Starting immediately..." >> $LOG_FILE

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
    python3 pop-client.py --type $GAME_TYPE --device_id $DEVICE_ID 2>&1 | tee -a $LOG_FILE
    echo "$(date): Game client stopped. Restarting in 10 seconds..." >> $LOG_FILE
    sleep 10
done