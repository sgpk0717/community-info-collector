import asyncio
from app.services.supabase_reports_service import SupabaseReportsService

async def check_supabase_data():
    service = SupabaseReportsService()
    
    # 최근 보고서 확인
    print("=== 최근 보고서 확인 ===")
    reports = await service.get_user_reports("rex", 5)
    
    if reports["success"]:
        print(f"보고서 {len(reports['data'])}개 발견")
        for i, report in enumerate(reports['data'][:2]):
            print(f"\n보고서 {i+1}:")
            print(f"  ID: {report['id']}")
            print(f"  제목: {report['query_text']}")
            print(f"  생성일: {report['created_at']}")
            print(f"  내용 (처음 200자): {report['full_report'][:200]}...")
            
            # 해당 보고서의 링크 확인
            print(f"\n=== 보고서 {report['id']} 링크 확인 ===")
            links = await service.get_report_links(report['id'])
            
            if links["success"]:
                print(f"링크 {len(links['data'])}개 발견")
                for link in links['data']:
                    print(f"  각주 [{link['footnote_number']}]: {link['url']}")
                    print(f"    제목: {link.get('title', 'N/A')}")
                    print(f"    추천: {link.get('score', 'N/A')}, 댓글: {link.get('comments', 'N/A')}")
                    print(f"    서브레딧: r/{link.get('subreddit', 'N/A')}")
            else:
                print(f"링크 조회 실패: {links['error']}")
    else:
        print(f"보고서 조회 실패: {reports['error']}")

if __name__ == "__main__":
    asyncio.run(check_supabase_data())