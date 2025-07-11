#!/usr/bin/env python3
import requests
import json
import time
from datetime import datetime, timedelta

# API 엔드포인트
API_URL = "http://192.168.0.83:8000/api/v1/search"

# 테스트 케이스 1: 일회성 검색 (schedule_yn = N)
test_data_onetime = {
    "query": "Tesla news",
    "sources": ["reddit"],
    "length": "simple",
    "user_nickname": "testuser",
    "schedule_yn": "N"  # 일회성 분석
}

# 테스트 케이스 2: 스케줄링 검색 (schedule_yn = Y)
test_data_scheduled = {
    "query": "Tesla news",
    "sources": ["reddit"],
    "length": "simple",
    "user_nickname": "testuser",
    "schedule_yn": "Y",  # 스케줄링 분석
    "schedule_period": 60,  # 60분마다
    "schedule_count": 5,  # 5번 반복
    "schedule_start_time": (datetime.now() + timedelta(minutes=10)).isoformat()  # 10분 후 시작
}

def test_search_api(test_data, test_name):
    """검색 API 테스트"""
    print(f"\n{'='*60}")
    print(f"테스트: {test_name}")
    print(f"{'='*60}")
    print(f"테스트 데이터: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    print(f"API URL: {API_URL}")
    print("-" * 50)
    
    try:
        # API 호출
        print("API 호출 중...")
        response = requests.post(API_URL, json=test_data)
        
        # 응답 확인
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("성공! 응답 데이터:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return True
        else:
            print(f"실패: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("연결 실패: 백엔드 서버가 실행 중인지 확인하세요.")
        return False
    except Exception as e:
        print(f"오류 발생: {e}")
        return False

def test_nickname_duplicate_check():
    """닉네임 중복 체크 API 테스트"""
    print(f"\n{'='*60}")
    print("테스트: 닉네임 중복 체크")
    print(f"{'='*60}")
    
    # 닉네임 중복 체크 API
    check_url = "http://192.168.0.83:8000/api/v1/users/check-nickname"
    
    # 테스트 케이스 1: 존재하지 않는 닉네임
    nickname = "newuser123"
    print(f"\n1. 존재하지 않는 닉네임 확인: {nickname}")
    try:
        response = requests.get(f"{check_url}/{nickname}")
        print(f"상태 코드: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"결과: {json.dumps(result, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"오류: {e}")
    
    # 테스트 케이스 2: 존재하는 닉네임 (testuser)
    nickname = "testuser"
    print(f"\n2. 존재하는 닉네임 확인: {nickname}")
    try:
        response = requests.get(f"{check_url}/{nickname}")
        print(f"상태 코드: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"결과: {json.dumps(result, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    # 백엔드 서버가 시작될 때까지 잠시 대기
    print("백엔드 서버 연결 테스트...")
    time.sleep(2)
    
    # 1. 일회성 검색 테스트
    test_search_api(test_data_onetime, "일회성 검색 (schedule_yn=N)")
    
    # 2. 스케줄링 검색 테스트 (실패 예상 - 필수 파라미터 없음)
    test_search_api({
        "query": "Tesla news",
        "sources": ["reddit"],
        "length": "simple",
        "user_nickname": "testuser",
        "schedule_yn": "Y"  # 필수 파라미터 없이
    }, "스케줄링 검색 - 필수 파라미터 누락 (실패 예상)")
    
    # 3. 스케줄링 검색 테스트 (성공 예상)
    test_search_api(test_data_scheduled, "스케줄링 검색 (schedule_yn=Y)")
    
    # 4. 닉네임 중복 체크 테스트
    test_nickname_duplicate_check()