-- 보고서 링크 테이블 생성
CREATE TABLE report_links (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    footnote_number INTEGER NOT NULL,  -- 각주 번호 [1], [2] 등
    url TEXT NOT NULL,
    title TEXT,
    score INTEGER,
    comments INTEGER,
    created_utc FLOAT,
    subreddit TEXT,
    author TEXT,
    position_in_report INTEGER,  -- 보고서 내 위치 (정렬용)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_report_links_report_id ON report_links(report_id);
CREATE INDEX idx_report_links_footnote ON report_links(report_id, footnote_number);

-- reports 테이블에서 posts_metadata 컬럼 제거 (이미 추가했다면)
-- ALTER TABLE reports DROP COLUMN IF EXISTS posts_metadata;