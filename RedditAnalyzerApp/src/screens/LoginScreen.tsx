import React, { useState } from 'react';
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
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialIcons as Icon } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { useAuth } from '../context/AuthContext';

const LoginScreen: React.FC = () => {
  const isDarkMode = useColorScheme() === 'dark';
  const navigation = useNavigation<any>();
  const { login } = useAuth();
  const [nickname, setNickname] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async () => {
    if (!nickname.trim()) {
      Alert.alert('알림', '닉네임을 입력해주세요.');
      return;
    }

    setIsLoading(true);
    try {
      const success = await login(nickname);
      if (success) {
        // 로그인 성공 - AuthContext에서 상태 관리
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