import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ActivityIndicator,
  useColorScheme,
  Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialIcons as Icon } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { useAuth } from '../context/AuthContext';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL } from '../utils/constants';

const LoginScreen: React.FC = () => {
  const isDarkMode = useColorScheme() === 'dark';
  const navigation = useNavigation<any>();
  const { login } = useAuth();
  const [nickname, setNickname] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [saveNickname, setSaveNickname] = useState(true); // 기본적으로 닉네임 저장
  const slideAnimation = useRef(new Animated.Value(1)).current;
  const backgroundAnimation = useRef(new Animated.Value(1)).current;
  const iconRotation = useRef(new Animated.Value(0)).current;

  // 저장된 닉네임 불러오기
  useEffect(() => {
    loadSavedNickname();
  }, []);

  const loadSavedNickname = async () => {
    try {
      const saved = await AsyncStorage.getItem('savedNickname');
      if (saved) {
        setNickname(saved);
      }
    } catch (error) {
      console.error('Error loading saved nickname:', error);
    }
  };

  const handleLogin = async () => {
    if (!nickname.trim()) {
      Alert.alert('알림', '닉네임을 입력해주세요.');
      return;
    }

    setIsLoading(true);
    try {
      const success = await login(nickname);
      if (success) {
        // 로그인 성공 시 사용자가 선택한 경우에만 닉네임 저장
        if (saveNickname) {
          await AsyncStorage.setItem('savedNickname', nickname);
        } else {
          // 저장하지 않기로 선택한 경우 기존 저장된 닉네임 삭제
          await AsyncStorage.removeItem('savedNickname');
        }
        // AuthContext에서 상태 관리
        // 자동으로 메인 화면으로 이동됨
      }
    } catch (error) {
      Alert.alert('오류', '네트워크 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = () => {
    navigation.navigate('Register');
  };

  const toggleSaveNickname = () => {
    const newValue = !saveNickname;
    
    // 슬라이드 애니메이션
    Animated.parallel([
      Animated.spring(slideAnimation, {
        toValue: newValue ? 1 : 0,
        tension: 50,
        friction: 8,
        useNativeDriver: false,
      }),
      Animated.timing(backgroundAnimation, {
        toValue: newValue ? 1 : 0,
        duration: 300,
        useNativeDriver: false,
      }),
      Animated.timing(iconRotation, {
        toValue: newValue ? 0 : 1,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start();
    
    setSaveNickname(newValue);
  };

  return (
    <LinearGradient
      colors={isDarkMode ? ['#1a202c', '#2d3748'] : ['#667eea', '#764ba2']}
      style={styles.container}
    >
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <View style={styles.content}>
          <View style={styles.logoContainer}>
            <Icon name="reddit" size={80} color="#ffffff" />
          </View>
          
          <Text style={styles.title}>Community Analyzer</Text>
          <Text style={styles.subtitle}>로그인</Text>

          <View style={styles.inputContainer}>
            <Icon name="person" size={24} color="#ffffff" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="닉네임을 입력하세요"
              placeholderTextColor="rgba(255, 255, 255, 0.6)"
              value={nickname}
              onChangeText={setNickname}
              autoCapitalize="none"
              autoCorrect={false}
              editable={!isLoading}
            />
          </View>

          <View style={styles.saveNicknameWrapper}>
            <TouchableOpacity 
              style={styles.saveNicknameContainer}
              onPress={toggleSaveNickname}
              activeOpacity={0.9}
            >
              <Animated.View style={[
                styles.switchTrack,
                {
                  backgroundColor: backgroundAnimation.interpolate({
                    inputRange: [0, 1],
                    outputRange: ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.2)'],
                  }),
                }
              ]}>
                <Animated.View style={[
                  styles.switchThumb,
                  {
                    transform: [{
                      translateX: slideAnimation.interpolate({
                        inputRange: [0, 1],
                        outputRange: [2, 28],
                      }),
                    }],
                    backgroundColor: backgroundAnimation.interpolate({
                      inputRange: [0, 1],
                      outputRange: ['#ef4444', '#ffffff'],
                    }),
                  }
                ]}>
                  <Animated.View style={{
                    transform: [{
                      rotate: iconRotation.interpolate({
                        inputRange: [0, 1],
                        outputRange: ['0deg', '180deg'],
                      }),
                    }],
                  }}>
                    <Icon 
                      name={saveNickname ? "lock" : "lock-open"} 
                      size={14} 
                      color={saveNickname ? "#667eea" : "#ffffff"} 
                    />
                  </Animated.View>
                </Animated.View>
                
                <View style={styles.trackLabels}>
                  <Text style={[styles.trackLabel, !saveNickname && styles.trackLabelActive]}>OFF</Text>
                  <Text style={[styles.trackLabel, saveNickname && styles.trackLabelActive]}>ON</Text>
                </View>
              </Animated.View>
            </TouchableOpacity>
            
            <View style={styles.saveInfoContainer}>
              <Text style={styles.saveInfoTitle}>닉네임 저장</Text>
              <Text style={styles.saveInfoDesc}>
                {saveNickname ? '다음 로그인 시 자동 입력됩니다' : '매번 닉네임을 입력해야 합니다'}
              </Text>
            </View>
          </View>

          <TouchableOpacity
            style={[styles.loginButton, isLoading && styles.disabledButton]}
            onPress={handleLogin}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator color="#667eea" />
            ) : (
              <Text style={styles.loginButtonText}>로그인</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.registerButton}
            onPress={handleRegister}
            disabled={isLoading}
          >
            <Text style={styles.registerButtonText}>사용자 등록</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  logoContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 30,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 20,
    color: 'rgba(255, 255, 255, 0.8)',
    marginBottom: 40,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 12,
    paddingHorizontal: 15,
    marginBottom: 20,
    width: '100%',
  },
  saveNicknameWrapper: {
    width: '100%',
    alignItems: 'flex-end',
    marginBottom: 30,
  },
  saveNicknameContainer: {
    marginBottom: 8,
  },
  switchTrack: {
    width: 60,
    height: 32,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    justifyContent: 'center',
    position: 'relative',
  },
  switchThumb: {
    position: 'absolute',
    width: 26,
    height: 26,
    borderRadius: 13,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  trackLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 8,
  },
  trackLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: 'rgba(255, 255, 255, 0.3)',
    letterSpacing: 0.5,
  },
  trackLabelActive: {
    color: 'rgba(255, 255, 255, 0.7)',
  },
  saveInfoContainer: {
    alignItems: 'flex-end',
  },
  saveInfoTitle: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 2,
  },
  saveInfoDesc: {
    color: 'rgba(255, 255, 255, 0.6)',
    fontSize: 12,
    fontWeight: '400',
  },
  inputIcon: {
    marginRight: 10,
  },
  input: {
    flex: 1,
    height: 50,
    color: '#ffffff',
    fontSize: 16,
  },
  loginButton: {
    backgroundColor: '#ffffff',
    paddingVertical: 15,
    paddingHorizontal: 40,
    borderRadius: 25,
    marginBottom: 15,
    width: '100%',
    alignItems: 'center',
  },
  disabledButton: {
    opacity: 0.7,
  },
  loginButtonText: {
    color: '#667eea',
    fontSize: 18,
    fontWeight: 'bold',
  },
  registerButton: {
    paddingVertical: 10,
  },
  registerButtonText: {
    color: '#ffffff',
    fontSize: 16,
    textDecorationLine: 'underline',
  },
});

export default LoginScreen;