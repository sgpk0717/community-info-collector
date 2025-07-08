"""
Reddit 상세 검색 결과 출력 테스트
검색 결과를 매우 디테일하게 출력
"""
import asyncio
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
import praw

# 환경변수 로드
load_dotenv()

# 서비스 임포트
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.services.reddit_service import RedditService

async def get_detailed_post_info(reddit_service, query: str, limit: int = 3):
    """상세한 게시물 정보 가져오기"""
    print(f"\n{'='*80}")
    print(f"검색어: '{query}'")
    print(f"{'='*80}")
    
    # 검색 실행
    posts = await reddit_service.search_posts(query, limit=limit)
    
    if not posts:
        print("❌ 검색 결과가 없습니다.")
        return
    
    print(f"✅ 총 {len(posts)}개의 게시물을 찾았습니다.\n")
    
    # Reddit API 직접 접근하여 더 많은 정보 가져오기
    for idx, post in enumerate(posts, 1):
        print(f"\n{'-'*80}")
        print(f"📄 게시물 #{idx}")
        print(f"{'-'*80}")
        
        # 기본 정보
        print(f"🔹 제목: {post.title}")
        print(f"🔹 게시물 ID: {post.post_id}")
        print(f"🔹 작성자: {post.author}")
        print(f"🔹 서브레딧: r/{post.source.replace('reddit/', '')}")
        print(f"🔹 URL: {post.url}")
        
        # Reddit API를 통해 추가 정보 가져오기
        try:
            submission = reddit_service.reddit.submission(id=post.post_id)
            submission._fetch()  # 모든 속성 로드
            
            # 시간 정보
            created_time = datetime.fromtimestamp(submission.created_utc)
            print(f"\n📅 시간 정보:")
            print(f"   - 작성일: {created_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            print(f"   - 경과 시간: {(datetime.now() - created_time).days}일 전")
            
            # 점수 및 투표 정보
            print(f"\n📊 투표 정보:")
            print(f"   - 점수: {submission.score}점")
            print(f"   - 좋아요 비율: {submission.upvote_ratio * 100:.1f}%")
            print(f"   - 추정 좋아요 수: {int(submission.score / (2 * submission.upvote_ratio - 1)) if submission.upvote_ratio > 0.5 else 0}")
            
            # 댓글 정보
            print(f"\n💬 댓글 정보:")
            print(f"   - 총 댓글 수: {submission.num_comments}개")
            
            # 게시물 유형
            print(f"\n📝 게시물 유형:")
            print(f"   - 텍스트 게시물: {'예' if submission.is_self else '아니오'}")
            print(f"   - 비디오: {'예' if submission.is_video else '아니오'}")
            print(f"   - 고정된 게시물: {'예' if submission.stickied else '아니오'}")
            print(f"   - NSFW: {'예' if submission.over_18 else '아니오'}")
            print(f"   - 스포일러: {'예' if submission.spoiler else '아니오'}")
            
            # 본문 내용
            if submission.selftext:
                print(f"\n📖 본문 내용:")
                content_lines = submission.selftext.split('\n')
                for i, line in enumerate(content_lines[:10]):  # 처음 10줄만
                    if line.strip():
                        print(f"   {line[:100]}{'...' if len(line) > 100 else ''}")
                if len(content_lines) > 10:
                    print(f"   ... (총 {len(content_lines)}줄)")
            
            # 미디어 정보
            if hasattr(submission, 'preview') and submission.preview:
                print(f"\n🖼️ 미디어 정보:")
                try:
                    images = submission.preview.get('images', [])
                    if images:
                        print(f"   - 이미지 수: {len(images)}개")
                        print(f"   - 썸네일 URL: {images[0]['source']['url'][:80]}...")
                except:
                    pass
            
            # 외부 링크
            if not submission.is_self and submission.url:
                print(f"\n🔗 외부 링크:")
                print(f"   - URL: {submission.url}")
                print(f"   - 도메인: {submission.domain}")
            
            # 플레어 정보
            if submission.link_flair_text:
                print(f"\n🏷️ 플레어: {submission.link_flair_text}")
            
            # 수상 정보
            if submission.all_awardings:
                print(f"\n🏆 수상 정보:")
                for award in submission.all_awardings[:5]:  # 최대 5개만
                    print(f"   - {award['name']}: {award['count']}개")
            
            # 상위 댓글 3개
            submission.comments.replace_more(limit=0)
            top_comments = sorted(submission.comments.list(), 
                                 key=lambda x: x.score if hasattr(x, 'score') else 0, 
                                 reverse=True)[:3]
            
            if top_comments:
                print(f"\n💭 인기 댓글 TOP 3:")
                for i, comment in enumerate(top_comments, 1):
                    if hasattr(comment, 'body'):
                        comment_preview = comment.body.replace('\n', ' ')[:100]
                        score = comment.score if hasattr(comment, 'score') else 0
                        print(f"   {i}. [{score}점] {comment_preview}{'...' if len(comment.body) > 100 else ''}")
            
        except Exception as e:
            print(f"\n⚠️ 추가 정보를 가져오는 중 오류 발생: {e}")
    
    print(f"\n{'='*80}")

async def search_and_analyze(query: str):
    """검색 및 분석"""
    reddit = RedditService()
    
    if not reddit.reddit:
        print("❌ Reddit 서비스 초기화 실패!")
        return
    
    await get_detailed_post_info(reddit, query, limit=5)
    
    # 통계 요약
    print(f"\n📊 검색 통계 요약")
    print(f"{'-'*80}")
    
    # 더 많은 게시물로 통계 계산
    all_posts = await reddit.search_posts(query, limit=50)
    
    if all_posts:
        # 서브레딧별 분포
        subreddit_count = {}
        total_score = 0
        total_comments = 0
        
        for post in all_posts:
            subreddit = post.source.replace('reddit/', '')
            subreddit_count[subreddit] = subreddit_count.get(subreddit, 0) + 1
        
        print(f"\n🏠 서브레딧 분포 (상위 10개):")
        sorted_subs = sorted(subreddit_count.items(), key=lambda x: x[1], reverse=True)[:10]
        for sub, count in sorted_subs:
            print(f"   - r/{sub}: {count}개 ({count/len(all_posts)*100:.1f}%)")
        
        # 추가 통계를 위해 Reddit API 직접 사용
        print(f"\n📈 게시물 통계:")
        scores = []
        comments = []
        
        for post in all_posts[:20]:  # 처음 20개만 상세 분석
            try:
                submission = reddit.reddit.submission(id=post.post_id)
                scores.append(submission.score)
                comments.append(submission.num_comments)
            except:
                pass
        
        if scores:
            avg_score = sum(scores) / len(scores)
            avg_comments = sum(comments) / len(comments)
            max_score = max(scores)
            max_comments = max(comments)
            
            print(f"   - 평균 점수: {avg_score:.1f}점")
            print(f"   - 평균 댓글 수: {avg_comments:.1f}개")
            print(f"   - 최고 점수: {max_score}점")
            print(f"   - 최다 댓글: {max_comments}개")

async def main():
    """메인 함수"""
    print("🔍 Reddit 상세 검색 결과 테스트")
    print("="*80)
    print(f"실행 시간: {datetime.now()}")
    print("="*80)
    
    # 테스트할 검색어
    test_queries = [
        "Tesla 2025",
        "AI technology breakthrough",
        "Python programming tips"
    ]
    
    for query in test_queries:
        await search_and_analyze(query)
        print("\n" + "="*80 + "\n")
        await asyncio.sleep(1)  # API 제한 방지

if __name__ == "__main__":
    asyncio.run(main())