#!/bin/bash

# GIGS Game Client - Enter Screen Auto Start Script
# 입장 화면 자동 시작 스크립트

SCREEN_TYPE="Enter"
DEVICE_ID=7

# 스크립트 실행 위치를 기준으로 프로젝트 디렉토리 자동 탐지
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$HOME/gigs-enter.log"

echo "========================================" >> $LOG_FILE
echo "$(date): Starting GIGS $SCREEN_TYPE Screen..." >> $LOG_FILE

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

# 입장 화면 실행 (무한 재시작)
while true; do
    echo "$(date): Starting $SCREEN_TYPE screen (Device ID: $DEVICE_ID)..." >> $LOG_FILE
    python3 pop-client.py --enter --device_id $DEVICE_ID 2>&1 | tee -a $LOG_FILE
    echo "$(date): Enter screen stopped. Restarting in 10 seconds..." >> $LOG_FILE
    sleep 10
done