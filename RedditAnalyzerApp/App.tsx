import 'react-native-gesture-handler';
import React, { useEffect, useState, useRef } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { StatusBar, useColorScheme, LogBox } from 'react-native';
import { MaterialIcons as Icon } from '@expo/vector-icons';
import { SafeAreaProvider, useSafeAreaInsets } from 'react-native-safe-area-context';

import HomeScreen from './src/screens/HomeScreen';
import ScheduleCreateScreen from './src/screens/ScheduleCreateScreen';
import ScheduleListScreen from './src/screens/ScheduleListScreen';
import ReportsScreen from './src/screens/ReportsScreen';
import SplashScreen from './src/screens/SplashScreen';
import SecondSplashScreen from './src/screens/SecondSplashScreen';
import LoginScreen from './src/screens/LoginScreen';
import RegisterScreen from './src/screens/RegisterScreen';
import AuthService from './src/services/auth.service';
import { AuthProvider, useAuth } from './src/context/AuthContext';
import NotificationService from './src/services/notification.service';
import * as Notifications from 'expo-notifications';

// Expo Go에서 나오는 알림 관련 경고 숨기기
LogBox.ignoreLogs([
  'expo-notifications: Android Push notifications',
  '`expo-notifications` functionality is not fully supported in Expo Go',
]);

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

function MainTabNavigator() {
  const isDarkMode = useColorScheme() === 'dark';
  const insets = useSafeAreaInsets();

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName;

          if (route.name === 'Home') {
            iconName = 'search';
          } else if (route.name === 'ScheduleCreate') {
            iconName = 'schedule';
          } else if (route.name === 'ScheduleList') {
            iconName = 'list';
          } else if (route.name === 'Reports') {
            iconName = 'folder';
          }

          return <Icon name={iconName!} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#667eea',
        tabBarInactiveTintColor: 'gray',
        tabBarStyle: {
          backgroundColor: isDarkMode ? '#2d2d2d' : '#ffffff',
          borderTopColor: isDarkMode ? '#444' : '#eee',
          paddingBottom: insets.bottom > 0 ? insets.bottom : 10,
          paddingTop: 5,
          height: 60 + (insets.bottom > 0 ? insets.bottom : 10),
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: '600',
        },
        headerStyle: {
          backgroundColor: isDarkMode ? '#1a1a1a' : '#ffffff',
        },
        headerTintColor: isDarkMode ? '#ffffff' : '#000000',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      })}
    >
      <Tab.Screen 
        name="Home" 
        component={HomeScreen} 
        options={{ 
          title: '실시간 분석',
          headerTitle: '🔍 커뮤니티 실시간 분석'
        }} 
      />
      <Tab.Screen 
        name="ScheduleCreate" 
        component={ScheduleCreateScreen} 
        options={{ 
          title: '스케줄 등록',
          headerTitle: '⏰ 스케줄 등록'
        }} 
      />
      <Tab.Screen 
        name="ScheduleList" 
        component={ScheduleListScreen} 
        options={{ 
          title: '스케줄 목록',
          headerTitle: '📋 내 스케줄'
        }} 
      />
      <Tab.Screen 
        name="Reports" 
        component={ReportsScreen} 
        options={{ 
          title: '보고서',
          headerTitle: '📊 분석 보고서'
        }} 
      />
    </Tab.Navigator>
  );
}

function AppNavigator() {
  const { isAuthenticated, isLoading, user } = useAuth();
  const [isInitialSplash, setIsInitialSplash] = useState(true);
  const [isSecondSplash, setIsSecondSplash] = useState(false);
  const navigation = useRef<any>(null);

  useEffect(() => {
    // 앱 시작 시 초기화
    initializeApp();
    
    // 알림 리스너 설정
    setupNotificationListeners();
  }, []);

  const initializeApp = async () => {
    try {
      // 알림 서비스 초기화
      await NotificationService.initialize();
      console.log('App initialized');
    } catch (error) {
      console.error('App initialization error:', error);
    }
  };

  const setupNotificationListeners = () => {
    // 알림 수신 리스너 (앱이 foreground일 때)
    const notificationListener = Notifications.addNotificationReceivedListener(notification => {
      console.log('알림 수신:', notification);
    });

    // 알림 클릭 리스너
    const responseListener = Notifications.addNotificationResponseReceivedListener(response => {
      console.log('알림 클릭:', response);
      const data = response.notification.request.content.data;
      
      if (data?.type === 'analysis_complete' && navigation.current) {
        // 보고서 화면으로 이동
        navigation.current.navigate('Reports');
      }
    });

    return () => {
      notificationListener.remove();
      responseListener.remove();
    };
  };

  const handleInitialSplashFinish = () => {
    setIsInitialSplash(false);
  };

  const handleSecondSplashFinish = () => {
    setIsSecondSplash(false);
  };

  // 로그인 성공 시 두 번째 스플래시 실행
  useEffect(() => {
    if (isAuthenticated && !isInitialSplash) {
      setIsSecondSplash(true);
    }
  }, [isAuthenticated, isInitialSplash]);

  if (isInitialSplash) {
    return <SplashScreen onFinish={handleInitialSplashFinish} />;
  }

  if (isLoading) {
    return <SplashScreen onFinish={() => {}} />;
  }

  if (!isAuthenticated) {
    return (
      <NavigationContainer>
        <Stack.Navigator screenOptions={{ headerShown: false }}>
          <Stack.Screen name="Login" component={LoginScreen} />
          <Stack.Screen name="Register" component={RegisterScreen} />
        </Stack.Navigator>
      </NavigationContainer>
    );
  }

  if (isSecondSplash) {
    return <SecondSplashScreen onFinish={handleSecondSplashFinish} userName={user?.nickname} />;
  }

  return (
    <>
      <StatusBar 
        barStyle={'light-content'}
        backgroundColor={'#1a1a1a'}
      />
      <NavigationContainer>
        <MainTabNavigator />
      </NavigationContainer>
    </>
  );
}

function MainApp() {
  return (
    <AuthProvider>
      <SafeAreaProvider>
        <AppNavigator />
      </SafeAreaProvider>
    </AuthProvider>
  );
}

function App() {
  return <MainApp />;
}

export default App;