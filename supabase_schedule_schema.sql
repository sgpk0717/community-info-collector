-- =====================================================
-- 스케줄링 시스템을 위한 테이블 생성 스크립트
-- Supabase PostgreSQL용
-- =====================================================

-- 1. Users 테이블 (기존 Supabase users 테이블과 별도)
CREATE TABLE IF NOT EXISTS app_users (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(200) UNIQUE NOT NULL,
    name VARCHAR(200),
    push_token VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. Search Queries 테이블
CREATE TABLE IF NOT EXISTS search_queries (
    id SERIAL PRIMARY KEY,
    query_text VARCHAR(500) NOT NULL,
    user_id INTEGER REFERENCES app_users(id),
    schedule_id INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Schedules 테이블
CREATE TABLE IF NOT EXISTS schedules (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES app_users(id),
    keyword VARCHAR(500) NOT NULL,
    interval_minutes INTEGER NOT NULL,
    report_length VARCHAR(50) NOT NULL,
    total_reports INTEGER NOT NULL,
    completed_reports INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    next_run TIMESTAMP,
    last_run TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 4. Collected Posts 테이블
CREATE TABLE IF NOT EXISTS collected_posts (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    post_id VARCHAR(200),
    author VARCHAR(200),
    title TEXT,
    content TEXT,
    url TEXT,
    score INTEGER,
    comments INTEGER,
    created_utc INTEGER,
    subreddit VARCHAR(200),
    search_query_id INTEGER REFERENCES search_queries(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 5. Reports 테이블
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    search_query_id INTEGER REFERENCES search_queries(id),
    summary TEXT,
    full_report TEXT,
    schedule_id INTEGER REFERENCES schedules(id),
    user_id VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6. Notifications 테이블
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES app_users(id),
    title VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    data JSONB,
    is_read BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_search_queries_user_id ON search_queries(user_id);
CREATE INDEX IF NOT EXISTS idx_search_queries_schedule_id ON search_queries(schedule_id);
CREATE INDEX IF NOT EXISTS idx_schedules_user_id ON schedules(user_id);
CREATE INDEX IF NOT EXISTS idx_schedules_status ON schedules(status);
CREATE INDEX IF NOT EXISTS idx_schedules_next_run ON schedules(next_run);
CREATE INDEX IF NOT EXISTS idx_collected_posts_search_query_id ON collected_posts(search_query_id);
CREATE INDEX IF NOT EXISTS idx_reports_schedule_id ON reports(schedule_id);
CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);

-- 외래키 제약조건 추가
ALTER TABLE search_queries 
ADD CONSTRAINT fk_search_queries_schedule_id 
FOREIGN KEY (schedule_id) REFERENCES schedules(id);

-- RLS (Row Level Security) 정책 설정 (선택사항)
ALTER TABLE app_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_queries ENABLE ROW LEVEL SECURITY;
ALTER TABLE collected_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- 기본 정책: 모든 사용자가 접근 가능 (나중에 세분화 가능)
CREATE POLICY "Enable all for app_users" ON app_users FOR ALL USING (true);
CREATE POLICY "Enable all for schedules" ON schedules FOR ALL USING (true);
CREATE POLICY "Enable all for search_queries" ON search_queries FOR ALL USING (true);
CREATE POLICY "Enable all for collected_posts" ON collected_posts FOR ALL USING (true);
CREATE POLICY "Enable all for reports" ON reports FOR ALL USING (true);
CREATE POLICY "Enable all for notifications" ON notifications FOR ALL USING (true);

-- 업데이트 시간 자동 업데이트 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 업데이트 트리거 생성
CREATE TRIGGER update_app_users_updated_at 
    BEFORE UPDATE ON app_users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_schedules_updated_at 
    BEFORE UPDATE ON schedules 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 샘플 데이터 삽입 (테스트용)
INSERT INTO app_users (device_id, name) VALUES 
    ('Rex', 'Rex'),
    ('testuser', 'Test User')
ON CONFLICT (device_id) DO NOTHING;

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE '✅ 스케줄링 시스템 테이블이 성공적으로 생성되었습니다!';
    RAISE NOTICE '📊 생성된 테이블: app_users, schedules, search_queries, collected_posts, reports, notifications';
    RAISE NOTICE '🔧 인덱스 및 외래키 제약조건도 설정되었습니다.';
END $$;