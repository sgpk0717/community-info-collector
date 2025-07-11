export const API_BASE_URL = 'http://192.168.0.83:8000'; // TODO: 실제 배포 URL로 변경
export const WS_BASE_URL = 'ws://192.168.0.83:8000'; // WebSocket URL

export const STORAGE_KEYS = {
  USER: '@reddit_analyzer_user',
  REPORTS: '@reddit_analyzer_reports',
  SCHEDULE: '@reddit_analyzer_schedule',
  SETTINGS: '@reddit_analyzer_settings',
};

export const DEFAULT_SCHEDULE_INTERVAL = 360; // 6시간 (분 단위)

export const REPORT_LENGTHS = {
  simple: { label: '간단', chars: 1200 },
  moderate: { label: '보통', chars: 1800 },
  detailed: { label: '상세', chars: 2400 },
};