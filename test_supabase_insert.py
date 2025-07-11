#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/seonggukpark/community-info-collector')

from app.services.supabase_reports_service import supabase_reports_service
import asyncio

async def test_supabase_insert():
    """Supabase에 테스트 보고서 삽입"""
    
    test_report = {
        "user_nickname": "test_user",
        "query_text": "테스트 키워드",
        "full_report": "이것은 테스트 보고서입니다. " * 50,  # 긴 텍스트
        "summary": "테스트 요약",
        "posts_collected": 10,
        "report_length": "moderate",
        "session_id": "test_session_123"
    }
    
    print("🚀 Supabase에 테스트 보고서 저장 중...")
    result = await supabase_reports_service.save_report(test_report)
    
    if result["success"]:
        print("✅ 보고서 저장 성공!")
        print(f"보고서 ID: {result['report_id']}")
        
        # 저장된 보고서 조회 테스트
        print("\n📖 저장된 보고서 조회 중...")
        reports_result = await supabase_reports_service.get_user_reports("test_user")
        
        if reports_result["success"]:
            print(f"✅ 조회 성공! 총 {reports_result['count']}개 보고서 발견")
            for report in reports_result["data"]:
                print(f"- {report['query_text']} ({report['created_at']})")
        else:
            print(f"❌ 조회 실패: {reports_result['error']}")
    else:
        print(f"❌ 보고서 저장 실패: {result['error']}")

if __name__ == "__main__":
    asyncio.run(test_supabase_insert())