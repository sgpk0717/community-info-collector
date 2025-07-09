# 백엔드 Supabase 설정 가이드

## 1. Supabase 프로젝트 생성

1. [Supabase](https://supabase.com)에 로그인
2. "New Project" 클릭
3. 프로젝트 이름: `community-info-collector`
4. 데이터베이스 패스워드 설정
5. 지역 선택 (Asia Pacific - Seoul 권장)
6. 프로젝트 생성

## 2. 데이터베이스 테이블 생성

1. Supabase 대시보드에서 "SQL Editor" 클릭
2. `RedditAnalyzerApp/supabase-schema.sql` 파일의 내용을 복사하여 붙여넣기
3. "RUN" 버튼 클릭하여 테이블 생성

## 3. 백엔드 환경 변수 설정

1. Supabase 대시보드 → Settings → API
2. 다음 값들을 복사:
   - `Project URL`
   - `service_role` key (⚠️ **anon key가 아닌 service_role key 사용**)

3. `/community-info-collector/.env` 파일 업데이트:
```env
# Supabase
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here
```

## 4. 백엔드 의존성 설치

```bash
cd /Users/seonggukpark/community-info-collector
pip install -r requirements.txt
```

## 5. 백엔드 서버 실행

```bash
cd /Users/seonggukpark/community-info-collector
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 6. API 엔드포인트

### 사용자 등록
```
POST /api/v1/users/register
Content-Type: application/json

{
  "nickname": "사용자닉네임"
}
```

### 사용자 로그인
```
POST /api/v1/users/login
Content-Type: application/json

{
  "nickname": "사용자닉네임"
}
```

### 대기 중인 사용자 조회 (관리자용)
```
GET /api/v1/users/pending
```

### 사용자 승인 (관리자용)
```
POST /api/v1/users/approve/{user_id}
```

### 모든 사용자 조회 (관리자용)
```
GET /api/v1/users/all
```

## 7. 사용자 관리

### 신규 사용자 승인
```sql
UPDATE users SET approval_status = 'Y' WHERE nickname = '사용자닉네임';
```

### 대기 중인 사용자 조회
```sql
SELECT * FROM users WHERE approval_status = 'N' ORDER BY created_at DESC;
```

## 8. 아키텍처

```
모바일 앱 → 백엔드 API → Supabase
```

- 모바일 앱에서 백엔드 API 호출
- 백엔드에서 Supabase 데이터베이스 접근
- Service Role Key로 모든 권한 접근 (백엔드에서만)

## 주의사항

- **Service Role Key**를 사용하므로 절대 외부에 노출하지 마세요
- 백엔드 서버에서만 Supabase에 접근
- 모바일 앱에는 Supabase 키가 필요 없습니다
- API 응답에 민감한 정보 노출 금지