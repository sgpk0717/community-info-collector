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
import ApiService from '../services/api.service';

const RegisterScreen: React.FC = () => {
  const isDarkMode = useColorScheme() === 'dark';
  const navigation = useNavigation<any>();
  const [nickname, setNickname] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleRegister = async () => {
    if (!nickname.trim()) {
      Alert.alert('알림', '닉네임을 입력해주세요.');
      return;
    }

    if (nickname.trim().length < 2) {
      Alert.alert('알림', '닉네임은 2자 이상이어야 합니다.');
      return;
    }

    if (nickname.trim().length > 20) {
      Alert.alert('알림', '닉네임은 20자 이하여야 합니다.');
      return;
    }

    setIsLoading(true);
    try {
      const result = await ApiService.registerUser(nickname);
      
      if (result.success) {
        Alert.alert(
          '등록 완료',
          '사용자 등록이 완료되었습니다.\n관리자 승인 후 이용 가능합니다.',
          [
            {
              text: '확인',
              onPress: () => navigation.goBack(),
            },
          ]
        );
      } else if (result.error === 'NICKNAME_EXISTS') {
        Alert.alert('등록 실패', '이미 사용 중인 닉네임입니다.');
      } else {
        Alert.alert('오류', '등록에 실패했습니다. 다시 시도해주세요.');
      }
    } catch (error) {
      Alert.alert('오류', '네트워크 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
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
          <TouchableOpacity 
            style={styles.backButton}
            onPress={() => navigation.goBack()}
          >
            <Icon name="arrow-back" size={24} color="#ffffff" />
          </TouchableOpacity>

          <View style={styles.iconContainer}>
            <Icon name="person-add" size={60} color="#ffffff" />
          </View>
          
          <Text style={styles.title}>사용자 등록</Text>
          <Text style={styles.subtitle}>사용할 닉네임을 입력해주세요</Text>

          <View style={styles.inputContainer}>
            <Icon name="person" size={24} color="#ffffff" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="닉네임 (2-20자)"
              placeholderTextColor="rgba(255, 255, 255, 0.6)"
              value={nickname}
              onChangeText={setNickname}
              autoCapitalize="none"
              autoCorrect={false}
              maxLength={20}
              editable={!isLoading}
            />
          </View>

          <Text style={styles.infoText}>
            * 등록 후 관리자 승인이 필요합니다
          </Text>

          <TouchableOpacity
            style={[styles.registerButton, isLoading && styles.disabledButton]}
            onPress={handleRegister}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator color="#667eea" />
            ) : (
              <Text style={styles.registerButtonText}>등록하기</Text>
            )}
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
  backButton: {
    position: 'absolute',
    top: 50,
    left: 20,
    padding: 10,
  },
  iconContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
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
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    marginBottom: 40,
    textAlign: 'center',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 12,
    paddingHorizontal: 15,
    marginBottom: 15,
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
  infoText: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.6)',
    marginBottom: 30,
    textAlign: 'center',
  },
  registerButton: {
    backgroundColor: '#ffffff',
    paddingVertical: 15,
    paddingHorizontal: 40,
    borderRadius: 25,
    width: '100%',
    alignItems: 'center',
  },
  disabledButton: {
    opacity: 0.7,
  },
  registerButtonText: {
    color: '#667eea',
    fontSize: 18,
    fontWeight: 'bold',
  },
});

export default RegisterScreen;