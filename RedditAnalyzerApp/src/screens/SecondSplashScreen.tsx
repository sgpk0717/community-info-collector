import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  useColorScheme,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialIcons as Icon } from '@expo/vector-icons';

interface SecondSplashScreenProps {
  onFinish: () => void;
  userName?: string;
}

const { width, height } = Dimensions.get('window');

const SecondSplashScreen: React.FC<SecondSplashScreenProps> = ({ onFinish, userName }) => {
  const isDarkMode = useColorScheme() === 'dark';
  
  // 애니메이션 값들
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(-50)).current;
  const scaleAnim = useRef(new Animated.Value(0)).current;
  const rotateAnim = useRef(new Animated.Value(0)).current;
  
  // 파티클 애니메이션을 위한 값들
  const particles = Array(6).fill(0).map(() => ({
    x: useRef(new Animated.Value(0)).current,
    y: useRef(new Animated.Value(0)).current,
    opacity: useRef(new Animated.Value(0)).current,
  }));

  useEffect(() => {
    // 메인 애니메이션
    Animated.sequence([
      // 웰컴 텍스트 등장
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 600,
          useNativeDriver: true,
        }),
        Animated.spring(slideAnim, {
          toValue: 0,
          tension: 40,
          friction: 7,
          useNativeDriver: true,
        }),
      ]),
      // 아이콘 등장
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 20,
        friction: 5,
        useNativeDriver: true,
      }),
      // 파티클 애니메이션
      Animated.parallel([
        // 아이콘 회전
        Animated.loop(
          Animated.sequence([
            Animated.timing(rotateAnim, {
              toValue: 1,
              duration: 1000,
              useNativeDriver: true,
            }),
            Animated.timing(rotateAnim, {
              toValue: 0,
              duration: 1000,
              useNativeDriver: true,
            }),
          ])
        ),
        // 파티클 움직임
        ...particles.map((particle, index) => {
          const angle = (index * 60) * Math.PI / 180;
          const radius = 100;
          
          return Animated.parallel([
            Animated.sequence([
              Animated.delay(index * 100),
              Animated.parallel([
                Animated.timing(particle.opacity, {
                  toValue: 1,
                  duration: 300,
                  useNativeDriver: true,
                }),
                Animated.spring(particle.x, {
                  toValue: Math.cos(angle) * radius,
                  tension: 40,
                  friction: 7,
                  useNativeDriver: true,
                }),
                Animated.spring(particle.y, {
                  toValue: Math.sin(angle) * radius,
                  tension: 40,
                  friction: 7,
                  useNativeDriver: true,
                }),
              ]),
            ]),
          ]);
        }),
      ]),
    ]).start();

    // 3초 후 종료
    const timer = setTimeout(() => {
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 300,
        useNativeDriver: true,
      }).start(() => onFinish());
    }, 3000);

    return () => clearTimeout(timer);
  }, []);

  const spin = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  const iconScale = scaleAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0, 1.2],
  });

  return (
    <LinearGradient
      colors={isDarkMode ? ['#0f0c29', '#302b63', '#24243e'] : ['#667eea', '#764ba2', '#f093fb']}
      style={styles.container}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
    >
      <Animated.View style={[styles.content, { opacity: fadeAnim }]}>
        {/* 웰컴 메시지 */}
        <Animated.View
          style={{
            transform: [{ translateY: slideAnim }],
          }}
        >
          <Text style={styles.welcomeText}>환영합니다!</Text>
          {userName && (
            <Text style={styles.userNameText}>{userName}님</Text>
          )}
        </Animated.View>

        {/* 메인 아이콘 컨테이너 */}
        <View style={styles.iconWrapper}>
          {/* 파티클들 */}
          {particles.map((particle, index) => (
            <Animated.View
              key={index}
              style={[
                styles.particle,
                {
                  opacity: particle.opacity,
                  transform: [
                    { translateX: particle.x },
                    { translateY: particle.y },
                  ],
                },
              ]}
            >
              <View style={[
                styles.particleInner,
                { backgroundColor: ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57', '#ff9ff3'][index] }
              ]} />
            </Animated.View>
          ))}

          {/* 메인 아이콘 */}
          <Animated.View
            style={[
              styles.mainIconContainer,
              {
                transform: [
                  { scale: iconScale },
                  { rotate: spin },
                ],
              },
            ]}
          >
            <Icon name="rocket-launch" size={60} color="#ffffff" />
          </Animated.View>
        </View>

        {/* 로딩 메시지 */}
        <View style={styles.loadingTextContainer}>
          <Text style={styles.loadingText}>커뮤니티 분석 준비 중...</Text>
          <View style={styles.progressBar}>
            <Animated.View
              style={[
                styles.progressFill,
                {
                  transform: [{
                    scaleX: fadeAnim.interpolate({
                      inputRange: [0, 1],
                      outputRange: [0, 1],
                    }),
                  }],
                },
              ]}
            />
          </View>
        </View>

        {/* 팁 메시지 */}
        <Animated.View
          style={[
            styles.tipContainer,
            {
              opacity: fadeAnim,
              transform: [{
                translateY: fadeAnim.interpolate({
                  inputRange: [0, 1],
                  outputRange: [20, 0],
                }),
              }],
            },
          ]}
        >
          <Icon name="lightbulb" size={20} color="rgba(255, 255, 255, 0.7)" />
          <Text style={styles.tipText}>
            팁: 여러 키워드는 쉼표로 구분하세요
          </Text>
        </Animated.View>
      </Animated.View>
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
    width: '100%',
  },
  welcomeText: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 8,
    textAlign: 'center',
  },
  userNameText: {
    fontSize: 24,
    color: 'rgba(255, 255, 255, 0.9)',
    marginBottom: 40,
    textAlign: 'center',
  },
  iconWrapper: {
    width: 200,
    height: 200,
    justifyContent: 'center',
    alignItems: 'center',
    marginVertical: 40,
  },
  mainIconContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#ffffff',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.5,
    shadowRadius: 20,
    elevation: 10,
  },
  particle: {
    position: 'absolute',
    width: 20,
    height: 20,
  },
  particleInner: {
    width: '100%',
    height: '100%',
    borderRadius: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 5,
  },
  loadingTextContainer: {
    alignItems: 'center',
    marginTop: 20,
  },
  loadingText: {
    fontSize: 18,
    color: 'rgba(255, 255, 255, 0.9)',
    marginBottom: 15,
  },
  progressBar: {
    width: 200,
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    width: 200,
    backgroundColor: '#ffffff',
    borderRadius: 2,
    transformOrigin: 'left',
  },
  tipContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    position: 'absolute',
    bottom: 80,
    paddingHorizontal: 20,
  },
  tipText: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    marginLeft: 8,
  },
});

export default SecondSplashScreen;