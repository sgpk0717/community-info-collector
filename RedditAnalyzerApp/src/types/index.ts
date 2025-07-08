export interface User {
  deviceId: string;
  name?: string;
  createdAt: Date;
  lastActive: Date;
}

export interface Report {
  id: string;
  userId: string;
  keyword: string;
  content: string;
  htmlContent?: string;
  metadata: {
    charCount: number;
    processingTime: number;
    timestamp: string;
    reportFile?: string;
  };
  createdAt: Date;
}

export interface ScheduleConfig {
  enabled: boolean;
  intervalMinutes: number;
  keywords: string[];
  lastRun?: Date;
  nextRun?: Date;
}

export type ReportLength = 'simple' | 'moderate' | 'detailed';

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  details?: string[];
}