# Supabase 설정 가이드

## 1. Supabase 프로젝트 생성

1. [Supabase](https://supabase.com)에 로그인
2. "New Project" 클릭
3. 프로젝트 이름: `community-info-collector`
4. 데이터베이스 패스워드 설정
5. 지역 선택 (Asia Pacific - Seoul 권장)
6. 프로젝트 생성

## 2. 데이터베이스 테이블 생성

1. Supabase 대시보드에서 "SQL Editor" 클릭
2. `supabase-schema.sql` 파일의 내용을 복사하여 붙여넣기
3. "RUN" 버튼 클릭하여 테이블 생성

## 3. 환경 변수 설정

1. Supabase 대시보드 → Settings → API
2. 다음 값들을 복사:
   - `Project URL`
   - `anon public` key

3. `.env` 파일 업데이트:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
```

## 4. 테이블 구조

```sql
users (
  id UUID PRIMARY KEY,
  nickname VARCHAR(20) UNIQUE NOT NULL,
  approval_status CHAR(1) DEFAULT 'N',
  created_at TIMESTAMP DEFAULT NOW(),
  last_access TIMESTAMP DEFAULT NOW()
)
```

## 5. 사용자 관리

### 신규 사용자 승인
```sql
UPDATE users SET approval_status = 'Y' WHERE nickname = '사용자닉네임';
```

### 대기 중인 사용자 조회
```sql
SELECT * FROM users WHERE approval_status = 'N' ORDER BY created_at DESC;
```

### 모든 사용자 조회
```sql
SELECT * FROM users ORDER BY created_at DESC;
```

## 6. 앱 실행

환경 변수 설정 후 앱 재시작:
```bash
expo start
```

## 주의사항

- `.env` 파일은 `.gitignore`에 포함되어 있어 Git에 커밋되지 않습니다
- 프로덕션 환경에서는 적절한 Row Level Security 정책을 설정하세요
- API 키는 안전하게 관리하세요