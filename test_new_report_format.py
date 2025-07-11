import requests
import json
import time

# API 베이스 URL
BASE_URL = "http://localhost:8000/api/v1"

# 테스트 데이터
test_data = {
    "query": "애플 비전프로",
    "sources": ["reddit"],
    "length": "moderate",
    "user_nickname": "rex",
    "session_id": f"test_session_{int(time.time())}",
    "push_token": "expo-go-dummy-token"
}

print("=" * 50)
print("새로운 보고서 형식 테스트")
print("=" * 50)

print("\n1. 보고서 생성 요청...")
print(f"   검색어: {test_data['query']}")
print(f"   사용자: {test_data['user_nickname']}")

response = requests.post(f"{BASE_URL}/search", json=test_data, timeout=300)

if response.status_code == 200:
    result = response.json()
    print(f"\n✅ 보고서 생성 성공!")
    
    # 생성된 보고서 내용 확인
    if 'report' in result and result['report']:
        print(f"\n📄 보고서 요약:")
        print(f"   {result['report']['summary'][:100]}...")
        
        print(f"\n📝 보고서 본문 (처음 500자):")
        print("-" * 50)
        print(result['report']['full_report'][:500])
        print("-" * 50)
        
        # 각주 패턴 확인
        import re
        full_report = result['report']['full_report']
        
        # [숫자] 형식의 각주 찾기
        simple_footnotes = re.findall(r'\[(\d+)\](?!\()', full_report)
        # [숫자](URL) 형식의 각주 찾기
        url_footnotes = re.findall(r'\[(\d+)\]\(https?://[^\)]+\)', full_report)
        
        print(f"\n📌 각주 분석:")
        print(f"   - 단순 각주 [숫자]: {len(simple_footnotes)}개 발견")
        if simple_footnotes:
            print(f"     예시: {simple_footnotes[:5]}")
        print(f"   - URL 포함 각주 [숫자](URL): {len(url_footnotes)}개 발견")
        if url_footnotes:
            print(f"     예시: {url_footnotes[:2]}")
    
    # Supabase에서 보고서 조회
    print("\n\n2. 저장된 보고서 확인...")
    time.sleep(2)  # 저장 완료 대기
    
    reports_response = requests.get(f"{BASE_URL}/reports/{test_data['user_nickname']}?limit=1")
    
    if reports_response.status_code == 200:
        reports_data = reports_response.json()
        if reports_data['success'] and reports_data['reports']:
            latest_report = reports_data['reports'][0]
            report_id = latest_report['id']
            print(f"✅ 최신 보고서 ID: {report_id}")
            
            # 보고서 링크 조회
            print("\n3. 보고서 링크 조회...")
            links_response = requests.get(f"{BASE_URL}/report/{report_id}/links")
            
            if links_response.status_code == 200:
                links_data = links_response.json()
                if links_data['success']:
                    links = links_data['links']
                    print(f"\n✅ 링크 {len(links)}개 저장됨!")
                    
                    print("\n📎 저장된 링크 정보:")
                    print("-" * 80)
                    for link in links[:5]:  # 처음 5개만
                        print(f"\n각주 [{link['footnote_number']}]")
                        print(f"  URL: {link['url']}")
                        print(f"  제목: {link.get('title', 'N/A')}")
                        print(f"  추천수: {link.get('score', 0)}")
                        print(f"  댓글수: {link.get('comments', 0)}")
                        print(f"  서브레딧: r/{link.get('subreddit', 'N/A')}")
                        
                        if link.get('created_utc'):
                            hours_ago = int((time.time() - link['created_utc']) / 3600)
                            print(f"  작성시간: {hours_ago}시간 전")
                else:
                    print("❌ 링크 조회 실패:", links_data.get('error'))
            else:
                print(f"❌ 링크 조회 API 오류: {links_response.status_code}")
                print(links_response.text)
        else:
            print("❌ 보고서가 없습니다.")
    else:
        print(f"❌ 보고서 목록 조회 실패: {reports_response.status_code}")
else:
    print(f"❌ 보고서 생성 실패: {response.status_code}")
    print(response.text)

print("\n" + "=" * 50)
print("테스트 완료")
print("=" * 50)