import React, { createContext, useContext, useState, useEffect } from 'react';
import { Alert } from 'react-native';
import ApiService from '../services/api.service';
import AuthService from '../services/auth.service';
import StorageService from '../services/storage.service';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: any;
  login: (nickname: string) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    // 앱 시작 시 자동 로그인 체크 (저장된 사용자 정보 확인)
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    console.log('AuthContext: checkAuthStatus 시작');
    try {
      // AuthService 초기화 및 저장된 사용자 정보 확인
      console.log('AuthContext: AuthService.initialize() 호출');
      await AuthService.initialize();
      console.log('AuthContext: AuthService.initialize() 완료');
      
      const currentUser = AuthService.getCurrentUser();
      console.log('AuthContext: currentUser:', currentUser);
      
      if (currentUser && currentUser.nickname) {
        // 기존 사용자가 있고 닉네임이 있으면 로그인 상태로 설정
        setUser(currentUser);
        setIsAuthenticated(true);
        console.log('AuthContext: 인증됨');
      } else {
        console.log('AuthContext: 인증되지 않음');
      }
      
      setIsLoading(false);
      console.log('AuthContext: isLoading false로 설정');
    } catch (error) {
      console.error('Auth check failed:', error);
      setIsLoading(false);
    }
  };

  const login = async (nickname: string): Promise<boolean> => {
    try {
      const result = await ApiService.loginUser(nickname);
      
      if (result.success) {
        if (result.data.status === 'approved') {
          // AuthService에도 닉네임 저장
          await AuthService.updateUserNickname(nickname);
          setUser({ ...result.data, nickname });
          setIsAuthenticated(true);
          return true;
        } else if (result.data.status === 'pending') {
          Alert.alert('승인 대기', '아직 승인되지 않은 닉네임입니다.');
          return false;
        }
      } else if (result.error === 'USER_NOT_FOUND') {
        Alert.alert('등록되지 않은 닉네임', '등록되지 않은 닉네임입니다.');
        return false;
      } else if (result.error === '등록되지 않은 닉네임입니다.') {
        Alert.alert('등록되지 않은 닉네임', '등록되지 않은 닉네임입니다.');
        return false;
      } else {
        Alert.alert('오류', '로그인에 실패했습니다.');
        return false;
      }
    } catch (error) {
      Alert.alert('오류', '네트워크 오류가 발생했습니다.');
      return false;
    }
    return false;
  };

  const logout = () => {
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ 
      isAuthenticated, 
      isLoading, 
      user, 
      login, 
      logout 
    }}>
      {children}
    </AuthContext.Provider>
  );
};