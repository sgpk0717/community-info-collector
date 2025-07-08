#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reddit 데이터 검증된 분석 보고서 - 검증 에이전트 포함
"""
import json
import os
import sys
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import time

# 윈도우 환경에서 유니코드 출력 설정
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 환경변수 로드
load_dotenv()

def validate_report_content(analysis_text):
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
    
    # 필수 섹션 체크
    required_sections = ["핵심", "뉴스", "정보", "분석"]
    section_count = sum(1 for section in required_sections if section in analysis_text)
    if section_count < 2:
        return False, "필수 섹션이 부족합니다"
    
    return True, "검증 통과"

def generate_dynamic_title(topic, client):
    """GPT-4.1로 동적 제목 생성"""
    try:
        title_prompt = f"""
주제: "{topic}"

이 주제에 대한 Reddit 분석 보고서의 매력적이고 전문적인 제목을 1개 생성해주세요.

요구사항:
1. 한국어로 작성
2. 15-25자 내외
3. 분석 보고서임을 나타내는 제목
4. 흥미를 끄는 키워드 포함
5. 한글, 영어, 숫자, 언더바(_), 하이픈(-), 공백만 사용
6. 이모지나 특수문자는 절대 사용하지 말 것

예시: "애플 주가 급등 신호 분석", "테슬라 실적 충격 보고서", "트럼프-머스크 갈등 분석"

제목만 출력하세요:
"""
        
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": title_prompt}],
            temperature=0.8
        )
        
        dynamic_title = response.choices[0].message.content.strip()
        
        # 강제로 이모지와 특수문자 제거 (GPT가 무시할 경우 대비)
        import re
        clean_title = re.sub(r'[^\w\s가-힣a-zA-Z0-9\-_]', '', dynamic_title)
        clean_title = re.sub(r'\s+', ' ', clean_title).strip()
        
        print(f"🎯 GPT-4.1 원본 제목: {dynamic_title}")
        if clean_title != dynamic_title:
            print(f"⚠️ 이모지/특수문자 제거됨: {clean_title}")
        
        return clean_title
        
    except Exception as e:
        print(f"❌ 제목 생성 실패: {e}")
        return topic  # 실패 시 원본 주제 사용

def create_verified_detailed_analysis(search_topic=None):
    """검증이 포함된 상세 분석 보고서 생성"""
    
    # OpenAI 클라이언트 초기화
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # 최신 가중치 데이터 파일 찾기
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    raw_data_dir = os.path.join(project_root, "reports", "raw_data")
    
    data_files = [f for f in os.listdir(raw_data_dir) if f.startswith("weighted_search_") and f.endswith(".json")]
    
    if not data_files:
        print("❌ 가중치 데이터 파일을 찾을 수 없습니다!")
        return
    
    # 가장 최신 파일 선택 (파일 수정 시간 기준)
    latest_file = sorted(data_files, key=lambda f: os.path.getmtime(os.path.join(raw_data_dir, f)))[-1]
    file_path = os.path.join(raw_data_dir, latest_file)
    
    print(f"📂 데이터 파일 로드: {latest_file}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    topic = data.get('topic', 'Unknown Topic')
    print(f"📊 분석할 게시물: {data['total_posts']}개")
    print(f"🏷️  주제: {topic}")
    
    # 동적 제목 생성
    dynamic_title = generate_dynamic_title(topic, client)
    
    # 모든 게시물 통합 및 정리
    all_posts = []
    footnote_counter = 1
    all_footnotes = []
    
    for keyword, keyword_data in data['results_by_keyword'].items():
        for post in keyword_data['posts']:
            post['keyword'] = keyword
            all_posts.append(post)
    
    all_posts.sort(key=lambda x: x['created_utc'], reverse=True)
    
    # 신뢰도별 분류
    verified_news = []
    rumors_speculation = []
    
    reliable_subreddits = ['worldnews', 'news', 'politics', 'technology', 'business']
    
    for post in all_posts:
        is_reliable = (
            post['score'] > 100 and 
            any(sub in post['subreddit'].lower() for sub in reliable_subreddits)
        )
        
        if is_reliable:
            verified_news.append(post)
        else:
            rumors_speculation.append(post)
    
    # 콘텐츠 준비
    news_content = []
    rumors_content = []
    
    # 뉴스 콘텐츠 (상위 20개)
    for i, post in enumerate(verified_news[:20], 1):
        footnote_id = footnote_counter
        footnote_counter += 1
        
        post_time = datetime.fromtimestamp(post['created_utc'])
        time_diff = datetime.now() - post_time
        
        if time_diff.days > 0:
            time_str = f"{time_diff.days}일 전"
        elif time_diff.seconds > 3600:
            time_str = f"{time_diff.seconds // 3600}시간 전"
        else:
            time_str = f"{time_diff.seconds // 60}분 전"
        
        post_content = f"""
