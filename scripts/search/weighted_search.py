#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
가중치 검색 - 키워드별 중요도 반영
"""
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
import time

# 윈도우 환경에서 유니코드 출력 설정
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv()

from app.services.reddit_service import RedditService
from openai import OpenAI

def expand_keywords_with_gpt4(user_input):
    """GPT-4를 사용하여 키워드를 확장하고 영어로 변환"""
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        prompt = f"""
사용자가 입력한 키워드: "{user_input}"

이 키워드를 기반으로 Reddit에서 최신 정보와 찌라시, 루머, 뉴스를 잘 찾을 수 있도록 6개의 영어 검색 키워드를 만들어주세요.

요구사항:
1. 첫 번째 키워드는 원래 키워드의 직접 번역
2. 나머지 5개는 관련된 최신 정보, 뉴스, 루머, 분석을 잘 찾을 수 있는 키워드
3. 각 키워드는 Reddit 검색에 적합하도록 2-4개 단어로 구성
4. 투자, 주식, 기업 관련이면 earnings, forecast, analysis, news, rumor 등 포함
5. 인물 관련이면 controversy, scandal, latest, update 등 포함

JSON 형식으로 응답:
{{
    "keywords": [
        {{"keyword": "키워드1", "reason": "선택 이유"}},
        {{"keyword": "키워드2", "reason": "선택 이유"}},
        {{"keyword": "키워드3", "reason": "선택 이유"}},
        {{"keyword": "키워드4", "reason": "선택 이유"}},
        {{"keyword": "키워드5", "reason": "선택 이유"}},
        {{"keyword": "키워드6", "reason": "선택 이유"}}
    ]
}}
"""
        
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        # JSON 응답 파싱
        import json
        result = json.loads(response.choices[0].message.content)
        
        print(f"🤖 GPT-4.1이 생성한 확장 키워드:")
        print("="*70)
        
        expanded_keywords = []
        for i, item in enumerate(result["keywords"], 1):
            expanded_keywords.append({
                "rank": i,
                "query": item["keyword"],
                "posts_to_collect": 10,
                "reason": item["reason"]
            })
            print(f"{i}. \"{item['keyword']}\" - {item['reason']}")
        
        print(f"\n총 목표 수집량: {len(expanded_keywords) * 10}개")
        print("="*70)
        
        return expanded_keywords
        
    except Exception as e:
        print(f"❌ GPT-4 키워드 확장 실패: {e}")
        # 실패 시 기본 변환 로직 사용
        return [{"rank": 1, "query": translate_to_english_keywords(user_input), "posts_to_collect": 10, "reason": "기본 번역"}]

def translate_to_english_keywords(korean_input):
    """한국어 키워드를 영어로 변환"""
    # 주요 키워드 매핑
    keyword_mapping = {
        "애플": "Apple",
        "주가": "stock price",
        "전망": "outlook forecast",
        "삼성": "Samsung",
        "네이버": "Naver",
        "카카오": "Kakao",
        "LG": "LG",
        "현대": "Hyundai",
        "기아": "Kia",
        "SK": "SK",
        "분석": "analysis",
        "투자": "investment",
        "수익": "profit earnings",
        "실적": "performance earnings",
        "매출": "revenue sales",
        "배당": "dividend",
        "상승": "rise increase",
        "하락": "fall decrease",
        "예측": "prediction forecast",
        "전망": "outlook forecast",
        "뉴스": "news",
        "발표": "announcement",
        "실적": "earnings results"
    }
    
    # 한국어 키워드를 영어로 변환
    english_keywords = []
    for word in korean_input.split():
        if word in keyword_mapping:
            english_keywords.append(keyword_mapping[word])
        else:
            english_keywords.append(word)
    
    return " ".join(english_keywords)

def weighted_search(user_input=None):
    """가중치 기반 검색 - 중요도 순위별 게시물 수집"""
    reddit = RedditService()
    
    if not reddit.reddit:
        print("❌ Reddit 서비스 초기화 실패!")
        return
    
    # 사용자 입력이 있으면 키워드 생성, 없으면 기본값 사용
    if user_input:
        # GPT-4를 사용하여 키워드 확장
        print(f"🤖 GPT-4로 키워드 확장 중...")
        search_keywords = expand_keywords_with_gpt4(user_input)
    else:
        # 기본 트럼프-머스크 키워드
        search_keywords = [
            {
                "rank": 1,
                "query": "Trump Musk conflict 2025",
                "posts_to_collect": 20,
                "reason": "최신 갈등 상황을 직접적으로 다루는 키워드"
            },
            {
                "rank": 2,
                "query": "Musk America Party Trump",
                "posts_to_collect": 15,
                "reason": "머스크의 새로운 정당 창당과 트럼프와의 대립"
            },
            {
                "rank": 3,
                "query": "Trump vs Elon Musk feud",
                "posts_to_collect": 12,
                "reason": "두 인물 간 불화와 논쟁"
            },
            {
                "rank": 4,
                "query": "Musk criticizes Trump GOP",
                "posts_to_collect": 8,
                "reason": "머스크의 트럼프/공화당 비판"
            },
            {
                "rank": 5,
                "query": "Trump Musk relationship news",
                "posts_to_collect": 5,
                "reason": "관계 변화에 대한 일반적 뉴스"
            }
        ]
    
    topic = user_input if user_input else "Trump vs Musk"
    print(f"🔍 {topic} 가중치 검색")
    print("📊 키워드별 중요도 및 수집 계획:")
    print("="*70)
    for kw in search_keywords:
        print(f"{kw['rank']}순위: \"{kw['query']}\" - {kw['posts_to_collect']}개")
        print(f"   이유: {kw['reason']}")
    print(f"\n총 목표 수집량: {sum(kw['posts_to_collect'] for kw in search_keywords)}개")
    print("="*70)
    
    all_posts_by_keyword = {}
    all_posts_combined = []
    seen_ids = set()
    
    for keyword_info in search_keywords:
        query = keyword_info['query']
        target_count = keyword_info['posts_to_collect']
        keyword_posts = []
        
        print(f"\n[{keyword_info['rank']}순위] '{query}' 검색 중... (목표: {target_count}개)")
        
        # 다양한 정렬 방식으로 검색하여 목표 개수 달성
        for sort_method in ['hot', 'relevance', 'top']:
            if len(keyword_posts) >= target_count:
                break
                
            try:
                posts = reddit.search_posts(query, limit=20, sort=sort_method)
                
                for post in posts:
                    if len(keyword_posts) >= target_count:
                        break
                        
                    if post.post_id not in seen_ids:
                        seen_ids.add(post.post_id)
                        
                        try:
                            submission = reddit.reddit.submission(id=post.post_id)
                            
                            # 점수 20 이상인 게시물만
                            if submission.score >= 20:
                                # 댓글 수집 (상위 5개)
                                submission.comments.replace_more(limit=0)
                                top_comments = []
                                
                                comment_count = 0
                                for comment in sorted(submission.comments.list()[:20], 
                                                    key=lambda x: x.score if hasattr(x, 'score') else 0, 
                                                    reverse=True):
                                    if hasattr(comment, 'body') and comment_count < 5:
                                        top_comments.append({
                                            "author": str(comment.author) if comment.author else "[deleted]",
                                            "score": comment.score,
                                            "body": comment.body,
                                            "created_utc": comment.created_utc
                                        })
                                        comment_count += 1
                                
                                post_data = {
                                    "title": submission.title,
                                    "post_id": submission.id,
                                    "subreddit": submission.subreddit.display_name,
                                    "author": str(submission.author) if submission.author else "[deleted]",
                                    "score": submission.score,
                                    "upvote_ratio": submission.upvote_ratio,
                                    "num_comments": submission.num_comments,
                                    "created_utc": submission.created_utc,
                                    "url": f"https://reddit.com{submission.permalink}",
                                    "selftext": submission.selftext if submission.is_self else "",
                                    "link_url": submission.url if not submission.is_self else "",
                                    "top_comments": top_comments,
                                    "keyword_rank": keyword_info['rank'],
                                    "search_query": query,
                                    "sort_method": sort_method
                                }
                                
                                keyword_posts.append(post_data)
                                all_posts_combined.append(post_data)
                                print(f"  ✓ [{submission.score}점] {submission.title[:50]}...")
                                
                        except Exception as e:
                            continue
                        
            except Exception as e:
                print(f"  ❌ 오류: {e}")
            
            # API 제한 방지
            time.sleep(0.5)
        
        # 키워드별 결과 저장
        all_posts_by_keyword[query] = {
            "rank": keyword_info['rank'],
            "reason": keyword_info['reason'],
            "target_count": target_count,
            "actual_count": len(keyword_posts),
            "posts": sorted(keyword_posts, key=lambda x: x['score'], reverse=True)
        }
        
        print(f"  수집 완료: {len(keyword_posts)}개 / 목표 {target_count}개")
    
    # 전체 게시물 점수순 정렬
    all_posts_combined.sort(key=lambda x: x['score'], reverse=True)
    
    # 통계 정보
    total_target = sum(kw['posts_to_collect'] for kw in search_keywords)
    print(f"\n📊 전체 수집 통계:")
    print(f"  - 총 게시물: {len(all_posts_combined)}개")
    print(f"  - 목표 달성률: {len(all_posts_combined)/total_target*100:.1f}%")
    
    print(f"\n📍 키워드별 수집 결과:")
    for query, data in all_posts_by_keyword.items():
        print(f"  [{data['rank']}순위] {query}: {data['actual_count']}개/{data['target_count']}개")
    
    # 저장
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_data = {
        "topic": topic,
        "search_time": datetime.now().isoformat(),
        "total_posts": len(all_posts_combined),
        "collection_strategy": "키워드 중요도별 가중치 적용",
        "keywords_by_rank": search_keywords,
        "results_by_keyword": all_posts_by_keyword,
        "all_posts_combined": all_posts_combined
    }
    
    # 스크립트 위치에서 프로젝트 루트 찾기
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    reports_dir = os.path.join(project_root, "reports", "raw_data")
    
    os.makedirs(reports_dir, exist_ok=True)
    # 파일명을 주제에 맞게 생성 (공백은 언더스코어로 변경)
    safe_topic = topic.replace(' ', '_').replace(',', '_').lower()[:50]  # 최대 50자
    filename = os.path.join(reports_dir, f"weighted_search_{safe_topic}_{timestamp}.json")
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 가중치 검색 완료!")
    print(f"💾 저장: {filename}")
    
    # TOP 5 미리보기
    print("\n🔥 전체 TOP 5 핫 게시물:")
    for i, post in enumerate(all_posts_combined[:5], 1):
        print(f"\n{i}. [{post['score']}점] {post['title']}")
        print(f"   키워드 순위: {post['keyword_rank']}순위 | r/{post['subreddit']}")
    
    return filename

if __name__ == "__main__":
    # 명령줄 인자 확인
    if len(sys.argv) > 1:
        user_input = sys.argv[1]
        weighted_search(user_input)
    else:
        weighted_search()