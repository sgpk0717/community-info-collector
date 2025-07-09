#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

def fix_korean_encoding(file_path):
    """Fix corrupted Korean text in the given file."""
    
    # Read the file with replacement of invalid characters
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    # Define all replacements
    replacements = [
        # HomeScreen.tsx replacements
        (r"Reddit [^\s]+ [^\s]+", "Reddit 분석"),
        (r"\\[^\s]+ [^\s]+\| [^\s]+<\\ [^\s]+X[^\s]+ [^\s]+i[^\s]+", "키워드로 커뮤니티를 분석하세요"),
        (r"[^\s]+`[^\s]+ [^\s]+", "분석할 키워드"),
        (r"Alert\.alert\('L[^\s]+'", "Alert.alert('알림'"),
        (r"'[^\s]+`[^\s]+ [^\s]+\| [^\s]+%t[^\s]+8[^\s]+\.'", "'키워드를 입력해주세요.'"),
        (r"Alert\.alert\('\$X'", "Alert.alert('오류'"),
        (r"'[^\s]+ [^\s]+\| >D  [^\s]+\.'", "'사용자 정보를 찾을 수 없습니다.'"),
        (r"Alert\.alert\('1[^\s]+'", "Alert.alert('성공'"),
        (r"'[^\s]+t D[^\s]+[^\s]+!'", "'분석이 완료되었습니다!'"),
        (r"text: 'Ux'", "text: '확인'"),
        (r"'[^\s]+ [^\s]+\([^\s]+\.'", "'분석에 실패했습니다.'"),
        (r"'[^\s]+ [^\s]+ [^\s]+\([^\s]+\.'", "'분석 중 오류가 발생했습니다.'"),
        (r"\{REPORT_LENGTHS\[value\]\.chars\}[^\s]+", "{REPORT_LENGTHS[value].chars}자"),
        (r"[^\s]+ [^\s]+[^\s]+ \|\\\\,\\\\,\\\\ l[^\s]+X8[^\s]+", "여러 키워드는 콤마(,)로 구분하세요"),
        (r"[^\s]+ 8t", "보고서 길이"),
        (r'label="[^\s]+"', 'label="간단"'),
        (r'label="[^\s][^\s]+"', 'label="보통"'),
        (r'label="[^\s]+8X[^\s]+"', 'label="상세하게"'),
        (r">[^\s]+ \.\.\.</Text>", ">분석 중...</Text>"),
        (r">[^\s]+ & [^\s]+</Text>", ">분석 시작</Text>"),
        (r"Reddit[^\s]+ [^\s]+\| [^\s]+X[^\s]+ [^\s]+\.\.\.", "Reddit 커뮤니티를 분석하고 있습니다..."),
        (r"= Reddit [^\s]+ ", "• Reddit 데이터 수집 중"),
        (r"=[^\s]+ pt0 [^\s]+ ", "• 관련 게시물 분석 중"),
        (r"> GPT-4 [^\s]+ ", "• GPT-4 보고서 생성 중"),
        (r"=[^\s]+ [^\s]+ [^\s]+1 ", "• 최종 보고서 정리 중"),
        (r"[^\s]+ D[^\s]+", "분석 완료"),
        (r"=[^\s]+ \{analysisResult", "총 {analysisResult"),
        (r"\}[^\s]+\n", "}자\n"),
        (r"[^\s]+ \{\(analysisResult", "소요시간 {(analysisResult"),
        (r"toFixed\(1\)\}[^\s]+", "toFixed(1)}초"),
        (r"'[^\s]+ [^\s]+ [^\s]+ [^\s]+ UxX8[^\s]+'", "'전체 보고서는 보고서 탭에서 확인하세요'"),
        (r">[^\s]+ [^\s]+ [^\s]+0</Text>", ">전체 보기</Text>"),
        
        # ReportsScreen.tsx replacements
        (r"'[^\s]+ Ux'", "'삭제 확인'"),
        (r"'t [^\s]+\| [^\s]+X[^\s]+L\?'", "'이 보고서를 삭제하시겠습니까?'"),
        (r"text: '[^\s]+'", "text: '취소'"),
        (r"text: '[^\s]+'[^\n]*style: 'destructive'", "text: '삭제', style: 'destructive'"),
        (r"'[^\s]+  [^\s]+\.'", "'보고서가 삭제되었습니다.'"),
        (r"\{days\}\| ", "{days}일 전"),
        (r"\{hours\}[^\s]+ ", "{hours}시간 전"),
        (r"\{minutes\}[^\s]+ ", "{minutes}분 전"),
        (r"\}[^\s]+\n[^\s]*</Text>", "}자\n                </Text>"),
        (r"toFixed\(1\)\}[^\s]+\n", "toFixed(1)}초\n"),
        (r"[^\s]+ [^\s]+ [^\s]+  [^\s]+", "저장된 보고서가 없습니다"),
        (r"H [^\s]+ [^\s]+\| [^\s]+X[^\s]+ [^\s]+D [^\s]+X8[^\s]+", "홈 화면에서 키워드를 분석해 보고서를 생성하세요"),
        (r">[^\s]+ [^\s]+</Text>", ">보고서 목록</Text>"),
        (r"\{reports\.length\}X [^\s]+   [^\s]+ [^\s]+", "{reports.length}개의 보고서가 저장되어 있습니다"),
        (r"'[^\s]+\('", "'복사됨'"),
        (r"'[^\s]+  t[^\s]+ [^\s]+\.'", "'보고서가 클립보드에 복사되었습니다.'"),
        (r"'[^\s]+ '", "'공유'"),
        (r"'[^\s]+  0[^\s]+@  D [^\s]+\.'", "'공유 기능은 추후 추가 예정입니다.'"),
        (r">[^\s]+</Text>[^\n]*content-copy", ">복사</Text>"),
        (r">[^\s]+ </Text>[^\n]*share", ">공유</Text>"),
    ]
    
    # Apply replacements
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Additional specific replacements that need exact matching
    specific_replacements = [
        ("title}>Reddit � �</Text>", "title}>Reddit 분석</Text>"),
        ("subtitle}>\n            \\� �| ��<\\ �X� �i��", "subtitle}>\n            키워드로 커뮤니티를 분석하세요"),
        ("textDark]}>\n              ��` ���", "textDark]}>\n              분석할 키워드"),
        ("helperTextDark]}>\n              �� ��ܔ |\\(,)\\ l�X8�", "helperTextDark]}>\n              여러 키워드는 콤마(,)로 구분하세요"),
        ("textDark]}>\n              �� 8t", "textDark]}>\n              보고서 길이"),
        ("label=\"�\"", "label=\"간단\""),
        ("label=\"��\"", "label=\"보통\""),
        ("label=\"�8X�\"", "label=\"상세하게\""),
        (">� ...</Text>", ">분석 중...</Text>"),
        (">� & �</Text>", ">분석 시작</Text>"),
        ("textDark]}>\n                Reddit� �| �X� ����...", "textDark]}>\n                Reddit 커뮤니티를 분석하고 있습니다..."),
        ("textDark]}>\n                  = Reddit �� ", "textDark]}>\n                  • Reddit 데이터 수집 중"),
        ("textDark]}>\n                  =� pt0 � ", "textDark]}>\n                  • 관련 게시물 분석 중"),
        ("textDark]}>\n                  > GPT-4 � ", "textDark]}>\n                  • GPT-4 보고서 생성 중"),
        ("textDark]}>\n                  =� �� �1 ", "textDark]}>\n                  • 최종 보고서 정리 중"),
        ("textDark]}>\n                  � D�", "textDark]}>\n                  분석 완료"),
        ("subtextDark]}>\n                  =� {analysisResult", "subtextDark]}>\n                  총 {analysisResult"),
        ("charCount}�", "charCount}자"),
        ("subtextDark]}>\n                  � {(analysisResult", "subtextDark]}>\n                  소요시간 {(analysisResult"),
        ("toFixed(1)}", "toFixed(1)}초"),
        ("Alert.alert('� ��� �� �� UxX8�')", "Alert.alert('전체 보고서는 보고서 탭에서 확인하세요')"),
        (">� �� �0</Text>", ">전체 보기</Text>"),
        
        # ReportsScreen.tsx specific replacements
        ("Alert.alert(\n      '� Ux',", "Alert.alert(\n      '삭제 확인',"),
        ("'t ��| �Xܠ��L?'", "'이 보고서를 삭제하시겠습니까?'"),
        ("{ text: '�', style: 'cancel' }", "{ text: '취소', style: 'cancel' }"),
        ("text: '�',", "text: '삭제',"),
        ("Alert.alert('1�', '��  �ȵ��.')", "Alert.alert('성공', '보고서가 삭제되었습니다.')"),
        ("return `${days}| `;", "return `${days}일 전`;"),
        ("return `${hours}� `;", "return `${hours}시간 전`;"),
        ("return `${minutes}� `;", "return `${minutes}분 전`;"),
        ("{item.metadata.charCount}�", "{item.metadata.charCount}자"),
        ("toFixed(1)}", "toFixed(1)}초"),
        ("textDark]}>\n         � ��  Ƶ��", "textDark]}>\n        저장된 보고서가 없습니다"),
        ("subtextDark]}>\n        H �� ���| ��X� �D ܑX8�", "subtextDark]}>\n        홈 화면에서 키워드를 분석해 보고서를 생성하세요"),
        (">� ��</Text>", ">보고서 목록</Text>"),
        ("subtitle}>\n           {reports.length}X ��   �� ����", "subtitle}>\n          {reports.length}개의 보고서가 저장되어 있습니다"),
        ("Alert.alert('��(', '��  t���� ��ȵ��.')", "Alert.alert('복사됨', '보고서가 클립보드에 복사되었습니다.')"),
        (">��</Text>", ">복사</Text>"),
        ("Alert.alert('� ', '�  0�@  D ���.')", "Alert.alert('공유', '공유 기능은 추후 추가 예정입니다.')"),
        (">� </Text>", ">공유</Text>"),
        ("=� {selectedReport", "총 {selectedReport"),
        ("charCount}�", "charCount}자"),
        ("� {(selectedReport", "소요시간 {(selectedReport"),
    ]
    
    for old, new in specific_replacements:
        content = content.replace(old, new)
    
    # Write the fixed content back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed encoding in {file_path}")

# Main execution
if __name__ == "__main__":
    base_dir = "/Users/seonggukpark/community-info-collector/RedditAnalyzerApp/src"
    
    # Fix HomeScreen.tsx
    home_screen_path = os.path.join(base_dir, "screens/HomeScreen.tsx")
    if os.path.exists(home_screen_path):
        fix_korean_encoding(home_screen_path)
    
    # Fix ReportsScreen.tsx
    reports_screen_path = os.path.join(base_dir, "screens/ReportsScreen.tsx")
    if os.path.exists(reports_screen_path):
        fix_korean_encoding(reports_screen_path)
    
    # Note: SettingsScreen.tsx already has proper Korean encoding
    print("\nNote: SettingsScreen.tsx already has proper Korean encoding and doesn't need fixing.")
    print("Also note: ReportItem.tsx and ScheduleButton.tsx are empty files.")