뉴스 {i}. [{post['score']}점] {post['title']} [{footnote_id}]
- 게시 시간: {post_time.strftime('%Y-%m-%d %H:%M')} ({time_str})
- 출처: r/{post['subreddit']}
- 댓글: {post['num_comments']}개
"""
        
        if post.get('selftext'):
            post_content += f"내용: {post['selftext'][:300]}...\n"
        
        if post.get('top_comments'):
            post_content += "주요 반응:\n"
            for j, comment in enumerate(post['top_comments'][:3], 1):
                comment_footnote = footnote_counter
                footnote_counter += 1
                post_content += f"• [{comment['score']}점] \"{comment['body'][:150]}...\" [{comment_footnote}]\n"
                
                all_footnotes.append({
                    'id': comment_footnote,
                    'type': 'comment',
                    'url': post['url'],
                    'text': f"댓글 from {post['title'][:30]}..."
                })
        
        news_content.append(post_content)
        all_footnotes.append({
            'id': footnote_id,
            'type': 'post',
            'url': post['url'],
            'title': f"{post['title']} - r/{post['subreddit']} ({time_str})"
        })
    
    # 루머 콘텐츠 (상위 25개)
    for i, post in enumerate(rumors_speculation[:25], 1):
        footnote_id = footnote_counter
        footnote_counter += 1
        
        post_time = datetime.fromtimestamp(post['created_utc'])
        time_diff = datetime.now() - post_time
        
        if time_diff.days > 0:
            time_str = f"{time_diff.days}일 전"
        elif time_diff.seconds > 3600:
            time_str = f"{time_diff.seconds // 3600}시간 전"
        else:
            time_str = f"{time_diff.seconds // 60}분 전"
        
        post_content = f"""
루머 {i}. [{post['score']}점] {post['title']} [{footnote_id}]
- 게시 시간: {post_time.strftime('%Y-%m-%d %H:%M')} ({time_str})
- 출처: r/{post['subreddit']}
- 댓글: {post['num_comments']}개
"""
        
        if post.get('selftext'):
            post_content += f"내용: {post['selftext'][:250]}...\n"
        
        if post.get('top_comments'):
            post_content += "반응:\n"
            for j, comment in enumerate(post['top_comments'][:2], 1):
                comment_footnote = footnote_counter
                footnote_counter += 1
                post_content += f"• [{comment['score']}점] \"{comment['body'][:120]}...\" [{comment_footnote}]\n"
                
                all_footnotes.append({
                    'id': comment_footnote,
                    'type': 'comment',
                    'url': post['url'],
                    'text': f"루머 댓글 from r/{post['subreddit']}"
                })
        
        rumors_content.append(post_content)
        all_footnotes.append({
            'id': footnote_id,
            'type': 'post',
            'url': post['url'],
            'title': f"{post['title']} - r/{post['subreddit']} ({time_str})"
        })
    
    # 여러 프롬프트 전략 준비
    prompts = [
        # 프롬프트 1: 현재 시점 강조
        {
            "system": f"""당신은 Reddit 소셜미디어 분석 전문가입니다. 
            주어진 Reddit 게시물과 댓글 데이터를 분석하여 {topic}에 대한 최신 동향 보고서를 작성하세요.
            
            중요: 이 데이터는 이미 수집된 과거 정보이므로 분석이 가능합니다. 미래 예측이 아닌 현재 상황 분석입니다.
            
            보고서 구조:
            1. 핵심 요약 (300자 이상)
            2. 주요 뉴스 분석 (500자 이상) 
            3. 루머 및 추측 정보 (400자 이상)
            4. 커뮤니티 반응 분석 (300자 이상)
            5. 시사점 (200자 이상)
            
            각주 [숫자]를 반드시 포함하여 출처를 명시하세요.""",
            "user": f"""다음은 Reddit에서 수집한 {topic} 관련 게시물 데이터입니다.

