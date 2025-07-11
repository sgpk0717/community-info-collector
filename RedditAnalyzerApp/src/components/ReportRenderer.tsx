import React, { useState, useRef, useEffect, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  Linking,
  useColorScheme,
  Modal,
  Dimensions,
  Animated,
} from 'react-native';
import { MaterialIcons as Icon } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import ApiService from '../services/api.service';

interface ReportRendererProps {
  content: string;
  isDarkMode?: boolean;
  reportId?: string;  // 보고서 ID (링크 별도 로드용)
}

interface FootnoteInfo {
  number: string;
  url: string;
  title?: string;
  score?: number;
  comments?: number;
  timeAgo?: string;
  subreddit?: string;
}

interface TooltipPosition {
  x: number;
  y: number;
}

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

const ReportRenderer: React.FC<ReportRendererProps> = ({ content, isDarkMode, reportId }) => {
  const colorScheme = useColorScheme();
  const isDark = isDarkMode ?? colorScheme === 'dark';
  const [footnoteLinks, setFootnoteLinks] = useState<FootnoteInfo[]>([]);
  const [selectedFootnote, setSelectedFootnote] = useState<FootnoteInfo | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState<TooltipPosition>({ x: 0, y: 0 });
  const [showTooltip, setShowTooltip] = useState(false);
  const [reportLinks, setReportLinks] = useState<any[]>([]);  // 서버에서 로드한 링크
  const [focusedLinkNumber, setFocusedLinkNumber] = useState<string | null>(null);  // 포커스된 링크 번호
  const pulseAnim = useRef(new Animated.Value(1)).current;  // 펄스 애니메이션
  const scrollViewRef = useRef<ScrollView>(null);
  const footnoteRefs = useRef<{ [key: string]: View | null }>({});
  const linksSectionRef = useRef<View>(null);  // 링크 섹션 참조
  const [linkPositions, setLinkPositions] = useState<{ [key: string]: number }>({});  // 링크 위치 저장
  const [linksSectionY, setLinksSectionY] = useState<number>(0);  // 링크 섹션의 전체 문서 기준 Y 위치

  // reportId가 있으면 링크 데이터 로드
  useEffect(() => {
    if (reportId) {
      loadReportLinks();
    }
  }, [reportId]);

  const loadReportLinks = async () => {
    try {
      const result = await ApiService.getReportLinks(reportId!);
      if (result.success && result.data) {
        setReportLinks(result.data);
      }
    } catch (error) {
      console.error('Failed to load report links:', error);
    }
  };

  // 보고서 내용을 섹션별로 파싱
  const parseContent = useMemo(() => {
    const sections = content.split(/\n(?=\d+\.\s)/);
    return sections.map(section => {
      const lines = section.trim().split('\n');
      const titleMatch = lines[0]?.match(/^(\d+)\.\s*(.+?)(?:\s*\((\d+)자\s*이상\))?$/);
      
      if (titleMatch) {
        return {
          number: titleMatch[1],
          title: titleMatch[2],
          charCount: titleMatch[3],
          content: lines.slice(1).join('\n').trim()
        };
      }
      
      return {
        number: '',
        title: '',
        content: section.trim()
      };
    }).filter(section => section.content);
  }, [content]);

  // 각주 링크 파싱
  const processedContent = useMemo(() => {
    const links: FootnoteInfo[] = [];
    
    // 서버에서 로드한 링크 데이터 사용
    reportLinks.forEach(link => {
      // 시간 계산 (created_utc가 있으면 사용)
      let timeAgo = '방금 전';
      if (link.created_utc) {
        const now = Date.now() / 1000;
        const hoursDiff = Math.floor((now - link.created_utc) / 3600);
        if (hoursDiff < 1) {
          timeAgo = '방금 전';
        } else if (hoursDiff < 24) {
          timeAgo = `${hoursDiff}시간 전`;
        } else {
          const daysDiff = Math.floor(hoursDiff / 24);
          timeAgo = `${daysDiff}일 전`;
        }
      }
      
      links.push({
        number: link.footnote_number.toString(),
        url: link.url,
        title: link.title || `게시물 ${link.footnote_number}`,
        score: link.score || 0,
        comments: link.comments || 0,
        timeAgo,
        subreddit: link.subreddit
      });
    });

    // 각주 번호로 정렬
    links.sort((a, b) => parseInt(a.number) - parseInt(b.number));

    return { text: content, links };
  }, [content, reportLinks]);

  useEffect(() => {
    setFootnoteLinks(processedContent.links);
  }, [processedContent.links]);

  // 각주 클릭 시 툴팁 표시
  const handleFootnotePress = (event: any, footnoteNumber: string) => {
    console.log('Footnote pressed:', footnoteNumber);
    console.log('Available footnotes:', footnoteLinks.map(f => f.number));
    
    const footnote = footnoteLinks.find(f => f.number === footnoteNumber);
    if (!footnote) {
      console.log('Footnote not found');
      return;
    }

    console.log('Found footnote:', footnote);

    // TouchableOpacity의 measure 사용
    const touchableRef = event.currentTarget;
    if (touchableRef && touchableRef.measure) {
      touchableRef.measure((x: number, y: number, width: number, height: number, pageX: number, pageY: number) => {
        console.log('Touch position:', { pageX, pageY });
        setTooltipPosition({ 
          x: Math.max(10, Math.min(pageX - 150, screenWidth - 310)), // 화면 경계 고려
          y: Math.max(50, pageY - 180)  // 툴팁 높이 + 여유
        });
        setSelectedFootnote(footnote);
        setShowTooltip(true);
      });
    } else {
      // 대체 방법: 화면 중앙에 표시
      setTooltipPosition({ 
        x: screenWidth / 2 - 150,
        y: screenHeight / 2 - 200
      });
      setSelectedFootnote(footnote);
      setShowTooltip(true);
    }
  };

  // 링크 섹션 위치 저장
  const handleLinksSectionLayout = (event: any) => {
    const { y } = event.nativeEvent.layout;
    console.log('Links section layout Y:', y);
    setLinksSectionY(y);
  };

  // 링크 위치 저장 (링크 섹션 기준 상대 위치)
  const handleLinkLayout = (footnoteNumber: string, event: any) => {
    const { x, y, width, height } = event.nativeEvent.layout;
    console.log(`Link ${footnoteNumber} layout (relative to links section):`, { x, y, width, height });
    
    setLinkPositions(prev => {
      const newPositions = {
        ...prev,
        [footnoteNumber]: y
      };
      console.log('Updated link positions (relative):', newPositions);
      return newPositions;
    });
  };

  // 링크로 스크롤 - 정확한 좌표로 이동
  const scrollToLink = (footnoteNumber: string) => {
    setShowTooltip(false);
    
    console.log('=== 🎯 SCROLL TO LINK START ===');
    console.log('🔍 Target footnote:', footnoteNumber);
    
    if (!scrollViewRef.current) {
      console.error('❌ ScrollView ref is null');
      return;
    }

    // 1단계: 포커스 효과 먼저 적용
    console.log('✨ Step 1: Apply focus effect');
    setFocusedLinkNumber(footnoteNumber);
    
    // 2단계: 정확한 좌표 계산
    const linkRelativeY = linkPositions[footnoteNumber];
    console.log('📊 Link positions:', linkPositions);
    console.log('📊 Links section Y:', linksSectionY);
    console.log('📊 Link relative Y:', linkRelativeY);
    
    if (linksSectionY > 0 && linkRelativeY !== undefined) {
      // 정확한 위치 계산: 링크 섹션 시작 + 링크 상대 위치 - 화면 여유 공간
      const targetY = linksSectionY + linkRelativeY - 100; // 100px 여유 공간
      console.log('🎯 Calculated target Y:', targetY);
      
      try {
        console.log('🚀 Scrolling to exact position:', targetY);
        scrollViewRef.current.scrollTo({ y: targetY, animated: true });
      } catch (error) {
        console.error('❌ Exact scroll failed:', error);
        // 실패 시 대체 방법
        try {
          console.log('🔄 Fallback: scrolling to links section');
          scrollViewRef.current.scrollTo({ y: linksSectionY, animated: true });
        } catch (fallbackError) {
          console.error('❌ Fallback scroll failed:', fallbackError);
        }
      }
    } else {
      console.log('📍 Missing position data, using fallback scroll');
      // 위치 데이터가 없으면 링크 섹션 시작으로 스크롤
      try {
        if (linksSectionY > 0) {
          console.log('🚀 Scrolling to links section start:', linksSectionY);
          scrollViewRef.current.scrollTo({ y: linksSectionY, animated: true });
        } else {
          console.log('🚀 No position data, scrolling to bottom');
          scrollViewRef.current.scrollToEnd({ animated: true });
        }
      } catch (error) {
        console.error('❌ Fallback scroll failed:', error);
      }
    }
    
    // 3단계: 세련된 포커스 애니메이션 (1초 이하)
    setTimeout(() => {
      console.log('✨ Step 3: Start elegant focus animation');
      
      // 세련된 fade-in + subtle scale 애니메이션
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.08,
          duration: 200,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1.05,
          duration: 150,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1.08,
          duration: 200,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 200,
          useNativeDriver: true,
        }),
      ]).start(() => {
        console.log('🎉 Elegant animation completed');
      });
      
      // 2초 후 포커스 제거 (더 짧게)
      setTimeout(() => {
        console.log('🔄 Removing focus from footnote:', footnoteNumber);
        setFocusedLinkNumber(null);
      }, 2000);
      
    }, 300); // 스크롤 후 애니메이션 시작
    
    console.log('=== ✅ SCROLL TO LINK END ===');
  };

  // 링크 열기
  const openLink = async (url: string) => {
    try {
      const supported = await Linking.canOpenURL(url);
      if (supported) {
        await Linking.openURL(url);
      } else {
        Alert.alert('오류', '이 링크를 열 수 없습니다.');
      }
    } catch (error) {
      console.error('링크 열기 오류:', error);
      Alert.alert('오류', '링크를 여는 중 오류가 발생했습니다.');
    }
  };

  // 각주가 포함된 텍스트를 렌더링하는 함수
  const renderTextWithFootnotes = (text: string) => {
    const parts = text.split(/(\[\d+\])/g);
    
    return parts.map((part, index) => {
      const footnoteMatch = part.match(/\[(\d+)\]/);
      if (footnoteMatch) {
        const footnoteNumber = footnoteMatch[1];
        return (
          <TouchableOpacity
            key={index}
            onPress={(e) => handleFootnotePress(e, footnoteNumber)}
            style={[styles.footnoteInline, isDark && styles.footnoteInlineDark]}
          >
            <Text style={[styles.footnoteText, isDark && styles.footnoteTextDark]}>
              [{footnoteNumber}]
            </Text>
          </TouchableOpacity>
        );
      }
      return <Text key={index} style={[styles.sectionContent, isDark && styles.sectionContentDark]}>{part}</Text>;
    });
  };

  // 섹션별 콘텐츠 렌더링
  const renderSection = (section: any, index: number) => {
    return (
      <View key={index} style={[styles.sectionContainer, isDark && styles.sectionContainerDark]}>
        {section.title && (
          <>
            <View style={styles.sectionHeader}>
              <View style={styles.sectionNumberContainer}>
                <LinearGradient
                  colors={isDark ? ['#667eea', '#764ba2'] : ['#667eea', '#764ba2']}
                  style={styles.sectionNumber}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                >
                  <Text style={styles.sectionNumberText}>{section.number}</Text>
                </LinearGradient>
              </View>
              <View style={styles.sectionTitleContainer}>
                <Text style={[styles.sectionTitle, isDark && styles.sectionTitleDark]}>
                  {section.title}
                </Text>
                {section.charCount && (
                  <View style={[styles.charCountBadge, isDark && styles.charCountBadgeDark]}>
                    <Text style={[styles.charCount, isDark && styles.charCountDark]}>
                      {section.charCount}자 이상
                    </Text>
                  </View>
                )}
              </View>
            </View>
            <View style={styles.sectionDivider} />
          </>
        )}
        
        <Text style={[styles.sectionContent, isDark && styles.sectionContentDark]}>
          {renderTextWithFootnotes(section.content)}
        </Text>
      </View>
    );
  };

  return (
    <>
      <ScrollView 
        ref={scrollViewRef} 
        style={[styles.container, { maxHeight: screenHeight - 100 }]}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        scrollEnabled={true}
        nestedScrollEnabled={true}
        removeClippedSubviews={false}
        onScrollBeginDrag={() => console.log('📱 ScrollView: User started scrolling')}
        onScrollEndDrag={() => console.log('📱 ScrollView: User ended scrolling')}
        onMomentumScrollBegin={() => console.log('📱 ScrollView: Momentum scroll began')}
        onMomentumScrollEnd={(event) => {
          const { contentOffset, contentSize, layoutMeasurement } = event.nativeEvent;
          console.log('📱 ScrollView: Momentum scroll ended');
          console.log('  📍 Current Y:', contentOffset.y);
          console.log('  📏 Content height:', contentSize.height);
          console.log('  📐 Layout height:', layoutMeasurement.height);
          console.log('  🔚 At bottom?', contentOffset.y + layoutMeasurement.height >= contentSize.height - 50);
          console.log('  🔄 Scrollable distance:', contentSize.height - layoutMeasurement.height);
        }}
        onScroll={(event) => {
          const { contentOffset } = event.nativeEvent;
          // 너무 많은 로그를 방지하기 위해 100 단위로만 로깅
          if (contentOffset.y % 100 < 10) {
            console.log('📊 Scrolling to Y:', Math.round(contentOffset.y));
          }
        }}
        scrollEventThrottle={100}
        onContentSizeChange={(width, height) => {
          console.log('📏 Content size changed:', { width, height });
        }}
        onLayout={(event) => {
          const { x, y, width, height } = event.nativeEvent.layout;
          console.log('📐 ScrollView layout:', { x, y, width, height });
        }}
      >
        <View style={styles.contentContainer}>
          {/* 제목 */}
          <View style={styles.titleContainer}>
            <Icon name="analytics" size={28} color={isDark ? '#90cdf4' : '#667eea'} />
            <Text style={[styles.mainTitle, isDark && styles.mainTitleDark]}>
              분석 보고서
            </Text>
          </View>

          {/* 섹션별 콘텐츠 */}
          <View style={styles.sectionsContainer}>
            {parseContent.map((section, index) => renderSection(section, index))}
          </View>
        </View>
        
        {/* 참고 링크 섹션 */}
        {footnoteLinks.length > 0 && (
          <View 
            ref={linksSectionRef}
            style={[styles.linksSection, isDark && styles.linksSectionDark]}
            onLayout={handleLinksSectionLayout}
          >
            <View style={styles.divider} />
            
            <View style={styles.linksSectionHeader}>
              <Icon name="link" size={24} color={isDark ? '#e2e8f0' : '#4a5568'} />
              <Text style={[styles.linksSectionTitle, isDark && styles.linksSectionTitleDark]}>
                참고 링크
              </Text>
            </View>
            
            {footnoteLinks.map((link) => (
              <Animated.View
                key={link.number}
                style={{
                  transform: [{ 
                    scale: focusedLinkNumber === link.number ? pulseAnim : 1 
                  }]
                }}
                onLayout={(event) => handleLinkLayout(link.number, event)}
              >
                <TouchableOpacity
                  ref={(ref) => footnoteRefs.current[link.number] = ref}
                  style={[
                    styles.linkItem, 
                    isDark && styles.linkItemDark,
                    focusedLinkNumber === link.number && styles.linkItemFocused,
                    focusedLinkNumber === link.number && isDark && styles.linkItemFocusedDark
                  ]}
                  onPress={() => openLink(link.url)}
                  activeOpacity={0.8}
                >
                <View style={styles.linkHeader}>
                  <View style={styles.linkNumberContainer}>
                    <Text style={[styles.linkNumber, isDark && styles.linkNumberDark]}>
                      [{link.number}]
                    </Text>
                    {link.title && (
                      <Text style={[styles.linkTitle, isDark && styles.linkTitleDark]} numberOfLines={2}>
                        {link.title}
                      </Text>
                    )}
                    {link.subreddit && (
                      <Text style={[styles.subredditTag, isDark && styles.subredditTagDark]}>
                        r/{link.subreddit}
                      </Text>
                    )}
                  </View>
                  <Icon name="open-in-new" size={18} color="#667eea" />
                </View>
                
                <Text 
                  style={[styles.linkUrl, isDark && styles.linkUrlDark]}
                  numberOfLines={2}
                  ellipsizeMode="middle"
                >
                  {link.url}
                </Text>
                
                <View style={styles.linkMeta}>
                  <View style={styles.metaItem}>
                    <Icon name="arrow-upward" size={14} color="#48bb78" />
                    <Text style={[styles.metaText, isDark && styles.metaTextDark]}>
                      {link.score}
                    </Text>
                  </View>
                  <View style={styles.metaItem}>
                    <Icon name="comment" size={14} color="#718096" />
                    <Text style={[styles.metaText, isDark && styles.metaTextDark]}>
                      {link.comments}
                    </Text>
                  </View>
                  <Text style={[styles.timeText, isDark && styles.metaTextDark]}>
                    {link.timeAgo}
                  </Text>
                </View>
              </TouchableOpacity>
              </Animated.View>
            ))}
          </View>
        )}
      </ScrollView>

      {/* 툴팁 모달 */}
      <Modal
        visible={showTooltip}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setShowTooltip(false)}
      >
        <TouchableOpacity 
          style={styles.tooltipOverlay} 
          activeOpacity={1}
          onPress={() => setShowTooltip(false)}
        >
          {selectedFootnote && (
            <View 
              style={[
                styles.tooltip,
                isDark && styles.tooltipDark,
                {
                  left: Math.max(10, Math.min(tooltipPosition.x, screenWidth - 310)),
                  top: Math.max(50, tooltipPosition.y)
                }
              ]}
            >
              <View style={styles.tooltipHeader}>
                <Text style={[styles.tooltipTitle, isDark && styles.tooltipTitleDark]}>
                  게시물 정보
                </Text>
                <TouchableOpacity onPress={() => setShowTooltip(false)}>
                  <Icon name="close" size={20} color={isDark ? '#e2e8f0' : '#4a5568'} />
                </TouchableOpacity>
              </View>
              
              {selectedFootnote.subreddit && (
                <View style={[styles.subredditBadge, isDark && styles.subredditBadgeDark]}>
                  <Text style={[styles.subredditText, isDark && styles.subredditTextDark]}>
                    r/{selectedFootnote.subreddit}
                  </Text>
                </View>
              )}
              
              <View style={styles.tooltipStats}>
                <View style={styles.statItem}>
                  <Icon name="trending-up" size={16} color="#48bb78" />
                  <Text style={[styles.statText, isDark && styles.statTextDark]}>
                    {selectedFootnote.score || 0} 추천
                  </Text>
                </View>
                <View style={styles.statItem}>
                  <Icon name="chat-bubble" size={16} color="#667eea" />
                  <Text style={[styles.statText, isDark && styles.statTextDark]}>
                    {selectedFootnote.comments || 0} 댓글
                  </Text>
                </View>
              </View>
              
              <Text style={[styles.timeAgo, isDark && styles.timeAgoDark]}>
                {selectedFootnote.timeAgo} 게시됨
              </Text>
              
              <TouchableOpacity
                style={styles.viewLinkButton}
                onPress={() => scrollToLink(selectedFootnote.number)}
              >
                <LinearGradient
                  colors={['#667eea', '#764ba2']}
                  style={styles.viewLinkGradient}
                >
                  <Icon name="visibility" size={16} color="#ffffff" />
                  <Text style={styles.viewLinkText}>링크 보기</Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>
          )}
        </TouchableOpacity>
      </Modal>
    </>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    height: '100%',
  },
  scrollContent: {
    flexGrow: 1,
    minHeight: screenHeight + 500, // 스크롤 가능하도록 강제로 높이 추가
  },
  contentContainer: {
    paddingHorizontal: 0,
    paddingVertical: 20,
  },
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
    paddingHorizontal: 8,
  },
  mainTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2d3748',
    marginLeft: 12,
  },
  mainTitleDark: {
    color: '#e2e8f0',
  },
  sectionsContainer: {
    gap: 0,
    paddingHorizontal: 0,
  },
  sectionContainer: {
    backgroundColor: '#ffffff',
    marginBottom: 0,
    paddingVertical: 16,
    paddingHorizontal: 6,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#e2e8f0',
  },
  sectionContainerDark: {
    backgroundColor: '#2d3748',
    borderColor: '#4a5568',
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  sectionDivider: {
    height: 1,
    backgroundColor: '#e2e8f0',
    marginVertical: 8,
    marginHorizontal: -6,
  },
  sectionNumberContainer: {
    marginRight: 16,
    alignItems: 'center',
  },
  sectionNumber: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#667eea',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
  sectionNumberText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  sectionTitleContainer: {
    flex: 1,
    justifyContent: 'center',
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#2d3748',
    lineHeight: 28,
    letterSpacing: -0.5,
  },
  sectionTitleDark: {
    color: '#e2e8f0',
  },
  charCountBadge: {
    backgroundColor: '#f7fafc',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
    marginTop: 8,
    alignSelf: 'flex-start',
  },
  charCountBadgeDark: {
    backgroundColor: '#4a5568',
  },
  charCount: {
    fontSize: 11,
    color: '#667eea',
    fontWeight: '600',
    letterSpacing: 0.3,
  },
  charCountDark: {
    color: '#90cdf4',
  },
  sectionContent: {
    fontSize: 16,
    lineHeight: 26,
    color: '#2d3748',
    textAlign: 'left',
    fontWeight: '400',
    letterSpacing: 0.2,
  },
  sectionContentDark: {
    color: '#cbd5e0',
  },
  footnoteInline: {
    marginHorizontal: 1,
    marginVertical: 0,
    paddingHorizontal: 4,
    paddingVertical: 1,
    borderRadius: 4,
    backgroundColor: '#f7fafc',
    borderWidth: 0.5,
    borderColor: '#e2e8f0',
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    alignSelf: 'baseline',
  },
  footnoteInlineDark: {
    backgroundColor: '#4a5568',
    borderColor: '#718096',
  },
  footnoteText: {
    fontSize: 10,
    color: '#667eea',
    fontWeight: '600',
    lineHeight: 14,
    minWidth: 16,
    textAlign: 'center',
  },
  footnoteTextDark: {
    color: '#90cdf4',
  },
  linksSection: {
    backgroundColor: '#f7fafc',
    paddingHorizontal: 0,
    paddingVertical: 24,
  },
  linksSectionDark: {
    backgroundColor: '#1a202c',
  },
  divider: {
    height: 1,
    backgroundColor: '#e2e8f0',
    marginBottom: 24,
  },
  linksSectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    paddingHorizontal: 8,
  },
  linksSectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#2d3748',
    marginLeft: 12,
  },
  linksSectionTitleDark: {
    color: '#e2e8f0',
  },
  linkItem: {
    backgroundColor: '#ffffff',
    borderRadius: 0,
    padding: 8,
    marginBottom: 12,
    marginHorizontal: 0,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  linkItemDark: {
    backgroundColor: '#2d3748',
  },
  linkItemFocused: {
    backgroundColor: '#f0f8ff',
    borderWidth: 2,
    borderColor: '#667eea',
    shadowColor: '#667eea',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  linkItemFocusedDark: {
    backgroundColor: '#1e3a5f',
    borderColor: '#90cdf4',
    shadowColor: '#90cdf4',
  },
  linkHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  linkNumberContainer: {
    flex: 1,
    flexDirection: 'column',
    alignItems: 'flex-start',
  },
  linkNumber: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#667eea',
    marginBottom: 4,
  },
  linkNumberDark: {
    color: '#90cdf4',
  },
  linkTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2d3748',
    marginBottom: 4,
    lineHeight: 20,
  },
  linkTitleDark: {
    color: '#e2e8f0',
  },
  subredditTag: {
    fontSize: 12,
    color: '#718096',
    backgroundColor: '#edf2f7',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    alignSelf: 'flex-start',
  },
  subredditTagDark: {
    color: '#e2e8f0',
    backgroundColor: '#4a5568',
  },
  linkUrl: {
    fontSize: 14,
    color: '#718096',
    marginBottom: 8,
  },
  linkUrlDark: {
    color: '#a0aec0',
  },
  linkMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 16,
  },
  metaText: {
    fontSize: 12,
    color: '#718096',
    marginLeft: 4,
  },
  metaTextDark: {
    color: '#a0aec0',
  },
  timeText: {
    fontSize: 12,
    color: '#718096',
    marginLeft: 'auto',
  },
  tooltipOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
  },
  tooltip: {
    position: 'absolute',
    width: 300,
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 8,
  },
  tooltipDark: {
    backgroundColor: '#2d3748',
  },
  tooltipHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  tooltipTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2d3748',
  },
  tooltipTitleDark: {
    color: '#e2e8f0',
  },
  subredditBadge: {
    backgroundColor: '#edf2f7',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    alignSelf: 'flex-start',
    marginBottom: 12,
  },
  subredditBadgeDark: {
    backgroundColor: '#4a5568',
  },
  subredditText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4a5568',
  },
  subredditTextDark: {
    color: '#e2e8f0',
  },
  tooltipStats: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 20,
  },
  statText: {
    fontSize: 14,
    color: '#4a5568',
    marginLeft: 6,
  },
  statTextDark: {
    color: '#cbd5e0',
  },
  timeAgo: {
    fontSize: 12,
    color: '#718096',
    marginBottom: 16,
  },
  timeAgoDark: {
    color: '#a0aec0',
  },
  viewLinkButton: {
    width: '100%',
  },
  viewLinkGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    borderRadius: 8,
  },
  viewLinkText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 6,
  },
});

export default ReportRenderer;