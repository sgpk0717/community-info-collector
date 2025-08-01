import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Switch,
  Alert,
  useColorScheme,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialIcons as Icon } from '@expo/vector-icons';
import ApiService from '../services/api.service';
import AuthService from '../services/auth.service';
import StorageService from '../services/storage.service';

interface ScheduleSettings {
  enabled: boolean;
  intervalMinutes: number;
  keywords: string[];
  nextRun?: string;
  lastRun?: string;
}

const SettingsScreen: React.FC = () => {
  const isDarkMode = useColorScheme() === 'dark';
  const [userName, setUserName] = useState('');
  const [notificationEnabled, setNotificationEnabled] = useState(true);
  const [scheduleSettings, setScheduleSettings] = useState<ScheduleSettings>({
    enabled: false,
    intervalMinutes: 360,
    keywords: [''],
  });
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    const user = AuthService.getCurrentUser();
    if (user) {
      setUserName(user.name || '');
    }

    // 스케줄 설정 불러오기
    try {
      const status = await ApiService.getScheduleStatus();
      if (status) {
        setScheduleSettings(status);
      }
    } catch (error) {
      console.error('Failed to load schedule status:', error);
    }
  };

  const handleScheduleToggle = async () => {
    const newEnabled = !scheduleSettings.enabled;
    
    if (newEnabled) {
      // 스케줄 활성화
      const validKeywords = scheduleSettings.keywords.filter(k => k.trim());
      if (validKeywords.length === 0) {
        Alert.alert('알림', '최소 하나 이상의 키워드를 입력해주세요.');
        return;
      }

      setIsLoading(true);
      try {
        const result = await ApiService.startSchedule({
          intervalMinutes: scheduleSettings.intervalMinutes,
          keywords: validKeywords,
        });

        if (result.success) {
          setScheduleSettings({ ...scheduleSettings, enabled: true });
          Alert.alert('성공', '스케줄이 활성화되었습니다.');
        } else {
          Alert.alert('오류', result.error || '스케줄 활성화에 실패했습니다.');
        }
      } catch (error) {
        Alert.alert('오류', '스케줄 설정에 실패했습니다.');
      }
      setIsLoading(false);
    } else {
      // 스케줄 비활성화
      Alert.alert(
        '스케줄 중지',
        '스케줄을 중지하시겠습니까?',
        [
          { text: '취소', style: 'cancel' },
          {
            text: '중지',
            style: 'destructive',
            onPress: async () => {
              setIsLoading(true);
              try {
                const result = await ApiService.stopSchedule();
                if (result.success) {
                  setScheduleSettings({ ...scheduleSettings, enabled: false });
                  Alert.alert('알림', '스케줄이 중지되었습니다.');
                }
              } catch (error) {
                Alert.alert('오류', '스케줄 중지에 실패했습니다.');
              }
              setIsLoading(false);
            },
          },
        ]
      );
    }
  };

  const updateKeyword = (index: number, value: string) => {
    const newKeywords = [...scheduleSettings.keywords];
    newKeywords[index] = value;
    setScheduleSettings({ ...scheduleSettings, keywords: newKeywords });
  };

  const addKeyword = () => {
    setScheduleSettings({
      ...scheduleSettings,
      keywords: [...scheduleSettings.keywords, ''],
    });
  };

  const removeKeyword = (index: number) => {
    const newKeywords = scheduleSettings.keywords.filter((_, i) => i !== index);
    setScheduleSettings({
      ...scheduleSettings,
      keywords: newKeywords.length > 0 ? newKeywords : [''],
    });
  };

  const IntervalButton = ({ minutes, label }: { minutes: number; label: string }) => (
    <TouchableOpacity
      style={[
        styles.intervalButton,
        scheduleSettings.intervalMinutes === minutes && styles.intervalButtonActive,
        isDarkMode && styles.intervalButtonDark,
      ]}
      onPress={() => setScheduleSettings({ ...scheduleSettings, intervalMinutes: minutes })}
      disabled={scheduleSettings.enabled}
    >
      <Text
        style={[
          styles.intervalButtonText,
          scheduleSettings.intervalMinutes === minutes && styles.intervalButtonTextActive,
          isDarkMode && styles.textDark,
          scheduleSettings.enabled && styles.disabledText,
        ]}
      >
        {label}
      </Text>
    </TouchableOpacity>
  );

  const handleLogout = () => {
    Alert.alert(
      '로그아웃',
      '모든 데이터가 삭제됩니다. 정말 로그아웃하시겠습니까?',
      [
        { text: '취소', style: 'cancel' },
        {
          text: '로그아웃',
          style: 'destructive',
          onPress: async () => {
            await AuthService.logout();
            Alert.alert('알림', '로그아웃되었습니다.');
          },
        },
      ]
    );
  };

  return (
    <ScrollView style={[styles.container, isDarkMode && styles.containerDark]}>
      <LinearGradient
        colors={isDarkMode ? ['#2d3748', '#1a202c'] : ['#667eea', '#764ba2']}
        style={styles.header}
      >
        <Icon name="settings" size={50} color="#ffffff" />
        <Text style={styles.headerTitle}>설정</Text>
        <Text style={styles.headerSubtitle}>앱 설정 및 스케줄 관리</Text>
      </LinearGradient>

      <View style={[styles.content, isDarkMode && styles.contentDark]}>
        {/* 사용자 정보 */}
        <View style={[styles.card, isDarkMode && styles.cardDark]}>
          <Text style={[styles.sectionTitle, isDarkMode && styles.textDark]}>
            사용자 정보
          </Text>
          <View style={styles.userInfoRow}>
            <Text style={[styles.label, isDarkMode && styles.textDark]}>이름</Text>
            <TextInput
              style={[styles.nameInput, isDarkMode && styles.inputDark]}
              placeholder="사용자 이름 (선택사항)"
              placeholderTextColor={isDarkMode ? '#888' : '#999'}
              value={userName}
              onChangeText={setUserName}
              onBlur={() => AuthService.updateUserName(userName)}
            />
          </View>
        </View>

        {/* 스케줄 설정 */}
        <View style={[styles.card, isDarkMode && styles.cardDark]}>
          <View style={styles.switchContainer}>
            <View>
              <Text style={[styles.switchLabel, isDarkMode && styles.textDark]}>
                스케줄 실행
              </Text>
              <Text style={[styles.switchSubtext, isDarkMode && styles.subtextDark]}>
                주기적으로 보고서를 자동 생성합니다
              </Text>
            </View>
            <Switch
              value={scheduleSettings.enabled}
              onValueChange={handleScheduleToggle}
              trackColor={{ false: '#767577', true: '#667eea' }}
              thumbColor={scheduleSettings.enabled ? '#764ba2' : '#f4f3f4'}
              disabled={isLoading}
            />
          </View>

          {scheduleSettings.enabled ? (
            <>
              <View style={styles.divider} />
              
              {/* 활성화된 스케줄 정보 표시 */}
              <View style={styles.scheduleInfoContainer}>
                <View style={styles.scheduleInfoRow}>
                  <Icon name="access-time" size={20} color="#667eea" />
                  <Text style={[styles.scheduleInfoLabel, isDarkMode && styles.textDark]}>
                    실행 간격
                  </Text>
                  <Text style={[styles.scheduleInfoValue, isDarkMode && styles.textDark]}>
                    {scheduleSettings.intervalMinutes / 60}시간마다
                  </Text>
                </View>

                {scheduleSettings.nextRun && (
                  <View style={styles.scheduleInfoRow}>
                    <Icon name="schedule" size={20} color="#667eea" />
                    <Text style={[styles.scheduleInfoLabel, isDarkMode && styles.textDark]}>
                      다음 실행
                    </Text>
                    <Text style={[styles.scheduleInfoValue, isDarkMode && styles.textDark]}>
                      {new Date(scheduleSettings.nextRun).toLocaleString('ko-KR')}
                    </Text>
                  </View>
                )}

                {scheduleSettings.lastRun && (
                  <View style={styles.scheduleInfoRow}>
                    <Icon name="history" size={20} color="#667eea" />
                    <Text style={[styles.scheduleInfoLabel, isDarkMode && styles.textDark]}>
                      마지막 실행
                    </Text>
                    <Text style={[styles.scheduleInfoValue, isDarkMode && styles.textDark]}>
                      {new Date(scheduleSettings.lastRun).toLocaleString('ko-KR')}
                    </Text>
                  </View>
                )}

                <View style={styles.keywordsContainer}>
                  <Text style={[styles.subLabel, isDarkMode && styles.textDark]}>
                    분석 중인 키워드
                  </Text>
                  {scheduleSettings.keywords.map((keyword, index) => (
                    <View key={index} style={styles.activeKeywordItem}>
                      <Icon name="label" size={16} color="#667eea" />
                      <Text style={[styles.activeKeywordText, isDarkMode && styles.textDark]}>
                        {keyword}
                      </Text>
                    </View>
                  ))}
                </View>
              </View>
            </>
          ) : (
            <>
              <View style={styles.divider} />
              
              <Text style={[styles.subLabel, isDarkMode && styles.textDark]}>
                실행 간격
              </Text>
              <View style={styles.intervalButtons}>
                <IntervalButton minutes={60} label="1시간" />
                <IntervalButton minutes={360} label="6시간" />
                <IntervalButton minutes={720} label="12시간" />
                <IntervalButton minutes={1440} label="24시간" />
              </View>

              <Text style={[styles.subLabel, isDarkMode && styles.textDark, { marginTop: 20 }]}>
                분석할 키워드
              </Text>
              {scheduleSettings.keywords.map((keyword, index) => (
                <View key={index} style={styles.keywordRow}>
                  <TextInput
                    style={[styles.keywordInput, isDarkMode && styles.inputDark]}
                    placeholder="키워드 입력"
                    placeholderTextColor={isDarkMode ? '#888' : '#999'}
                    value={keyword}
                    onChangeText={(value) => updateKeyword(index, value)}
                    editable={!scheduleSettings.enabled}
                  />
                  {scheduleSettings.keywords.length > 1 && (
                    <TouchableOpacity
                      onPress={() => removeKeyword(index)}
                      disabled={scheduleSettings.enabled}
                    >
                      <Icon name="remove-circle" size={24} color="#e53e3e" />
                    </TouchableOpacity>
                  )}
                </View>
              ))}
              
              <TouchableOpacity
                style={styles.addKeywordButton}
                onPress={addKeyword}
                disabled={scheduleSettings.enabled}
              >
                <Icon name="add-circle" size={24} color="#667eea" />
                <Text style={styles.addKeywordText}>키워드 추가</Text>
              </TouchableOpacity>
            </>
          )}
        </View>

        {/* 알림 설정 */}
        <View style={[styles.card, isDarkMode && styles.cardDark]}>
          <View style={styles.switchContainer}>
            <View>
              <Text style={[styles.switchLabel, isDarkMode && styles.textDark]}>
                푸시 알림
              </Text>
              <Text style={[styles.switchSubtext, isDarkMode && styles.subtextDark]}>
                새 보고서 생성 시 알림을 받습니다
              </Text>
            </View>
            <Switch
              value={notificationEnabled}
              onValueChange={setNotificationEnabled}
              trackColor={{ false: '#767577', true: '#667eea' }}
              thumbColor={notificationEnabled ? '#764ba2' : '#f4f3f4'}
            />
          </View>
        </View>

        {/* 앱 정보 */}
        <View style={[styles.card, isDarkMode && styles.cardDark]}>
          <Text style={[styles.sectionTitle, isDarkMode && styles.textDark]}>
            앱 정보
          </Text>
          <View style={styles.infoRow}>
            <Text style={[styles.infoLabel, isDarkMode && styles.textDark]}>버전</Text>
            <Text style={[styles.infoValue, isDarkMode && styles.subtextDark]}>1.0.0</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={[styles.infoLabel, isDarkMode && styles.textDark]}>API 서버</Text>
            <Text style={[styles.infoValue, isDarkMode && styles.subtextDark]}>
              {process.env.API_BASE_URL || 'Not configured'}
            </Text>
          </View>
        </View>

        {/* 로그아웃 */}
        <TouchableOpacity
          style={[styles.logoutButton, isDarkMode && styles.logoutButtonDark]}
          onPress={handleLogout}
        >
          <Icon name="logout" size={20} color="#e53e3e" />
          <Text style={styles.logoutText}>로그아웃</Text>
        </TouchableOpacity>

        <View style={styles.footer}>
          <Text style={[styles.footerText, isDarkMode && styles.subtextDark]}>
            Reddit Community Info Collector
          </Text>
          <Text style={[styles.footerText, isDarkMode && styles.subtextDark]}>
            © 2025 All rights reserved
          </Text>
        </View>
      </View>
    </ScrollView>
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
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  cardDark: {
    backgroundColor: '#2d3748',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 15,
    color: '#2d3748',
  },
  switchContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  switchLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#2d3748',
  },
  switchSubtext: {
    fontSize: 14,
    color: '#718096',
    marginTop: 4,
  },
  label: {
    fontSize: 16,
    color: '#2d3748',
    marginRight: 10,
  },
  subLabel: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 10,
    color: '#2d3748',
  },
  textDark: {
    color: '#e2e8f0',
  },
  subtextDark: {
    color: '#a0aec0',
  },
  userInfoRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  nameInput: {
    flex: 1,
    backgroundColor: '#f7fafc',
    borderRadius: 12,
    paddingHorizontal: 15,
    paddingVertical: 10,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  inputDark: {
    backgroundColor: '#1a202c',
    borderColor: '#4a5568',
    color: '#e2e8f0',
  },
  divider: {
    height: 1,
    backgroundColor: '#e2e8f0',
    marginVertical: 20,
  },
  intervalButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -5,
  },
  intervalButton: {
    backgroundColor: '#ffffff',
    paddingVertical: 10,
    paddingHorizontal: 20,
    margin: 5,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#e2e8f0',
  },
  intervalButtonDark: {
    backgroundColor: '#4a5568',
    borderColor: '#718096',
  },
  intervalButtonActive: {
    borderColor: '#667eea',
    backgroundColor: '#f0f4ff',
  },
  intervalButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4a5568',
  },
  intervalButtonTextActive: {
    color: '#667eea',
  },
  disabledText: {
    opacity: 0.5,
  },
  keywordRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  keywordInput: {
    flex: 1,
    backgroundColor: '#f7fafc',
    borderRadius: 12,
    paddingHorizontal: 15,
    paddingVertical: 10,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    marginRight: 10,
  },
  addKeywordButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 10,
  },
  addKeywordText: {
    fontSize: 16,
    color: '#667eea',
    marginLeft: 8,
    fontWeight: '600',
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  infoLabel: {
    fontSize: 16,
    color: '#4a5568',
  },
  infoValue: {
    fontSize: 16,
    color: '#718096',
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fee',
    paddingVertical: 15,
    borderRadius: 12,
    marginTop: 10,
  },
  logoutButtonDark: {
    backgroundColor: '#742a2a',
  },
  logoutText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#e53e3e',
    marginLeft: 8,
  },
  footer: {
    alignItems: 'center',
    marginTop: 40,
    marginBottom: 20,
  },
  footerText: {
    fontSize: 14,
    color: '#718096',
    marginBottom: 5,
  },
  scheduleInfoContainer: {
    marginTop: 10,
  },
  scheduleInfoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
  },
  scheduleInfoLabel: {
    fontSize: 16,
    color: '#4a5568',
    marginLeft: 10,
    flex: 1,
  },
  scheduleInfoValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#2d3748',
  },
  keywordsContainer: {
    marginTop: 20,
  },
  activeKeywordItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f0f4ff',
    paddingHorizontal: 15,
    paddingVertical: 10,
    borderRadius: 12,
    marginBottom: 8,
  },
  activeKeywordText: {
    fontSize: 16,
    color: '#2d3748',
    marginLeft: 10,
    fontWeight: '500',
  },
});

export default SettingsScreen;