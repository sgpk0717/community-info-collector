-- Supabase reports 테이블에 posts_metadata 컬럼 추가
ALTER TABLE reports 
ADD COLUMN posts_metadata JSONB;

-- 인덱스 추가 (선택사항 - 성능 향상을 위해)
CREATE INDEX idx_reports_posts_metadata ON reports USING GIN (posts_metadata);