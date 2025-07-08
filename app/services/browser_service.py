"""
헤드리스 브라우저 기반 동적 웹 크롤링 서비스
JavaScript 렌더링이 필요한 사이트 크롤링
"""
import asyncio
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Browser, Page
import logging
from fake_useragent import UserAgent
import random
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class BrowserService:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright = None
        self.ua = UserAgent()
        
    async def start(self):
        """브라우저 시작"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-gpu',
                    '--window-size=1920,1080',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            logger.info("Headless browser started")
    
    async def stop(self):
        """브라우저 종료"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Headless browser stopped")
    
    async def create_stealth_page(self) -> Page:
        """탐지 방지 설정이 적용된 페이지 생성"""
        if not self.browser:
            await self.start()
        
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=self.ua.random,
            java_script_enabled=True,
            ignore_https_errors=True,
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        # 자동화 탐지 우회
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            window.chrome = {
                runtime: {}
            };
            
            Object.defineProperty(navigator, 'permissions', {
                get: () => ({
                    query: () => Promise.resolve({ state: 'granted' })
                })
            });
        """)
        
        page = await context.new_page()
        
        # 추가 헤더 설정
        await page.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        return page
    
    async def scroll_and_wait(self, page: Page, max_scrolls: int = 5):
        """페이지 스크롤하며 동적 콘텐츠 로드"""
        for i in range(max_scrolls):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(random.uniform(1, 2))
            
            # 새로운 콘텐츠가 로드되었는지 확인
            new_height = await page.evaluate('document.body.scrollHeight')
            if i > 0 and new_height == await page.evaluate('document.body.scrollHeight'):
                break
    
    async def extract_dynamic_content(self, url: str, selectors: Dict[str, str]) -> Dict:
        """동적 콘텐츠 추출"""
        page = await self.create_stealth_page()
        
        try:
            # 페이지 로드
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(random.uniform(2, 4))
            
            # 스크롤하여 모든 콘텐츠 로드
            await self.scroll_and_wait(page)
            
            # 셀렉터를 사용하여 데이터 추출
            data = {}
            for key, selector in selectors.items():
                try:
                    elements = await page.query_selector_all(selector)
                    data[key] = []
                    for element in elements:
                        text = await element.text_content()
                        if text:
                            data[key].append(text.strip())
                except Exception as e:
                    logger.error(f"Error extracting {key}: {e}")
                    data[key] = []
            
            # 스크린샷 (디버깅용)
            # await page.screenshot(path=f'debug_{datetime.now().timestamp()}.png')
            
            return data
            
        except Exception as e:
            logger.error(f"Error extracting dynamic content from {url}: {e}")
            return {}
        finally:
            await page.close()
    
    async def handle_infinite_scroll(self, url: str, item_selector: str, max_items: int = 50) -> List[Dict]:
        """무한 스크롤 페이지 처리"""
        page = await self.create_stealth_page()
        items = []
        
        try:
            await page.goto(url, wait_until='networkidle')
            await asyncio.sleep(2)
            
            previous_count = 0
            scroll_attempts = 0
            max_scroll_attempts = 20
            
            while len(items) < max_items and scroll_attempts < max_scroll_attempts:
                # 현재 아이템들 수집
                elements = await page.query_selector_all(item_selector)
                
                for element in elements[previous_count:]:
                    try:
                        # 각 아이템에서 필요한 정보 추출
                        item_data = await self._extract_item_data(element)
                        if item_data:
                            items.append(item_data)
                    except Exception as e:
                        logger.error(f"Error extracting item: {e}")
                
                previous_count = len(elements)
                
                # 스크롤
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(random.uniform(1, 3))
                
                # 로딩 대기
                try:
                    await page.wait_for_selector(f'{item_selector}:nth-child({previous_count + 1})', timeout=5000)
                except:
                    scroll_attempts += 1
                
                if len(items) >= max_items:
                    break
            
            return items[:max_items]
            
        except Exception as e:
            logger.error(f"Error handling infinite scroll: {e}")
            return items
        finally:
            await page.close()
    
    async def _extract_item_data(self, element) -> Optional[Dict]:
        """개별 아이템에서 데이터 추출"""
        try:
            data = {}
            
            # 텍스트 콘텐츠
            text = await element.text_content()
            if text:
                data['text'] = text.strip()
            
            # 링크 추출
            links = await element.query_selector_all('a')
            if links:
                data['links'] = []
                for link in links[:3]:  # 최대 3개 링크
                    href = await link.get_attribute('href')
                    if href:
                        data['links'].append(href)
            
            # 이미지 추출
            images = await element.query_selector_all('img')
            if images:
                data['images'] = []
                for img in images[:2]:  # 최대 2개 이미지
                    src = await img.get_attribute('src')
                    if src:
                        data['images'].append(src)
            
            # 시간 정보 추출 (time, datetime 태그)
            time_element = await element.query_selector('time, [datetime]')
            if time_element:
                datetime_attr = await time_element.get_attribute('datetime')
                if datetime_attr:
                    data['timestamp'] = datetime_attr
            
            return data if data else None
            
        except Exception as e:
            logger.error(f"Error extracting item data: {e}")
            return None
    
    async def bypass_cloudflare(self, url: str) -> Optional[str]:
        """Cloudflare 보호 우회"""
        page = await self.create_stealth_page()
        
        try:
            await page.goto(url)
            
            # Cloudflare 챌린지 대기
            for _ in range(30):  # 최대 30초 대기
                await asyncio.sleep(1)
                
                # 타이틀 확인
                title = await page.title()
                if "Just a moment" not in title and "Checking your browser" not in title:
                    break
                
                # Cloudflare 체크박스 클릭 시도
                try:
                    checkbox = await page.query_selector('input[type="checkbox"]')
                    if checkbox:
                        await checkbox.click()
                except:
                    pass
            
            # 페이지 콘텐츠 반환
            content = await page.content()
            return content
            
        except Exception as e:
            logger.error(f"Error bypassing Cloudflare: {e}")
            return None
        finally:
            await page.close()
    
    async def execute_custom_script(self, url: str, script: str) -> any:
        """커스텀 JavaScript 실행"""
        page = await self.create_stealth_page()
        
        try:
            await page.goto(url, wait_until='networkidle')
            await asyncio.sleep(2)
            
            # 커스텀 스크립트 실행
            result = await page.evaluate(script)
            return result
            
        except Exception as e:
            logger.error(f"Error executing custom script: {e}")
            return None
        finally:
            await page.close()