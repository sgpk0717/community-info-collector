#!/usr/bin/env python3
"""
Debug the actual report generation process
"""
import asyncio
from app.services.supabase_reports_service import SupabaseReportsService
import re

async def debug_actual_report():
    """Debug the actual report to see what's happening"""
    service = SupabaseReportsService()
    
    # Get the most recent report
    reports = await service.get_user_reports("rex", 1)
    
    if reports["success"] and reports["data"]:
        report = reports["data"][0]
        print("=== Most Recent Report Analysis ===")
        print(f"Report ID: {report['id']}")
        print(f"Query: {report['query_text']}")
        print(f"Created: {report['created_at']}")
        print(f"Posts collected: {report['posts_collected']}")
        
        # Analyze the full report content
        full_report = report['full_report']
        print(f"\nFull Report Length: {len(full_report)}")
        
        # Check for footnotes
        footnotes = re.findall(r'\[(\d+)\]', full_report)
        print(f"Footnotes found: {footnotes}")
        
        # Show first 500 chars of report
        print(f"\nFirst 500 chars of report:")
        print(full_report[:500])
        
        # Check if there are any URLs in the report
        urls = re.findall(r'https?://[^\s\)]+', full_report)
        print(f"\nURLs found in report: {len(urls)}")
        for url in urls[:5]:  # Show first 5 URLs
            print(f"  - {url}")
        
        # Check the link extraction manually
        print(f"\n=== Manual Link Extraction Test ===")
        links = service._extract_links_from_report(full_report, [])
        print(f"Links extracted: {len(links)}")
        for link in links:
            print(f"  - [{link['footnote_number']}] {link['url']}")
        
        # Check if we can find the pattern the extraction is looking for
        print(f"\n=== Pattern Analysis ===")
        # Pattern 1: [number]
        pattern1 = r'\[(\d+)\]'
        matches1 = re.findall(pattern1, full_report)
        print(f"[number] pattern matches: {matches1}")
        
        # Pattern 2: [number](url)
        pattern2 = r'\[(\d+)\]\((https?://[^\)]+)\)'
        matches2 = re.findall(pattern2, full_report)
        print(f"[number](url) pattern matches: {len(matches2)}")
        
        return report
    else:
        print("No reports found")
        return None

if __name__ == "__main__":
    asyncio.run(debug_actual_report())