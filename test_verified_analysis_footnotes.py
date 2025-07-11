#!/usr/bin/env python3
"""
Test script to verify the updated VerifiedAnalysisService with footnote generation
"""
import asyncio
from app.services.verified_analysis_service import VerifiedAnalysisService
from app.schemas.schemas import PostBase

# Create test posts with metadata
test_posts = [
    PostBase(
        source="reddit",
        post_id="test1",
        title="Tesla stock performance Q4 2024",
        content="Tesla stock reached a new high today after earnings announcement. The company reported record revenues and strong growth in EV sales.",
        author="investor123",
        url="https://reddit.com/r/teslamotors/post1",
        score=250,
        comments=89,
        created_utc=1702000000,
        subreddit="teslamotors"
    ),
    PostBase(
        source="reddit", 
        post_id="test2",
        title="Elon Musk's latest tweet about Tesla",
        content="Elon Musk tweeted about Tesla's plans for expanding production capacity. The tweet caused a 5% stock price increase.",
        author="elonfan",
        url="https://reddit.com/r/stocks/post2",
        score=180,
        comments=45,
        created_utc=1702000100,
        subreddit="stocks"
    ),
    PostBase(
        source="reddit",
        post_id="test3", 
        title="Tesla recalls 100,000 vehicles",
        content="Tesla announced a recall of 100,000 vehicles due to software issues. This is expected to impact Q1 2025 deliveries.",
        author="teslaowner",
        url="https://reddit.com/r/news/post3",
        score=95,
        comments=156,
        created_utc=1702000200,
        subreddit="news"
    ),
    PostBase(
        source="reddit",
        post_id="test4",
        title="Tesla Cybertruck production delays",
        content="Reports suggest Tesla Cybertruck production is facing delays due to supply chain issues. Delivery dates may be pushed back.",
        author="cybertruck_fan",
        url="https://reddit.com/r/cybertruck/post4",
        score=67,
        comments=78,
        created_utc=1702000300,
        subreddit="cybertruck"
    ),
    PostBase(
        source="reddit",
        post_id="test5",
        title="Tesla AI Day announcements",
        content="Tesla's AI Day showcased new developments in autonomous driving. The company claims significant improvements in FSD beta.",
        author="airesearcher",
        url="https://reddit.com/r/technology/post5",
        score=134,
        comments=203,
        created_utc=1702000400,
        subreddit="technology"
    )
]

async def test_verified_analysis_footnotes():
    """Test VerifiedAnalysisService with footnote generation"""
    print("=== Testing VerifiedAnalysisService Footnote Generation ===")
    
    service = VerifiedAnalysisService()
    
    # Test with simple report
    print("\n1. Generating verified analysis report...")
    result = await service.generate_verified_report(
        query="테슬라 주식",
        posts=test_posts,
        report_length="moderate"
    )
    
    print(f"Summary: {result['summary']}")
    print(f"\nFull Report:\n{result['full_report']}")
    
    # Check for footnotes in the report
    import re
    footnotes = re.findall(r'\[(\d+)\]', result['full_report'])
    print(f"\nFootnotes found: {footnotes}")
    
    # Check post mappings 
    if 'post_mappings' in result:
        print(f"\nPost mappings: {len(result['post_mappings'])}")
        for mapping in result['post_mappings']:
            print(f"  [{mapping['footnote_number']}] {mapping['url']}")
            print(f"    Title: {mapping['title']}")
            print(f"    Score: {mapping['score']}, Comments: {mapping['comments']}")
            print(f"    Subreddit: r/{mapping['subreddit']}")
    else:
        print("\nNo post mappings found")
    
    # Analyze the results
    print("\n=== Analysis ===")
    if footnotes:
        print(f"✓ Footnotes generated: {len(footnotes)}")
        print(f"✓ Unique footnotes: {len(set(footnotes))}")
    else:
        print("✗ No footnotes generated")
    
    if 'post_mappings' in result and result['post_mappings']:
        print(f"✓ Post mappings generated: {len(result['post_mappings'])}")
        
        # Test if the Supabase system would work
        print("\n=== Supabase Integration Test ===")
        from app.services.supabase_reports_service import SupabaseReportsService
        supabase_service = SupabaseReportsService()
        
        # Test the link extraction logic
        extracted_links = supabase_service._extract_links_from_report(
            result['full_report'], 
            result['post_mappings']
        )
        print(f"Links that would be extracted: {len(extracted_links)}")
        for link in extracted_links:
            print(f"  [{link['footnote_number']}] {link['url']}")
    else:
        print("✗ No post mappings generated")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_verified_analysis_footnotes())