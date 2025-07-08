# 데이터베이스 설정 가이드

## 빠른 설정 (Windows)

1. **setup-db.bat 실행**
   ```cmd
   setup-db.bat
   ```
   이 스크립트가 자동으로:
   - Docker로 PostgreSQL 시작
   - 데이터베이스 생성
   - 테이블 생성

## DBeaver 연결 방법

### 1. DBeaver 다운로드
https://dbeaver.io/download/ 에서 다운로드 및 설치

### 2. 새 연결 생성
1. DBeaver 실행
2. "새 데이터베이스 연결" 클릭 (또는 Ctrl+N)
3. PostgreSQL 선택

### 3. 연결 정보 입력
- **Host**: localhost
- **Port**: 5432
- **Database**: community_collector
- **Username**: postgres
- **Password**: password

### 4. 연결 테스트
"Test Connection" 버튼 클릭하여 연결 확인

## 데이터베이스 구조

### 테이블 설명

1. **search_queries** - 검색 이력
   - id: 고유 ID
   - query_text: 검색어
   - created_at: 검색 시간

2. **collected_posts** - 수집된 게시물
   - id: 고유 ID
   - source: 출처 (reddit/twitter/threads)
   - post_id: 원본 게시물 ID
   - author: 작성자
   - title: 제목
   - content: 내용
   - url: 링크
   - search_query_id: 검색 쿼리 참조

3. **reports** - 분석 보고서
   - id: 고유 ID
   - search_query_id: 검색 쿼리 참조
   - summary: 요약
   - full_report: 전체 보고서
   - created_at: 생성 시간

## 테스트 및 확인

### 1. 연결 테스트
```cmd
python test-db-connection.py
```

### 2. 샘플 데이터 생성
```cmd
python create-sample-data.py
```

### 3. DBeaver에서 데이터 확인
1. 왼쪽 트리에서 community_collector > Schemas > public > Tables 확장
2. 각 테이블 우클릭 > "View Data" 선택

## 문제 해결

### Docker가 설치되지 않은 경우
1. https://www.docker.com/products/docker-desktop/ 에서 Docker Desktop 설치
2. Docker Desktop 실행
3. setup-db.bat 다시 실행

### 포트 5432가 이미 사용 중인 경우
1. 기존 PostgreSQL 서비스 중지
2. 또는 docker-compose.yml에서 포트 변경:
   ```yaml
   ports:
     - "5433:5432"  # 5433으로 변경
   ```
3. .env 파일도 함께 수정:
   ```
   DATABASE_URL=postgresql://postgres:password@localhost:5433/community_collector
   ```

### 테이블이 생성되지 않은 경우
```cmd
venv\Scripts\activate
alembic revision --autogenerate -m "Create tables"
alembic upgrade head
```