-- 스케줄링 시스템을 위한 테이블 생성 (기존 users 테이블 활용)
-- Supabase SQL Editor에서 실행하세요

-- 1. schedules 테이블 생성
CREATE TABLE IF NOT EXISTS schedules (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_nickname VARCHAR(100) NOT NULL,
    keyword VARCHAR(500) NOT NULL,
    interval_minutes INTEGER NOT NULL,
    report_length VARCHAR(50) NOT NULL DEFAULT 'moderate',
    total_reports INTEGER NOT NULL,
    completed_reports INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    next_run TIMESTAMP WITH TIME ZONE,
    last_run TIMESTAMP WITH TIME ZONE,
    notification_enabled BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. schedule_reports 테이블 생성 (스케줄로 생성된 보고서 추적)
CREATE TABLE IF NOT EXISTS schedule_reports (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    schedule_id UUID NOT NULL REFERENCES schedules(id),
    report_id UUID NOT NULL REFERENCES reports(id),
    execution_number INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. notifications 테이블 생성
CREATE TABLE IF NOT EXISTS notifications (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_nickname VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    data JSONB,
    is_read BOOLEAN DEFAULT false,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_schedules_user_nickname ON schedules(user_nickname);
CREATE INDEX IF NOT EXISTS idx_schedules_status ON schedules(status);
CREATE INDEX IF NOT EXISTS idx_schedules_next_run ON schedules(next_run);
CREATE INDEX IF NOT EXISTS idx_schedule_reports_schedule_id ON schedule_reports(schedule_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_nickname ON notifications(user_nickname);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);

-- RLS 정책 설정
ALTER TABLE schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE schedule_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- 기존 정책 제거 후 다시 생성
DROP POLICY IF EXISTS "Enable all for schedules" ON schedules;
DROP POLICY IF EXISTS "Enable all for schedule_reports" ON schedule_reports;
DROP POLICY IF EXISTS "Enable all for notifications" ON notifications;

-- 새로운 정책 생성
CREATE POLICY "Enable all for schedules" ON schedules FOR ALL USING (true);
CREATE POLICY "Enable all for schedule_reports" ON schedule_reports FOR ALL USING (true);
CREATE POLICY "Enable all for notifications" ON notifications FOR ALL USING (true);

-- 업데이트 시간 자동 업데이트 함수 (이미 존재하는 경우 무시)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 생성 (기존 트리거 제거 후 다시 생성)
DROP TRIGGER IF EXISTS update_schedules_updated_at ON schedules;
CREATE TRIGGER update_schedules_updated_at 
    BEFORE UPDATE ON schedules 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE '✅ 스케줄링 테이블이 성공적으로 생성되었습니다!';
    RAISE NOTICE '📊 생성된 테이블: schedules, schedule_reports, notifications';
END $$;