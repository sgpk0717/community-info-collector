from typing import List, Optional
from app.core.config import settings
from app.schemas.schemas import PostBase
import logging
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import ssl
import httpx

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            # SSL 검증을 비활성화한 HTTP 클라이언트 생성
            http_client = httpx.Client(verify=False)
            self.openai_client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                http_client=http_client
            )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_report(self, query: str, posts: List[PostBase], report_length: str = "moderate") -> dict:
        if not self.openai_client:
            logger.warning("OpenAI client not initialized")
            return {
                "summary": "LLM 서비스가 설정되지 않았습니다.",
                "full_report": "API 키를 설정해주세요."
            }
        
        # 보고서 길이에 따른 설정
        report_configs = {
            "simple": {
                "max_tokens": 800,
                "format": """
주제별로 그룹핑하여 작성하세요:
- 2개 이상 게시물이 다루는 주제는 독립 섹션으로
- 인기도 순으로 배치
- 단발성 정보는 "기타 정보들"로
- 마지막에 "종합 요약" 추가
""",
                "posts_limit": 10
            },
            "moderate": {
                "max_tokens": 1500,
                "format": """
주제별로 그룹핑하여 작성하세요:
- 2개 이상 게시물이 다루는 주제는 독립 섹션으로
- 인기도/점수가 높은 주제를 상단에 배치
- 각 섹션 제목은 구체적인 주제로
- 단발성 정보는 "기타 정보들"로
- 마지막에 "종합 요약" 추가
""",
                "posts_limit": 20
            },
            "detailed": {
                "max_tokens": 3000,
                "format": """
주제별로 상세하게 그룹핑하여 작성하세요:
- 2개 이상 게시물이 다루는 주제는 독립 섹션으로
- 인기도/점수/댓글수가 높은 주제를 상단에 배치
- 각 섹션 제목은 구체적인 주제로 (예: "테슬라 Q4 실적 발표 - 매출 부진")
- 각 섹션에서 관련 정보를 상세히 정리
- 단발성 정보는 "기타 정보들"로
- 마지막에 "종합 요약"으로 전체 트렌드 분석
""",
                "posts_limit": 30
            }
        }
        
        config = report_configs.get(report_length, report_configs["moderate"])
        posts_text = self._format_posts_for_llm(posts, config['posts_limit'])
        
        try:
            system_prompt = f"""당신은 Reddit 소셜미디어 분석 전문가입니다. 
주어진 게시물들을 분석하여 {query}에 대한 보고서를 작성하세요.

**CRITICAL REQUIREMENT: 게시물을 참조할 때는 반드시 [1], [2], [3] 형식의 각주를 사용해야 합니다.**

This is MANDATORY. Every claim must include a footnote reference.

**보고서 작성 방법:**
1. 모든 게시물을 읽고 공통된 주제나 테마를 파악하세요.
2. 2개 이상의 게시물이 다루는 주제는 독립 섹션으로 만드세요.
3. 각 섹션의 제목은 해당 주제를 구체적으로 표현하세요.
4. 가장 많이 언급되거나 인기 있는 주제를 상단에 배치하세요.
5. 2개 미만의 게시물만 다루는 정보는 "기타 정보들" 섹션에 넣으세요.
6. 마지막에는 "종합 요약" 섹션을 추가하세요.

YOU MUST USE [1], [2], [3] FORMAT FOR ALL REFERENCES."""
            
            user_prompt = f"""
다음은 '{query}'에 대한 소셜 미디어 게시물들입니다:

{posts_text}

위 게시물들을 분석하여 다음 형식으로 보고서를 작성해주세요:
{config['format']}

**반드시 지켜야 할 사항:**
- 게시물을 인용할 때는 항상 [게시물 번호] 형식의 각주를 사용하세요.
- 예: "사용자들이 비전프로의 몰입감에 감탄하고 있습니다[3]."
- 구체적인 수치나 주장을 언급할 때는 반드시 출처 각주를 포함하세요.
- 절대 [뉴스 1], [루머 2] 같은 형식을 사용하지 마세요. 오직 [1], [2], [3] 형식만 사용합니다.
- 게시물 번호는 위에 제공된 "게시물 1", "게시물 2" 순서와 일치해야 합니다."""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=config['max_tokens']
            )
            
            full_report = response.choices[0].message.content
            summary = full_report.split('\n')[0][:200]
            
            # 각주가 없으면 강제로 추가
            import re
            existing_footnotes = re.findall(r'\[(\d+)\]', full_report)
            
            if not existing_footnotes:
                logger.warning("No footnotes found in report, adding them manually")
                # 보고서 내용에 각주 추가
                full_report = self._add_footnotes_to_report(full_report, posts[:config['posts_limit']])
            
            # 게시물 번호와 URL 매핑 생성
            post_mappings = []
            for i, post in enumerate(posts[:config['posts_limit']], 1):
                if post.url:
                    post_mappings.append({
                        "footnote_number": i,
                        "url": post.url,
                        "title": post.title,
                        "score": post.score,
                        "comments": post.comments,
                        "created_utc": post.created_utc,
                        "subreddit": post.subreddit,
                        "author": post.author
                    })
            
            return {
                "summary": summary,
                "full_report": full_report,
                "post_mappings": post_mappings  # 각주 매핑 정보 추가
            }
            
        except Exception as e:
            logger.error(f"Error generating report with LLM: {e}")
            return {
                "summary": "보고서 생성 중 오류가 발생했습니다.",
                "full_report": str(e)
            }
    
    def _format_posts_for_llm(self, posts: List[PostBase], limit: int = 20) -> str:
        formatted_posts = []
        for i, post in enumerate(posts[:limit], 1):
            post_text = f"\n[게시물 {i} - {post.source}]\n"
            if post.title:
                post_text += f"제목: {post.title}\n"
            if post.author:
                post_text += f"작성자: {post.author}\n"
            if post.content:
                post_text += f"내용: {post.content[:500]}...\n"
            # 메타데이터 추가
            if post.score is not None:
                post_text += f"추천수: {post.score}\n"
            if post.comments is not None:
                post_text += f"댓글수: {post.comments}\n"
            if post.subreddit:
                post_text += f"서브레딧: r/{post.subreddit}\n"
            if post.url:
                post_text += f"링크: {post.url}\n"
            formatted_posts.append(post_text)
        
        return "\n".join(formatted_posts)
    
    def _add_footnotes_to_report(self, report: str, posts: List[PostBase]) -> str:
        """보고서에 각주를 강제로 추가하는 함수"""
        if not posts:
            return report
        
        # 각 문단에서 중요한 주장이나 정보를 찾아 각주 추가
        lines = report.split('\n')
        processed_lines = []
        footnote_counter = 1
        
        for line in lines:
            if line.strip() and not line.startswith('#') and not line.startswith('-'):
                # 이미 각주가 있는지 확인
                if '[' not in line or ']' not in line:
                    # 문장 끝에 각주 추가 (단, 너무 많이 추가하지 않도록 제한)
                    if ('.' in line or '다' in line or '됩니다' in line or '있습니다' in line) and footnote_counter <= len(posts):
                        # 마지막 문장 끝에 각주 추가
                        sentences = line.split('.')
                        if len(sentences) >= 2 and sentences[-2].strip():
                            sentences[-2] += f'[{footnote_counter}]'
                            line = '.'.join(sentences)
                            footnote_counter += 1
                        elif '다' in line or '됩니다' in line or '있습니다' in line:
                            # 한국어 문장 끝에 각주 추가
                            import re
                            line = re.sub(r'(다|됩니다|있습니다)([^가-힣]*?)(?=\s|$)', f'\\1[{footnote_counter}]\\2', line, count=1)
                            footnote_counter += 1
            
            processed_lines.append(line)
            
            # 최대 5개 각주까지만 추가
            if footnote_counter > 5:
                break
        
        return '\n'.join(processed_lines)