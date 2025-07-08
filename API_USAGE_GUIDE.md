# API 사용 가이드

## 주요 엔드포인트

### 1. 정보 검색 및 분석
```http
POST /api/v1/search
```

**요청 본문:**
```json
{
  "query": "AI trends 2024",
  "sources": ["reddit", "twitter", "threads"]
}
```

**응답:**
```json
{
  "query_id": 1,
  "query_text": "AI trends 2024",
  "posts_collected": 45,
  "report": {
    "id": 1,
    "summary": "AI 트렌드 요약...",
    "full_report": "전체 분석 보고서...",
    "created_at": "2024-01-01T12:00:00"
  }
}
```

### 2. 트렌딩 토픽 조회
```http
GET /api/v1/trending
```

**응답:**
```json
{
  "reddit": [
    {
      "subreddit": "technology",
      "title": "Breaking: New AI Model...",
      "score": 5432,
      "comments": 234
    }
  ],
  "twitter": [
    {
      "name": "#AITrends",
      "tweet_volume": 12345
    }
  ],
  "threads": [
    {
      "name": "#programming",
      "mentions": 45
    }
  ]
}
```

### 3. 수집된 게시물 조회
```http
GET /api/v1/posts/{query_id}?source=reddit&limit=10
```

### 4. 분석 보고서 조회
```http
GET /api/v1/report/{query_id}
```

### 5. 검색 이력 조회
```http
GET /api/v1/search/history?limit=10
```

### 6. 시스템 통계
```http
GET /api/v1/stats
```

## 각 커뮤니티별 특징

### Reddit
- **장점**: 
  - 깊이 있는 토론
  - 전문 서브레딧별 검색 가능
  - 높은 품질의 기술 콘텐츠
- **제한사항**:
  - API 요청 제한 (분당 60회)
  - 인증 필요

### X (Twitter)
- **장점**:
  - 실시간 트렌드
  - 빠른 정보 전파
  - 영향력 있는 사용자들의 의견
- **제한사항**:
  - 무료 티어는 월 500개 트윗 검색
  - 최근 7일간의 트윗만 검색 가능

### Threads
- **장점**:
  - Meta 생태계 연동
  - 빠르게 성장하는 플랫폼
- **제한사항**:
  - 공식 API 없음 (웹 스크래핑 사용)
  - 검색 기능 제한적

## 사용 예시

### Python으로 API 호출
```python
import requests

# 1. 검색 실행
response = requests.post(
    "http://localhost:8000/api/v1/search",
    json={
        "query": "FastAPI best practices",
        "sources": ["reddit", "twitter"]
    }
)
result = response.json()
query_id = result["query_id"]

# 2. 보고서 확인
report = requests.get(
    f"http://localhost:8000/api/v1/report/{query_id}"
).json()

print(report["full_report"])

# 3. 원본 게시물 확인
posts = requests.get(
    f"http://localhost:8000/api/v1/posts/{query_id}?source=reddit"
).json()

for post in posts[:5]:
    print(f"- {post['title']}")
    print(f"  by {post['author']}")
    print(f"  {post['url']}\n")
```

### cURL 예시
```bash
# 검색 실행
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Python tips", "sources": ["reddit", "twitter"]}'

# 트렌딩 조회
curl http://localhost:8000/api/v1/trending

# 통계 조회
curl http://localhost:8000/api/v1/stats
```

## 팁과 모범 사례

1. **검색 쿼리 최적화**
   - Reddit: 서브레딧명 포함 (예: "python subreddit:learnpython")
   - Twitter: 해시태그 사용 (예: "#Python #Programming")
   - Threads: 해시태그 필수 (예: "#PythonProgramming")

2. **API 제한 관리**
   - 각 플랫폼의 rate limit 고려
   - 필요한 플랫폼만 선택적으로 검색
   - 캐싱 활용 (동일 검색 반복 피하기)

3. **보고서 활용**
   - LLM이 생성한 보고서는 한국어로 제공
   - 요약과 전체 보고서 구분하여 사용
   - 원본 게시물 링크 확인 가능

## 문제 해결

### API 키 없을 때
- Reddit/Twitter는 API 키 없이 작동 안 함
- Threads는 웹 스크래핑이므로 키 불필요
- LLM 보고서는 OpenAI 키 필요

### 검색 결과가 없을 때
1. 검색어 확인 (오타, 특수문자)
2. 다른 플랫폼 시도
3. 시간대 변경하여 재검색
4. 더 일반적인 키워드 사용