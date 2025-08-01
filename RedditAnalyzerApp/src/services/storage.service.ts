import AsyncStorage from '@react-native-async-storage/async-storage';
import { User, Report, ScheduleConfig } from '../types';
import { STORAGE_KEYS } from '../utils/constants';

class StorageService {
  // User  (
  async getUser(): Promise<User | null> {
    try {
      const data = await AsyncStorage.getItem(STORAGE_KEYS.USER);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Error getting user:', error);
      return null;
    }
  }

  async saveUser(user: User): Promise<void> {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
    } catch (error) {
      console.error('Error saving user:', error);
    }
  }

  // Reports  (
  async getReports(): Promise<Report[]> {
    try {
      const data = await AsyncStorage.getItem(STORAGE_KEYS.REPORTS);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Error getting reports:', error);
      return [];
    }
  }

  async saveReport(report: Report): Promise<void> {
    try {
      const reports = await this.getReports();
      reports.unshift(report); // \� �D ^�
      
      // \  100L��  �
      const trimmedReports = reports.slice(0, 100);
      
      await AsyncStorage.setItem(STORAGE_KEYS.REPORTS, JSON.stringify(trimmedReports));
    } catch (error) {
      console.error('Error saving report:', error);
    }
  }

  async deleteReport(reportId: string): Promise<void> {
    try {
      const reports = await this.getReports();
      const filtered = reports.filter(r => r.id !== reportId);
      await AsyncStorage.setItem(STORAGE_KEYS.REPORTS, JSON.stringify(filtered));
    } catch (error) {
      console.error('Error deleting report:', error);
    }
  }

  // Schedule  (
  async getScheduleConfig(): Promise<ScheduleConfig | null> {
    try {
      const data = await AsyncStorage.getItem(STORAGE_KEYS.SCHEDULE);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Error getting schedule config:', error);
      return null;
    }
  }

  async saveScheduleConfig(config: ScheduleConfig): Promise<void> {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.SCHEDULE, JSON.stringify(config));
    } catch (error) {
      console.error('Error saving schedule config:', error);
    }
  }

  // � pt0 �
  async clearAllData(): Promise<void> {
    try {
      await AsyncStorage.multiRemove(Object.values(STORAGE_KEYS));
    } catch (error) {
      console.error('Error clearing all data:', error);
    }
  }
}

export default new StorageService();