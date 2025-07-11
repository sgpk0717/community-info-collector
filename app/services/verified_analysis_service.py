#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
검증된 분석 서비스 - verified_analysis.py 기반
"""
import logging
import time
from typing import List, Dict, Any
from datetime import datetime
from openai import OpenAI
from app.core.config import settings
from app.schemas.schemas import PostBase
import httpx

logger = logging.getLogger(__name__)

class VerifiedAnalysisService:
    def __init__(self):
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            # SSL 검증을 비활성화한 HTTP 클라이언트 생성
            http_client = httpx.Client(verify=False)
            self.openai_client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                http_client=http_client
            )
    
    def validate_report_content(self, analysis_text: str) -> tuple[bool, str]:
        """보고서 내용 검증 함수"""
        
        # 기본 검증 조건들
        failure_indicators = [
            "죄송합니다",
            "작성할 수 없습니다",
            "제공할 수 없습니다", 
            "생성할 수 없습니다",
            "미래의 정보",
            "실시간 정보에 접근할 수 없습니다",
            "sorry",
            "cannot provide",
            "unable to",
            "I can't",
            "I cannot"
        ]
        
        # 최소 길이 체크 (너무 짧으면 실패)
        if len(analysis_text) < 1000:
            return False, "보고서가 너무 짧습니다"
        
        # 실패 지시어 체크
        for indicator in failure_indicators:
            if indicator.lower() in analysis_text.lower():
                return False, f"거부 응답 감지: '{indicator}'"
        
        # 필수 섹션 체크 (새로운 형식)
        required_sections = ["종합 요약", "기타 정보"]
        has_summary = any(section in analysis_text for section in ["종합 요약", "종합요약"])
        if not has_summary:
            return False, "종합 요약 섹션이 없습니다"
        
        return True, "검증 통과"
    
    async def generate_verified_report(self, query: str, posts: List[PostBase], report_length: str = "moderate", session_id: str = None) -> Dict[str, Any]:
        """검증이 포함된 상세 분석 보고서 생성"""
        
        if not self.openai_client:
            logger.warning("OpenAI client not initialized")
            return {
                "summary": "LLM 서비스가 설정되지 않았습니다.",
                "full_report": "API 키를 설정해주세요."
            }
        
        # 신뢰도별 분류
        verified_news = []
        rumors_speculation = []
        
        reliable_indicators = ['worldnews', 'news', 'politics', 'technology', 'business']
        
        for post in posts:
            # 점수와 소스를 기반으로 신뢰도 판단
            score = self._extract_score_from_content(post.content)
            is_reliable = (
                score > 100 and 
                any(indicator in post.content.lower() for indicator in reliable_indicators)
            )
            
            if is_reliable:
                verified_news.append(post)
            else:
                rumors_speculation.append(post)
        
        # 콘텐츠 준비 - 모든 게시물을 순서대로 번호 매김
        all_posts = verified_news[:15] + rumors_speculation[:20]
        formatted_content = self._format_posts_for_analysis(all_posts, "게시물")
        
        # 분류별 콘텐츠 (참고용)
        news_content = self._format_posts_for_analysis(verified_news[:15], "뉴스")
        rumors_content = self._format_posts_for_analysis(rumors_speculation[:20], "루머")
        
        # 여러 프롬프트 전략 준비
        prompts = [
            # 프롬프트 1: 주제별 그룹핑 방식
            {
                "system": f"""당신은 Reddit 소셜미디어 분석 전문가입니다. 
                주어진 Reddit 게시물 데이터를 분석하여 {query}에 대한 보고서를 작성하세요.
                
                **CRITICAL REQUIREMENT: 게시물을 참조할 때는 반드시 [1], [2], [3] 형식의 각주를 사용해야 합니다.**
                
                This is MANDATORY. Every claim must include a footnote reference.
                
                **형식 규칙:**
                - 올바른 형식: "테슬라 주가가 7% 하락했습니다[1]."
                - 잘못된 형식: "테슬라 주가가 7% 하락했습니다." (각주 없음)
                
                YOU MUST USE [1], [2], [3] FORMAT FOR ALL REFERENCES.
                
                **보고서 작성 방법:**
                1. 먼저 모든 게시물을 읽고 공통된 주제나 테마를 파악하세요.
                2. 2개 이상의 게시물이 다루는 주제는 독립 섹션으로 만드세요.
                3. 각 섹션의 제목은 해당 주제를 구체적으로 표현하세요.
                   예: "### 1. 테슬라 Q4 실적 발표 - 매출 예상치 하회"
                4. 가장 많이 언급되거나 인기 있는 주제를 상단에 배치하세요.
                5. 2개 미만의 게시물만 다루는 정보는 "기타 정보들" 섹션에 넣으세요.
                6. 마지막에는 "종합 요약" 섹션을 추가하세요.
                
                **섹션 구성 예시:**
                ### 1. [가장 핫한 주제] (X개 게시물)
                - 관련 정보 정리...
                
                ### 2. [두 번째로 많이 언급된 주제] (Y개 게시물)
                - 관련 정보 정리...
                
                ### N. 기타 정보들
                - 단발성 정보 나열...
                
                ### N+1. 종합 요약
                - 전체적인 분석과 요약...
                
                반드시 구체적인 데이터를 인용하고 각주를 포함하세요.""",
                "user": f"""다음은 Reddit에서 수집한 {query} 관련 게시물 데이터입니다.