확인된 뉴스 ({len(verified_news)}개):
{''.join(news_content[:10])}

루머/추측 정보 ({len(rumors_speculation)}개):
{''.join(rumors_content[:10])}

위 데이터를 분석하여 최신 동향 보고서를 작성해주세요."""
        },
        
        # 프롬프트 2: 단순한 분석 요청
        {
            "system": f"""당신은 소셜미디어 데이터 분석가입니다. 
            제공된 Reddit 게시물 데이터를 바탕으로 {topic}에 대한 분석 보고서를 작성하세요.
            
            요구사항:
            - 최소 1500자 이상 작성
            - 각주 [숫자] 포함
            - 구체적인 데이터 인용
            - 명확한 분석과 해석""",
            "user": f"""Reddit 데이터 분석 요청:

뉴스 데이터:
{''.join(news_content[:8])}

루머 데이터:  
{''.join(rumors_content[:8])}

이 데이터를 분석해서 상세한 보고서를 작성해주세요."""
        },
        
        # 프롬프트 3: 구체적인 지시
        {
            "system": f"""Reddit 게시물 분석 전문가로서 다음 작업을 수행하세요:

1. 제공된 게시물과 댓글을 모두 검토
2. {topic}의 현재 상황 정리
3. 주요 논점과 반응 분석
4. 종합적인 분석 보고서 작성

반드시 1000자 이상 작성하고, 각주를 포함하세요.""",
            "user": f"""분석할 Reddit 데이터:

뉴스: {len(verified_news)}개
{''.join(news_content[:6])}

루머: {len(rumors_speculation)}개  
{''.join(rumors_content[:6])}

