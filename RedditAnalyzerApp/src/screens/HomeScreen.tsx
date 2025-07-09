import React, { useState } from 'react';
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
} from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import Icon from 'react-native-vector-icons/MaterialIcons';
import ApiService from '../services/api.service';
import StorageService from '../services/storage.service';
import AuthService from '../services/auth.service';
import { Report, ReportLength } from '../types';
import { REPORT_LENGTHS } from '../utils/constants';

const HomeScreen: React.FC = () => {
  const isDarkMode = useColorScheme() === 'dark';
  const [keyword, setKeyword] = useState('');
  const [reportLength, setReportLength] = useState<ReportLength>('moderate');
  const [isLoading, setIsLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<Report | null>(null);

  const handleAnalyze = async () => {
    if (!keyword.trim()) {
      Alert.alert('Lº', 'Ñ` §Ã‹| Ö%t¸8î.');
      return;
    }

    setIsLoading(true);
    setAnalysisResult(null);

    try {
      const result = await ApiService.analyze(keyword, reportLength);

      if (result.success && result.data) {
        const user = AuthService.getCurrentUser();
        if (!user) {
          Alert.alert('$X', '¨©ê Ù| >D  ∆µ»‰.');
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
        
        Alert.alert('1ı', 'Ñt DÃ»µ»‰!', [
          { text: 'Ux', style: 'default' }
        ]);
      } else {
        Alert.alert('$X', result.error || 'Ñ– ‰(àµ»‰.');
      }
    } catch (error) {
      Alert.alert('$X', 'Ñ ∞– ‰(àµ»‰.');
    } finally {
      setIsLoading(false);
    }
  };

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
        {REPORT_LENGTHS[value].chars}ê
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
          <Text style={styles.headerTitle}>Reddit Ù Ñ</Text>
          <Text style={styles.headerSubtitle}>
            \‡ Ù| ‰‹<\ —X‡ Ñi»‰
          </Text>
        </LinearGradient>

        <View style={[styles.content, isDarkMode && styles.contentDark]}>
          <View style={styles.inputSection}>
            <Text style={[styles.label, isDarkMode && styles.textDark]}>
              Ä…` §Ã‹
            </Text>
            <TextInput
              style={[styles.input, isDarkMode && styles.inputDark]}
              placeholder=": Tesla 2025 news, Apple stock"
              placeholderTextColor={isDarkMode ? '#888' : '#999'}
              value={keyword}
              onChangeText={setKeyword}
              editable={!isLoading}
            />
            <Text style={[styles.helperText, isDarkMode && styles.helperTextDark]}>
              ÏÏ §Ã‹î |\(,)\ lÑX8î
            </Text>
          </View>

          <View style={styles.lengthSection}>
            <Text style={[styles.label, isDarkMode && styles.textDark]}>
              Ù‡ 8t
            </Text>
            <View style={styles.lengthButtons}>
              <ReportLengthButton value="simple" label="Ëà" />
              <ReportLengthButton value="moderate" label="˘à" />
              <ReportLengthButton value="detailed" label="¡8Xå" />
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
                  <Text style={styles.analyzeButtonText}>Ñ ...</Text>
                </>
              ) : (
                <>
                  <Icon name="search" size={24} color="#ffffff" />
                  <Text style={styles.analyzeButtonText}>— & Ñ</Text>
                </>
              )}
            </LinearGradient>
          </TouchableOpacity>

          {isLoading && (
            <View style={[styles.loadingCard, isDarkMode && styles.cardDark]}>
              <ActivityIndicator size="large" color="#667eea" />
              <Text style={[styles.loadingTitle, isDarkMode && styles.textDark]}>
                Reddit– Ù| —X‡ àµ»‰...
              </Text>
              <View style={styles.loadingSteps}>
                <Text style={[styles.loadingStep, isDarkMode && styles.textDark]}>
                  = Reddit Ä… 
                </Text>
                <Text style={[styles.loadingStep, isDarkMode && styles.textDark]}>
                  =  pt0 — 
                </Text>
                <Text style={[styles.loadingStep, isDarkMode && styles.textDark]}>
                  > GPT-4 Ñ 
                </Text>
                <Text style={[styles.loadingStep, isDarkMode && styles.textDark]}>
                  =› Ù‡ ›1 
                </Text>
              </View>
            </View>
          )}

          {analysisResult && !isLoading && (
            <View style={[styles.resultCard, isDarkMode && styles.cardDark]}>
              <View style={styles.resultHeader}>
                <Icon name="check-circle" size={24} color="#48bb78" />
                <Text style={[styles.resultTitle, isDarkMode && styles.textDark]}>
                  Ñ DÃ
                </Text>
              </View>
              
              <View style={styles.resultMeta}>
                <Text style={[styles.metaText, isDarkMode && styles.textDark]}>
                  =  {analysisResult.metadata.charCount}ê
                </Text>
                <Text style={[styles.metaText, isDarkMode && styles.textDark]}>
                  Ò {(analysisResult.metadata.processingTime / 1000).toFixed(1)}
                </Text>
              </View>

              <ScrollView style={styles.resultContent} nestedScrollEnabled>
                <Text style={[styles.resultText, isDarkMode && styles.textDark]}>
                  {analysisResult.content.slice(0, 500)}...
                </Text>
              </ScrollView>

              <TouchableOpacity
                style={styles.viewFullButton}
                onPress={() => Alert.alert('¥ Ù‡î Ù‡ Ì– UxX8î')}
              >
                <Text style={styles.viewFullButtonText}>¥ Ù‡ Ù0</Text>
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
  loadingCard: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 25,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  cardDark: {
    backgroundColor: '#2d3748',
  },
  loadingTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginTop: 15,
    marginBottom: 20,
    color: '#2d3748',
  },
  loadingSteps: {
    alignItems: 'flex-start',
    width: '100%',
  },
  loadingStep: {
    fontSize: 16,
    marginVertical: 5,
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
});

export default HomeScreen;