{formatted_content}

위 데이터를 주제별로 그룹핑하여 보고서를 작성해주세요.

**반드시 지켜야 할 사항:**
- 게시물을 인용할 때는 항상 [게시물 번호] 형식의 각주를 사용하세요.
- 공통된 주제를 다루는 게시물들을 하나의 섹션으로 묶으세요.
- 가장 많이 언급된 주제를 상단에 배치하세요.
- 구체적인 수치나 주장을 언급할 때는 반드시 출처 각주를 포함하세요.
- 게시물 번호는 위에 제공된 "게시물 1", "게시물 2" 순서와 일치해야 합니다."""
            },
            
            # 프롬프트 2: 테마 기반 분석
            {
                "system": f"""당신은 소셜미디어 데이터 분석가입니다. 
                제공된 Reddit 게시물을 테마별로 분류하고 {query}에 대한 보고서를 작성하세요.
                
                **CRITICAL REQUIREMENT: 게시물을 참조할 때는 반드시 [1], [2], [3] 형식의 각주를 사용해야 합니다.**
                
                **보고서 작성 지침:**
                1. 데이터에서 자연스럽게 나타나는 주제별로 섹션 구성
                2. 동일 주제 2개 이상 게시물 → 독립 섹션
                3. 인기도/점수가 높은 주제를 앞쪽에 배치
                4. 단발성 정보는 "기타 정보들"로 묶기
                5. 마지막에 종합 요약 추가
                
                **각 섹션 작성법:**
                - 섹션 제목: 구체적인 주제 명시
                - 내용: 해당 주제 관련 정보들을 정리/나열
                - 각 정보마다 출처 각주 필수
                
                최소 1500자 이상 작성하세요.""",
                "user": f"""Reddit 데이터를 주제별로 분석해주세요:

{formatted_content}

**작성 규칙:**
- 공통 주제별로 그룹핑
- 인기도 순으로 배치 
- 모든 인용에 [번호] 각주 사용
- 2개 미만 게시물은 "기타 정보들"로
- 마지막에 종합 요약"""
            },
            
            # 프롬프트 3: 직접적인 주제 분류 지시
            {
                "system": f"""Reddit 게시물 분석 전문가로서 {query} 관련 데이터를 주제별로 정리하세요.

**작업 순서:**
1. 모든 게시물 읽고 주제 파악
2. 비슷한 주제끼리 그룹핑 (최소 2개 이상)
3. 각 그룹을 하나의 섹션으로 작성
4. 인기 있는 주제를 상위에 배치
5. 나머지는 기타 정보로 처리
6. 마지막에 종합 요약

