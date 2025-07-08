# Community Info Collector 설정 가이드

## 1. Windows에서 설정하기

### 1-1. Python 가상환경 설정
```bash
# Windows 명령 프롬프트 또는 PowerShell에서 실행
setup_windows.bat
```

또는 수동으로:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 1-2. PostgreSQL 설치
두 가지 방법 중 선택:

**방법 1: Docker 사용 (추천)**
```bash
docker-compose up -d
```

**방법 2: PostgreSQL 직접 설치**
1. https://www.postgresql.org/download/windows/ 에서 다운로드
2. 설치 시 비밀번호를 'password'로 설정
3. pgAdmin 또는 psql로 'community_collector' 데이터베이스 생성

### 1-3. 데이터베이스 테이블 생성
```bash
# 가상환경 활성화된 상태에서
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### 1-4. API 키 설정
`.env` 파일을 열어서 필요한 API 키 입력:

- **Reddit API**: https://www.reddit.com/prefs/apps 에서 앱 생성
- **Twitter API**: https://developer.twitter.com/ 에서 앱 생성
- **OpenAI API**: https://platform.openai.com/api-keys 에서 키 생성

### 1-5. 서버 실행
```bash
python run.py
```

서버가 실행되면 http://localhost:8000/docs 에서 API 테스트 가능

## 2. 문제 해결

### PostgreSQL 연결 오류
- PostgreSQL 서비스가 실행 중인지 확인
- 포트 5432가 사용 가능한지 확인
- .env의 DATABASE_URL이 올바른지 확인

### 패키지 설치 오류
```bash
# pip 업그레이드
python -m pip install --upgrade pip

# 특정 패키지만 설치
pip install fastapi uvicorn sqlalchemy
```

## 3. API 사용 예시

Swagger UI (http://localhost:8000/docs)에서 직접 테스트하거나:

```python
import requests

# 검색 요청
response = requests.post("http://localhost:8000/api/v1/search", 
    json={
        "query": "AI trends",
        "sources": ["reddit", "twitter"]
    }
)
print(response.json())
```