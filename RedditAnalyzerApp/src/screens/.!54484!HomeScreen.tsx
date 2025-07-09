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
