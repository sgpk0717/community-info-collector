#!/bin/bash

# 8000번 포트를 사용 중인 프로세스 종료
echo "기존 8000번 포트 프로세스 종료 중..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# 잠시 대기
sleep 1

# 가상환경 활성화 및 백엔드 시작
echo "백엔드 서버 시작 중..."
source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000