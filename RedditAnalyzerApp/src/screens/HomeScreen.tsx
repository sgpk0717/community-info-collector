import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  useColorScheme,
  Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialIcons as Icon } from '@expo/vector-icons';
import ApiService from '../services/api.service';
import StorageService from '../services/storage.service';
import AuthService from '../services/auth.service';
import NotificationService from '../services/notification.service';
import { Report, ReportLength } from '../types';
import { REPORT_LENGTHS, WS_BASE_URL } from '../utils/constants';

interface ProgressState {
  stage: string;
  percentage: number;
  message: string;
  details: string;
}

const HomeScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const isDarkMode = useColorScheme() === 'dark';
  const [keyword, setKeyword] = useState('');
  const [reportLength, setReportLength] = useState<ReportLength>('moderate');
  const [isLoading, setIsLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<Report | null>(null);
  const [progress, setProgress] = useState<ProgressState>({
    stage: '',
    percentage: 0,
    message: '',
    details: ''
  });
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [hasNotificationPermission, setHasNotificationPermission] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const progressAnim = useRef(new Animated.Value(0)).current;

  // 디버깅: 현재 사용자 정보 확인
  useEffect(() => {
    const currentUser = AuthService.getCurrentUser();
    console.log('🐛 [DEBUG] Current user info:', currentUser);
    console.log('🐛 [DEBUG] User nickname:', currentUser?.nickname);
  }, []);

  // WebSocket 관련 코드는 제거 (Push Notification으로 대체)

  const handleAnalyze = async () => {
    if (!keyword.trim()) {
      Alert.alert('알림', '분석할 키워드를 입력해주세요.');
      return;
    }

    setIsLoading(true);
    setAnalysisResult(null);
    
    // 푸시 알림 권한 확인 및 요청
    const notificationPermission = await NotificationService.checkAndRequestPermission();
    setHasNotificationPermission(notificationPermission);
    const pushToken = notificationPermission ? await NotificationService.getPushToken() : null;
    
    // 예상 시간 표시로 시작
    setProgress({
      stage: 'initializing',
      percentage: 10,
      message: '🚀 분석을 시작합니다...',
      details: '예상 소요시간: 1-2분'
    });

    // 세션 ID 미리 생성
    const newSessionId = `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);
    
    try {
      // 간단한 진행률 표시 (WebSocket 대신)
      const progressInterval = setInterval(() => {
        setProgress(prev => ({
          ...prev,
          percentage: Math.min(prev.percentage + 10, 90),
          message: '🔍 AI가 열심히 분석 중입니다...',
          details: '조금만 기다려주세요!'
        }));
      }, 5000);

      // API 호출 (푸시 토큰 포함)
      const result = await ApiService.analyze(keyword, reportLength, newSessionId, pushToken);
      
      // 진행률 업데이트 중지
      clearInterval(progressInterval);

      if (result.success && result.data) {
        // 분석 완료 - 진행률 100%로 설정
        setProgress({
          stage: 'completed',
          percentage: 100,
          message: '✅ 분석이 완료되었습니다!',
          details: '보고서가 성공적으로 생성되었습니다'
        });
        
        Animated.timing(progressAnim, {
          toValue: 100,
          duration: 500,
          useNativeDriver: false,
        }).start();

        const user = AuthService.getCurrentUser();
        if (!user) {
          Alert.alert('오류', '사용자 정보를 찾을 수 없습니다.');
          return;
        }

        const report: Report = {
          id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          userId: user.deviceId,
          keyword,
          content: result.data.content,
          htmlContent: result.data.htmlReport,
          metadata: result.data.metadata,
          createdAt: new Date(),
        };

        await StorageService.saveReport(report);
        setAnalysisResult(report);
        
        // 푸시 알림이 설정되어 있으면 로컬 알림 표시
        if (notificationPermission) {
          await NotificationService.showLocalNotification(
            '📊 분석이 완료되었습니다!',
            `'${keyword}' 분석 보고서가 준비되었습니다.`,
            { type: 'analysis_complete', report_id: report.id }
          );
        }
        
        Alert.alert('성공', '분석이 완료되었습니다! 보고서 탭에서 확인하세요.', [
          { 
            text: '보고서 보기', 
            onPress: () => navigation.navigate('Reports') 
          },
          { text: '확인', style: 'default' }
        ]);
      } else {
        Alert.alert('오류', result.error || '분석에 실패했습니다.');
      }
    } catch (error) {
      Alert.alert('오류', '네트워크 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
      // WebSocket 연결 종료
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    }
  };

  useEffect(() => {
    return () => {
      // 컴포넌트 언마운트 시 WebSocket 연결 정리
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  const ReportLengthButton = ({ value, label }: { value: ReportLength; label: string }) => (
    <TouchableOpacity
      style={[
        styles.lengthButton,
        reportLength === value && styles.lengthButtonActive,
        isDarkMode && styles.lengthButtonDark,
      ]}
      onPress={() => setReportLength(value)}
    >
      <Text
        style={[
          styles.lengthButtonText,
          reportLength === value && styles.lengthButtonTextActive,
          isDarkMode && styles.textDark,
        ]}
      >
        {label}
      </Text>
      <Text
        style={[
          styles.lengthButtonSubtext,
          reportLength === value && styles.lengthButtonTextActive,
          isDarkMode && styles.textDark,
        ]}
      >
        {REPORT_LENGTHS[value].chars}자
      </Text>
    </TouchableOpacity>
  );

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={[styles.container, isDarkMode && styles.containerDark]}
    >
      <ScrollView showsVerticalScrollIndicator={false}>
        <LinearGradient
          colors={isDarkMode ? ['#2d3748', '#1a202c'] : ['#667eea', '#764ba2']}
          style={styles.header}
        >
          <Icon name="reddit" size={50} color="#ffffff" />
          <Text style={styles.headerTitle}>커뮤니티 분석</Text>
          <Text style={styles.headerSubtitle}>
            키워드로 커뮤니티를 분석하세요
          </Text>
        </LinearGradient>

        <View style={[styles.content, isDarkMode && styles.contentDark]}>
          <View style={styles.inputSection}>
            <Text style={[styles.label, isDarkMode && styles.textDark]}>
              분석할 키워드
            </Text>
            <TextInput
              style={[styles.input, isDarkMode && styles.inputDark]}
              placeholder="예: Tesla 2025 news, Apple stock"
              placeholderTextColor={isDarkMode ? '#888' : '#999'}
              value={keyword}
              onChangeText={setKeyword}
              editable={!isLoading}
              multiline
              numberOfLines={4}
              textAlignVertical="top"
            />
            <Text style={[styles.helperText, isDarkMode && styles.helperTextDark]}>
              여러 키워드는 콤마(,)로 구분하세요
            </Text>
          </View>

          <View style={styles.lengthSection}>
            <Text style={[styles.label, isDarkMode && styles.textDark]}>
              보고서 길이
            </Text>
            <View style={styles.lengthButtons}>
              <ReportLengthButton value="simple" label="간단" />
              <ReportLengthButton value="moderate" label="보통" />
              <ReportLengthButton value="detailed" label="상세" />
            </View>
          </View>

          <TouchableOpacity
            style={[
              styles.analyzeButton,
              isLoading && styles.analyzeButtonDisabled,
            ]}
            onPress={handleAnalyze}
            disabled={isLoading || !keyword.trim()}
          >
            <LinearGradient
              colors={
                isLoading || !keyword.trim()
                  ? ['#999', '#777']
                  : ['#667eea', '#764ba2']
              }
              style={styles.analyzeButtonGradient}
            >
              {isLoading ? (
                <>
                  <ActivityIndicator color="#ffffff" />
                  <Text style={styles.analyzeButtonText}>분석 중...</Text>
                </>
              ) : (
                <>
                  <Icon name="search" size={24} color="#ffffff" />
                  <Text style={styles.analyzeButtonText}>수집&분석 시작</Text>
                </>
              )}
            </LinearGradient>
          </TouchableOpacity>

          {isLoading && (
            <View style={[styles.progressCard, isDarkMode && styles.cardDark]}>
              {/* 원형 진행률 표시 */}
              <View style={styles.progressCircleContainer}>
                <View style={styles.progressCircle}>
                  <Animated.View
                    style={[
                      styles.progressCircleFill,
                      {
                        transform: [
                          {
                            rotate: progressAnim.interpolate({
                              inputRange: [0, 100],
                              outputRange: ['0deg', '360deg'],
                            }),
                          },
                        ],
                      },
                    ]}
                  />
                  <View style={styles.progressCircleInner}>
                    <Text style={[styles.progressPercentage, isDarkMode && styles.textDark]}>
                      {progress.percentage}%
                    </Text>
                  </View>
                </View>
              </View>

              {/* 진행 상태 메시지 */}
              <Text style={[styles.progressTitle, isDarkMode && styles.textDark]}>
                {progress.message || '분석을 시작합니다...'}
              </Text>

              {/* 상세 정보 */}
              {progress.details && (
                <Text style={[styles.progressDetails, isDarkMode && styles.textDark]}>
                  {progress.details}
                </Text>
              )}

              {/* 진행률 바 */}
              <View style={styles.progressBarContainer}>
                <View style={styles.progressBar}>
                  <Animated.View
                    style={[
                      styles.progressBarFill,
                      {
                        width: progressAnim.interpolate({
                          inputRange: [0, 100],
                          outputRange: ['0%', '100%'],
                        }),
                      },
                    ]}
                  />
                </View>
              </View>
              
              {/* 예상 시간 표시 */}
              <View style={styles.estimatedTimeContainer}>
                <Icon name="schedule" size={18} color="#667eea" />
                <Text style={[styles.estimatedTimeText, isDarkMode && styles.textDark]}>
                  예상 소요시간: 1-2분
                </Text>
              </View>
              
              {/* 알림 안내 */}
              {hasNotificationPermission && (
                <View style={styles.notificationInfo}>
                  <Icon name="notifications-active" size={16} color="#48bb78" />
                  <Text style={[styles.notificationText, isDarkMode && styles.textDark]}>
                    완료되면 알림으로 알려드립니다
                  </Text>
                </View>
              )}

              {/* 단계별 상태 표시 */}
              <View style={styles.stageIndicators}>
                <View style={[styles.stageIndicator, progress.stage === 'initializing' && styles.stageActive]}>
                  <Text style={styles.stageText}>준비</Text>
                </View>
                <View style={[styles.stageIndicator, progress.stage === 'keyword_expansion' && styles.stageActive]}>
                  <Text style={styles.stageText}>키워드</Text>
                </View>
                <View style={[styles.stageIndicator, progress.stage === 'reddit_search' && styles.stageActive]}>
                  <Text style={styles.stageText}>수집</Text>
                </View>
                <View style={[styles.stageIndicator, progress.stage === 'analysis' && styles.stageActive]}>
                  <Text style={styles.stageText}>분석</Text>
                </View>
                <View style={[styles.stageIndicator, progress.stage === 'completed' && styles.stageActive]}>
                  <Text style={styles.stageText}>완료</Text>
                </View>
              </View>
            </View>
          )}

          {analysisResult && !isLoading && (
            <View style={[styles.resultCard, isDarkMode && styles.cardDark]}>
              <View style={styles.resultHeader}>
                <Icon name="check-circle" size={24} color="#48bb78" />
                <Text style={[styles.resultTitle, isDarkMode && styles.textDark]}>
                  분석 완료
                </Text>
              </View>
              
              <View style={styles.resultMeta}>
                <Text style={[styles.metaText, isDarkMode && styles.textDark]}>
                  총 {analysisResult.metadata.charCount}자
                </Text>
                <Text style={[styles.metaText, isDarkMode && styles.textDark]}>
                  소요시간 {(analysisResult.metadata.processingTime / 1000).toFixed(1)}초
                </Text>
              </View>

              <ScrollView style={styles.resultContent} nestedScrollEnabled>
                <Text style={[styles.resultText, isDarkMode && styles.textDark]}>
                  {analysisResult.content.slice(0, 500)}...
                </Text>
              </ScrollView>

              <TouchableOpacity
                style={styles.viewFullButton}
                onPress={() => Alert.alert('보고서 탭에서 전체 내용을 확인하세요')}
              >
                <Text style={styles.viewFullButtonText}>전체 보고서 보기</Text>
                <Icon name="arrow-forward" size={20} color="#667eea" />
              </TouchableOpacity>
            </View>
          )}
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f7fafc',
  },
  containerDark: {
    backgroundColor: '#1a202c',
  },
  header: {
    paddingTop: 40,
    paddingBottom: 40,
    paddingHorizontal: 20,
    alignItems: 'center',
    borderBottomLeftRadius: 30,
    borderBottomRightRadius: 30,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
    marginTop: 10,
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#ffffff',
    opacity: 0.9,
    marginTop: 5,
    textAlign: 'center',
  },
  content: {
    padding: 20,
  },
  contentDark: {
    backgroundColor: '#1a202c',
  },
  inputSection: {
    marginBottom: 25,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 10,
    color: '#2d3748',
  },
  textDark: {
    color: '#e2e8f0',
  },
  input: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    paddingHorizontal: 15,
    paddingVertical: 15,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    minHeight: 100,
  },
  inputDark: {
    backgroundColor: '#2d3748',
    borderColor: '#4a5568',
    color: '#e2e8f0',
  },
  helperText: {
    fontSize: 14,
    color: '#718096',
    marginTop: 8,
  },
  helperTextDark: {
    color: '#a0aec0',
  },
  lengthSection: {
    marginBottom: 30,
  },
  lengthButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  lengthButton: {
    flex: 1,
    backgroundColor: '#ffffff',
    paddingVertical: 15,
    paddingHorizontal: 10,
    marginHorizontal: 5,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#e2e8f0',
  },
  lengthButtonDark: {
    backgroundColor: '#2d3748',
    borderColor: '#4a5568',
  },
  lengthButtonActive: {
    borderColor: '#667eea',
    backgroundColor: '#f0f4ff',
  },
  lengthButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#4a5568',
  },
  lengthButtonTextActive: {
    color: '#667eea',
  },
  lengthButtonSubtext: {
    fontSize: 12,
    color: '#718096',
    marginTop: 2,
  },
  analyzeButton: {
    marginBottom: 20,
  },
  analyzeButtonDisabled: {
    opacity: 0.6,
  },
  analyzeButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 18,
    borderRadius: 12,
  },
  analyzeButtonText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: 'bold',
    marginLeft: 10,
  },
  progressCard: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 25,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
    marginBottom: 20,
  },
  cardDark: {
    backgroundColor: '#2d3748',
  },
  progressCircleContainer: {
    alignItems: 'center',
    marginBottom: 20,
  },
  progressCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
    overflow: 'hidden',
  },
  progressCircleFill: {
    position: 'absolute',
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#667eea',
    opacity: 0.2,
  },
  progressCircleInner: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#ffffff',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1,
  },
  progressPercentage: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#667eea',
  },
  progressTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 10,
    color: '#2d3748',
    textAlign: 'center',
  },
  progressDetails: {
    fontSize: 14,
    color: '#718096',
    textAlign: 'center',
    marginBottom: 20,
  },
  progressBarContainer: {
    width: '100%',
    marginBottom: 20,
  },
  progressBar: {
    width: '100%',
    height: 8,
    backgroundColor: '#e2e8f0',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#667eea',
    borderRadius: 4,
  },
  stageIndicators: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
    marginTop: 10,
  },
  stageIndicator: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 4,
    borderRadius: 8,
    backgroundColor: '#f7fafc',
    marginHorizontal: 2,
  },
  stageActive: {
    backgroundColor: '#667eea',
  },
  stageText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4a5568',
  },
  resultCard: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  resultHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15,
  },
  resultTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginLeft: 10,
    color: '#2d3748',
  },
  resultMeta: {
    flexDirection: 'row',
    marginBottom: 15,
  },
  metaText: {
    fontSize: 14,
    color: '#718096',
    marginRight: 15,
  },
  resultContent: {
    maxHeight: 200,
    marginBottom: 15,
  },
  resultText: {
    fontSize: 16,
    lineHeight: 24,
    color: '#4a5568',
  },
  viewFullButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
  },
  viewFullButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#667eea',
    marginRight: 5,
  },
  estimatedTimeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 10,
    paddingHorizontal: 20,
    paddingVertical: 8,
    backgroundColor: '#f7fafc',
    borderRadius: 20,
  },
  estimatedTimeText: {
    fontSize: 14,
    color: '#4a5568',
    marginLeft: 8,
  },
  notificationInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 8,
  },
  notificationText: {
    fontSize: 13,
    color: '#48bb78',
    marginLeft: 6,
  },
});

export default HomeScreen;