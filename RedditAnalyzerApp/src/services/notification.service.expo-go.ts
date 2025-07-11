// Expo Go용 더미 NotificationService
// 실제 알림 기능 없이 인터페이스만 제공

import { Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

class NotificationServiceExpoGo {
  private NOTIFICATION_PERMISSION_KEY = '@notification_permission';

  async initialize() {
    console.log('Expo Go - 알림 서비스 비활성화');
    return false;
  }

  async requestPermissions(): Promise<boolean> {
    // Expo Go에서는 항상 false
    return false;
  }

  async registerForPushNotifications(): Promise<string | null> {
    return null;
  }

  async getPushToken(): Promise<string | null> {
    return null;
  }

  async checkAndRequestPermission(): Promise<boolean> {
    const permission = await AsyncStorage.getItem(this.NOTIFICATION_PERMISSION_KEY);
    
    if (permission === 'denied') {
      return false;
    }
    
    if (permission === 'granted') {
      return false; // Expo Go에서는 항상 false
    }
    
    // 처음 묻는 경우
    return new Promise((resolve) => {
      Alert.alert(
        '알림 기능 안내',
        'Expo Go에서는 알림 기능이 제한됩니다.\n분석 완료 시 앱 내에서 확인해주세요.',
        [
          {
            text: '확인',
            onPress: async () => {
              await AsyncStorage.setItem(this.NOTIFICATION_PERMISSION_KEY, 'denied');
              resolve(false);
            },
          },
        ],
        { cancelable: false }
      );
    });
  }

  async showLocalNotification(title: string, body: string, data?: any) {
    // Expo Go에서는 아무것도 하지 않음
    console.log('로컬 알림 (Expo Go에서는 비활성화):', title, body);
  }

  async resetPermissionStatus() {
    await AsyncStorage.removeItem(this.NOTIFICATION_PERMISSION_KEY);
  }
}

export default new NotificationServiceExpoGo();