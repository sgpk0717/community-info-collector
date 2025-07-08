"""
Reddit API 전용 테스트 스크립트
Reddit 검색 기능만 집중적으로 테스트
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

async def test_reddit_service():
    print("Reddit API 테스트")
    print("=" * 70)
    print(f"시간: {datetime.now()}")
    print("=" * 70)
    
    # 환경변수 확인
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    user_agent = os.getenv('REDDIT_USER_AGENT')
    
    print("\n환경변수 상태:")
    print(f"REDDIT_CLIENT_ID: {'설정됨' if client_id else '미설정'} ({len(client_id) if client_id else 0}자)")
    print(f"REDDIT_CLIENT_SECRET: {'설정됨' if client_secret else '미설정'} ({len(client_secret) if client_secret else 0}자)")
    print(f"REDDIT_USER_AGENT: {user_agent if user_agent else '미설정'}")
    print("-" * 70)
    
    # Reddit 서비스 초기화
    reddit = RedditService()
    
    if not reddit.reddit:
        print("\n✗ Reddit 서비스 초기화 실패!")
        print("  원인: API 키가 올바르게 설정되지 않았습니다.")
        return
    
    print("\n✓ Reddit 서비스 초기화 성공!")
    
    # 여러 검색어로 테스트
    test_queries = [
        "Tesla latest news",
        "Python programming",
        "artificial intelligence",
        "SpaceX",
        "technology"
    ]
    
    for query in test_queries:
        print(f"\n\n검색어: '{query}'")
        print("-" * 50)
        
        try:
            # 검색 실행
            posts = await reddit.search_posts(query, limit=5)
            
            if posts:
                print(f"✓ 성공: {len(posts)}개 게시물 검색됨")
                
                for i, post in enumerate(posts[:3], 1):
                    print(f"\n  [{i}] 제목: {post.title[:80]}{'...' if len(post.title) > 80 else ''}")
                    print(f"      서브레딧: r/{post.source.replace('reddit/', '')}")
                    print(f"      작성자: {post.author}")
                    print(f"      URL: {post.url}")
                    if hasattr(post, 'score'):
                        print(f"      점수: {post.score}")
                    if post.content:
                        print(f"      내용: {post.content[:100]}{'...' if len(post.content) > 100 else ''}")
            else:
                print("✗ 검색 결과 없음")
                
        except Exception as e:
            print(f"✗ 오류 발생: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # 특정 서브레딧 검색 테스트
    print("\n\n특정 서브레딧 검색 테스트")
    print("=" * 70)
    
    subreddits = ["teslamotors", "programming", "technology"]
    
    for subreddit in subreddits:
        print(f"\n서브레딧: r/{subreddit}")
        print("-" * 50)
        
        try:
            # 서브레딧 객체 가져오기
            sub = reddit.reddit.subreddit(subreddit)
            
            # Hot 게시물 가져오기
            print("  최신 인기 게시물:")
            hot_posts = list(sub.hot(limit=3))
            
            for i, submission in enumerate(hot_posts, 1):
                print(f"    [{i}] {submission.title[:60]}...")
                print(f"        점수: {submission.score}, 댓글: {submission.num_comments}")
                
        except Exception as e:
            print(f"  ✗ 오류: {type(e).__name__}: {str(e)}")
    
    print("\n\n테스트 완료!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_reddit_service())