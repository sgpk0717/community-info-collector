import requests
import json
import time

# API 베이스 URL
BASE_URL = "http://localhost:8000/api/v1"

# 디버그용 테스트 데이터
test_data = {
    "query": "테슬라 주가",
    "sources": ["reddit"],
    "length": "simple",  # 짧은 보고서로
    "user_nickname": "rex",
    "session_id": f"debug_session_{int(time.time())}",
    "push_token": "expo-go-dummy-token"
}

print("LLM 입력 디버그 테스트")
print("=" * 50)

# 백엔드 로그를 보기 위해 디버그 모드로 실행
print("\n백엔드 로그를 확인하세요...")
print("검색 시작...")

response = requests.post(f"{BASE_URL}/search", json=test_data, timeout=300)

if response.status_code == 200:
    result = response.json()
    print("\n✅ 보고서 생성 성공!")
    
    # 전체 응답 확인
    print("\n전체 응답 구조:")
    print(json.dumps(result, indent=2, ensure_ascii=False)[:1000])
    
    if 'report' in result and result['report']:
        full_report = result['report']['full_report']
        
        # 각주 패턴 찾기
        import re
        
        # 모든 대괄호 내용 찾기
        brackets = re.findall(r'\[([^\]]+)\]', full_report)
        print(f"\n대괄호 내용: {brackets[:10]}")
        
        # 숫자만 있는 각주 찾기
        simple_footnotes = re.findall(r'\[(\d+)\]', full_report)
        print(f"\n단순 각주 [숫자]: {simple_footnotes[:10]}")
        
        # 전체 보고서 출력
        print("\n전체 보고서:")
        print("=" * 80)
        print(full_report)
        print("=" * 80)
else:
    print(f"❌ 오류: {response.status_code}")
    print(response.text)