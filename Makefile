# 백엔드 서버 실행
run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 백엔드 서버 백그라운드 실행
run-bg:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &

# 백엔드 서버 중지
stop:
	pkill -f "uvicorn app.main:app"

# 의존성 설치
install:
	pip install -r requirements.txt

# 데이터베이스 마이그레이션
migrate:
	alembic upgrade head

# 모든 설정 및 실행
setup: install migrate run