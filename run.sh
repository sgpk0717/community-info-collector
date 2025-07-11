#!/bin/bash
# 백엔드 서버 실행 스크립트

echo "🚀 Community Info Collector 백엔드 시작..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000