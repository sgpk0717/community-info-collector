# Community Info Collector

해외 커뮤니티(Reddit, X, Threads 등)에서 정보를 수집하고 분석하는 백엔드 API + React Native 앱

## 프로젝트 구성

- **백엔드 서버**: FastAPI 기반 REST API 서버
- **모바일 앱**: React Native 기반 iOS/Android 앱
- **스케줄링 시스템**: 주기적 자동 보고서 생성 및 푸시 알림

## 주요 기능

### 1. 커뮤니티 정보 수집
- Reddit, Twitter, Threads, LinkedIn, Discord, HackerNews 등 다양한 플랫폼 지원
- 키워드 기반 검색 및 수집
- GPT-4 기반 자동 분석 보고서 생성

### 2. 스케줄링 시스템
- 사용자가 설정한 키워드에 대해 주기적으로 보고서 자동 생성
- 보고서 길이 선택 가능 (간단/보통/상세)
- 총 보고 횟수 제한 설정
- 다중 스케줄 관리

### 3. 푸시 알림
- 새 보고서 생성 시 모바일 푸시 알림
- Firebase Cloud Messaging (FCM) 지원

### 4. 보고서 관리
- 생성된 보고서 히스토리 관리
- 보고서 조회, 복사, 공유 기능

## 워크플로우

1. **사용자가 앱에서 스케줄 설정**
   - 키워드 입력
   - 실행 주기 선택 (1시간, 6시간, 12시간, 24시간)
   - 보고서 길이 선택 (간단/보통/상세)
   - 총 보고 횟수 설정

2. **서버에서 주기적으로 보고서 생성**
   - 설정된 주기마다 커뮤니티에서 정보 수집
   - GPT-4를 사용하여 분석 보고서 작성
   - 데이터베이스에 보고서 저장

3. **푸시 알림 발송**
   - 보고서 생성 완료 시 사용자에게 푸시 알림
   - 알림을 통해 앱에서 바로 보고서 확인 가능

4. **보고서 확인 및 관리**
   - 앱에서 새 보고서 및 과거 보고서 조회
   - 보고서 복사, 공유 기능

5. **스케줄 관리**
   - 진행 중인 스케줄 일시정지/재개
   - 스케줄 취소
   - 다중 스케줄 동시 관리

## 설치 방법

### 백엔드 서버

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
# 필수: OPENAI_API_KEY, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET
# 선택: FCM_PROJECT_ID, FCM_CREDENTIALS_PATH (푸시 알림용)
```

4. 데이터베이스 설정
```bash
# PostgreSQL 사용 시
docker-compose up -d

# SQLite 사용 시 (개발용)
# config.py에서 DATABASE_URL을 sqlite로 변경

# 마이그레이션 실행
alembic upgrade head
```

5. 서버 실행
```bash
uvicorn app.main:app --reload
```

### React Native 앱

1. 의존성 설치
```bash
cd RedditAnalyzerApp
npm install
# iOS의 경우
cd ios && pod install
```

2. 환경 설정
```bash
# src/utils/constants.ts에서 API_BASE_URL 수정
export const API_BASE_URL = 'http://your-server-url:8000';
```

3. 앱 실행
```bash
# iOS
npm run ios

# Android
npm run android
```

## API 문서

서버 실행 후 http://localhost:8000/docs 에서 Swagger UI를 통해 API 테스트 가능

### 주요 엔드포인트

#### 검색 및 분석
- `POST /api/v1/search`: 키워드로 커뮤니티 검색 및 분석
- `GET /api/v1/posts/{query_id}`: 검색된 게시물 조회
- `GET /api/v1/report/{query_id}`: 분석 보고서 조회

#### 스케줄링
- `POST /api/v1/schedule/users`: 사용자 등록
- `POST /api/v1/schedule/schedules`: 새 스케줄 생성
- `GET /api/v1/schedule/schedules`: 사용자의 스케줄 목록 조회
- `PUT /api/v1/schedule/schedules/{id}`: 스케줄 수정
- `DELETE /api/v1/schedule/schedules/{id}`: 스케줄 취소
- `POST /api/v1/schedule/schedules/{id}/pause`: 스케줄 일시정지
- `POST /api/v1/schedule/schedules/{id}/resume`: 스케줄 재개

#### 알림
- `GET /api/v1/schedule/notifications`: 알림 목록 조회
- `PUT /api/v1/schedule/notifications/{id}/read`: 알림 읽음 처리

## 기술 스택

### 백엔드
- FastAPI
- SQLAlchemy
- PostgreSQL/SQLite
- APScheduler
- OpenAI GPT-4
- Praw (Reddit API)
- Tweepy (Twitter API)
- Playwright (동적 웹 스크래핑)

### 프론트엔드
- React Native
- TypeScript
- React Navigation
- Axios
- AsyncStorage

## 라이선스

MIT License