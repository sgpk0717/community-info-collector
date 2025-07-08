"""
Reddit 검색 결과 상세 출력 (간소화 버전)
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

async def print_detailed_results(query: str, limit: int = 3):
    """검색 결과를 상세하게 출력"""
    reddit = RedditService()
    
    if not reddit.reddit:
        print("❌ Reddit 서비스 초기화 실패!")
        return
    
    print(f"\n{'='*80}")
    print(f"🔍 검색어: '{query}'")
    print(f"{'='*80}")
    
    # 검색 실행
    posts = await reddit.search_posts(query, limit=limit)
    
    if not posts:
        print("❌ 검색 결과가 없습니다.")
        return
    
    print(f"✅ 총 {len(posts)}개의 게시물을 찾았습니다.\n")
    
    # 각 게시물 상세 출력
    for idx, post in enumerate(posts, 1):
        print(f"\n{'━'*80}")
        print(f"📄 게시물 #{idx}")
        print(f"{'━'*80}")
        
        # 기본 정보
        print(f"\n📌 기본 정보:")
        print(f"  • 제목: {post.title}")
        print(f"  • 게시물 ID: {post.post_id}")
        print(f"  • 작성자: {post.author}")
        print(f"  • 서브레딧: r/{post.source.replace('reddit/', '')}")
        print(f"  • URL: {post.url}")
        
        # Reddit API로 추가 정보 가져오기
        try:
            submission = reddit.reddit.submission(id=post.post_id)
            
            # 시간 정보
            created_time = datetime.fromtimestamp(submission.created_utc)
            time_diff = datetime.now() - created_time
            
            print(f"\n⏰ 시간 정보:")
            print(f"  • 작성일: {created_time.strftime('%Y년 %m월 %d일 %H:%M:%S')}")
            print(f"  • 경과 시간: ", end="")
            if time_diff.days > 0:
                print(f"{time_diff.days}일 전")
            elif time_diff.seconds > 3600:
                print(f"{time_diff.seconds // 3600}시간 전")
            else:
                print(f"{time_diff.seconds // 60}분 전")
            
            # 인기도 정보
            print(f"\n📊 인기도:")
            print(f"  • 점수: {submission.score:,}점")
            print(f"  • 댓글: {submission.num_comments:,}개")
            print(f"  • 좋아요 비율: {submission.upvote_ratio * 100:.0f}%")
            
            # 추정 통계
            if submission.upvote_ratio > 0.5:
                estimated_upvotes = int(submission.score / (2 * submission.upvote_ratio - 1))
                estimated_downvotes = estimated_upvotes - submission.score
                print(f"  • 추정 좋아요: {estimated_upvotes:,}개")
                print(f"  • 추정 싫어요: {estimated_downvotes:,}개")
            
            # 게시물 특성
            print(f"\n🏷️ 게시물 특성:")
            characteristics = []
            if submission.is_self:
                characteristics.append("텍스트 게시물")
            else:
                characteristics.append("링크 게시물")
            if submission.is_video:
                characteristics.append("비디오")
            if submission.stickied:
                characteristics.append("고정됨")
            if submission.over_18:
                characteristics.append("성인 콘텐츠")
            if submission.spoiler:
                characteristics.append("스포일러")
            if submission.locked:
                characteristics.append("잠김")
            if submission.distinguished:
                characteristics.append(f"공식({submission.distinguished})")
            
            print(f"  • 특성: {', '.join(characteristics) if characteristics else '일반 게시물'}")
            
            # 플레어
            if submission.link_flair_text:
                print(f"  • 플레어: {submission.link_flair_text}")
            
            # 본문 내용 (텍스트 게시물인 경우)
            if submission.is_self and submission.selftext:
                print(f"\n📝 본문 내용:")
                lines = submission.selftext.split('\n')
                preview_lines = lines[:5]  # 처음 5줄만
                for line in preview_lines:
                    if line.strip():
                        print(f"  {line[:100]}{'...' if len(line) > 100 else ''}")
                if len(lines) > 5:
                    print(f"  ... (총 {len(lines)}줄, {len(submission.selftext)}자)")
            
            # 외부 링크 정보
            if not submission.is_self and submission.url:
                print(f"\n🔗 링크 정보:")
                print(f"  • URL: {submission.url[:80]}{'...' if len(submission.url) > 80 else ''}")
                print(f"  • 도메인: {submission.domain}")
            
            # 수상 정보
            if submission.all_awardings:
                print(f"\n🏆 수상:")
                total_awards = sum(award['count'] for award in submission.all_awardings)
                print(f"  • 총 {total_awards}개의 상 수상")
                for award in submission.all_awardings[:3]:  # 상위 3개만
                    print(f"    - {award['name']}: {award['count']}개")
            
            # 상위 댓글 미리보기
            try:
                submission.comments.replace_more(limit=0)
                top_comments = sorted(
                    [c for c in submission.comments if hasattr(c, 'score')],
                    key=lambda x: x.score,
                    reverse=True
                )[:2]  # 상위 2개만
                
                if top_comments:
                    print(f"\n💬 인기 댓글:")
                    for i, comment in enumerate(top_comments, 1):
                        comment_text = comment.body.replace('\n', ' ')[:80]
                        print(f"  {i}. [{comment.score}점] {comment_text}...")
            except:
                pass
            
        except Exception as e:
            print(f"\n⚠️ 추가 정보 로드 중 오류: {type(e).__name__}")
    
    # 검색 결과 요약
    print(f"\n\n{'='*80}")
    print(f"📊 검색 결과 요약")
    print(f"{'='*80}")
    
    # 서브레딧 분포
    subreddit_count = {}
    for post in posts:
        sub = post.source.replace('reddit/', '')
        subreddit_count[sub] = subreddit_count.get(sub, 0) + 1
    
    print(f"\n🏠 서브레딧 분포:")
    for sub, count in sorted(subreddit_count.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(posts)) * 100
        print(f"  • r/{sub}: {count}개 ({percentage:.0f}%)")
    
    print(f"\n✅ 검색 완료!")

async def main():
    """메인 함수"""
    print("🚀 Reddit 상세 검색 테스트 시작")
    print("="*80)
    
    # 테스트 검색어
    test_queries = [
        "Tesla Model Y 2025",
        "Python Django tutorial",
        "AI chatbot development"
    ]
    
    for query in test_queries:
        await print_detailed_results(query, limit=5)
        print("\n" + "="*80 + "\n")
        await asyncio.sleep(2)  # API 제한 방지

if __name__ == "__main__":
    asyncio.run(main())