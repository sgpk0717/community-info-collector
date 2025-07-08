"""
LinkedIn 크롤링 서비스
프로필, 포스트, 채용 정보 수집
"""
from typing import List, Dict, Optional
from app.schemas.schemas import PostBase
from app.services.browser_service import BrowserService
import logging
import asyncio
import re
from datetime import datetime
from bs4 import BeautifulSoup
import cloudscraper

logger = logging.getLogger(__name__)

class LinkedInService:
    def __init__(self):
        self.browser_service = BrowserService()
        self.base_url = "https://www.linkedin.com"
        self.scraper = cloudscraper.create_scraper()
        
    async def search_posts(self, query: str, limit: int = 25) -> List[PostBase]:
        """
        LinkedIn 게시물 검색 (공개 콘텐츠만)
        Note: LinkedIn은 로그인이 필요하지만, 일부 공개 콘텐츠는 접근 가능
        """
        posts = []
        
        try:
            # 1. 공개 검색 페이지 시도
            search_url = f"{self.base_url}/search/results/content/?keywords={query}"
            
            # 브라우저 서비스 사용
            await self.browser_service.start()
            
            # 공개 프로필과 회사 페이지에서 정보 수집
            company_posts = await self._search_company_posts(query)
            posts.extend(company_posts)
            
            # 해시태그 검색
            hashtag_posts = await self._search_hashtag(query.replace(" ", ""))
            posts.extend(hashtag_posts)
            
            logger.info(f"Retrieved {len(posts)} posts from LinkedIn for query: {query}")
            
        except Exception as e:
            logger.error(f"Error searching LinkedIn: {e}")
        finally:
            await self.browser_service.stop()
        
        return posts[:limit]
    
    async def _search_company_posts(self, query: str) -> List[PostBase]:
        """회사 페이지에서 공개 게시물 검색"""
        posts = []
        
        try:
            # 회사 검색 URL
            company_search_url = f"{self.base_url}/search/results/companies/?keywords={query}"
            
            page = await self.browser_service.create_stealth_page()
            await page.goto(company_search_url, wait_until='domcontentloaded')
            await asyncio.sleep(3)
            
            # 회사 링크 추출
            company_links = await page.query_selector_all('a[href*="/company/"]')
            company_urls = []
            
            for link in company_links[:5]:  # 상위 5개 회사
                href = await link.get_attribute('href')
                if href and '/company/' in href:
                    company_urls.append(href)
            
            await page.close()
            
            # 각 회사 페이지에서 게시물 수집
            for company_url in company_urls:
                company_posts = await self._extract_company_posts(company_url)
                posts.extend(company_posts)
                
        except Exception as e:
            logger.error(f"Error searching company posts: {e}")
        
        return posts
    
    async def _extract_company_posts(self, company_url: str) -> List[PostBase]:
        """특정 회사 페이지에서 게시물 추출"""
        posts = []
        
        try:
            page = await self.browser_service.create_stealth_page()
            await page.goto(company_url, wait_until='domcontentloaded')
            await asyncio.sleep(2)
            
            # 회사명 추출
            company_name = await page.text_content('h1')
            if not company_name:
                company_name = "Unknown Company"
            
            # 게시물 컨테이너 찾기
            post_containers = await page.query_selector_all('[data-urn*="activity"], .feed-shared-update-v2')
            
            for container in post_containers[:10]:
                try:
                    # 텍스트 내용
                    text_element = await container.query_selector('.feed-shared-text, .break-words')
                    content = ""
                    if text_element:
                        content = await text_element.text_content()
                    
                    if not content:
                        continue
                    
                    # 메타데이터
                    time_element = await container.query_selector('time')
                    timestamp = ""
                    if time_element:
                        timestamp = await time_element.get_attribute('datetime')
                    
                    # 상호작용 수
                    reactions = await container.query_selector('[data-test-social-counts]')
                    engagement = ""
                    if reactions:
                        engagement = await reactions.text_content()
                    
                    post = PostBase(
                        source=f"linkedin/{company_name.lower().replace(' ', '_')}",
                        post_id=None,
                        author=company_name,
                        title=None,
                        content=f"{content.strip()}\n\n---\n💼 Company: {company_name}\n{engagement}",
                        url=company_url
                    )
                    posts.append(post)
                    
                except Exception as e:
                    logger.error(f"Error extracting post: {e}")
            
            await page.close()
            
        except Exception as e:
            logger.error(f"Error extracting company posts: {e}")
        
        return posts
    
    async def _search_hashtag(self, hashtag: str) -> List[PostBase]:
        """해시태그로 검색"""
        posts = []
        
        try:
            # 해시태그 URL
            hashtag_url = f"{self.base_url}/feed/hashtag/{hashtag.lower()}/"
            
            page = await self.browser_service.create_stealth_page()
            await page.goto(hashtag_url, wait_until='domcontentloaded')
            await asyncio.sleep(2)
            
            # 간단한 정보 추출
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # 메타 태그에서 정보 추출
            description_meta = soup.find('meta', {'property': 'og:description'})
            if description_meta:
                post = PostBase(
                    source=f"linkedin/#{hashtag}",
                    post_id=None,
                    author="LinkedIn Hashtag",
                    title=f"#{hashtag}",
                    content=description_meta.get('content', ''),
                    url=hashtag_url
                )
                posts.append(post)
            
            await page.close()
            
        except Exception as e:
            logger.error(f"Error searching hashtag: {e}")
        
        return posts
    
    async def get_job_postings(self, query: str, location: str = "") -> List[Dict]:
        """채용 공고 검색"""
        jobs = []
        
        try:
            # 채용 검색 URL
            jobs_url = f"{self.base_url}/jobs/search/?keywords={query}"
            if location:
                jobs_url += f"&location={location}"
            
            page = await self.browser_service.create_stealth_page()
            await page.goto(jobs_url, wait_until='domcontentloaded')
            await asyncio.sleep(3)
            
            # 채용 공고 카드 추출
            job_cards = await page.query_selector_all('.job-card-container, [data-job-id]')
            
            for card in job_cards[:20]:
                try:
                    job = {}
                    
                    # 직무명
                    title_elem = await card.query_selector('h3, .job-card-list__title')
                    if title_elem:
                        job['title'] = await title_elem.text_content()
                    
                    # 회사명
                    company_elem = await card.query_selector('h4, .job-card-container__company-name')
                    if company_elem:
                        job['company'] = await company_elem.text_content()
                    
                    # 위치
                    location_elem = await card.query_selector('.job-card-container__metadata-item')
                    if location_elem:
                        job['location'] = await location_elem.text_content()
                    
                    # 링크
                    link_elem = await card.query_selector('a')
                    if link_elem:
                        href = await link_elem.get_attribute('href')
                        job['url'] = f"{self.base_url}{href}" if href.startswith('/') else href
                    
                    if job.get('title') and job.get('company'):
                        jobs.append(job)
                        
                except Exception as e:
                    logger.error(f"Error extracting job: {e}")
            
            await page.close()
            
        except Exception as e:
            logger.error(f"Error getting job postings: {e}")
        
        return jobs
    
    async def extract_profile_info(self, profile_url: str) -> Optional[Dict]:
        """공개 프로필 정보 추출"""
        try:
            page = await self.browser_service.create_stealth_page()
            await page.goto(profile_url, wait_until='domcontentloaded')
            await asyncio.sleep(2)
            
            profile = {}
            
            # 이름
            name_elem = await page.query_selector('h1')
            if name_elem:
                profile['name'] = await name_elem.text_content()
            
            # 헤드라인
            headline_elem = await page.query_selector('.text-body-medium')
            if headline_elem:
                profile['headline'] = await headline_elem.text_content()
            
            # 위치
            location_elem = await page.query_selector('.text-body-small.inline')
            if location_elem:
                profile['location'] = await location_elem.text_content()
            
            # 소개
            about_elem = await page.query_selector('#about ~ div .inline-show-more-text')
            if about_elem:
                profile['about'] = await about_elem.text_content()
            
            await page.close()
            return profile
            
        except Exception as e:
            logger.error(f"Error extracting profile: {e}")
            return None