# Community Info Collector

해외 커뮤니티(Reddit, X, Threads)에서 정보를 수집하고 분석하는 백엔드 API

## 설치 방법

1. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 의존성 설치
```bash
pip install -r requirements.txt
```

3. 환경변수 설정
```bash
cp .env.example .env
# .env 파일을 열어 필요한 API 키들을 입력
```

4. 데이터베이스 마이그레이션
```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

5. 서버 실행
```bash
python run.py
```

## API 문서

서버 실행 후 http://localhost:8000/docs 에서 Swagger UI를 통해 API 테스트 가능

## 주요 엔드포인트

- `POST /api/v1/search`: 키워드로 커뮤니티 검색 및 분석
- `GET /api/v1/posts/{query_id}`: 검색된 게시물 조회
- `GET /api/v1/report/{query_id}`: 분석 보고서 조회