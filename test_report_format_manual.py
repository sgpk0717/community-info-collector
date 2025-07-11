#!/usr/bin/env python3
"""
새로운 보고서 포맷 수동 테스트
"""
import asyncio
import sys
sys.path.append('/Users/seonggukpark/community-info-collector')

from app.services.reddit_service import RedditService
from app.services.verified_analysis_service import VerifiedAnalysisService
from app.schemas.schemas import PostBase
from datetime import datetime

async def test_report_format():
    print("=== 구글 주가 전망 - 새로운 보고서 포맷 테스트 ===\n")
    
    # Reddit 서비스 직접 초기화
    reddit_service = RedditService()
    
    try:
        # 1. Reddit API로 직접 데이터 수집
        print("1. Reddit에서 데이터 수집 중...")
        
        # search_posts 메서드 직접 호출 (동기 메서드이므로 run_in_executor 사용)
        loop = asyncio.get_event_loop()
        # 더 많은 데이터를 수집하기 위해 여러 검색어 사용
        posts1 = await loop.run_in_executor(None, reddit_service.search_posts, "구글 주가", 15)
        posts2 = await loop.run_in_executor(None, reddit_service.search_posts, "Google stock", 15)
        posts3 = await loop.run_in_executor(None, reddit_service.search_posts, "GOOGL", 10)
        
        # 중복 제거하며 합치기
        all_posts = posts1 + posts2 + posts3
        seen_urls = set()
        posts = []
        for post in all_posts:
            if post.url and post.url not in seen_urls:
                seen_urls.add(post.url)
                posts.append(post)
        
        print(f"   수집된 게시물 수: {len(posts)}")
        
        if posts:
            print("\n   수집된 게시물 샘플:")
            for i, post in enumerate(posts[:5], 1):
                print(f"   [{i}] {post.title[:60]}...")
                print(f"       점수: {post.score}, 댓글: {post.comments}, 서브레딧: r/{post.subreddit}")
        
        # 2. 새로운 포맷으로 보고서 생성
        print("\n2. 주제별 그룹핑 포맷으로 보고서 생성 중...")
        analysis_service = VerifiedAnalysisService()
        
        result = await analysis_service.generate_verified_report(
            query='구글 주가 전망',
            posts=posts,
            report_length='moderate',
            session_id='test-session'
        )
        
        # 3. 결과 출력
        print("\n=== 생성된 보고서 ===")
        print("-" * 60)
        print(result['full_report'])
        print("-" * 60)
        
        # 4. 포맷 검증
        report = result['full_report']
        print("\n=== 보고서 구조 분석 ===")
        
        # 섹션 찾기
        import re
        sections = re.findall(r'### \d+\. (.+)', report)
        print(f"\n발견된 섹션 ({len(sections)}개):")
        for i, section in enumerate(sections, 1):
            print(f"  {i}. {section}")
        
        # 각주 확인
        footnotes = re.findall(r'\[(\d+)\]', report)
        unique_footnotes = sorted(set(map(int, footnotes)))
        print(f"\n사용된 각주: {len(footnotes)}개")
        print(f"고유 각주 번호: {unique_footnotes}")
        
        # 필수 섹션 확인
        print("\n필수 섹션 체크:")
        print(f"  - '기타 정보' 포함: {'기타 정보' in report}")
        print(f"  - '종합 요약' 포함: {'종합 요약' in report}")
        
        # 5. 각주 매핑 확인
        if 'post_mappings' in result:
            print(f"\n=== 각주-URL 매핑 ({len(result['post_mappings'])}개) ===")
            for mapping in result['post_mappings'][:5]:
                print(f"[{mapping['footnote_number']}] → {mapping['url']}")
                
    except Exception as e:
        print(f"\n오류 발생: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_report_format())