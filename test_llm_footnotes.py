#!/usr/bin/env python3
"""
Test script to diagnose footnote generation issues in LLM service
"""
import asyncio
from app.services.llm_service import LLMService
from app.schemas.schemas import PostBase

# Create mock posts with metadata
test_posts = [
    PostBase(
        source="reddit",
        post_id="test1",
        title="Tesla stock hits new high",
        content="Tesla stock reached a new high today after earnings announcement...",
        author="user1",
        url="https://reddit.com/r/teslamotors/post1",
        score=150,
        comments=45,
        created_utc=1702000000,
        subreddit="teslamotors"
    ),
    PostBase(
        source="reddit", 
        post_id="test2",
        title="Tesla quarterly earnings beat expectations",
        content="Tesla reported better than expected earnings for Q4...",
        author="user2", 
        url="https://reddit.com/r/stocks/post2",
        score=200,
        comments=67,
        created_utc=1702000100,
        subreddit="stocks"
    ),
    PostBase(
        source="reddit",
        post_id="test3", 
        title="Elon Musk comments on Tesla growth",
        content="Elon Musk tweeted about Tesla's future growth plans...",
        author="user3",
        url="https://reddit.com/r/elonmusk/post3",
        score=89,
        comments=23,
        created_utc=1702000200,
        subreddit="elonmusk"
    )
]

async def test_llm_footnotes():
    """Test LLM service footnote generation"""
    print("=== Testing LLM Service Footnote Generation ===")
    
    llm_service = LLMService()
    
    # Test with simple report
    print("\n1. Generating simple report...")
    result = await llm_service.generate_report(
        query="테슬라 주식",
        posts=test_posts,
        report_length="simple"
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
    else:
        print("\nNo post mappings found")
    
    # Analyze the issue
    print("\n=== Analysis ===")
    if footnotes:
        print(f"✓ Footnotes generated: {len(footnotes)}")
    else:
        print("✗ No footnotes generated - This is the problem!")
        
    print("\n=== Raw LLM Response Analysis ===")
    print(f"Report length: {len(result['full_report'])}")
    print("Contains [1]:", "[1]" in result['full_report'])
    print("Contains [2]:", "[2]" in result['full_report'])
    print("Contains [3]:", "[3]" in result['full_report'])
    
    return result

if __name__ == "__main__":
    asyncio.run(test_llm_footnotes())