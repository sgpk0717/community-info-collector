-- 보고서 테이블 생성 (RLS 없이 테스트용)
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_nickname VARCHAR(100) NOT NULL,
    query_text TEXT NOT NULL,
    full_report TEXT NOT NULL,
    summary TEXT,
    posts_collected INTEGER DEFAULT 0,
    report_length VARCHAR(20) DEFAULT 'moderate',
    session_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성 (성능 향상)
CREATE INDEX IF NOT EXISTS idx_reports_user_nickname ON reports(user_nickname);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_user_created ON reports(user_nickname, created_at DESC);

-- 업데이트 시각 자동 갱신을 위한 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 생성
DROP TRIGGER IF EXISTS update_reports_updated_at ON reports;
CREATE TRIGGER update_reports_updated_at 
    BEFORE UPDATE ON reports 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at_column();