import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Alert, Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';

// 알림 설정
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

class NotificationService {
  private PUSH_TOKEN_KEY = '@push_token';
  private NOTIFICATION_PERMISSION_KEY = '@notification_permission';
  private isExpoGo = Constants.appOwnership === 'expo';

  async initialize() {
    try {
      // Expo Go에서는 로컬 알림만 사용
      if (this.isExpoGo) {
        console.log('Expo Go에서 실행 중 - 로컬 알림만 사용합니다.');
        return await this.requestPermissions();
      }

      // 실제 기기인지 확인
      if (!Device.isDevice) {
        console.log('푸시 알림은 실제 기기에서만 작동합니다.');
        return false;
      }

      // 저장된 권한 상태 확인
      const savedPermission = await AsyncStorage.getItem(this.NOTIFICATION_PERMISSION_KEY);
      if (savedPermission === 'denied') {
        console.log('사용자가 이전에 알림을 거부했습니다.');
        return false;
      }

      // 권한 확인 및 요청
      const hasPermission = await this.requestPermissions();
      if (hasPermission) {
        const token = await this.registerForPushNotifications();
        if (token) {
          await AsyncStorage.setItem(this.PUSH_TOKEN_KEY, token);
          return true;
        }
      }
      
      return false;
    } catch (error) {
      console.error('NotificationService 초기화 오류:', error);
      return false;
    }
  }

  async requestPermissions(): Promise<boolean> {
    try {
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;
      
      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }
      
      if (finalStatus !== 'granted') {
        await AsyncStorage.setItem(this.NOTIFICATION_PERMISSION_KEY, 'denied');
        return false;
      }
      
      await AsyncStorage.setItem(this.NOTIFICATION_PERMISSION_KEY, 'granted');
      return true;
    } catch (error) {
      console.error('권한 요청 오류:', error);
      return false;
    }
  }

  async registerForPushNotifications(): Promise<string | null> {
    try {
      // Expo Go에서는 Push Token을 가져올 수 없음
      if (this.isExpoGo) {
        console.log('Expo Go에서는 Push Token을 사용할 수 없습니다.');
        return 'expo-go-dummy-token'; // 더미 토큰 반환
      }

      if (Platform.OS === 'android') {
        await Notifications.setNotificationChannelAsync('default', {
          name: 'default',
          importance: Notifications.AndroidImportance.MAX,
          vibrationPattern: [0, 250, 250, 250],
          lightColor: '#667eea',
        });
      }

      // projectId는 app.json에서 가져오거나 Constants에서 가져옴
      const projectId = Constants.expoConfig?.extra?.eas?.projectId || 
                       Constants.easConfig?.projectId ||
                       undefined;

      const token = await Notifications.getExpoPushTokenAsync({
        projectId: projectId
      });
      
      console.log('Push token:', token.data);
      return token.data;
    } catch (error) {
      console.error('Push token 등록 오류:', error);
      return null;
    }
  }

  async getPushToken(): Promise<string | null> {
    try {
      // Expo Go에서는 더미 토큰 반환
      if (this.isExpoGo) {
        return 'expo-go-dummy-token';
      }
      
      const token = await AsyncStorage.getItem(this.PUSH_TOKEN_KEY);
      return token;
    } catch (error) {
      console.error('Push token 조회 오류:', error);
      return null;
    }
  }

  async checkAndRequestPermission(): Promise<boolean> {
    const permission = await AsyncStorage.getItem(this.NOTIFICATION_PERMISSION_KEY);
    
    if (permission === 'denied') {
      // 이미 거부한 사용자
      return false;
    }
    
    if (permission === 'granted') {
      // 이미 허용한 사용자
      return true;
    }
    
    // 처음 묻는 경우
    return new Promise((resolve) => {
      // Expo Go에서는 로컬 알림만 사용한다고 안내
      const alertMessage = this.isExpoGo 
        ? '분석이 완료되면 앱 내 알림으로 알려드릴까요?\n(Expo Go에서는 앱이 열려있을 때만 알림이 표시됩니다)'
        : '분석이 완료되면 알림으로 알려드릴까요?';

      Alert.alert(
        '알림 권한 요청',
        alertMessage,
        [
          {
            text: '아니요',
            onPress: async () => {
              await AsyncStorage.setItem(this.NOTIFICATION_PERMISSION_KEY, 'denied');
              resolve(false);
            },
            style: 'cancel',
          },
          {
            text: '네, 알려주세요',
            onPress: async () => {
              const hasPermission = await this.requestPermissions();
              if (hasPermission) {
                const token = await this.registerForPushNotifications();
                if (token) {
                  await AsyncStorage.setItem(this.PUSH_TOKEN_KEY, token);
                }
              }
              resolve(hasPermission);
            },
          },
        ],
        { cancelable: false }
      );
    });
  }

  // 로컬 알림 표시 (테스트용)
  async showLocalNotification(title: string, body: string, data?: any) {
    await Notifications.scheduleNotificationAsync({
      content: {
        title,
        body,
        data,
        sound: true,
      },
      trigger: null, // 즉시 표시
    });
  }

  // 권한 상태 리셋 (설정에서 사용)
  async resetPermissionStatus() {
    await AsyncStorage.removeItem(this.NOTIFICATION_PERMISSION_KEY);
    await AsyncStorage.removeItem(this.PUSH_TOKEN_KEY);
  }
}

export default new NotificationService();