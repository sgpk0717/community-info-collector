import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  Alert,
  RefreshControl,
  useColorScheme,
  Modal,
  ScrollView,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialIcons as Icon } from '@expo/vector-icons';
import ApiService from '../services/api.service';
import AuthService from '../services/auth.service';
import ReportRenderer from '../components/ReportRenderer';
import { Report } from '../types';

const ReportsScreen: React.FC = () => {
  const isDarkMode = useColorScheme() === 'dark';
  const [reports, setReports] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedReport, setSelectedReport] = useState<any | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isSelectionMode, setIsSelectionMode] = useState(false);
  const [selectedReportIds, setSelectedReportIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      setLoading(true);
      const user = AuthService.getCurrentUser();
      
      console.log('🐛 [DEBUG] ReportsScreen - Current user:', user);
      console.log('🐛 [DEBUG] ReportsScreen - User nickname:', user?.nickname);
      
      if (!user || !user.nickname) {
        console.log('🐛 [DEBUG] ReportsScreen - No user or nickname found');
        Alert.alert('오류', '로그인이 필요합니다.');
        setReports([]);
        return;
      }

      console.log('🐛 [DEBUG] ReportsScreen - Fetching reports for:', user.nickname);
      const result = await ApiService.getUserReports(user.nickname);
      console.log('🐛 [DEBUG] ReportsScreen - API result:', result);
      
      if (result.success) {
        setReports(result.data || []);
      } else {
        Alert.alert('오류', result.error || '보고서를 불러오는데 실패했습니다.');
        setReports([]);
      }
    } catch (error) {
      console.error('Load reports error:', error);
      Alert.alert('오류', '보고서를 불러오는데 실패했습니다.');
      setReports([]);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadReports();
    setRefreshing(false);
  }, []);

  const deleteReport = async (reportId: string) => {
    Alert.alert(
      '보고서 삭제',
      '이 보고서를 삭제하시겠습니까?',
      [
        { text: '취소', style: 'cancel' },
        {
          text: '삭제',
          style: 'destructive',
          onPress: async () => {
            try {
              const result = await ApiService.deleteReport(reportId);
              if (result.success) {
                await loadReports();
                Alert.alert('성공', '보고서가 삭제되었습니다.');
              } else {
                Alert.alert('오류', result.error || '보고서 삭제에 실패했습니다.');
              }
            } catch (error) {
              console.error('Delete report error:', error);
              Alert.alert('오류', '보고서 삭제에 실패했습니다.');
            }
          },
        },
      ]
    );
  };

  const toggleSelectionMode = () => {
    setIsSelectionMode(!isSelectionMode);
    setSelectedReportIds(new Set());
  };

  const toggleReportSelection = (reportId: string) => {
    const newSelected = new Set(selectedReportIds);
    if (newSelected.has(reportId)) {
      newSelected.delete(reportId);
    } else {
      newSelected.add(reportId);
    }
    setSelectedReportIds(newSelected);
  };

  const deleteSelectedReports = async () => {
    if (selectedReportIds.size === 0) {
      Alert.alert('알림', '삭제할 보고서를 선택해주세요.');
      return;
    }

    Alert.alert(
      '다중 삭제',
      `선택한 ${selectedReportIds.size}개의 보고서를 삭제하시겠습니까?`,
      [
        { text: '취소', style: 'cancel' },
        {
          text: '삭제',
          style: 'destructive',
          onPress: async () => {
            try {
              const deletePromises = Array.from(selectedReportIds).map(id =>
                ApiService.deleteReport(id)
              );
              await Promise.all(deletePromises);
              
              await loadReports();
              Alert.alert('성공', `${selectedReportIds.size}개의 보고서가 삭제되었습니다.`);
              setIsSelectionMode(false);
              setSelectedReportIds(new Set());
            } catch (error) {
              console.error('Delete multiple reports error:', error);
              Alert.alert('오류', '보고서 삭제에 실패했습니다.');
            }
          },
        },
      ]
    );
  };

  const viewReport = (report: Report) => {
    setSelectedReport(report);
    setModalVisible(true);
  };

  const formatDate = (dateString: string) => {
    const d = new Date(dateString);
    return d.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getTimeDiff = (dateString: string) => {
    const d = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}일 전`;
    if (hours > 0) return `${hours}시간 전`;
    return `${minutes}분 전`;
  };

  const renderReportItem = ({ item }: { item: any }) => {
    const isSelected = selectedReportIds.has(item.id);
    
    return (
      <TouchableOpacity
        style={[
          styles.reportCard, 
          isDarkMode && styles.cardDark,
          isSelected && styles.selectedCard
        ]}
        onPress={() => {
          if (isSelectionMode) {
            toggleReportSelection(item.id);
          } else {
            viewReport(item);
          }
        }}
        onLongPress={() => {
          if (!isSelectionMode) {
            setIsSelectionMode(true);
            toggleReportSelection(item.id);
          }
        }}
      >
        <View style={styles.reportHeader}>
          <View style={styles.reportTitleContainer}>
            {isSelectionMode ? (
              <TouchableOpacity
                onPress={() => toggleReportSelection(item.id)}
                style={styles.checkbox}
              >
                <Icon 
                  name={isSelected ? "check-box" : "check-box-outline-blank"} 
                  size={24} 
                  color={isSelected ? "#667eea" : "#718096"} 
                />
              </TouchableOpacity>
            ) : (
              <Icon name="description" size={24} color="#667eea" />
            )}
            <View style={styles.reportInfo}>
              <Text style={[styles.reportKeyword, isDarkMode && styles.textDark]}>
                {item.query_text}
              </Text>
              <Text style={[styles.reportDate, isDarkMode && styles.subtextDark]}>
                {getTimeDiff(item.created_at)}
              </Text>
            </View>
          </View>
          {!isSelectionMode && (
            <TouchableOpacity
              onPress={() => deleteReport(item.id)}
              style={styles.deleteButton}
            >
              <Icon name="delete" size={24} color="#e53e3e" />
            </TouchableOpacity>
          )}
        </View>

        <View style={styles.reportMeta}>
          <View style={styles.metaItem}>
            <Icon name="format-size" size={16} color="#718096" />
            <Text style={[styles.metaText, isDarkMode && styles.subtextDark]}>
              {item.full_report?.length || 0}자
            </Text>
          </View>
          <View style={styles.metaItem}>
            <Icon name="collections" size={16} color="#718096" />
            <Text style={[styles.metaText, isDarkMode && styles.subtextDark]}>
              {item.posts_collected || 0}개 게시물
            </Text>
          </View>
        </View>

        <Text
          style={[styles.reportPreview, isDarkMode && styles.subtextDark]}
          numberOfLines={3}
        >
          {item.summary || item.full_report?.substring(0, 200) + '...' || '내용 없음'}
        </Text>
      </TouchableOpacity>
    );
  };

  const EmptyComponent = () => (
    <View style={styles.emptyContainer}>
      <Icon name="folder-open" size={80} color="#cbd5e0" />
      <Text style={[styles.emptyTitle, isDarkMode && styles.textDark]}>
        저장된 보고서가 없습니다
      </Text>
      <Text style={[styles.emptySubtext, isDarkMode && styles.subtextDark]}>
        홈 화면에서 키워드를 검색하여 보고서를 생성하세요
      </Text>
    </View>
  );

  return (
    <View style={[styles.container, isDarkMode && styles.containerDark]}>
      <LinearGradient
        colors={isDarkMode ? ['#2d3748', '#1a202c'] : ['#667eea', '#764ba2']}
        style={styles.header}
      >
        <View style={styles.headerContent}>
          <Icon name="folder" size={50} color="#ffffff" />
          <Text style={styles.headerTitle}>분석 보고서</Text>
          <Text style={styles.headerSubtitle}>
            {isSelectionMode 
              ? `${selectedReportIds.size}개 선택됨` 
              : `총 ${reports.length}개의 보고서가 저장되어 있습니다`}
          </Text>
        </View>
        <View style={styles.headerActions}>
          {isSelectionMode ? (
            <>
              <TouchableOpacity
                style={styles.headerButton}
                onPress={deleteSelectedReports}
              >
                <Icon name="delete" size={24} color="#ffffff" />
                <Text style={styles.headerButtonText}>삭제</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.headerButton}
                onPress={toggleSelectionMode}
              >
                <Icon name="close" size={24} color="#ffffff" />
                <Text style={styles.headerButtonText}>취소</Text>
              </TouchableOpacity>
            </>
          ) : (
            <TouchableOpacity
              style={styles.headerButton}
              onPress={toggleSelectionMode}
              disabled={reports.length === 0}
            >
              <Icon name="check-circle" size={24} color="#ffffff" />
              <Text style={styles.headerButtonText}>선택</Text>
            </TouchableOpacity>
          )}
        </View>
      </LinearGradient>

      <FlatList
        data={reports}
        renderItem={renderReportItem}
        keyExtractor={(item) => item.id}
        contentContainerStyle={[
          styles.listContent,
          reports.length === 0 && styles.emptyListContent,
        ]}
        ListEmptyComponent={EmptyComponent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={['#667eea']}
          />
        }
      />

      <Modal
        animationType="slide"
        transparent={false}
        visible={modalVisible}
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={[styles.modalContainer, isDarkMode && styles.containerDark]}>
          <View style={[styles.modalHeader, isDarkMode && styles.modalHeaderDark]}>
            <TouchableOpacity
              onPress={() => setModalVisible(false)}
              style={styles.closeButton}
            >
              <Icon name="close" size={28} color={isDarkMode ? '#fff' : '#000'} />
            </TouchableOpacity>
            <Text style={[styles.modalTitle, isDarkMode && styles.textDark]}>
              {selectedReport?.query_text}
            </Text>
            <View style={styles.placeholder} />
          </View>

          {selectedReport && (
            <ScrollView style={styles.modalContent}>
              <View style={[styles.modalMetaContainer, isDarkMode && styles.cardDark]}>
                <Text style={[styles.modalDate, isDarkMode && styles.textDark]}>
                  {formatDate(selectedReport.created_at)}
                </Text>
                <View style={styles.modalMeta}>
                  <Text style={[styles.metaText, isDarkMode && styles.subtextDark]}>
                    총 {selectedReport.full_report?.length || 0}자
                  </Text>
                  <Text style={[styles.metaText, isDarkMode && styles.subtextDark]}>
                    수집된 게시물 {selectedReport.posts_collected || 0}개
                  </Text>
                </View>
              </View>

              <View style={[styles.modalReportContent, isDarkMode && styles.cardDark]}>
                <ReportRenderer 
                  content={selectedReport.full_report || '내용을 불러올 수 없습니다.'}
                  isDarkMode={isDarkMode}
                  reportId={selectedReport.id}
                />
              </View>

              <View style={styles.modalActions}>
                <TouchableOpacity
                  style={styles.actionButton}
                  onPress={() => {
                    // 복사 기능 구현
                    Alert.alert('알림', '보고서가 클립보드에 복사되었습니다.');
                  }}
                >
                  <LinearGradient
                    colors={['#667eea', '#764ba2']}
                    style={styles.actionButtonGradient}
                  >
                    <Icon name="content-copy" size={20} color="#ffffff" />
                    <Text style={styles.actionButtonText}>복사</Text>
                  </LinearGradient>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.actionButton}
                  onPress={() => {
                    // 공유 기능 구현
                    Alert.alert('공유', '공유 기능은 추후 업데이트 예정입니다.');
                  }}
                >
                  <LinearGradient
                    colors={['#48bb78', '#38a169']}
                    style={styles.actionButtonGradient}
                  >
                    <Icon name="share" size={20} color="#ffffff" />
                    <Text style={styles.actionButtonText}>공유</Text>
                  </LinearGradient>
                </TouchableOpacity>
              </View>
            </ScrollView>
          )}
        </View>
      </Modal>
    </View>
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
    paddingBottom: 30,
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
  },
  listContent: {
    padding: 20,
  },
  emptyListContent: {
    flex: 1,
  },
  reportCard: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 20,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  cardDark: {
    backgroundColor: '#2d3748',
  },
  reportHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  reportTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  reportInfo: {
    marginLeft: 12,
    flex: 1,
  },
  reportKeyword: {
    fontSize: 18,
    fontWeight: '600',
    color: '#2d3748',
  },
  reportDate: {
    fontSize: 14,
    color: '#718096',
    marginTop: 2,
  },
  deleteButton: {
    padding: 5,
  },
  reportMeta: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 20,
  },
  metaText: {
    fontSize: 14,
    color: '#718096',
    marginLeft: 5,
  },
  reportPreview: {
    fontSize: 15,
    lineHeight: 22,
    color: '#4a5568',
  },
  textDark: {
    color: '#e2e8f0',
  },
  subtextDark: {
    color: '#a0aec0',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 100,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#4a5568',
    marginTop: 20,
  },
  emptySubtext: {
    fontSize: 16,
    color: '#718096',
    marginTop: 8,
    textAlign: 'center',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#f7fafc',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 50,
    paddingBottom: 20,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  modalHeaderDark: {
    backgroundColor: '#2d3748',
    borderBottomColor: '#4a5568',
  },
  closeButton: {
    padding: 5,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#2d3748',
    flex: 1,
    textAlign: 'center',
    marginHorizontal: 10,
  },
  placeholder: {
    width: 38,
  },
  headerContent: {
    alignItems: 'center',
    marginBottom: 20,
  },
  headerActions: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 15,
  },
  headerButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
    marginHorizontal: 5,
  },
  headerButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  selectedCard: {
    borderWidth: 2,
    borderColor: '#667eea',
  },
  checkbox: {
    marginRight: 5,
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  modalMetaContainer: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 15,
    marginBottom: 20,
  },
  modalDate: {
    fontSize: 16,
    fontWeight: '600',
    color: '#2d3748',
    marginBottom: 10,
  },
  modalMeta: {
    flexDirection: 'row',
  },
  modalReportContent: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
  },
  reportFullText: {
    fontSize: 16,
    lineHeight: 26,
    color: '#2d3748',
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 40,
  },
  actionButton: {
    flex: 1,
    marginHorizontal: 10,
  },
  actionButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 15,
    borderRadius: 12,
  },
  actionButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
});

export default ReportsScreen;