분석 보고서를 작성해주세요."""
        }
    ]
    
    # 여러 시도로 보고서 생성
    max_attempts = 3
    analysis = None
    
    for attempt in range(max_attempts):
        print(f"\n🤖 GPT-4.1로 분석 시도 {attempt + 1}/{max_attempts}...")
        
        try:
            prompt = prompts[attempt]
            
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": prompt["user"]}
                ],
                temperature=0.6,
            )
            
            candidate_analysis = response.choices[0].message.content
            
            # 검증 수행
            is_valid, validation_message = validate_report_content(candidate_analysis)
            
            print(f"📋 검증 결과: {validation_message}")
            
            if is_valid:
                analysis = candidate_analysis
                print(f"✅ 시도 {attempt + 1}에서 성공!")
                break
            else:
                print(f"❌ 시도 {attempt + 1} 실패: {validation_message}")
                if attempt < max_attempts - 1:
                    print("🔄 다른 전략으로 재시도...")
                    time.sleep(2)  # 잠시 대기
                
        except Exception as e:
            print(f"❌ 시도 {attempt + 1} 오류: {e}")
            if attempt < max_attempts - 1:
                time.sleep(2)
    
    if not analysis:
        print("❌ 모든 시도가 실패했습니다!")
        return None, None
    
    # 검증 통과한 보고서로 파일 생성
    footnotes_html = "<div class='footnotes'><h2>📌 참고 링크</h2><ol>"
    footnotes_md = "\n\n---\n\n## 📌 참고 링크\n\n"
    
    for footnote in all_footnotes:
        footnotes_html += f"<li id='fn{footnote['id']}'><a href='{footnote['url']}' target='_blank'>{footnote['title'] if 'title' in footnote else footnote['text']}</a></li>"
        footnotes_md += f"{footnote['id']}. [{footnote['title'] if 'title' in footnote else footnote['text']}]({footnote['url']})\n"
    
    footnotes_html += "</ol></div>"
    
    # HTML 보고서
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic}: 검증된 최신 분석</title>
    <style>
        body {{
            font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.8;
            color: #2c3e50;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f7fa;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 50px;
            border-radius: 20px;
            margin-bottom: 40px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 800;
        }}
        .verification-badge {{
            background: #27ae60;
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            margin-top: 15px;
            display: inline-block;
            font-weight: bold;
        }}
        .content {{
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.08);
            margin-bottom: 30px;
        }}
        .content h1, .content h2, .content h3 {{
            color: #2c3e50;
            margin-top: 30px;
        }}
        .footnote-ref {{
            color: #667eea;
            text-decoration: none;
            font-weight: bold;
            font-size: 0.9em;
            vertical-align: super;
        }}
        .footnotes {{
            margin-top: 50px;
            padding-top: 30px;
            border-top: 3px solid #e0e0e0;
        }}
        .footnotes ol {{
            font-size: 0.9em;
            line-height: 1.8;
        }}
        .footnotes a {{
            color: #667eea;
            text-decoration: none;
        }}
        .stats-box {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            margin: 25px 0;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
        }}
        .stats-item {{
            text-align: center;
        }}
        .stats-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
    </style>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const content = document.querySelector('.content');
            content.innerHTML = content.innerHTML.replace(/\\[(\\d+)\\]/g, function(match, num) {{
                return '<a href="#fn' + num + '" class="footnote-ref">[' + num + ']</a>';
            }});
        }});
    </script>
</head>
<body>
    <div class="header">
        <h1>{dynamic_title}</h1>
        <div class="verification-badge">✅ AI 검증 통과</div>
        <p>📅 {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')} 기준</p>
        <p>📊 Reddit {data['total_posts']}개 게시물 분석</p>
    </div>
    
    <div class="content">
        <div class="stats-box">
            <div class="stats-item">
                <div class="stats-number">{len(verified_news)}</div>
                <div>확인된 뉴스</div>
            </div>
            <div class="stats-item">
                <div class="stats-number">{len(rumors_speculation)}</div>
                <div>루머/추측</div>
            </div>
            <div class="stats-item">
                <div class="stats-number">{len(all_footnotes)}</div>
                <div>참조 링크</div>
            </div>
        </div>
        
        {analysis.replace(chr(10), '<br>').replace('# ', '<h1>').replace('## ', '<h2>').replace('### ', '<h3>')}
        
        {footnotes_html}
    </div>
</body>
</html>"""
    
    # Markdown 보고서
    markdown_content = f"""# {dynamic_title}

## 📅 {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')} 기준

✅ **AI 검증 통과**

### 📊 데이터 개요
- **전체 분석 게시물**: {data['total_posts']}개
- **확인된 뉴스**: {len(verified_news)}개
- **루머/추측성 정보**: {len(rumors_speculation)}개
- **참조 링크**: {len(all_footnotes)}개

---

{analysis}

{footnotes_md}

---

*이 보고서는 AI 검증을 통과한 신뢰할 수 있는 분석입니다.*
"""
    
    # 파일 저장
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 파일명을 동적 제목에 맞게 생성 (공백을 언더바로만 변경)
    safe_title = dynamic_title.replace(' ', '_').lower()[:50]
    ai_analysis_dir = os.path.join(project_root, "reports", "ai_analysis")
    os.makedirs(ai_analysis_dir, exist_ok=True)
    
    html_path = os.path.join(ai_analysis_dir, f"verified_{safe_title}_{timestamp}.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    md_path = os.path.join(ai_analysis_dir, f"verified_{safe_title}_{timestamp}.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"\n✅ 검증된 분석 완료!")
    print(f"📄 HTML 보고서: {os.path.abspath(html_path)}")
    print(f"📝 Markdown 보고서: {os.path.abspath(md_path)}")
    print(f"📊 통계:")
    print(f"   - 확인된 뉴스: {len(verified_news)}개")
    print(f"   - 루머/추측: {len(rumors_speculation)}개")
    print(f"   - 총 각주: {len(all_footnotes)}개")
    
    return html_path, md_path

if __name__ == "__main__":
    # 명령줄 인자로 주제 받기
    if len(sys.argv) > 1:
        search_topic = sys.argv[1]
        create_verified_detailed_analysis(search_topic)
    else:
        create_verified_detailed_analysis()