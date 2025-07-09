import React, { useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  useColorScheme,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialIcons as Icon } from '@expo/vector-icons';

interface SplashScreenProps {
  onFinish: () => void;
}

const SplashScreen: React.FC<SplashScreenProps> = ({ onFinish }) => {
  const isDarkMode = useColorScheme() === 'dark';
  const fadeAnim = new Animated.Value(0);
  const scaleAnim = new Animated.Value(0.8);
  const rotateAnim = new Animated.Value(0);

  useEffect(() => {
    // 애니메이션 시작
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 10,
        friction: 3,
        useNativeDriver: true,
      }),
      Animated.loop(
        Animated.timing(rotateAnim, {
          toValue: 1,
          duration: 3000,
          useNativeDriver: true,
        })
      ),
    ]).start();

    // 2초 후 종료
    const timer = setTimeout(() => {
      onFinish();
    }, 2000);

    return () => clearTimeout(timer);
  }, []);

  const spin = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  return (
    <LinearGradient
      colors={isDarkMode ? ['#1a202c', '#2d3748'] : ['#667eea', '#764ba2']}
      style={styles.container}
    >
      <Animated.View
        style={[
          styles.content,
          {
            opacity: fadeAnim,
            transform: [{ scale: scaleAnim }],
          },
        ]}
      >
        <Animated.View
          style={[
            styles.iconContainer,
            { transform: [{ rotate: spin }] },
          ]}
        >
          <Icon name="reddit" size={80} color="#ffffff" />
        </Animated.View>
        
        <Text style={styles.title}>Community Analyzer</Text>
        <Text style={styles.subtitle}>실시간 커뮤니티 분석 도구</Text>
        
        <View style={styles.loadingContainer}>
          <View style={styles.loadingDot} />
          <View style={[styles.loadingDot, styles.loadingDotDelay1]} />
          <View style={[styles.loadingDot, styles.loadingDotDelay2]} />
        </View>
      </Animated.View>
      
      <Text style={styles.footer}>Powered by AI</Text>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    alignItems: 'center',
  },
  iconContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 30,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 10,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 18,
    color: 'rgba(255, 255, 255, 0.8)',
    marginBottom: 40,
    textAlign: 'center',
  },
  loadingContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#ffffff',
    marginHorizontal: 5,
    opacity: 0.3,
    animationName: 'pulse',
    animationDuration: '1.5s',
    animationIterationCount: 'infinite',
  },
  loadingDotDelay1: {
    animationDelay: '0.5s',
  },
  loadingDotDelay2: {
    animationDelay: '1s',
  },
  footer: {
    position: 'absolute',
    bottom: 50,
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.6)',
  },
});

export default SplashScreen;