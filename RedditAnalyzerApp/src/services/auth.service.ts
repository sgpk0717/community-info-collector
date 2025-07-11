import * as Device from 'expo-device';
import * as Application from 'expo-application';
import StorageService from './storage.service';
import { User } from '../types';

class AuthService {
  private currentUser: User | null = null;

  async initialize(): Promise<User> {
    console.log('AuthService: initialize() 시작');
    try {
      // 저장된 사용자 정보 확인
      console.log('AuthService: StorageService.getUser() 호출');
      const savedUser = await StorageService.getUser();
      console.log('AuthService: savedUser:', savedUser);
      
      if (savedUser) {
        // 사용자 마지막 활동 시간 업데이트
        savedUser.lastActive = new Date();
        await StorageService.saveUser(savedUser);
        this.currentUser = savedUser;
        console.log('AuthService: 기존 사용자 로드 완료');
        return savedUser;
      }

      // 새 사용자 생성
      // Expo에서는 getUniqueId 대신 다른 방법을 사용
      let deviceId: string;
      
      try {
        // Android ID 먼저 시도
        const androidId = Application.getAndroidId();
        if (androidId) {
          deviceId = androidId;
        } else {
          // iOS의 경우 async 함수 사용
          const iosId = await Application.getIosIdForVendorAsync();
          deviceId = iosId || `${Device.modelName}-${Date.now()}`;
        }
      } catch (error) {
        console.error('Device ID generation error:', error);
        deviceId = `fallback-${Date.now()}`;
      }
      
      const newUser: User = {
        deviceId: deviceId,
        createdAt: new Date(),
        lastActive: new Date(),
      };

      await StorageService.saveUser(newUser);
      this.currentUser = newUser;
      return newUser;
    } catch (error) {
      console.error('Error initializing auth:', error);
      // 에러 발생 시 임시 ID 생성
      const fallbackUser: User = {
        deviceId: `user-${Date.now()}`,
        createdAt: new Date(),
        lastActive: new Date(),
      };
      this.currentUser = fallbackUser;
      return fallbackUser;
    }
  }

  getCurrentUser(): User | null {
    return this.currentUser;
  }

  async updateUserName(name: string): Promise<void> {
    if (!this.currentUser) return;

    this.currentUser.name = name;
    await StorageService.saveUser(this.currentUser);
  }

  async updateUserNickname(nickname: string): Promise<void> {
    if (!this.currentUser) return;

    this.currentUser.nickname = nickname;
    await StorageService.saveUser(this.currentUser);
  }

  async logout(): Promise<void> {
    await StorageService.clearAllData();
    this.currentUser = null;
  }
}

export default new AuthService();