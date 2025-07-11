-- Supabase schedules 테이블에 is_executing 컬럼 추가
-- 이 스크립트는 중복 보고서 생성 문제를 해결하기 위해 데이터베이스 레벨의 락 관리를 위한 컬럼을 추가합니다.

-- 1. is_executing 컬럼 추가 (기본값 false)
ALTER TABLE schedules 
ADD COLUMN IF NOT EXISTS is_executing BOOLEAN DEFAULT false;

-- 2. 인덱스 생성 (빠른 조회를 위해)
CREATE INDEX IF NOT EXISTS idx_schedules_is_executing 
ON schedules(is_executing);

-- 3. 기존 데이터 업데이트 (혹시 NULL인 경우 대비)
UPDATE schedules 
SET is_executing = false 
WHERE is_executing IS NULL;

-- 4. 컬럼 제약 조건 추가 (NOT NULL)
ALTER TABLE schedules 
ALTER COLUMN is_executing SET NOT NULL;

-- 5. 코멘트 추가
COMMENT ON COLUMN schedules.is_executing IS '스케줄이 현재 실행 중인지 여부를 나타내는 플래그. 중복 실행 방지를 위해 사용됨.';

-- 6. 서버 재시작 시 모든 플래그 초기화를 위한 함수 생성
CREATE OR REPLACE FUNCTION reset_all_executing_flags()
RETURNS void AS $$
BEGIN
    UPDATE schedules SET is_executing = false WHERE is_executing = true;
END;
$$ LANGUAGE plpgsql;

-- 7. 사용 예시 코멘트
-- SELECT reset_all_executing_flags(); -- 서버 시작 시 실행