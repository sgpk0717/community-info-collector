#!/usr/bin/env python3
"""
스케줄 락 메커니즘 테스트
"""
import asyncio
from datetime import datetime
from app.services.supabase_schedule_service import supabase_schedule_service

async def test_schedule_lock():
    """스케줄 락 획득 테스트"""
    # 테스트할 스케줄 ID (실제 존재하는 ID로 변경 필요)
    schedule_id = "13"
    
    print(f"\n=== 스케줄 락 테스트 시작 ({datetime.now()}) ===\n")
    
    # 1. 첫 번째 락 획득 시도
    print("1. 첫 번째 락 획득 시도:")
    result1 = supabase_schedule_service.try_acquire_schedule_lock(schedule_id)
    print(f"   결과: {result1}")
    
    # 2. 두 번째 락 획득 시도 (실패해야 함)
    print("\n2. 두 번째 락 획득 시도 (이미 락이 걸려있어 실패해야 함):")
    result2 = supabase_schedule_service.try_acquire_schedule_lock(schedule_id)
    print(f"   결과: {result2}")
    
    # 3. 락 해제
    print("\n3. 락 해제:")
    release_result = supabase_schedule_service.mark_schedule_executing(schedule_id, False)
    print(f"   결과: {release_result}")
    
    # 4. 락 해제 후 다시 획득 시도
    print("\n4. 락 해제 후 다시 획득 시도:")
    result3 = supabase_schedule_service.try_acquire_schedule_lock(schedule_id)
    print(f"   결과: {result3}")
    
    # 5. 정리 (락 해제)
    print("\n5. 테스트 정리 (락 해제):")
    cleanup_result = supabase_schedule_service.mark_schedule_executing(schedule_id, False)
    print(f"   결과: {cleanup_result}")
    
    print("\n=== 테스트 완료 ===\n")

if __name__ == "__main__":
    asyncio.run(test_schedule_lock())