**각주 규칙: 반드시 [1], [2], [3] 형식 사용**

**섹션 형식:**
### 1. [구체적인 주제 제목]
해당 주제 관련 정보들 정리 (각주 포함)

### N. 기타 정보들
단발성 정보 나열

### N+1. 종합 요약
전체 트렌드와 시사점""",
                "user": f"""다음 Reddit 데이터를 주제별로 정리해주세요:

{formatted_content}

**중요:**
- 같은 주제 2개 이상 → 독립 섹션
- 인기도/점수 높은 순으로 배치
- 모든 인용에 [숫자] 각주 필수
- 게시물 번호 순서대로 각주 사용"""
            }
        ]
        
        # 여러 시도로 보고서 생성
        max_attempts = 3
        analysis = None
        
        for attempt in range(max_attempts):
            logger.info(f"Generating report attempt {attempt + 1}/{max_attempts}")
            
            try:
                prompt = prompts[attempt]
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-4.1",
                    messages=[
                        {"role": "system", "content": prompt["system"]},
                        {"role": "user", "content": prompt["user"]}
                    ],
                    temperature=0.6,
                    max_tokens=3000
                )
                
                candidate_analysis = response.choices[0].message.content
                
                # 검증 수행
                is_valid, validation_message = self.validate_report_content(candidate_analysis)
                
                logger.info(f"Validation result: {validation_message}")
                
                if is_valid:
                    analysis = candidate_analysis
                    logger.info(f"Report generation successful on attempt {attempt + 1}")
                    break
                else:
                    logger.warning(f"Attempt {attempt + 1} failed validation: {validation_message}")
                    if attempt < max_attempts - 1:
                        logger.info("Retrying with different strategy...")
                        time.sleep(2)  # 잠시 대기
                    
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} error: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2)
        
        if not analysis:
            logger.error("All attempts failed!")
            return {
                "summary": "보고서 생성에 실패했습니다.",
                "full_report": "여러 시도를 했지만 검증을 통과한 보고서를 생성할 수 없었습니다."
            }
        
        # 성공한 보고서 처리
        summary = analysis.split('\n')[0][:200] if analysis else "요약 생성 실패"
        
        # 각주가 없으면 강제로 추가 (main LLM service와 동일한 로직)
        import re
        existing_footnotes = re.findall(r'\[(\d+)\]', analysis)
        
        if not existing_footnotes:
            logger.warning("No footnotes found in report, adding them manually")
            # 보고서 내용에 각주 추가
            analysis = self._add_footnotes_to_report(analysis, all_posts)
        
        # 게시물 번호와 URL 매핑 생성
        post_mappings = []
        for i, post in enumerate(all_posts, 1):
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
            "full_report": analysis,
            "post_mappings": post_mappings  # 각주 매핑 정보 추가
        }
    
    def _extract_score_from_content(self, content: str) -> int:
        """게시물 내용에서 점수 추출"""
        try:
            # "👍 Score: 123" 형태에서 숫자 추출
            if "Score:" in content:
                score_part = content.split("Score:")[1].split("|")[0].strip()
                return int(score_part)
        except (ValueError, IndexError):
            pass
        return 0
    
    def _format_posts_for_analysis(self, posts: List[PostBase], category: str) -> str:
        """분석용 게시물 포맷팅"""
        formatted_posts = []
        
        for i, post in enumerate(posts, 1):
            post_text = f"\n[{category} {i}]\n"
            if post.title:
                post_text += f"제목: {post.title}\n"
            if post.author:
                post_text += f"작성자: {post.author}\n"
            if post.content:
                post_text += f"내용: {post.content[:800]}...\n"
            if post.url:
                post_text += f"URL: {post.url}\n"
            
            formatted_posts.append(post_text)
        
        return "\n".join(formatted_posts)
    
    def _add_footnotes_to_report(self, report: str, posts: List[PostBase]) -> str:
        """보고서에 각주를 강제로 추가하는 함수 (main LLM service와 동일한 로직)"""
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