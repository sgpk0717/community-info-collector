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
  Platform,
  Modal,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialIcons as Icon } from '@expo/vector-icons';
import DateTimePicker from '@react-native-community/datetimepicker';
import * as Notifications from 'expo-notifications';
import ApiService from '../services/api.service';
import AuthService from '../services/auth.service';
import { useAuth } from '../context/AuthContext';

interface ScheduleForm {
  intervalMinutes: number;
  keywords: string[];
  startTime: Date;
  notificationEnabled: boolean;
  totalRuns: number | 'unlimited';
  customRuns?: number;
}

const ScheduleCreateScreen: React.FC = () => {
  const isDarkMode = useColorScheme() === 'dark';
  const { user } = useAuth();
  
  // 다음 10분 단위 시간 계산
  const getNextTenMinutes = () => {
    const now = new Date();
    const next = new Date(now);
    const minutes = next.getMinutes();
    const nextMinutes = Math.ceil((minutes + 5) / 10) * 10; // 5분 여유 추가
    
    if (nextMinutes >= 60) {
      next.setHours(next.getHours() + 1, nextMinutes - 60, 0, 0);
    } else {
      next.setMinutes(nextMinutes, 0, 0);
    }
    
    return next;
  };
  
  const [scheduleForm, setScheduleForm] = useState<ScheduleForm>({
    intervalMinutes: 10, // 기본값을 10분으로 설정
    keywords: [''],
    startTime: getNextTenMinutes(),
    notificationEnabled: false,
    totalRuns: 3,
    customRuns: undefined,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showTimePicker, setShowTimePicker] = useState(false);
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [calculatedEndTime, setCalculatedEndTime] = useState<Date | null>(null);
  const [showCustomTimePicker, setShowCustomTimePicker] = useState(false);

  // 마지막 실행 시점 계산
  useEffect(() => {
    calculateEndTime();
  }, [scheduleForm.startTime, scheduleForm.intervalMinutes, scheduleForm.totalRuns, scheduleForm.customRuns]);

  const calculateEndTime = () => {
    const { startTime, intervalMinutes, totalRuns, customRuns } = scheduleForm;
    let runs = totalRuns;
    
    if (totalRuns === 'unlimited') {
      setCalculatedEndTime(null);
      return;
    }
    
    if (totalRuns === 'custom' && customRuns) {
      runs = customRuns;
    }
    
    if (typeof runs === 'number' && runs > 1) {
      const endTime = new Date(startTime.getTime() + (runs - 1) * intervalMinutes * 60 * 1000);
      setCalculatedEndTime(endTime);
    } else {
      setCalculatedEndTime(null);
    }
  };

  // 푸시 알림 권한 요청
  const requestNotificationPermission = async () => {
    try {
      const { status } = await Notifications.requestPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('권한 필요', '푸시 알림을 받으려면 알림 권한을 허용해주세요.');
        return false;
      }
      return true;
    } catch (error) {
      console.error('Notification permission error:', error);
      return false;
    }
  };

  // 스케줄 등록
  const handleScheduleCreate = async () => {
    const validKeywords = scheduleForm.keywords.filter(k => k.trim());
    if (validKeywords.length === 0) {
      Alert.alert('알림', '최소 하나 이상의 키워드를 입력해주세요.');
      return;
    }

    // 푸시 알림 권한 확인
    if (scheduleForm.notificationEnabled) {
      const hasPermission = await requestNotificationPermission();
      if (!hasPermission) {
        setScheduleForm({ ...scheduleForm, notificationEnabled: false });
        return;
      }
    }

    setIsLoading(true);
    try {
      let totalReports: number;
      if (scheduleForm.totalRuns === 'unlimited') {
        totalReports = -1; // 서버에서 무제한을 -1로 처리
      } else if (scheduleForm.totalRuns === 'custom' && scheduleForm.customRuns) {
        totalReports = scheduleForm.customRuns;
      } else if (typeof scheduleForm.totalRuns === 'number') {
        totalReports = scheduleForm.totalRuns;
      } else {
        totalReports = 3; // 기본값
      }

      const scheduleData = {
        keyword: validKeywords.join(', '), // 키워드들을 문자열로 합침
        interval_minutes: scheduleForm.intervalMinutes,
        total_reports: totalReports,
        start_time: scheduleForm.startTime.toISOString(),
        notification_enabled: scheduleForm.notificationEnabled,
        user_nickname: user?.nickname || '',
      };

      console.log('로컬 시간:', scheduleForm.startTime.toString());
      console.log('ISO 시간:', scheduleForm.startTime.toISOString());
      console.log('스케줄 생성 요청 데이터:', scheduleData);
      const result = await ApiService.createNewSchedule(scheduleData);
      console.log('스케줄 생성 응답:', result);
      
      if (result.success) {
        Alert.alert('성공', '스케줄이 등록되었습니다!', [
          { text: '확인', onPress: () => resetForm() }
        ]);
      } else {
        console.error('스케줄 등록 실패:', result.error);
        Alert.alert('오류', result.error || '스케줄 등록에 실패했습니다.');
      }
    } catch (error) {
      console.error('스케줄 등록 예외:', error);
      Alert.alert('오류', '스케줄 등록에 실패했습니다.');
    }
    setIsLoading(false);
  };

  // 폼 초기화
  const resetForm = () => {
    setScheduleForm({
      intervalMinutes: 10, // 기본값을 10분으로 설정
      keywords: [''],
      startTime: getNextTenMinutes(),
      notificationEnabled: false,
      totalRuns: 3,
      customRuns: undefined,
    });
    setShowCustomInput(false);
  };

  const updateKeyword = (index: number, value: string) => {
    const newKeywords = [...scheduleForm.keywords];
    newKeywords[index] = value;
    setScheduleForm({ ...scheduleForm, keywords: newKeywords });
  };

  const addKeyword = () => {
    setScheduleForm({
      ...scheduleForm,
      keywords: [...scheduleForm.keywords, ''],
    });
  };

  const removeKeyword = (index: number) => {
    const newKeywords = scheduleForm.keywords.filter((_, i) => i !== index);
    setScheduleForm({
      ...scheduleForm,
      keywords: newKeywords.length > 0 ? newKeywords : [''],
    });
  };

  // 날짜 변경 핸들러
  const handleDateChange = (event: any, selectedDate?: Date) => {
    setShowDatePicker(Platform.OS === 'ios');
    if (selectedDate) {
      const newDateTime = new Date(scheduleForm.startTime);
      newDateTime.setFullYear(selectedDate.getFullYear());
      newDateTime.setMonth(selectedDate.getMonth());
      newDateTime.setDate(selectedDate.getDate());
      setScheduleForm({ ...scheduleForm, startTime: newDateTime });
    }
  };

  // 시간 변경 핸들러
  const handleTimeChange = (event: any, selectedTime?: Date) => {
    setShowTimePicker(Platform.OS === 'ios');
    if (selectedTime) {
      const newDateTime = new Date(scheduleForm.startTime);
      newDateTime.setHours(selectedTime.getHours());
      newDateTime.setMinutes(0); // 정시로 설정
      newDateTime.setSeconds(0);
      newDateTime.setMilliseconds(0);
      setScheduleForm({ ...scheduleForm, startTime: newDateTime });
    }
  };

  // 커스텀 시간 선택기 컴포넌트
  const CustomTimePicker = () => {
    const hours = Array.from({ length: 24 }, (_, i) => i);
    // 분 선택 제거 (정시만 선택 가능)
    const selectedHour = scheduleForm.startTime.getHours();
    const selectedMinute = scheduleForm.startTime.getMinutes();
    const [tempHour, setTempHour] = React.useState(selectedHour);
    const [tempMinute, setTempMinute] = React.useState(selectedMinute);
    
    return (
      <Modal
        visible={showCustomTimePicker}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setShowCustomTimePicker(false)}
      >
        <TouchableOpacity 
          style={[styles.customTimePickerModal, isDarkMode && styles.customTimePickerModalDark]}
          activeOpacity={1}
          onPress={() => setShowCustomTimePicker(false)}
        >
          <TouchableOpacity 
            activeOpacity={1}
            style={[styles.customTimePickerContainer, isDarkMode && styles.customTimePickerContainerDark]}
            onPress={(e) => e.stopPropagation()}
          >
          <View style={[styles.customTimePickerHeader, isDarkMode && { borderBottomColor: '#2a3040' }]}>
            <Text style={[styles.customTimePickerTitle, isDarkMode && styles.textDark]}>
              시간 선택
            </Text>
            <TouchableOpacity onPress={() => setShowCustomTimePicker(false)}>
              <Icon name="close" size={24} color={isDarkMode ? '#e2e8f0' : '#2d3748'} />
            </TouchableOpacity>
          </View>
          
          <ScrollView style={styles.customTimePickerScroll} showsVerticalScrollIndicator={false}>
            <Text style={[styles.customTimePickerSectionTitle, isDarkMode && styles.textDark]}>시간</Text>
            <View style={styles.customTimePickerGrid}>
              {hours.map((hour) => {
                const isSelected = hour === tempHour;
                const isPM = hour >= 12;
                const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
                
                return (
                  <TouchableOpacity
                    key={hour}
                    style={[
                      styles.customTimePickerItem,
                      isDarkMode && styles.customTimePickerItemDark,
                      isSelected && styles.customTimePickerItemSelected,
                      isSelected && isDarkMode && { backgroundColor: '#2a3040' },
                    ]}
                    onPress={() => setTempHour(hour)}
                  >
                    <Text
                      style={[
                        styles.customTimePickerItemText,
                        isDarkMode && styles.textDark,
                        isSelected && styles.customTimePickerItemTextSelected,
                      ]}
                    >
                      {displayHour}
                    </Text>
                    <Text
                      style={[
                        styles.customTimePickerItemPeriod,
                        isDarkMode && styles.subtextDark,
                        isSelected && styles.customTimePickerItemTextSelected,
                      ]}
                    >
                      {isPM ? '오후' : '오전'}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
            
            {/* 10분 단위 분 선택 */}
            <Text style={[styles.customTimePickerSectionTitle, isDarkMode && styles.textDark, { marginTop: 20 }]}>분</Text>
            <View style={styles.customTimePickerGrid}>
              {[0, 10, 20, 30, 40, 50].map((minute) => {
                const isSelected = minute === tempMinute;
                
                return (
                  <TouchableOpacity
                    key={minute}
                    style={[
                      styles.customTimePickerItem,
                      isDarkMode && styles.customTimePickerItemDark,
                      isSelected && styles.customTimePickerItemSelected,
                      isSelected && isDarkMode && { backgroundColor: '#2a3040' },
                    ]}
                    onPress={() => setTempMinute(minute)}
                  >
                    <Text
                      style={[
                        styles.customTimePickerItemText,
                        isDarkMode && styles.textDark,
                        isSelected && styles.customTimePickerItemTextSelected,
                      ]}
                    >
                      {minute.toString().padStart(2, '0')}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </ScrollView>
          
            <TouchableOpacity
              style={[styles.customTimePickerButton, isDarkMode && styles.customTimePickerButtonDark]}
              onPress={() => {
                const newDateTime = new Date(scheduleForm.startTime);
                newDateTime.setHours(tempHour);
                newDateTime.setMinutes(tempMinute); // 10분 단위로 설정
                newDateTime.setSeconds(0);
                newDateTime.setMilliseconds(0);
                setScheduleForm({ ...scheduleForm, startTime: newDateTime });
                setShowCustomTimePicker(false);
              }}
            >
              <Text style={styles.customTimePickerButtonText}>완료</Text>
            </TouchableOpacity>
          </TouchableOpacity>
        </TouchableOpacity>
      </Modal>
    );
  };

  const IntervalButton = ({ minutes, label }: { minutes: number; label: string }) => (
    <TouchableOpacity
      style={[
        styles.intervalButton,
        scheduleForm.intervalMinutes === minutes && styles.intervalButtonActive,
        isDarkMode && styles.intervalButtonDark,
      ]}
      onPress={() => setScheduleForm({ ...scheduleForm, intervalMinutes: minutes })}
    >
      <Text
        style={[
          styles.intervalButtonText,
          scheduleForm.intervalMinutes === minutes && styles.intervalButtonTextActive,
          isDarkMode && styles.textDark,
        ]}
      >
        {label}
      </Text>
    </TouchableOpacity>
  );

  const TotalRunsButton = ({ runs, label }: { runs: number | 'unlimited' | 'custom'; label: string }) => (
    <TouchableOpacity
      style={[
        styles.intervalButton,
        scheduleForm.totalRuns === runs && styles.intervalButtonActive,
        isDarkMode && styles.intervalButtonDark,
      ]}
      onPress={() => {
        setScheduleForm({ ...scheduleForm, totalRuns: runs });
        if (runs === 'custom') {
          setShowCustomInput(true);
        } else {
          setShowCustomInput(false);
        }
      }}
    >
      <Text
        style={[
          styles.intervalButtonText,
          scheduleForm.totalRuns === runs && styles.intervalButtonTextActive,
          isDarkMode && styles.textDark,
        ]}
      >
        {label}
      </Text>
    </TouchableOpacity>
  );

  return (
    <>
      <ScrollView style={[styles.container, isDarkMode && styles.containerDark]}>
      <LinearGradient
        colors={isDarkMode ? ['#1a1f2e', '#0a0e1a'] : ['#667eea', '#764ba2']}
        style={styles.header}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        <View style={styles.headerIconContainer}>
          <Icon name="schedule" size={56} color="#ffffff" />
        </View>
        <Text style={styles.headerTitle}>스케줄 등록</Text>
        <Text style={styles.headerSubtitle}>정기 분석 스케줄을 등록하세요</Text>
      </LinearGradient>

      <View style={[styles.content, isDarkMode && styles.contentDark]}>
        {/* 사용자 정보 표시 */}
        <View style={[styles.card, isDarkMode && styles.cardDark]}>
          <Text style={[styles.sectionTitle, isDarkMode && styles.textDark]}>
            등록자 정보
          </Text>
          <View style={[styles.userInfoDisplay, isDarkMode && { backgroundColor: '#2a3040' }]}>
            <Icon name="person" size={20} color={isDarkMode ? '#a78bfa' : '#667eea'} />
            <Text style={[styles.userNameText, isDarkMode && styles.textDark]}>
              {user?.nickname || '사용자'}
            </Text>
          </View>
        </View>

        {/* 실행 간격 설정 */}
        <View style={[styles.card, isDarkMode && styles.cardDark]}>
          <Text style={[styles.sectionTitle, isDarkMode && styles.textDark]}>
            실행 간격
          </Text>
          <View style={styles.intervalButtons}>
            <IntervalButton minutes={10} label="10분" />
            <IntervalButton minutes={30} label="30분" />
            <IntervalButton minutes={60} label="1시간" />
            <IntervalButton minutes={180} label="3시간" />
          </View>
        </View>

        {/* 시작 시간 설정 */}
        <View style={[styles.card, isDarkMode && styles.cardDark]}>
          <Text style={[styles.sectionTitle, isDarkMode && styles.textDark]}>
            시작 시간
          </Text>
          
          {/* 날짜 선택 */}
          <TouchableOpacity
            style={[styles.timeButton, isDarkMode && styles.timeButtonDark]}
            onPress={() => setShowDatePicker(true)}
          >
            <Icon name="event" size={20} color="#667eea" />
            <Text style={[styles.timeButtonText, isDarkMode && styles.textDark]}>
              {scheduleForm.startTime.toLocaleDateString('ko-KR')}
            </Text>
            <Icon name="keyboard-arrow-right" size={20} color="#667eea" />
          </TouchableOpacity>
          
          {/* 시간 선택 */}
          <TouchableOpacity
            style={[styles.timeButton, isDarkMode && styles.timeButtonDark, { marginTop: 10 }]}
            onPress={() => setShowCustomTimePicker(true)}
          >
            <Icon name="schedule" size={20} color="#667eea" />
            <Text style={[styles.timeButtonText, isDarkMode && styles.textDark]}>
              {/* 시간:분 표시 */}
              {scheduleForm.startTime.toLocaleTimeString('ko-KR', { 
                hour: '2-digit',
                minute: '2-digit',
                hour12: true 
              })}
            </Text>
            <Icon name="keyboard-arrow-right" size={20} color="#667eea" />
          </TouchableOpacity>
          
          {showDatePicker && (
            <DateTimePicker
              value={scheduleForm.startTime}
              mode="date"
              display="default"
              onChange={handleDateChange}
            />
          )}
        </View>

        {/* 분석할 키워드 */}
        <View style={[styles.card, isDarkMode && styles.cardDark]}>
          <Text style={[styles.sectionTitle, isDarkMode && styles.textDark]}>
            분석할 키워드
          </Text>
          {scheduleForm.keywords.map((keyword, index) => (
            <View key={index} style={styles.keywordRow}>
              <TextInput
                style={[styles.keywordInput, isDarkMode && styles.inputDark]}
                placeholder="키워드 입력"
                placeholderTextColor={isDarkMode ? '#888' : '#999'}
                value={keyword}
                onChangeText={(value) => updateKeyword(index, value)}
              />
              {scheduleForm.keywords.length > 1 && (
                <TouchableOpacity onPress={() => removeKeyword(index)}>
                  <Icon name="remove-circle" size={24} color="#e53e3e" />
                </TouchableOpacity>
              )}
            </View>
          ))}
          
          <TouchableOpacity style={styles.addKeywordButton} onPress={addKeyword}>
            <Icon name="add-circle" size={24} color="#667eea" />
            <Text style={styles.addKeywordText}>키워드 추가</Text>
          </TouchableOpacity>
        </View>

        {/* 총 실행 횟수 */}
        <View style={[styles.card, isDarkMode && styles.cardDark]}>
          <Text style={[styles.sectionTitle, isDarkMode && styles.textDark]}>
            총 실행 횟수
          </Text>
          <View style={styles.intervalButtons}>
            <TotalRunsButton runs={3} label="3회" />
            <TotalRunsButton runs={5} label="5회" />
            <TotalRunsButton runs={10} label="10회" />
            <TotalRunsButton runs="unlimited" label="무제한" />
          </View>
          
          <View style={[styles.intervalButtons, { marginTop: 10 }]}>
            <TotalRunsButton runs="custom" label="직접입력" />
          </View>
          
          {showCustomInput && (
            <View style={styles.customInputContainer}>
              <TextInput
                style={[styles.customInput, isDarkMode && styles.inputDark]}
                placeholder="실행 횟수를 입력하세요"
                placeholderTextColor={isDarkMode ? '#888' : '#999'}
                value={scheduleForm.customRuns?.toString() || ''}
                onChangeText={(text) => {
                  const num = parseInt(text) || 0;
                  setScheduleForm({ ...scheduleForm, customRuns: num > 0 ? num : undefined });
                }}
                keyboardType="numeric"
                maxLength={3}
              />
              <Text style={[styles.customInputLabel, isDarkMode && styles.subtextDark]}>
                회
              </Text>
            </View>
          )}
          
          {calculatedEndTime && (
            <View style={styles.endTimeContainer}>
              <Icon name="event" size={16} color="#667eea" />
              <Text style={[styles.endTimeText, isDarkMode && styles.textDark]}>
                마지막 실행: {calculatedEndTime.toLocaleString('ko-KR')}
              </Text>
            </View>
          )}
          
          {scheduleForm.totalRuns === 'unlimited' && (
            <View style={styles.endTimeContainer}>
              <Icon name="all-inclusive" size={16} color="#48bb78" />
              <Text style={[styles.endTimeText, isDarkMode && styles.textDark, { color: '#48bb78' }]}>
                무제한으로 실행됩니다
              </Text>
            </View>
          )}
        </View>

        {/* 푸시 알림 설정 */}
        <View style={[styles.card, isDarkMode && styles.cardDark]}>
          <View style={[styles.switchContainer, isDarkMode && { backgroundColor: '#0a0e1a' }]}>
            <View>
              <Text style={[styles.switchLabel, isDarkMode && styles.textDark]}>
                푸시 알림
              </Text>
              <Text style={[styles.switchSubtext, isDarkMode && styles.subtextDark]}>
                분석 완료 시 알림을 받습니다
              </Text>
            </View>
            <Switch
              value={scheduleForm.notificationEnabled}
              onValueChange={(value) => setScheduleForm({ ...scheduleForm, notificationEnabled: value })}
              trackColor={{ false: '#767577', true: '#667eea' }}
              thumbColor={scheduleForm.notificationEnabled ? '#764ba2' : '#f4f3f4'}
            />
          </View>
        </View>

        {/* 등록 버튼 */}
        <TouchableOpacity
          style={[styles.createButton, isDarkMode && styles.createButtonDark, isLoading && styles.createButtonDisabled]}
          onPress={handleScheduleCreate}
          disabled={isLoading}
        >
          <LinearGradient
            colors={isLoading ? ['#ccc', '#999'] : isDarkMode ? ['#5a67d8', '#553c9a'] : ['#667eea', '#764ba2']}
            style={styles.createButtonGradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          >
            <Icon name={isLoading ? "hourglass-empty" : "add-alarm"} size={20} color="#ffffff" />
            <Text style={styles.createButtonText}>
              {isLoading ? '등록 중...' : '스케줄 등록'}
            </Text>
          </LinearGradient>
        </TouchableOpacity>

        <View style={styles.footer}>
          <Text style={[styles.footerText, isDarkMode && styles.subtextDark]}>
            스케줄은 서버에서 자동으로 실행됩니다
          </Text>
        </View>
      </View>
    </ScrollView>
    
    {/* 커스텀 시간 선택기 */}
    <CustomTimePicker />
    </>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  containerDark: {
    backgroundColor: '#0a0e1a',
  },
  header: {
    paddingTop: 60,
    paddingBottom: 50,
    paddingHorizontal: 20,
    alignItems: 'center',
    borderBottomLeftRadius: 30,
    borderBottomRightRadius: 30,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.15,
    shadowRadius: 20,
    elevation: 10,
  },
  headerTitle: {
    fontSize: 32,
    fontWeight: '800',
    color: '#ffffff',
    marginTop: 15,
    letterSpacing: -0.5,
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#ffffff',
    opacity: 0.85,
    marginTop: 8,
    textAlign: 'center',
    fontWeight: '500',
  },
  content: {
    padding: 20,
    marginTop: -20,
  },
  contentDark: {
    backgroundColor: '#0a0e1a',
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 20,
    padding: 24,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 4,
    borderWidth: 1,
    borderColor: '#f0f0f0',
  },
  cardDark: {
    backgroundColor: '#1a1f2e',
    borderColor: '#2a3040',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 20,
    color: '#1a1a1a',
    letterSpacing: -0.3,
  },
  userInfoDisplay: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
  },
  userNameText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#2d3748',
    marginLeft: 12,
  },
  timeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
    borderRadius: 14,
    paddingVertical: 16,
    paddingHorizontal: 18,
    borderWidth: 1.5,
    borderColor: '#e2e8f0',
  },
  timeButtonDark: {
    backgroundColor: '#0a0e1a',
    borderColor: '#2a3040',
  },
  timeButtonText: {
    flex: 1,
    fontSize: 16,
    color: '#2d3748',
    marginLeft: 12,
    fontWeight: '600',
  },
  endTimeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
    backgroundColor: '#f8f9fa',
    marginHorizontal: -4,
    paddingHorizontal: 12,
    paddingBottom: 12,
    borderRadius: 12,
  },
  endTimeText: {
    fontSize: 14,
    color: '#4a5568',
    marginLeft: 8,
    fontStyle: 'italic',
    fontWeight: '500',
  },
  createButton: {
    borderRadius: 18,
    marginTop: 20,
    marginBottom: 20,
    overflow: 'hidden',
    shadowColor: '#667eea',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
  },
  createButtonDark: {
    shadowColor: '#764ba2',
  },
  createButtonDisabled: {
    opacity: 0.6,
    shadowOpacity: 0.1,
  },
  createButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 18,
    paddingHorizontal: 24,
  },
  createButtonText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#ffffff',
    marginLeft: 10,
    letterSpacing: -0.3,
  },
  switchContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
    padding: 16,
    borderRadius: 14,
  },
  switchLabel: {
    fontSize: 16,
    fontWeight: '700',
    color: '#2d3748',
  },
  switchSubtext: {
    fontSize: 14,
    color: '#718096',
    marginTop: 4,
    fontWeight: '500',
  },
  textDark: {
    color: '#e2e8f0',
  },
  subtextDark: {
    color: '#a0aec0',
  },
  intervalButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -6,
  },
  intervalButton: {
    backgroundColor: '#ffffff',
    paddingVertical: 12,
    paddingHorizontal: 24,
    margin: 6,
    borderRadius: 14,
    borderWidth: 2,
    borderColor: '#e8e8e8',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 2,
  },
  intervalButtonDark: {
    backgroundColor: '#2a3040',
    borderColor: '#3a4050',
  },
  intervalButtonActive: {
    borderColor: '#667eea',
    backgroundColor: '#f0f4ff',
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 3,
  },
  intervalButtonText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#4a5568',
  },
  intervalButtonTextActive: {
    color: '#667eea',
  },
  keywordRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  keywordInput: {
    flex: 1,
    backgroundColor: '#f8f9fa',
    borderRadius: 14,
    paddingHorizontal: 18,
    paddingVertical: 14,
    fontSize: 16,
    borderWidth: 1.5,
    borderColor: '#e2e8f0',
    marginRight: 12,
    fontWeight: '500',
  },
  inputDark: {
    backgroundColor: '#0a0e1a',
    borderColor: '#2a3040',
    color: '#e2e8f0',
  },
  addKeywordButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
    backgroundColor: '#f0f4ff',
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 12,
    alignSelf: 'flex-start',
  },
  addKeywordText: {
    fontSize: 15,
    color: '#667eea',
    marginLeft: 8,
    fontWeight: '700',
  },
  headerIconContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 20,
    padding: 16,
  },
  footer: {
    alignItems: 'center',
    marginTop: 30,
    marginBottom: 40,
  },
  footerText: {
    fontSize: 14,
    color: '#718096',
    textAlign: 'center',
    fontWeight: '500',
  },
  customInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
  },
  customInput: {
    flex: 1,
    backgroundColor: '#f8f9fa',
    borderRadius: 14,
    paddingHorizontal: 18,
    paddingVertical: 12,
    fontSize: 16,
    borderWidth: 1.5,
    borderColor: '#e2e8f0',
    marginRight: 12,
    fontWeight: '600',
  },
  customInputLabel: {
    fontSize: 16,
    color: '#4a5568',
    fontWeight: '700',
  },
  customTimePickerModal: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  customTimePickerModalDark: {
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
  },
  customTimePickerContainer: {
    backgroundColor: '#ffffff',
    borderRadius: 24,
    width: '90%',
    maxWidth: 400,
    maxHeight: '80%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.25,
    shadowRadius: 20,
    elevation: 10,
  },
  customTimePickerContainerDark: {
    backgroundColor: '#1a1f2e',
  },
  customTimePickerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  customTimePickerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#2d3748',
  },
  customTimePickerScroll: {
    maxHeight: 400,
  },
  customTimePickerGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 10,
  },
  customTimePickerItem: {
    width: '25%',
    padding: 10,
    alignItems: 'center',
    justifyContent: 'center',
    height: 80,
  },
  customTimePickerItemDark: {
    backgroundColor: 'transparent',
  },
  customTimePickerItemSelected: {
    backgroundColor: '#f0f4ff',
    borderRadius: 16,
    transform: [{ scale: 1.05 }],
  },
  customTimePickerItemText: {
    fontSize: 24,
    fontWeight: '700',
    color: '#4a5568',
    marginBottom: 4,
  },
  customTimePickerItemTextSelected: {
    color: '#667eea',
  },
  customTimePickerItemPeriod: {
    fontSize: 12,
    color: '#718096',
    fontWeight: '600',
  },
  customTimePickerButton: {
    backgroundColor: '#667eea',
    margin: 20,
    paddingVertical: 16,
    borderRadius: 16,
    alignItems: 'center',
  },
  customTimePickerButtonDark: {
    backgroundColor: '#5a67d8',
  },
  customTimePickerButtonText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '700',
  },
  customTimePickerSectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#2d3748',
    marginBottom: 10,
    paddingHorizontal: 10,
  },
});

export default ScheduleCreateScreen;
