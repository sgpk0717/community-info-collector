import React, { useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StatusBar, useColorScheme } from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

import HomeScreen from './src/screens/HomeScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import ReportsScreen from './src/screens/ReportsScreen';
import AuthService from './src/services/auth.service';

const Tab = createBottomTabNavigator();

function App() {
  const isDarkMode = useColorScheme() === 'dark';

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

  return (
    <>
      <StatusBar 
        barStyle={isDarkMode ? 'light-content' : 'dark-content'}
        backgroundColor={isDarkMode ? '#1a1a1a' : '#ffffff'}
      />
      <NavigationContainer>
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
              paddingBottom: 5,
              paddingTop: 5,
              height: 60,
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
      </NavigationContainer>
    </>
  );
}

export default App;