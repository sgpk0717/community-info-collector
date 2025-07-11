from openai import OpenAI
from app.core.config import settings
import os

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# 테스트 게시물 데이터
test_posts = """
[게시물 1 - reddit]
제목: Tesla stock drops 7% after Musk's political announcement
작성자: investor123
내용: Tesla stock fell 7% in pre-market trading after CEO Elon Musk announced his political party plans...
추천수: 1234
댓글수: 567
서브레딧: r/stocks

[게시물 2 - reddit]
제목: Tesla Q4 earnings miss expectations
작성자: analyst456
내용: Tesla reported Q4 earnings that missed Wall Street expectations, with revenue down 13.5%...
추천수: 890
댓글수: 234
서브레딧: r/investing

[게시물 3 - reddit]
제목: Why I'm buying more Tesla stock
작성자: bullish789
내용: Despite the recent volatility, I believe Tesla's fundamentals remain strong...
추천수: 456
댓글수: 123
서브레딧: r/teslamotors
"""

# 강화된 프롬프트
system_prompt = """당신은 전문적인 투자 분석가입니다. 
주어진 소셜 미디어 게시물을 분석하여 보고서를 작성해주세요.

**중요: 게시물을 참조할 때는 반드시 [1], [2], [3] 형식의 각주를 사용해야 합니다.**

예시:
- "테슬라 주가가 7% 하락했습니다[1]."
- "수익이 예상치를 하회했습니다[2]."
- "일부 투자자들은 여전히 낙관적입니다[3]."

절대로 다음과 같은 형식은 사용하지 마세요:
- [게시물 1] 
- [reddit 1]
- [뉴스 1]
- [루머 1]"""

user_prompt = f"""다음 게시물들을 분석하여 간단한 요약을 작성하세요:

{test_posts}

요약에서 각 게시물을 참조할 때는 반드시 [1], [2], [3] 형식의 각주를 사용하세요.
200자 정도로 작성해주세요."""

print("OpenAI GPT-4 직접 테스트")
print("=" * 50)

try:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        max_tokens=500
    )
    
    result = response.choices[0].message.content
    print("\n생성된 보고서:")
    print("-" * 50)
    print(result)
    print("-" * 50)
    
    # 각주 분석
    import re
    footnotes = re.findall(r'\[(\d+)\]', result)
    print(f"\n발견된 각주: {footnotes}")
    
except Exception as e:
    print(f"오류: {e}")