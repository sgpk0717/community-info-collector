# 📊 Reddit 검색 결과 및 분석 보고서

이 디렉토리는 Reddit API를 통해 수집한 데이터와 분석 보고서를 체계적으로 관리합니다.

## 📁 디렉토리 구조

### 🗂️ raw_data/
원본 JSON 형식의 Reddit 검색 결과
- `reddit_search_*.json`: 각 검색어별 원본 데이터
- `tesla_korean_search_*.json`: 한국 관련 Tesla 검색 결과
- 게시물의 모든 메타데이터 포함 (제목, 점수, 댓글, 작성자 등)

### 📄 html_reports/
데이터 시각화 HTML 보고서
- `reddit_search_report_*.html`: 검색 결과를 보기 좋게 정리한 HTML
- 웹브라우저에서 바로 열어볼 수 있음
- 스타일이 적용되어 읽기 편함

### 📝 markdown_reports/
데이터 시각화 Markdown 보고서
- `reddit_search_report_*.md`: 검색 결과를 마크다운 형식으로 정리
- GitHub, VS Code 등에서 미리보기 가능
- 텍스트 기반으로 가볍고 편집 가능

### 🤖 ai_analysis/
GPT-4 AI 분석 보고서
- `reddit_ai_analysis_report_*`: 초기 AI 분석 버전
- `reddit_ai_final_report_*`: **최종 종합 분석 보고서**
  - Tesla 시장 동향 (한국 시장 포함)
  - AI 기술 트렌드
  - Python 커뮤니티 인사이트
  - 통합 시장 분석 및 제언

## 🔍 주요 분석 내용

1. **Tesla 동향**
   - Cybertruck 판매 부진
   - Model Y 한국 시장 호응
   - 커뮤니티 정서 분석

2. **AI 기술**
   - 최신 기술 돌파구
   - 실제 활용 사례
   - 미래 전망

3. **Python 프로그래밍**
   - 학습 리소스
   - 커뮤니티 트렌드

## 📅 생성일
2025년 7월 7일

## 🛠️ 사용 기술
- Reddit API (PRAW)
- OpenAI GPT-4
- Python 3.12