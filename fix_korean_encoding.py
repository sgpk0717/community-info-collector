#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

def fix_file(filepath):
    """Fix Korean encoding in a specific file."""
    
    # Read the file in binary mode
    with open(filepath, 'rb') as f:
        content = f.read()
    
    # Convert to string, replacing invalid characters
    text = content.decode('utf-8', errors='replace')
    
    # Define replacements
    replacements = [
        # HomeScreen.tsx specific replacements
        ("Alert.alert('L�', '�` ���| �%t�8�.');", "Alert.alert('알림', '키워드를 입력해주세요.');"),
        ("Alert.alert('$X', '��� �| >D  Ƶ��.');", "Alert.alert('오류', '사용자 정보를 찾을 수 없습니다.');"),
        ("Alert.alert('1�', '�t D�ȵ��!', [", "Alert.alert('성공', '분석이 완료되었습니다!', ["),
        ("{ text: 'Ux', style: 'default' }", "{ text: '확인', style: 'default' }"),
        ("Alert.alert('$X', result.error || '�� �(����.');", "Alert.alert('오류', result.error || '분석에 실패했습니다.');"),
        ("Alert.alert('$X', '� �� �(����.');", "Alert.alert('오류', '분석 중 오류가 발생했습니다.');"),
        ("{REPORT_LENGTHS[value].chars}�", "{REPORT_LENGTHS[value].chars}자"),
        (">Reddit � �</Text>", ">Reddit 분석</Text>"),
        ("\\� �| ��<\\ �X� �i��", "키워드로 커뮤니티를 분석하세요"),
        ("��` ���", "분석할 키워드"),
        ("�� ��ܔ |\\(,)\\ l�X8�", "여러 키워드는 콤마(,)로 구분하세요"),
        ("�� 8t", "보고서 길이"),
        ('label="�"', 'label="간단"'),
        ('label="��"', 'label="보통"'),
        ('label="�8X�"', 'label="상세하게"'),
        (">� ...</Text>", ">분석 중...</Text>"),
        (">� & �</Text>", ">분석 시작</Text>"),
        ("Reddit� �| �X� ����...", "Reddit 커뮤니티를 분석하고 있습니다..."),
        ("= Reddit �� ", "• Reddit 데이터 수집 중"),
        ("=� pt0 � ", "• 관련 게시물 분석 중"),
        ("> GPT-4 � ", "• GPT-4 보고서 생성 중"),
        ("=� �� �1 ", "• 최종 보고서 정리 중"),
        ("� D�", "분석 완료"),
        ("=� {analysisResult.metadata.charCount}�", "총 {analysisResult.metadata.charCount}자"),
        ("� {(analysisResult.metadata.processingTime / 1000).toFixed(1)}", "소요시간 {(analysisResult.metadata.processingTime / 1000).toFixed(1)}초"),
        ("Alert.alert('� ��� �� �� UxX8�')", "Alert.alert('전체 보고서는 보고서 탭에서 확인하세요')"),
        (">� �� �0</Text>", ">전체 보기</Text>"),
        
        # ReportsScreen.tsx specific replacements
        ("'� Ux',", "'삭제 확인',"),
        ("'t ��| �Xܠ��L?',", "'이 보고서를 삭제하시겠습니까?',"),
        ("{ text: '�', style: 'cancel' },", "{ text: '취소', style: 'cancel' },"),
        ("text: '�',", "text: '삭제',"),
        ("Alert.alert('1�', '��  �ȵ��.');", "Alert.alert('성공', '보고서가 삭제되었습니다.');"),
        ("return `${days}| `;", "return `${days}일 전`;"),
        ("return `${hours}� `;", "return `${hours}시간 전`;"),
        ("return `${minutes}� `;", "return `${minutes}분 전`;"),
        ("{item.metadata.charCount}�", "{item.metadata.charCount}자"),
        (" � ��  Ƶ��", "저장된 보고서가 없습니다"),
        ("H �� ���| ��X� �D ܑX8�", "홈 화면에서 키워드를 분석해 보고서를 생성하세요"),
        (">� ��</Text>", ">보고서 목록</Text>"),
        (" {reports.length}X ��   �� ����", "{reports.length}개의 보고서가 저장되어 있습니다"),
        ("Alert.alert('��(', '��  t���� ��ȵ��.');", "Alert.alert('복사됨', '보고서가 클립보드에 복사되었습니다.');"),
        (">��</Text>", ">복사</Text>"),
        ("Alert.alert('� ', '�  0�@  D ���.');", "Alert.alert('공유', '공유 기능은 추후 추가 예정입니다.');"),
        (">� </Text>", ">공유</Text>"),
        ("=� {selectedReport.metadata.charCount}�", "총 {selectedReport.metadata.charCount}자"),
        ("� {(selectedReport.metadata.processingTime / 1000).toFixed(1)}", "소요시간 {(selectedReport.metadata.processingTime / 1000).toFixed(1)}초"),
        
        # Fix some comment placeholders
        ("// �� 0� l", "// 복사 기능 구현"),
        ("// �  0� l", "// 공유 기능 구현"),
    ]
    
    # Apply replacements
    for old, new in replacements:
        text = text.replace(old, new)
    
    # Write the fixed content back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)
    
    print(f"Fixed: {filepath}")

# Fix the files
if __name__ == "__main__":
    base_dir = "/Users/seonggukpark/community-info-collector/RedditAnalyzerApp/src"
    
    # Fix HomeScreen.tsx
    fix_file(os.path.join(base_dir, "screens/HomeScreen.tsx"))
    
    # Fix ReportsScreen.tsx  
    fix_file(os.path.join(base_dir, "screens/ReportsScreen.tsx"))
    
    print("\nEncoding fixes applied successfully!")
    print("Note: SettingsScreen.tsx already has proper Korean encoding.")