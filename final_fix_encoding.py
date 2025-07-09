#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

def fix_file_robust(filepath):
    """Fix Korean encoding with exact byte-level replacements."""
    
    # Read the file as raw bytes
    with open(filepath, 'rb') as f:
        content = f.read()
    
    # Define byte-level replacements for corrupted Korean text
    replacements = [
        # HomeScreen.tsx replacements
        (b"Alert.alert('L\xe0', '\xd0` \x8f\xf4\x0b| \x1c%t\xf88\xe4.');", 
         "Alert.alert('알림', '키워드를 입력해주세요.');".encode('utf-8')),
        
        (b"Alert.alert('$X', '\xc5\x93\xd7 \x13| >D  \xc5\xb5\x8f\x90.');", 
         "Alert.alert('오류', '사용자 정보를 찾을 수 없습니다.');".encode('utf-8')),
        
        (b"Alert.alert('1\xe1', '\xc8t D\xf8\xc8\xb5\x8f\x90!', [",
         "Alert.alert('성공', '분석이 완료되었습니다!', [".encode('utf-8')),
        
        (b"Alert.alert('$X', result.error || '\x08\xf8 \x1c(\x8f\x88\x8f\x90.');",
         "Alert.alert('오류', result.error || '분석에 실패했습니다.');".encode('utf-8')),
        
        (b"Alert.alert('$X', '\xc8 \x1c\xfc \x1c(\x8f\x88\x8f\x90.');",
         "Alert.alert('오류', '분석 중 오류가 발생했습니다.');".encode('utf-8')),
        
        (b">Reddit \x15\xf4 \x84\x1d</Text>",
         ">Reddit 분석</Text>".encode('utf-8')),
        
        (b"\\\xd3\xf8 \x1d| \x08\xf8<\\ \x1cX\xe0 \x88i\xf8\x93",
         "키워드로 커뮤니티를 분석하세요".encode('utf-8')),
        
        (b"\x14\xf8 8t",
         "보고서 길이".encode('utf-8')),
        
        (b'label="\xe5"',
         'label="간단"'.encode('utf-8')),
        
        (b'label="\x14\xf8"',
         'label="보통"'.encode('utf-8')),
        
        (b">\xe0 ...</Text>",
         ">분석 중...</Text>".encode('utf-8')),
        
        (b">\xe0 & \x89</Text>",
         ">분석 시작</Text>".encode('utf-8')),
        
        (b"Reddit\xd0\x1c \x15\xf4| \x18\xd1X\xe0 \x88\xb5\xc8\xe4...",
         "Reddit 커뮤니티를 분석하고 있습니다...".encode('utf-8')),
        
        (b"= Reddit \x80\xc9 ",
         "• Reddit 데이터 수집 중".encode('utf-8')),
        
        (b"=\x91 pt0 \xe0 ",
         "• 관련 게시물 분석 중".encode('utf-8')),
        
        (b"> GPT-4 \xe4 ",
         "• GPT-4 보고서 생성 중".encode('utf-8')),
        
        (b"=\xe4 \x84\xfc \x071 ",
         "• 최종 보고서 정리 중".encode('utf-8')),
        
        (b"\xe0 D\xc8",
         "분석 완료".encode('utf-8')),
        
        (b"\xe4 {(analysisResult.metadata.processingTime / 1000).toFixed(1)}",
         "소요시간 {(analysisResult.metadata.processingTime / 1000).toFixed(1)}초".encode('utf-8')),
        
        (b"Alert.alert('\xe4 \x15\xf8\xc5\x04 \x88\xfc \xd8\x7f UxX8\xe4')",
         "Alert.alert('전체 보고서는 보고서 탭에서 확인하세요')".encode('utf-8')),
        
        (b">\xe4 \x98\x10 \x100</Text>",
         ">전체 보기</Text>".encode('utf-8')),
        
        # ReportsScreen.tsx replacements
        (b"'\xf4 Ux',",
         "'삭제 확인',".encode('utf-8')),
        
        (b"'t \x88\xfc| \x18X\xdc\xa0\x95L?',",
         "'이 보고서를 삭제하시겠습니까?',".encode('utf-8')),
        
        (b"{ text: '\xd0', style: 'cancel' },",
         "{ text: '취소', style: 'cancel' },".encode('utf-8')),
        
        (b"text: '\xed',",
         "text: '삭제',".encode('utf-8')),
        
        (b"Alert.alert('1\xe1', '\x04\x88  \xf0\xc8\xb5\x8f\x90.');",
         "Alert.alert('성공', '보고서가 삭제되었습니다.');".encode('utf-8')),
        
        (b"return `${days}| `;",
         "return `${days}일 전`;".encode('utf-8')),
        
        (b"return `${hours}\xf8 `;",
         "return `${hours}시간 전`;".encode('utf-8')),
        
        (b"return `${minutes}\xfc `;",
         "return `${minutes}분 전`;".encode('utf-8')),
        
        (b" \xc4 \xb8\x04  \xc5\xb5\x8f\x90",
         "저장된 보고서가 없습니다".encode('utf-8')),
        
        (b"H \xfc\xf8 \x8f\xf4\x0b| \x89\xf8X\xe0 \x9dD \xdc\x91X8\xe4",
         "홈 화면에서 키워드를 분석해 보고서를 생성하세요".encode('utf-8')),
        
        (b">\xfc \xb8\x04</Text>",
         ">보고서 목록</Text>".encode('utf-8')),
        
        (b" {reports.length}X \xfc\x04   \xf0\x8f \x18\xb0\xa4",
         "{reports.length}개의 보고서가 저장되어 있습니다".encode('utf-8')),
        
        (b"Alert.alert('\xb8\xf4(', '\x04\x88  t\xe0\xd0\x10 \x8d\xf8\xc8\xb5\x8f\x90.');",
         "Alert.alert('복사됨', '보고서가 클립보드에 복사되었습니다.');".encode('utf-8')),
        
        (b"Alert.alert('\xf8 ', '\xe4  0\xc4@  D \x9c\xd0.');",
         "Alert.alert('공유', '공유 기능은 추후 추가 예정입니다.');".encode('utf-8')),
        
        (b">\xe4 </Text>",
         ">공유</Text>".encode('utf-8')),
        
        (b"\xe4 {(selectedReport.metadata.processingTime / 1000).toFixed(1)}",
         "소요시간 {(selectedReport.metadata.processingTime / 1000).toFixed(1)}초".encode('utf-8')),
    ]
    
    # Apply replacements
    for old, new in replacements:
        content = content.replace(old, new)
    
    # Write the fixed content back
    with open(filepath, 'wb') as f:
        f.write(content)
    
    print(f"Fixed: {filepath}")

# Fix the files
if __name__ == "__main__":
    base_dir = "/Users/seonggukpark/community-info-collector/RedditAnalyzerApp/src"
    
    # Fix HomeScreen.tsx
    fix_file_robust(os.path.join(base_dir, "screens/HomeScreen.tsx"))
    
    # Fix ReportsScreen.tsx  
    fix_file_robust(os.path.join(base_dir, "screens/ReportsScreen.tsx"))
    
    print("\nAll encoding issues have been fixed!")