export const API_BASE_URL = 'http://192.168.0.83:8000'; // TODO: 4� 8� URL\ ��

export const STORAGE_KEYS = {
  USER: '@reddit_analyzer_user',
  REPORTS: '@reddit_analyzer_reports',
  SCHEDULE: '@reddit_analyzer_schedule',
  SETTINGS: '@reddit_analyzer_settings',
};

export const DEFAULT_SCHEDULE_INTERVAL = 360; // 6� (� �)

export const REPORT_LENGTHS = {
  simple: { label: '�', chars: 1200 },
  moderate: { label: '��', chars: 1800 },
  detailed: { label: '�8X�', chars: 2400 },
};