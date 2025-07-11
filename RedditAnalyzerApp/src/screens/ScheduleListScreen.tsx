import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  useColorScheme,
  RefreshControl,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialIcons as Icon } from '@expo/vector-icons';
import { useFocusEffect } from '@react-navigation/native';
import ApiService from '../services/api.service';
import { useAuth } from '../context/AuthContext';

interface Schedule {
  id: number;
  keyword: string;
  interval_minutes: number;
  total_reports: number;
  completed_reports: number;
  status: string;
  next_run?: string;
  last_run?: string;
  created_at: string;
  is_executing?: boolean;  // 기본값은 undefined이므로 falsy
}

const ScheduleListScreen: React.FC = () => {
  const isDarkMode = useColorScheme() === 'dark';
  const { user } = useAuth();
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [completedSchedules, setCompletedSchedules] = useState<Schedule[]>([]);
  const [cancelledSchedules, setCancelledSchedules] = useState<Schedule[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [showCompleted, setShowCompleted] = useState(false);
  const [showCancelled, setShowCancelled] = useState(false);

  useEffect(() => {
    loadSchedules();
  }, []);

  // 탭 포커스 시 데이터 새로고침
  useFocusEffect(
    useCallback(() => {
      loadSchedules();
    }, [])
  );

  const loadSchedules = async () => {
    if (!user?.nickname) return;
    
    setIsLoading(true);
    try {
      const result = await ApiService.getUserSchedules(user.nickname);
      if (result.success && result.data) {
        console.log('받은 스케줄 데이터:', result.data);
        
        // 디버깅: is_executing 상태 확인
        result.data.forEach((schedule: Schedule) => {
          console.log(`스케줄 ${schedule.id}: is_executing = ${schedule.is_executing}, status = ${schedule.status}, next_run = ${schedule.next_run}`);
        });
        
        // 활성, 완료, 취소된 스케줄 분리
        const activeSchedules = result.data.filter(
          (schedule: Schedule) => schedule.status === 'active' || schedule.status === 'paused'
        );
        const completed = result.data.filter(
          (schedule: Schedule) => schedule.status === 'completed'
        );
        const cancelled = result.data.filter(
          (schedule: Schedule) => schedule.status === 'cancelled'
        );
        
        // 디버깅: 첫 번째 활성 스케줄의 시간 정보 출력
        if (activeSchedules.length > 0 && activeSchedules[0].next_run) {
          console.log('첫 번째 스케줄 next_run:', activeSchedules[0].next_run);
          console.log('Date 객체로 변환:', new Date(activeSchedules[0].next_run));
          console.log('로컬 시간으로 표시:', new Date(activeSchedules[0].next_run).toLocaleString('ko-KR'));
        }
        
        setSchedules(activeSchedules);
        setCompletedSchedules(completed);
        setCancelledSchedules(cancelled);
      }
    } catch (error) {
      console.error('Failed to load schedules:', error);
    }
    setIsLoading(false);
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadSchedules();
    setRefreshing(false);
  };

  const deleteSchedule = (scheduleId: number, isCancelled: boolean = false) => {
    const alertTitle = isCancelled ? '스케줄 완전 삭제' : '스케줄 삭제';
    const alertMessage = isCancelled 
      ? '이 스케줄을 완전히 삭제하시겠습니까?\n삭제된 스케줄은 복구할 수 없습니다.'
      : '이 스케줄을 삭제하시겠습니까?';
    
    Alert.alert(
      alertTitle,
      alertMessage,
      [
        { text: '취소', style: 'cancel' },
        {
          text: '삭제',
          style: 'destructive',
          onPress: async () => {
            try {
              const result = await ApiService.deleteSchedule(scheduleId, isCancelled);
              if (result.success) {
                Alert.alert(
                  '성공', 
                  isCancelled ? '스케줄이 완전히 삭제되었습니다.' : '스케줄이 취소되었습니다.'
                );
                loadSchedules();
              } else {
                Alert.alert('오류', result.error || '삭제에 실패했습니다.');
              }
            } catch (error) {
              Alert.alert('오류', '삭제 중 오류가 발생했습니다.');
            }
          },
        },
      ]
    );
  };

  const deleteAllCancelledSchedules = () => {
    Alert.alert(
      '취소된 스케줄 일괄 삭제',
      '모든 취소된 스케줄을 완전히 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.',
      [
        { text: '취소', style: 'cancel' },
        {
          text: '모두 삭제',
          style: 'destructive',
          onPress: async () => {
            try {
              if (!user?.nickname) return;
              
              const result = await ApiService.deleteAllCancelledSchedules(user.nickname);
              if (result.success) {
                Alert.alert(
                  '성공', 
                  result.data.message || '취소된 스케줄이 모두 삭제되었습니다.'
                );
                loadSchedules();
              } else {
                Alert.alert('오류', result.error || '일괄 삭제에 실패했습니다.');
              }
            } catch (error) {
              Alert.alert('오류', '일괄 삭제 중 오류가 발생했습니다.');
            }
          },
        },
      ]
    );
  };

  const pauseResumeSchedule = async (schedule: Schedule) => {
    const action = schedule.status === 'active' ? 'pause' : 'resume';
    const actionText = action === 'pause' ? '일시정지' : '재개';
    
    try {
      const result = await ApiService.updateScheduleStatus(schedule.id, action);
      if (result.success) {
        Alert.alert('성공', `스케줄이 ${actionText}되었습니다.`);
        loadSchedules();
      } else {
        Alert.alert('오류', result.error || `${actionText}에 실패했습니다.`);
      }
    } catch (error) {
      Alert.alert('오류', `${actionText} 중 오류가 발생했습니다.`);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return '#48bb78';
      case 'paused': return '#ed8936';
      case 'completed': return '#667eea';
      case 'cancelled': return '#e53e3e';
      default: return '#718096';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active': return '실행 중';
      case 'paused': return '일시정지';
      case 'completed': return '완료';
      case 'cancelled': return '취소됨';
      default: return '알 수 없음';
    }
  };

  const formatInterval = (minutes: number) => {
    if (minutes < 60) return `${minutes}분`;
    if (minutes < 1440) return `${minutes / 60}시간`;
    return `${minutes / 1440}일`;
  };

  const formatDateTime = (dateString: string) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const ScheduleCard = ({ schedule }: { schedule: Schedule }) => (
    <View style={[styles.scheduleCard, isDarkMode && styles.scheduleCardDark]}>
      <View style={styles.cardHeader}>
        <View style={styles.keywordContainer}>
          <Icon name="search" size={16} color="#667eea" />
          <Text style={[styles.keyword, isDarkMode && styles.textDark]}>
            {schedule.keyword}
          </Text>
        </View>
        <View style={[styles.statusBadge, { backgroundColor: getStatusColor(schedule.status) }]}>
          <Text style={styles.statusText}>{getStatusText(schedule.status)}</Text>
        </View>
      </View>

      <View style={styles.cardContent}>
        <View style={styles.infoRow}>
          <Icon name="schedule" size={16} color="#718096" />
          <Text style={[styles.infoText, isDarkMode && styles.subtextDark]}>
            {formatInterval(schedule.interval_minutes)}마다 실행
          </Text>
        </View>

        <View style={styles.infoRow}>
          <Icon name="repeat" size={16} color="#718096" />
          <Text style={[styles.infoText, isDarkMode && styles.subtextDark]}>
            {schedule.completed_reports} / {schedule.total_reports} 완료
          </Text>
        </View>

        {schedule.status === 'active' && (
          <View style={styles.infoRow}>
            {schedule.is_executing ? (
              <>
                <Icon name="autorenew" size={16} color="#48bb78" />
                <Text style={[styles.infoText, { color: '#48bb78' }, isDarkMode && { color: '#68d391' }]}>
                  실행 중...
                </Text>
              </>
            ) : (
              schedule.next_run && (
                <>
                  <Icon name="alarm" size={16} color="#667eea" />
                  <Text style={[styles.infoText, isDarkMode && styles.subtextDark]}>
                    다음 실행: {new Date(schedule.next_run).toLocaleString('ko-KR', { 
                      year: 'numeric',
                      month: 'numeric',
                      day: 'numeric',
                      hour: 'numeric',
                      minute: 'numeric',
                      hour12: true
                    })}
                  </Text>
                </>
              )
            )}
          </View>
        )}

        {schedule.last_run && (
          <View style={styles.infoRow}>
            <Icon name="history" size={16} color="#718096" />
            <Text style={[styles.infoText, isDarkMode && styles.subtextDark]}>
              마지막 실행: {new Date(schedule.last_run).toLocaleString('ko-KR', { 
                year: 'numeric',
                month: 'numeric',
                day: 'numeric',
                hour: 'numeric',
                minute: 'numeric',
                hour12: true
              })}
            </Text>
          </View>
        )}
      </View>

      <View style={styles.cardActions}>
        {schedule.status !== 'completed' && schedule.status !== 'cancelled' && (
          <TouchableOpacity
            style={[
              styles.actionButton, 
              styles.pauseButton,
              schedule.is_executing && styles.disabledButton
            ]}
            onPress={() => pauseResumeSchedule(schedule)}
            disabled={schedule.is_executing}
          >
            <Icon 
              name={schedule.status === 'active' ? 'pause' : 'play-arrow'} 
              size={16} 
              color={schedule.is_executing ? "#a0aec0" : "#ed8936"} 
            />
            <Text style={[
              styles.pauseButtonText,
              schedule.is_executing && styles.disabledButtonText
            ]}>
              {schedule.status === 'active' ? '일시정지' : '재개'}
            </Text>
          </TouchableOpacity>
        )}
        
        <TouchableOpacity
          style={[
            styles.actionButton, 
            styles.deleteButton,
            schedule.is_executing && styles.disabledButton
          ]}
          onPress={() => deleteSchedule(schedule.id, schedule.status === 'cancelled')}
          disabled={schedule.is_executing}
        >
          <Icon name="delete" size={16} color={schedule.is_executing ? "#a0aec0" : "#e53e3e"} />
          <Text style={[
            styles.deleteButtonText,
            schedule.is_executing && styles.disabledButtonText
          ]}>
            {schedule.status === 'cancelled' ? '완전 삭제' : '삭제'}
          </Text>
        </TouchableOpacity>
      </View>

      <View style={styles.cardFooter}>
        <Text style={[styles.createdAt, isDarkMode && styles.subtextDark]}>
          등록일: {new Date(schedule.created_at).toLocaleDateString('ko-KR')}
        </Text>
      </View>
    </View>
  );

  return (
    <ScrollView 
      style={[styles.container, isDarkMode && styles.containerDark]}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <LinearGradient
        colors={isDarkMode ? ['#2d3748', '#1a202c'] : ['#667eea', '#764ba2']}
        style={styles.header}
      >
        <Icon name="list" size={50} color="#ffffff" />
        <Text style={styles.headerTitle}>내 스케줄</Text>
        <Text style={styles.headerSubtitle}>등록된 분석 스케줄 목록</Text>
      </LinearGradient>

      <View style={[styles.content, isDarkMode && styles.contentDark]}>
        {/* 사용자 정보 */}
        <View style={[styles.userCard, isDarkMode && styles.userCardDark]}>
          <Icon name="person" size={20} color="#667eea" />
          <Text style={[styles.userName, isDarkMode && styles.textDark]}>
            {user?.nickname}님의 스케줄
          </Text>
          <View style={[styles.countBadge, isDarkMode && styles.countBadgeDark]}>
            <Text style={[styles.countText, isDarkMode && styles.textDark]}>
              {schedules.length}개
            </Text>
          </View>
        </View>

        {/* 스케줄 목록 */}
        {isLoading ? (
          <View style={styles.emptyContainer}>
            <Icon name="hourglass-empty" size={48} color="#718096" />
            <Text style={[styles.emptyText, isDarkMode && styles.subtextDark]}>
              로딩 중...
            </Text>
          </View>
        ) : (
          <>
            {/* 활성 스케줄이 없을 때 메시지 */}
            {schedules.length === 0 && cancelledSchedules.length === 0 && completedSchedules.length === 0 && (
              <View style={styles.emptyContainer}>
                <Icon name="schedule" size={48} color="#718096" />
                <Text style={[styles.emptyText, isDarkMode && styles.subtextDark]}>
                  등록된 스케줄이 없습니다
                </Text>
                <Text style={[styles.emptySubtext, isDarkMode && styles.subtextDark]}>
                  스케줄 등록 탭에서 새 스케줄을 등록해보세요
                </Text>
              </View>
            )}
            
            {/* 활성 스케줄만 없을 때 메시지 */}
            {schedules.length === 0 && (cancelledSchedules.length > 0 || completedSchedules.length > 0) && (
              <View style={styles.emptyContainer}>
                <Icon name="schedule" size={48} color="#718096" />
                <Text style={[styles.emptyText, isDarkMode && styles.subtextDark]}>
                  활성 스케줄이 없습니다
                </Text>
                <Text style={[styles.emptySubtext, isDarkMode && styles.subtextDark]}>
                  스케줄 등록 탭에서 새 스케줄을 등록해보세요
                </Text>
              </View>
            )}
            
            {/* 활성 스케줄 */}
            {schedules.map((schedule) => (
              <ScheduleCard key={schedule.id} schedule={schedule} />
            ))}
            
            {/* 완료된 스케줄 섹션 */}
            {completedSchedules.length > 0 && (
              <>
                <View>
                  <TouchableOpacity
                    style={[styles.completedSection, isDarkMode && styles.completedSectionDark]}
                    onPress={() => setShowCompleted(!showCompleted)}
                  >
                    <View style={styles.completedHeader}>
                      <Icon name="check-circle" size={20} color="#48bb78" />
                      <Text style={[styles.completedTitle, isDarkMode && styles.textDark]}>
                        완료된 스케줄
                      </Text>
                      <View style={[styles.completedBadge]}>
                        <Text style={[styles.completedCount]}>
                          {completedSchedules.length}
                        </Text>
                      </View>
                      <Icon 
                        name={showCompleted ? "expand-less" : "expand-more"} 
                        size={24} 
                        color="#48bb78" 
                        style={styles.expandIcon}
                      />
                    </View>
                  </TouchableOpacity>
                  
                  {showCompleted && (
                    <View style={styles.completedList}>
                      {completedSchedules.map((schedule) => (
                        <View key={schedule.id} style={[styles.completedItem, isDarkMode && styles.completedItemDark]}>
                          <View style={styles.completedInfo}>
                            <Text style={[styles.completedKeyword, isDarkMode && styles.textDark]}>
                              {schedule.keyword}
                            </Text>
                            <Text style={[styles.completedDetails, isDarkMode && styles.subtextDark]}>
                              총 {schedule.completed_reports}개 보고서 생성 완료
                            </Text>
                            <Text style={[styles.completedDate, isDarkMode && styles.subtextDark]}>
                              완료일: {schedule.last_run ? formatDateTime(schedule.last_run) : '-'}
                            </Text>
                          </View>
                          <TouchableOpacity
                            onPress={() => deleteSchedule(schedule.id, true)}
                            style={styles.deleteButton}
                          >
                            <Icon name="delete" size={20} color="#e53e3e" />
                          </TouchableOpacity>
                        </View>
                      ))}
                    </View>
                  )}
                </View>
              </>
            )}
            
            {/* 취소된 스케줄 섹션 - 항상 표시 */}
            {cancelledSchedules.length > 0 && (
              <>
                <View>
                  <TouchableOpacity
                    style={[styles.cancelledSection, isDarkMode && styles.cancelledSectionDark]}
                    onPress={() => setShowCancelled(!showCancelled)}
                  >
                    <View style={styles.cancelledHeader}>
                      <Icon name="history" size={20} color="#718096" />
                      <Text style={[styles.cancelledTitle, isDarkMode && styles.subtextDark]}>
                        취소된 스케줄
                      </Text>
                      <View style={[styles.cancelledBadge, isDarkMode && styles.countBadgeDark]}>
                        <Text style={[styles.cancelledCount, isDarkMode && styles.subtextDark]}>
                          {cancelledSchedules.length}
                        </Text>
                      </View>
                      <Icon 
                        name={showCancelled ? "expand-less" : "expand-more"} 
                        size={24} 
                        color="#718096" 
                        style={styles.expandIcon}
                      />
                    </View>
                  </TouchableOpacity>
                  
                  {showCancelled && cancelledSchedules.length > 0 && (
                    <TouchableOpacity
                      style={[styles.deleteAllButton, isDarkMode && styles.deleteAllButtonDark]}
                      onPress={deleteAllCancelledSchedules}
                    >
                      <Icon name="delete-sweep" size={20} color="#e53e3e" />
                      <Text style={styles.deleteAllButtonText}>모두 삭제</Text>
                    </TouchableOpacity>
                  )}
                </View>
                
                {showCancelled && (
                  <View style={styles.cancelledList}>
                    {cancelledSchedules.map((schedule) => (
                      <ScheduleCard key={schedule.id} schedule={schedule} />
                    ))}
                  </View>
                )}
              </>
            )}
          </>
        )}

        <View style={styles.footer}>
          <Text style={[styles.footerText, isDarkMode && styles.subtextDark]}>
            스케줄은 자동으로 실행되며 보고서가 생성됩니다
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
  userCard: {
    flexDirection: 'row',
    alignItems: 'center',
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
  userCardDark: {
    backgroundColor: '#2d3748',
  },
  userName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#2d3748',
    marginLeft: 10,
    flex: 1,
  },
  countBadge: {
    backgroundColor: '#f0f4ff',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  countBadgeDark: {
    backgroundColor: '#4a5568',
  },
  countText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#667eea',
  },
  scheduleCard: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  scheduleCardDark: {
    backgroundColor: '#2d3748',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  keywordContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  keyword: {
    fontSize: 18,
    fontWeight: '600',
    color: '#2d3748',
    marginLeft: 8,
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#ffffff',
  },
  cardContent: {
    marginBottom: 16,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    color: '#4a5568',
    marginLeft: 8,
  },
  cardActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginBottom: 12,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    marginLeft: 8,
  },
  pauseButton: {
    backgroundColor: '#fef5e7',
    borderWidth: 1,
    borderColor: '#ed8936',
  },
  pauseButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ed8936',
    marginLeft: 4,
  },
  deleteButton: {
    backgroundColor: '#fed7d7',
    borderWidth: 1,
    borderColor: '#e53e3e',
  },
  deleteButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#e53e3e',
    marginLeft: 4,
  },
  cardFooter: {
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
  },
  createdAt: {
    fontSize: 12,
    color: '#718096',
    textAlign: 'right',
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#4a5568',
    marginTop: 16,
    textAlign: 'center',
  },
  emptySubtext: {
    fontSize: 14,
    color: '#718096',
    marginTop: 8,
    textAlign: 'center',
  },
  footer: {
    alignItems: 'center',
    marginTop: 40,
    marginBottom: 20,
  },
  footerText: {
    fontSize: 14,
    color: '#718096',
    textAlign: 'center',
  },
  textDark: {
    color: '#e2e8f0',
  },
  subtextDark: {
    color: '#a0aec0',
  },
  cancelledSection: {
    backgroundColor: '#f7fafc',
    borderRadius: 16,
    padding: 16,
    marginTop: 20,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  cancelledSectionDark: {
    backgroundColor: '#2d3748',
    borderColor: '#4a5568',
  },
  cancelledHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  cancelledTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#718096',
    marginLeft: 10,
    flex: 1,
  },
  cancelledBadge: {
    backgroundColor: '#e2e8f0',
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 4,
    marginRight: 10,
  },
  cancelledCount: {
    fontSize: 14,
    fontWeight: '600',
    color: '#718096',
  },
  expandIcon: {
    marginLeft: 5,
  },
  completedSection: {
    backgroundColor: '#f0fdf4',
    borderRadius: 16,
    padding: 16,
    marginTop: 20,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#86efac',
  },
  completedSectionDark: {
    backgroundColor: '#1a2f2a',
    borderColor: '#22543d',
  },
  completedHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  completedTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#22543d',
    marginLeft: 10,
    flex: 1,
  },
  completedBadge: {
    backgroundColor: '#d1fae5',
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 4,
    marginRight: 10,
  },
  completedCount: {
    fontSize: 14,
    fontWeight: '600',
    color: '#22543d',
  },
  completedList: {
    marginTop: 10,
  },
  completedItem: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 10,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#d1fae5',
  },
  completedItemDark: {
    backgroundColor: '#2d3748',
    borderColor: '#4a5568',
  },
  completedInfo: {
    flex: 1,
  },
  completedKeyword: {
    fontSize: 16,
    fontWeight: '600',
    color: '#2d3748',
    marginBottom: 4,
  },
  completedDetails: {
    fontSize: 14,
    color: '#718096',
    marginBottom: 2,
  },
  completedDate: {
    fontSize: 12,
    color: '#a0aec0',
  },
  cancelledList: {
    marginTop: 10,
  },
  deleteAllButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fed7d7',
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 20,
    marginTop: 10,
    marginBottom: 10,
    marginHorizontal: 16,
    borderWidth: 1,
    borderColor: '#e53e3e',
  },
  deleteAllButtonDark: {
    backgroundColor: '#2d1414',
    borderColor: '#e53e3e',
  },
  deleteAllButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#e53e3e',
    marginLeft: 8,
  },
  disabledButton: {
    opacity: 0.5,
    backgroundColor: '#e2e8f0',
  },
  disabledButtonText: {
    color: '#a0aec0',
  },
});

export default ScheduleListScreen;