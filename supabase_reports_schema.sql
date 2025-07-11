-- 보고서 테이블 생성
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

-- RLS (Row Level Security) 활성화
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- 정책 생성 (사용자는 자신의 보고서만 조회 가능)
CREATE POLICY "Users can view their own reports" ON reports
    FOR SELECT USING (user_nickname = current_user OR auth.role() = 'service_role');

-- 정책 생성 (서비스는 모든 보고서 삽입 가능)
CREATE POLICY "Service can insert reports" ON reports
    FOR INSERT WITH CHECK (auth.role() = 'service_role' OR true);

-- 업데이트 시각 자동 갱신을 위한 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 생성
CREATE TRIGGER update_reports_updated_at 
    BEFORE UPDATE ON reports 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at_column();

-- 예시 데이터 조회 쿼리
-- SELECT * FROM reports WHERE user_nickname = 'your_nickname' ORDER BY created_at DESC;