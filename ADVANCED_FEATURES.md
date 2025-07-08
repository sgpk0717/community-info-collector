# 고급 크롤링 기능 가이드

## 🚀 새로운 기능 (v2.0)

### 1. 헤드리스 브라우저 크롤링
```http
POST /api/v1/advanced/dynamic-search
```

**동적 웹페이지 크롤링:**
```json
{
  "url": "https://example.com",
  "selectors": {
    "title": "h1.main-title",
    "content": ".article-body",
    "author": ".author-name"
  },
  "scroll": true
}
```

### 2. JavaScript 실행
```http
POST /api/v1/advanced/execute-script
```

**커스텀 JavaScript 실행:**
```json
{
  "url": "https://example.com",
  "script": "return document.querySelectorAll('a').length;",
  "wait_time": 3
}
```

### 3. LinkedIn 크롤링
```http
POST /api/v1/advanced/linkedin-search?search_type=posts
```

**검색 유형:**
- `posts`: 공개 게시물
- `jobs`: 채용 공고
- `profiles`: 공개 프로필

### 4. Discord 통합
```http
POST /api/v1/advanced/discord-webhook
```

**웹훅 설정:**
```json
{
  "webhook_url": "https://discord.com/api/webhooks/..."
}
```

### 5. Hacker News
```http
GET /api/v1/advanced/hackernews/top?story_type=top&limit=30
```

**스토리 유형:**
- `top`: 인기 글
- `new`: 최신 글
- `best`: 베스트
- `ask`: Ask HN
- `show`: Show HN
- `job`: 채용

### 6. 멀티소스 크롤링
```http
POST /api/v1/advanced/multi-source-crawl
```

**여러 소스 동시 검색:**
```json
{
  "query": "AI trends",
  "sources": ["hackernews", "linkedin", "discord"]
}
```

### 7. Cloudflare 우회
```http
POST /api/v1/advanced/cloudflare-bypass
```

**보호된 사이트 접근:**
```json
{
  "url": "https://protected-site.com"
}
```

## 🛠️ 기술적 특징

### BrowserService
- **Playwright** 기반 헤드리스 브라우저
- 자동화 탐지 우회 (webdriver 숨김)
- 랜덤 User-Agent
- 무한 스크롤 처리
- 스크린샷 캡처
- 커스텀 JavaScript 실행

### 크롤링 전략
1. **정적 크롤링**: BeautifulSoup, httpx
2. **동적 크롤링**: Playwright, Selenium
3. **API 우선**: 공식 API가 있으면 우선 사용
4. **Rate Limiting**: 서버 부하 방지
5. **에러 핸들링**: 재시도 로직

## 📊 사용 예시

### Python 예시
```python
import requests

# 1. Hacker News 트렌드
hn_trends = requests.get(
    "http://localhost:8000/api/v1/advanced/hackernews/top?story_type=best"
).json()

# 2. LinkedIn 채용 정보
jobs = requests.post(
    "http://localhost:8000/api/v1/advanced/linkedin-search",
    params={"search_type": "jobs"},
    json={"query": "Python Developer"}
).json()

# 3. 동적 웹 크롤링
dynamic_data = requests.post(
    "http://localhost:8000/api/v1/advanced/dynamic-search",
    json={
        "url": "https://news.ycombinator.com",
        "selectors": {
            "stories": ".athing .titleline",
            "scores": ".score"
        }
    }
).json()
```

## ⚠️ 주의사항

1. **법적 준수**
   - robots.txt 확인
   - 서비스 약관 준수
   - 개인정보 보호

2. **Rate Limiting**
   - 과도한 요청 자제
   - 적절한 딜레이 설정
   - 캐싱 활용

3. **API 키 관리**
   - 환경 변수 사용
   - 키 노출 방지
   - 정기적 갱신

## 🔧 설정

### Playwright 설치
```bash
pip install playwright
playwright install chromium
```

### Discord 봇 설정
`.env` 파일에 추가:
```
DISCORD_BOT_TOKEN=your_bot_token
```

### 프록시 설정 (선택사항)
```python
browser = await playwright.chromium.launch(
    proxy={
        "server": "http://proxy.example.com:8080",
        "username": "user",
        "password": "pass"
    }
)
```

## 📈 성능 최적화

1. **병렬 처리**: asyncio 활용
2. **캐싱**: Redis 연동 가능
3. **선택적 로딩**: 필요한 리소스만 로드
4. **압축**: gzip 응답 지원

## 🐛 디버깅

### 로그 확인
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 스크린샷 디버깅
```python
await page.screenshot(path="debug.png", full_page=True)
```

### 네트워크 모니터링
```python
await page.route("**/*", lambda route: print(route.request.url))
```