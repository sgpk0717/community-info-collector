import React from 'react';
import { View, ViewStyle, useColorScheme } from 'react-native';

interface NeumorphicViewProps {
  children: React.ReactNode;
  style?: ViewStyle | ViewStyle[];
  isInset?: boolean;
}

const NeumorphicView: React.FC<NeumorphicViewProps> = ({ 
  children, 
  style, 
  isInset = false 
}) => {
  const isDarkMode = useColorScheme() === 'dark';

  const getNeumorphicStyle = (): ViewStyle => {
    if (isDarkMode) {
      return isInset ? {
        shadowColor: '#000000',
        shadowOffset: { width: -4, height: -4 },
        shadowOpacity: 0.7,
        shadowRadius: 6,
        elevation: isInset ? 0 : 8,
      } : {
        shadowColor: '#000000',
        shadowOffset: { width: 6, height: 6 },
        shadowOpacity: 0.6,
        shadowRadius: 10,
        elevation: 8,
      };
    } else {
      return isInset ? {
        shadowColor: '#ffffff',
        shadowOffset: { width: -6, height: -6 },
        shadowOpacity: 1,
        shadowRadius: 10,
        elevation: isInset ? 0 : 8,
      } : {
        shadowColor: '#a8b0b9',
        shadowOffset: { width: 8, height: 8 },
        shadowOpacity: 0.5,
        shadowRadius: 12,
        elevation: 8,
      };
    }
  };

  return (
    <View style={[getNeumorphicStyle(), style]}>
      {!isInset && isDarkMode && (
        <View
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            borderRadius: style?.borderRadius || 0,
            shadowColor: '#2a2a2a',
            shadowOffset: { width: -6, height: -6 },
            shadowOpacity: 0.3,
            shadowRadius: 10,
          }}
        />
      )}
      {!isInset && !isDarkMode && (
        <View
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            borderRadius: style?.borderRadius || 0,
            shadowColor: '#ffffff',
            shadowOffset: { width: -8, height: -8 },
            shadowOpacity: 0.9,
            shadowRadius: 12,
          }}
        />
      )}
      {children}
    </View>
  );
};

export default NeumorphicView;