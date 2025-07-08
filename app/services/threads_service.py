import httpx
from typing import List, Dict, Optional
from app.schemas.schemas import PostBase
import logging
from bs4 import BeautifulSoup
import asyncio
import json
import re
from datetime import datetime
import urllib.parse

logger = logging.getLogger(__name__)

class ThreadsService:
    def __init__(self):
        self.base_url = "https://www.threads.net"
        self.api_base = "https://www.threads.net/api/graphql"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.session_headers = {
            'X-IG-App-ID': '238260118697367',  # Threads app ID
            'Content-Type': 'application/x-www-form-urlencoded',
        }
    
    async def search_posts(self, query: str, limit: int = 25) -> List[PostBase]:
        """
        Threads에서 게시물 검색 (웹 스크래핑)
        
        Note: Threads는 공식 API가 없어서 웹 스크래핑을 사용합니다.
        Instagram Graph API를 통한 접근도 제한적입니다.
        """
        posts = []
        
        try:
            # URL 인코딩
            encoded_query = urllib.parse.quote(query)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 1. 먼저 일반 웹 검색 시도
                posts_from_web = await self._search_web(client, query, limit)
                posts.extend(posts_from_web)
                
                # 2. 사용자 검색도 시도 (사용자명이 포함된 경우)
                if "@" in query:
                    username = query.split("@")[1].split()[0]
                    user_posts = await self._get_user_posts(client, username, limit=10)
                    posts.extend(user_posts)
                
                logger.info(f"Retrieved {len(posts)} posts from Threads for query: {query}")
                
        except httpx.TimeoutException:
            logger.error("Threads request timed out")
        except Exception as e:
            logger.error(f"Error searching Threads: {e}")
        
        return posts[:limit]  # 제한된 수만 반환
    
    async def _search_web(self, client: httpx.AsyncClient, query: str, limit: int) -> List[PostBase]:
        """웹 검색 페이지 스크래핑"""
        posts = []
        
        try:
            # Threads 검색 URL (해시태그 검색)
            if query.startswith("#"):
                tag = query[1:]
                url = f"{self.base_url}/t/{tag}"
            else:
                # 일반 검색은 제한적이므로 인기 게시물에서 관련 내용 찾기
                url = self.base_url
            
            response = await client.get(url, headers=self.headers, follow_redirects=True)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # JSON-LD 데이터 추출 시도
                scripts = soup.find_all('script', type='application/ld+json')
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, list):
                            for item in data:
                                if item.get('@type') == 'SocialMediaPosting':
                                    post = self._parse_json_ld_post(item)
                                    if post and query.lower() in post.content.lower():
                                        posts.append(post)
                    except:
                        continue
                
                # 메타 태그에서 정보 추출
                meta_posts = self._extract_from_meta_tags(soup, query)
                posts.extend(meta_posts)
                
            else:
                logger.warning(f"Threads web search returned status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error in Threads web search: {e}")
        
        return posts
    
    async def _get_user_posts(self, client: httpx.AsyncClient, username: str, limit: int = 10) -> List[PostBase]:
        """특정 사용자의 게시물 가져오기"""
        posts = []
        
        try:
            url = f"{self.base_url}/@{username}"
            response = await client.get(url, headers=self.headers, follow_redirects=True)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 사용자 프로필 페이지에서 게시물 추출
                # Threads는 동적 로딩을 사용하므로 초기 로드된 게시물만 가져올 수 있음
                post_containers = soup.find_all('div', {'role': 'article'})
                
                for container in post_containers[:limit]:
                    post = self._parse_post_container(container, username)
                    if post:
                        posts.append(post)
                        
            else:
                logger.warning(f"Failed to get user posts for @{username}")
                
        except Exception as e:
            logger.error(f"Error getting user posts: {e}")
        
        return posts
    
    def _parse_json_ld_post(self, data: dict) -> Optional[PostBase]:
        """JSON-LD 형식의 게시물 파싱"""
        try:
            author = data.get('author', {})
            author_name = author.get('name', 'Unknown')
            if isinstance(author, dict) and 'identifier' in author:
                author_name = f"@{author['identifier']['value']}"
            
            content = data.get('articleBody', '')
            url = data.get('url', '')
            
            if not content:
                return None
            
            # 날짜 정보 추가
            date_published = data.get('datePublished', '')
            if date_published:
                content += f"\n\n---\n📅 Posted: {date_published}"
            
            return PostBase(
                source="threads",
                post_id=url.split('/')[-1] if url else None,
                author=author_name,
                title=None,
                content=content[:1000],
                url=url
            )
        except Exception as e:
            logger.error(f"Error parsing JSON-LD post: {e}")
            return None
    
    def _parse_post_container(self, container, username: str) -> Optional[PostBase]:
        """HTML 컨테이너에서 게시물 파싱"""
        try:
            # 텍스트 내용 추출
            text_elements = container.find_all(['span', 'div'], string=True)
            content = ' '.join([elem.text.strip() for elem in text_elements if elem.text.strip()])
            
            if not content:
                return None
            
            # 링크 추출
            link = container.find('a', href=re.compile(r'/t/'))
            url = f"{self.base_url}{link['href']}" if link else None
            post_id = link['href'].split('/')[-1] if link else None
            
            return PostBase(
                source="threads",
                post_id=post_id,
                author=f"@{username}",
                title=None,
                content=content[:1000],
                url=url
            )
        except Exception as e:
            logger.error(f"Error parsing post container: {e}")
            return None
    
    def _extract_from_meta_tags(self, soup: BeautifulSoup, query: str) -> List[PostBase]:
        """메타 태그에서 관련 정보 추출"""
        posts = []
        
        try:
            # Open Graph 메타 태그 확인
            og_description = soup.find('meta', property='og:description')
            if og_description and og_description.get('content'):
                content = og_description['content']
                if query.lower() in content.lower():
                    # 간단한 메타 정보로 게시물 생성
                    posts.append(PostBase(
                        source="threads",
                        post_id=None,
                        author="Threads",
                        title=None,
                        content=content,
                        url=self.base_url
                    ))
        except Exception as e:
            logger.error(f"Error extracting from meta tags: {e}")
        
        return posts
    
    async def get_trending_topics(self) -> List[Dict]:
        """Threads 트렌딩 토픽 (제한적)"""
        trending = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.base_url, headers=self.headers)
                
                if response.status_code == 200:
                    # 현재 Threads는 공개적인 트렌딩 페이지가 없음
                    # 대신 인기 해시태그를 찾아볼 수 있음
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 해시태그 패턴 찾기
                    hashtags = re.findall(r'#\w+', response.text)
                    hashtag_counts = {}
                    
                    for tag in hashtags:
                        hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1
                    
                    # 상위 해시태그
                    for tag, count in sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                        trending.append({
                            'name': tag,
                            'url': f"{self.base_url}/t/{tag[1:]}",
                            'mentions': count
                        })
                        
        except Exception as e:
            logger.error(f"Error getting Threads trending topics: {e}")
        
        return trending