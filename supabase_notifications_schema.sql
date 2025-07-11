-- Supabase notifications 테이블 스키마
-- 알림 기능을 위한 테이블

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_nickname TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,  -- 'message' 컬럼이 필요함
    type TEXT NOT NULL CHECK (type IN ('report_completed', 'report_failed', 'schedule_reminder', 'system')),
    is_read BOOLEAN DEFAULT false,
    data JSONB,  -- 추가 데이터 (schedule_id, report_id 등)
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 외래키
    CONSTRAINT fk_user_nickname FOREIGN KEY (user_nickname) 
        REFERENCES users(nickname) ON DELETE CASCADE
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_notifications_user_nickname ON notifications(user_nickname);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_sent_at ON notifications(sent_at DESC);

-- RLS 정책
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- 사용자는 자신의 알림만 볼 수 있음
CREATE POLICY "Users can view own notifications" ON notifications
    FOR SELECT USING (auth.jwt() ->> 'nickname' = user_nickname);

-- 시스템은 모든 알림을 생성할 수 있음 (service role)
CREATE POLICY "Service role can create notifications" ON notifications
    FOR INSERT WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

-- 사용자는 자신의 알림만 업데이트할 수 있음 (읽음 표시)
CREATE POLICY "Users can update own notifications" ON notifications
    FOR UPDATE USING (auth.jwt() ->> 'nickname' = user_nickname);