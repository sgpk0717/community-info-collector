import BackgroundFetch from 'react-native-background-fetch';
import StorageService from './storage.service';
import ApiService from './api.service';
import { ScheduleConfig, Report } from '../types';
import AuthService from './auth.service';

class SchedulerService {
  async initialize(): Promise<void> {
    try {
      // Background Fetch $
      await BackgroundFetch.configure({
        minimumFetchInterval: 15, // \� 15�
        stopOnTerminate: false,
        startOnBoot: true,
        enableHeadless: true,
      }, async (taskId) => {
        console.log('[BackgroundFetch] taskId:', taskId);
        
        // �  �� �
        await this.executeScheduledTask();
        
        // �� D� �8
        BackgroundFetch.finish(taskId);
      }, (taskId) => {
        console.log('[BackgroundFetch] TIMEOUT taskId:', taskId);
        BackgroundFetch.finish(taskId);
      });

      // �� Ux
      const status = await BackgroundFetch.status();
      console.log('[BackgroundFetch] status:', status);
    } catch (error) {
      console.error('Error initializing scheduler:', error);
    }
  }

  async executeScheduledTask(): Promise<void> {
    try {
      const config = await StorageService.getScheduleConfig();
      
      if (!config || !config.enabled || config.keywords.length === 0) {
        console.log('Schedule is disabled or no keywords configured');
        return;
      }

      const now = new Date();
      const lastRun = config.lastRun ? new Date(config.lastRun) : null;
      
      if (lastRun) {
        const minutesSinceLastRun = (now.getTime() - lastRun.getTime()) / (1000 * 60);
        if (minutesSinceLastRun < config.intervalMinutes) {
          console.log(`Too soon since last run: ${minutesSinceLastRun} minutes`);
          return;
        }
      }

      //  ����  t � �
      for (const keyword of config.keywords) {
        try {
          const result = await ApiService.analyze(keyword, 'moderate');
          
          if (result.success && result.data) {
            const user = AuthService.getCurrentUser();
            if (!user) continue;

            const report: Report = {
              id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
              userId: user.deviceId,
              keyword,
              content: result.data.content,
              htmlContent: result.data.htmlReport,
              metadata: result.data.metadata,
              createdAt: new Date(),
            };

            await StorageService.saveReport(report);
          }
        } catch (error) {
          console.error(`Error analyzing keyword "${keyword}":`, error);
        }
      }

      // �  �pt�
      config.lastRun = now;
      config.nextRun = new Date(now.getTime() + config.intervalMinutes * 60 * 1000);
      await StorageService.saveScheduleConfig(config);
      
    } catch (error) {
      console.error('Error executing scheduled task:', error);
    }
  }

  async scheduleTask(): Promise<void> {
    try {
      await BackgroundFetch.scheduleTask({
        taskId: 'reddit-analyzer-task',
        delay: 5000, // 5 � �
        periodic: true,
        forceAlarmManager: true,
      });
    } catch (error) {
      console.error('Error scheduling task:', error);
    }
  }

  async stop(): Promise<void> {
    try {
      await BackgroundFetch.stop();
    } catch (error) {
      console.error('Error stopping scheduler:', error);
    }
  }
}

export default new SchedulerService();