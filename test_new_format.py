#!/usr/bin/env python3
"""
새로운 보고서 포맷 테스트 - 주제별 그룹핑
"""
import asyncio
import sys
sys.path.append('/Users/seonggukpark/community-info-collector')

from app.services.reddit_service import RedditService
from app.services.verified_analysis_service import VerifiedAnalysisService

async def test_new_report_format():
    print("=== 구글 주가 전망 키워드로 새로운 보고서 포맷 테스트 ===\n")
    
    # Reddit 서비스 초기화
    reddit_service = RedditService()
    
    # 1. Reddit에서 데이터 수집
    print("1. Reddit에서 '구글 주가 전망' 관련 게시물 수집 중...")
    posts = await reddit_service.collect_reddit_posts('구글 주가 전망')
    print(f"   수집된 게시물 수: {len(posts)}")
    
    if posts:
        print("\n   첫 5개 게시물 미리보기:")
        for i, post in enumerate(posts[:5], 1):
            print(f"   [{i}] {post.title[:60]}... (점수: {post.score}, 댓글: {post.comments})")
    
    # 2. 새로운 포맷으로 보고서 생성
    print("\n2. 새로운 주제별 그룹핑 포맷으로 보고서 생성 중...")
    analysis_service = VerifiedAnalysisService()
    result = await analysis_service.generate_verified_report(
        query='구글 주가 전망',
        posts=posts,
        report_length='moderate'
    )
    
    # 3. 결과 출력
    print("\n=== 생성된 보고서 ===")
    print(result['full_report'])
    
    # 4. 각주 매핑 확인
    print("\n=== 각주 매핑 정보 (첫 10개) ===")
    for mapping in result.get('post_mappings', [])[:10]:
        print(f"[{mapping['footnote_number']}] {mapping['title'][:60]}...")
        print(f"     점수: {mapping['score']}, 댓글: {mapping['comments']}, 서브레딧: r/{mapping['subreddit']}")
    
    # 5. 포맷 검증
    report = result['full_report']
    print("\n=== 포맷 검증 ===")
    
    # 주제별 섹션 확인
    import re
    sections = re.findall(r'### \d+\. (.+)', report)
    print(f"발견된 섹션 수: {len(sections)}")
    for i, section in enumerate(sections, 1):
        print(f"  섹션 {i}: {section}")
    
    # 각주 사용 확인
    footnotes = re.findall(r'\[(\d+)\]', report)
    print(f"\n사용된 각주 수: {len(footnotes)}")
    print(f"각주 번호: {sorted(set(map(int, footnotes)))}")
    
    # 필수 섹션 확인
    has_etc = "기타 정보" in report
    has_summary = "종합 요약" in report
    print(f"\n'기타 정보들' 섹션 포함: {has_etc}")
    print(f"'종합 요약' 섹션 포함: {has_summary}")

if __name__ == "__main__":
    asyncio.run(test_new_report_format())