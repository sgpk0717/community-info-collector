from typing import List, Optional
from app.core.config import settings
from app.schemas.schemas import PostBase
import logging
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_report(self, query: str, posts: List[PostBase]) -> dict:
        if not self.openai_client:
            logger.warning("OpenAI client not initialized")
            return {
                "summary": "LLM 서비스가 설정되지 않았습니다.",
                "full_report": "API 키를 설정해주세요."
            }
        
        posts_text = self._format_posts_for_llm(posts)
        
        try:
            system_prompt = """당신은 소셜 미디어 데이터를 분석하고 종합하는 전문가입니다. 
주어진 게시물들을 분석하여 핵심 정보를 추출하고, 트렌드를 파악하며, 
유용한 인사이트를 한국어로 제공해주세요."""
            
            user_prompt = f"""
다음은 '{query}'에 대한 소셜 미디어 게시물들입니다:

{posts_text}

위 게시물들을 분석하여 다음 형식으로 보고서를 작성해주세요:

1. 요약 (2-3문장)
2. 주요 발견사항
3. 트렌드 및 패턴
4. 핵심 인사이트
5. 추가 조사가 필요한 부분
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            full_report = response.choices[0].message.content
            summary = full_report.split('\n')[0][:200]
            
            return {
                "summary": summary,
                "full_report": full_report
            }
            
        except Exception as e:
            logger.error(f"Error generating report with LLM: {e}")
            return {
                "summary": "보고서 생성 중 오류가 발생했습니다.",
                "full_report": str(e)
            }
    
    def _format_posts_for_llm(self, posts: List[PostBase]) -> str:
        formatted_posts = []
        for i, post in enumerate(posts[:20], 1):
            post_text = f"\n[게시물 {i} - {post.source}]\n"
            if post.title:
                post_text += f"제목: {post.title}\n"
            if post.author:
                post_text += f"작성자: {post.author}\n"
            if post.content:
                post_text += f"내용: {post.content[:500]}...\n"
            formatted_posts.append(post_text)
        
        return "\n".join(formatted_posts)