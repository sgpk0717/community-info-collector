"""
Reddit API 한국어 검색 테스트
"""
import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 서비스 임포트
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.services.reddit_service import RedditService

async def test_korean_search():
    print("Reddit 한국어 검색 테스트")
    print("=" * 70)
    print(f"시간: {datetime.now()}")
    print("=" * 70)
    
    # Reddit 서비스 초기화
    reddit = RedditService()
    
    if not reddit.reddit:
        print("\n✗ Reddit 서비스 초기화 실패!")
        return
    
    # 한국어 및 한국 관련 검색어
    test_queries = [
        "테슬라",
        "Tesla Korea",
        "Korean technology",
        "Samsung",
        "BTS",
        "K-pop",
        "Seoul",
        "한국"
    ]
    
    for query in test_queries:
        print(f"\n\n검색어: '{query}'")
        print("-" * 50)
        
        try:
            # 검색 실행
            posts = await reddit.search_posts(query, limit=10)
            
            if posts:
                print(f"✓ 성공: {len(posts)}개 게시물 검색됨")
                
                # 한국 관련 게시물 필터링
                korean_related = 0
                
                for i, post in enumerate(posts[:5], 1):
                    # 한국 관련 키워드 체크
                    korean_keywords = ['korea', 'korean', 'seoul', '한국', '서울', '테슬라', 'k-pop', 'kpop']
                    is_korean_related = any(keyword in post.title.lower() or keyword in post.content.lower() 
                                          for keyword in korean_keywords)
                    
                    if is_korean_related:
                        korean_related += 1
                        print(f"\n  [{i}] 🇰🇷 한국 관련 게시물")
                    else:
                        print(f"\n  [{i}] 일반 게시물")
                    
                    print(f"      제목: {post.title[:80]}{'...' if len(post.title) > 80 else ''}")
                    print(f"      서브레딧: r/{post.source.replace('reddit/', '')}")
                    print(f"      URL: {post.url}")
                    
                    # 내용 미리보기 (한국어가 포함되어 있는지 확인)
                    content_preview = post.content[:150] if post.content else "내용 없음"
                    print(f"      내용: {content_preview}{'...' if len(post.content) > 150 else ''}")
                
                print(f"\n  → 한국 관련 게시물: {korean_related}개 / 전체: {len(posts)}개")
            else:
                print("✗ 검색 결과 없음")
                
        except Exception as e:
            print(f"✗ 오류 발생: {type(e).__name__}: {str(e)}")
    
    # 한국 관련 서브레딧 테스트
    print("\n\n한국 관련 서브레딧 검색")
    print("=" * 70)
    
    korean_subreddits = ["korea", "hanguk", "korean", "kpop"]
    
    for subreddit_name in korean_subreddits:
        print(f"\n서브레딧: r/{subreddit_name}")
        print("-" * 50)
        
        try:
            posts = await reddit.search_subreddit(subreddit_name, "Tesla", limit=5)
            
            if posts:
                print(f"✓ Tesla 관련 게시물 {len(posts)}개 발견")
                for i, post in enumerate(posts[:3], 1):
                    print(f"  [{i}] {post.title[:60]}...")
            else:
                print("  검색 결과 없음")
                
        except Exception as e:
            print(f"  ✗ 오류: {type(e).__name__}: {str(e)}")
    
    print("\n\n테스트 완료!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_korean_search())