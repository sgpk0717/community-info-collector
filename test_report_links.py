import requests
import json
import time

# API 베이스 URL
BASE_URL = "http://localhost:8000/api/v1"

# 테스트 데이터
test_data = {
    "query": "테슬라 주가",
    "sources": ["reddit"],
    "length": "moderate",
    "user_nickname": "test_user",
    "session_id": f"test_session_{int(time.time())}",
    "push_token": "expo-go-dummy-token"
}

print("1. 보고서 생성 요청...")
response = requests.post(f"{BASE_URL}/search", json=test_data)

if response.status_code == 200:
    result = response.json()
    print(f"✅ 보고서 생성 성공!")
    print(f"   - Response: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}...")
    
    # Supabase에서 보고서 목록 조회
    print("\n2. 사용자의 보고서 목록 조회...")
    reports_response = requests.get(f"{BASE_URL}/reports/{test_data['user_nickname']}")
    
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
                    print(f"✅ 링크 {len(links)}개 조회 성공!")
                    
                    # 링크 정보 출력
                    for i, link in enumerate(links[:5]):  # 처음 5개만
                        print(f"\n   링크 [{link['footnote_number']}]:")
                        print(f"   - URL: {link['url']}")
                        print(f"   - 제목: {link.get('title', 'N/A')[:50]}...")
                        print(f"   - 추천수: {link.get('score', 0)}")
                        print(f"   - 댓글수: {link.get('comments', 0)}")
                        print(f"   - 서브레딧: r/{link.get('subreddit', 'N/A')}")
                        
                        if link.get('created_utc'):
                            hours_ago = int((time.time() - link['created_utc']) / 3600)
                            print(f"   - 작성시간: {hours_ago}시간 전")
                else:
                    print("❌ 링크 조회 실패:", links_data.get('error'))
            else:
                print(f"❌ 링크 조회 API 오류: {links_response.status_code}")
        else:
            print("❌ 보고서가 없습니다.")
    else:
        print(f"❌ 보고서 목록 조회 실패: {reports_response.status_code}")
else:
    print(f"❌ 보고서 생성 실패: {response.status_code}")
    print(response.text)