-- Community Info Collector Users Table
-- Supabase 대시보드에서 SQL Editor에 붙여넣기하여 실행하세요

CREATE TABLE users (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  nickname VARCHAR(20) NOT NULL UNIQUE,
  approval_status CHAR(1) NOT NULL DEFAULT 'N' CHECK (approval_status IN ('Y', 'N')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_access TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_users_nickname ON users(nickname);
CREATE INDEX idx_users_approval_status ON users(approval_status);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Row Level Security (RLS) 활성화
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- 정책 생성 (모든 사용자가 읽기 가능, 쓰기 가능)
CREATE POLICY "Users can read all users" ON users FOR SELECT USING (true);
CREATE POLICY "Users can insert new users" ON users FOR INSERT WITH CHECK (true);
CREATE POLICY "Users can update their own record" ON users FOR UPDATE USING (true);

-- 닉네임 유효성 검사 함수
CREATE OR REPLACE FUNCTION validate_nickname()
RETURNS TRIGGER AS $$
BEGIN
  -- 닉네임 길이 체크 (2-20자)
  IF LENGTH(NEW.nickname) < 2 OR LENGTH(NEW.nickname) > 20 THEN
    RAISE EXCEPTION '닉네임은 2자 이상 20자 이하여야 합니다.';
  END IF;
  
  -- 닉네임 공백 체크
  IF TRIM(NEW.nickname) = '' THEN
    RAISE EXCEPTION '닉네임에 공백만 있을 수 없습니다.';
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 생성
CREATE TRIGGER validate_nickname_trigger
  BEFORE INSERT OR UPDATE ON users
  FOR EACH ROW
  EXECUTE FUNCTION validate_nickname();

-- 댓글: 테이블 생성 후 아래 데이터를 Supabase 대시보드에서 확인하세요
-- SELECT * FROM users;
-- 
-- 사용자 승인 예시:
-- UPDATE users SET approval_status = 'Y' WHERE nickname = '사용자닉네임';
-- 
-- 대기 중인 사용자 조회:
-- SELECT * FROM users WHERE approval_status = 'N' ORDER BY created_at DESC;