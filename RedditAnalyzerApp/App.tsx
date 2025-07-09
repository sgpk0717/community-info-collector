import 'react-native-gesture-handler';
import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { StatusBar, useColorScheme } from 'react-native';
import { MaterialIcons as Icon } from '@expo/vector-icons';
import { SafeAreaProvider, useSafeAreaInsets } from 'react-native-safe-area-context';

import HomeScreen from './src/screens/HomeScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import ReportsScreen from './src/screens/ReportsScreen';
import SplashScreen from './src/screens/SplashScreen';
import LoginScreen from './src/screens/LoginScreen';
import RegisterScreen from './src/screens/RegisterScreen';
import AuthService from './src/services/auth.service';
import { AuthProvider, useAuth } from './src/context/AuthContext';

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
          } else if (route.name === 'Settings') {
            iconName = 'settings';
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
          title: 'Reddit 분석',
          headerTitle: '🔍 Reddit 실시간 분석'
        }} 
      />
      <Tab.Screen 
        name="Settings" 
        component={SettingsScreen} 
        options={{ 
          title: '설정',
          headerTitle: '⚙️ 설정'
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
  const { isAuthenticated, isLoading } = useAuth();
  const [isInitialSplash, setIsInitialSplash] = useState(true);
  const [isSecondSplash, setIsSecondSplash] = useState(false);

  useEffect(() => {
    // 앱 시작 시 초기화
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      // 사용자 인증
      await AuthService.initialize();
    } catch (error) {
      console.error('App initialization error:', error);
    }
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
    return <SplashScreen onFinish={handleSecondSplashFinish} />;
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