import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';
import { ApiResponse, ReportLength, ScheduleConfig } from '../types';
import AuthService from './auth.service';

class ApiService {
  private api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 300000, // 5분 타임아웃
    headers: {
      'Content-Type': 'application/json',
    },
  });

  async analyze(userInput: string, reportLength: ReportLength, sessionId?: string, pushToken?: string | null): Promise<ApiResponse> {
    try {
      const user = AuthService.getCurrentUser();
      const response = await this.api.post('/api/v1/search', {
        query: userInput,
        sources: ['reddit'],
        length: reportLength,
        session_id: sessionId,
        user_nickname: user?.nickname, // 사용자 닉네임 추가
        push_token: pushToken, // 푸시 토큰 추가
      });

      const data = response.data;
      
      return {
        success: true,
        data: {
          queryId: data.query_id,
          content: data.report.full_report,
          htmlReport: data.report.full_report,
          sessionId: data.session_id,
          metadata: {
            postsCollected: data.posts_collected,
            charCount: data.report.full_report.length,
            processingTime: Date.now() - new Date().getTime(),
          },
        },
      };
    } catch (error) {
      if (axios.isAxiosError(error)) {
        return {
          success: false,
          error: error.response?.data?.detail || error.response?.data?.error || '분석에 실패했습니다',
          details: error.response?.data?.details,
        };
      }
      
      return {
        success: false,
        error: '네트워크 오류가 발생했습니다',
      };
    }
  }

  async checkStatus(): Promise<boolean> {
    try {
      const response = await this.api.get('/');
      return response.data.message === 'Community Info Collector API';
    } catch (error) {
      console.error('API status check failed:', error);
      return false;
    }
  }

  // 사용자 관련 API (백엔드 API 호출)
  async registerUser(nickname: string): Promise<ApiResponse> {
    try {
      const response = await this.api.post('/api/v1/users/register', {
        nickname: nickname,
      });

      return {
        success: true,
        data: response.data.data,
      };
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 409) {
          return {
            success: false,
            error: 'NICKNAME_EXISTS',
          };
        }
        return {
          success: false,
          error: error.response?.data?.detail || '사용자 등록에 실패했습니다',
        };
      }
      
      return {
        success: false,
        error: '사용자 등록에 실패했습니다',
      };
    }
  }

  async loginUser(nickname: string): Promise<ApiResponse> {
    try {
      const response = await this.api.post('/api/v1/users/login', {
        nickname: nickname,
      });

      return {
        success: true,
        data: response.data.data,
      };
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 404) {
          return {
            success: false,
            error: 'USER_NOT_FOUND',
          };
        }
        return {
          success: false,
          error: error.response?.data?.detail || 'UNKNOWN_ERROR',
        };
      }
      
      return {
        success: false,
        error: '로그인에 실패했습니다',
      };
    }
  }

  // 기존 사용자 등록 메서드 (하위 호환성을 위해 유지)
  async registerDeviceUser(deviceId: string, name?: string, pushToken?: string): Promise<ApiResponse> {
    try {
      const response = await this.api.post('/api/v1/schedule/users', {
        device_id: deviceId,
        name: name,
        push_token: pushToken,
      });

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('User registration error:', error);
      return {
        success: false,
        error: '사용자 등록에 실패했습니다',
      };
    }
  }

  // 스케줄 관련 API
  async createSchedule(
    deviceId: string,
    keyword: string,
    intervalMinutes: number,
    reportLength: ReportLength,
    totalReports: number
  ): Promise<ApiResponse> {
    try {
      const response = await this.api.post(
        `/api/v1/schedule/schedules?device_id=${deviceId}`,
        {
          keyword: keyword,
          interval_minutes: intervalMinutes,
          report_length: reportLength,
          total_reports: totalReports,
        }
      );

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Create schedule error:', error);
      return {
        success: false,
        error: '스케줄 생성에 실패했습니다',
      };
    }
  }

  async getSchedules(deviceId: string, status?: string): Promise<ApiResponse> {
    try {
      let url = `/api/v1/schedule/schedules?device_id=${deviceId}`;
      if (status) {
        url += `&status=${status}`;
      }

      const response = await this.api.get(url);

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Get schedules error:', error);
      return {
        success: false,
        error: '스케줄 조회에 실패했습니다',
      };
    }
  }

  async cancelSchedule(scheduleId: number): Promise<ApiResponse> {
    try {
      const response = await this.api.delete(
        `/api/v1/schedule/schedules/${scheduleId}`
      );

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Cancel schedule error:', error);
      return {
        success: false,
        error: '스케줄 취소에 실패했습니다',
      };
    }
  }

  async pauseSchedule(scheduleId: number): Promise<ApiResponse> {
    try {
      const response = await this.api.post(
        `/api/v1/schedule/schedules/${scheduleId}/pause`
      );

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Pause schedule error:', error);
      return {
        success: false,
        error: '스케줄 일시정지에 실패했습니다',
      };
    }
  }

  async resumeSchedule(scheduleId: number): Promise<ApiResponse> {
    try {
      const response = await this.api.post(
        `/api/v1/schedule/schedules/${scheduleId}/resume`
      );

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Resume schedule error:', error);
      return {
        success: false,
        error: '스케줄 재개에 실패했습니다',
      };
    }
  }

  // 알림 관련 API
  async getNotifications(deviceId: string, unreadOnly: boolean = false): Promise<ApiResponse> {
    try {
      const response = await this.api.get(
        `/api/v1/schedule/notifications?device_id=${deviceId}&unread_only=${unreadOnly}`
      );

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Get notifications error:', error);
      return {
        success: false,
        error: '알림 조회에 실패했습니다',
      };
    }
  }

  async markNotificationRead(notificationId: number): Promise<ApiResponse> {
    try {
      const response = await this.api.put(
        `/api/v1/schedule/notifications/${notificationId}/read`
      );

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Mark notification read error:', error);
      return {
        success: false,
        error: '알림 읽음 처리에 실패했습니다',
      };
    }
  }

  // 하위 호환성을 위한 기존 메서드들 (Settings 화면에서 사용)
  async startSchedule(config: ScheduleConfig): Promise<ApiResponse> {
    const user = AuthService.getCurrentUser();
    if (!user) {
      return {
        success: false,
        error: '사용자 정보를 찾을 수 없습니다',
      };
    }

    // 첫 번째 키워드로 스케줄 생성
    const keyword = config.keywords[0];
    const totalReports = Math.floor(10080 / config.intervalMinutes); // 일주일 동안의 보고서 수

    return this.createSchedule(
      user.deviceId,
      keyword,
      config.intervalMinutes,
      'moderate',
      totalReports
    );
  }

  async stopSchedule(): Promise<ApiResponse> {
    const user = AuthService.getCurrentUser();
    if (!user) {
      return {
        success: false,
        error: '사용자 정보를 찾을 수 없습니다',
      };
    }

    // 활성 스케줄 조회 후 첫 번째 스케줄 취소
    const schedulesResult = await this.getSchedules(user.deviceId, 'active');
    if (schedulesResult.success && schedulesResult.data && schedulesResult.data.length > 0) {
      const scheduleId = schedulesResult.data[0].id;
      return this.cancelSchedule(scheduleId);
    }

    return {
      success: true,
      data: { message: 'No active schedules found' },
    };
  }

  async getScheduleStatus(): Promise<any> {
    const user = AuthService.getCurrentUser();
    if (!user) return null;

    const result = await this.getSchedules(user.deviceId, 'active');
    if (result.success && result.data && result.data.length > 0) {
      const schedule = result.data[0];
      return {
        enabled: true,
        intervalMinutes: schedule.interval_minutes,
        keywords: [schedule.keyword],
        nextRun: schedule.next_run,
        lastRun: schedule.last_run,
      };
    }

    return null;
  }

  private async getUserIdentifier(): Promise<string> {
    const user = AuthService.getCurrentUser();
    return user?.deviceId || '';
  }

  // 보고서 관련 API
  async getUserReports(userNickname?: string, limit: number = 20): Promise<ApiResponse> {
    try {
      const user = AuthService.getCurrentUser();
      const nickname = userNickname || user?.nickname;
      
      if (!nickname) {
        return {
          success: false,
          error: '사용자 닉네임이 필요합니다',
        };
      }

      const response = await this.api.get(`/api/v1/reports/${nickname}?limit=${limit}`);

      return {
        success: true,
        data: response.data.reports,
      };
    } catch (error) {
      console.error('Get user reports error:', error);
      if (axios.isAxiosError(error)) {
        return {
          success: false,
          error: error.response?.data?.detail || '보고서 조회에 실패했습니다',
        };
      }
      
      return {
        success: false,
        error: '보고서 조회에 실패했습니다',
      };
    }
  }

  async getReportDetail(reportId: string): Promise<ApiResponse> {
    try {
      const response = await this.api.get(`/api/v1/reports/detail/${reportId}`);

      return {
        success: true,
        data: response.data.report,
      };
    } catch (error) {
      console.error('Get report detail error:', error);
      if (axios.isAxiosError(error)) {
        return {
          success: false,
          error: error.response?.data?.detail || '보고서 상세 조회에 실패했습니다',
        };
      }
      
      return {
        success: false,
        error: '보고서 상세 조회에 실패했습니다',
      };
    }
  }

  async deleteReport(reportId: string, userNickname?: string): Promise<ApiResponse> {
    try {
      const user = AuthService.getCurrentUser();
      const nickname = userNickname || user?.nickname;
      
      if (!nickname) {
        return {
          success: false,
          error: '사용자 닉네임이 필요합니다',
        };
      }

      const response = await this.api.delete(`/api/v1/reports/${reportId}?user_nickname=${nickname}`);

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Delete report error:', error);
      if (axios.isAxiosError(error)) {
        return {
          success: false,
          error: error.response?.data?.detail || '보고서 삭제에 실패했습니다',
        };
      }
      
      return {
        success: false,
        error: '보고서 삭제에 실패했습니다',
      };
    }
  }

  async getReportLinks(reportId: string): Promise<ApiResponse<any[]>> {
    try {
      const response = await this.api.get(`/api/v1/report/${reportId}/links`);

      return {
        success: true,
        data: response.data.links || [],
      };
    } catch (error) {
      console.error('Get report links error:', error);
      if (axios.isAxiosError(error)) {
        return {
          success: false,
          error: error.response?.data?.detail || '링크 조회에 실패했습니다',
          data: [],
        };
      }
      
      return {
        success: false,
        error: '링크 조회에 실패했습니다',
        data: [],
      };
    }
  }

  async getReportStats(userNickname?: string): Promise<ApiResponse> {
    try {
      const user = AuthService.getCurrentUser();
      const nickname = userNickname || user?.nickname;
      
      if (!nickname) {
        return {
          success: false,
          error: '사용자 닉네임이 필요합니다',
        };
      }

      const response = await this.api.get(`/api/v1/reports/${nickname}/stats`);

      return {
        success: true,
        data: response.data.stats,
      };
    } catch (error) {
      console.error('Get report stats error:', error);
      if (axios.isAxiosError(error)) {
        return {
          success: false,
          error: error.response?.data?.detail || '통계 조회에 실패했습니다',
        };
      }
      
      return {
        success: false,
        error: '통계 조회에 실패했습니다',
      };
    }
  }

  // 새로운 스케줄링 API (사용자 닉네임 기반)
  async createNewSchedule(scheduleData: {
    keyword: string;
    interval_minutes: number;
    total_reports: number;
    start_time: string;
    notification_enabled: boolean;
    user_nickname: string;
  }): Promise<ApiResponse> {
    try {
      const response = await this.api.post('/api/v1/schedule/create', scheduleData);

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Create new schedule error:', error);
      if (axios.isAxiosError(error)) {
        return {
          success: false,
          error: error.response?.data?.detail || '스케줄 등록에 실패했습니다',
        };
      }
      
      return {
        success: false,
        error: '스케줄 등록에 실패했습니다',
      };
    }
  }

  async getUserSchedules(userNickname: string): Promise<ApiResponse> {
    try {
      const response = await this.api.get(`/api/v1/schedule/user/${userNickname}`);

      return {
        success: true,
        data: response.data.schedules || [],
      };
    } catch (error) {
      console.error('Get user schedules error:', error);
      if (axios.isAxiosError(error)) {
        return {
          success: false,
          error: error.response?.data?.detail || '스케줄 목록 조회에 실패했습니다',
          data: [],
        };
      }
      
      return {
        success: false,
        error: '스케줄 목록 조회에 실패했습니다',
        data: [],
      };
    }
  }

  async deleteSchedule(scheduleId: number, forceDelete: boolean = false): Promise<ApiResponse> {
    try {
      const response = await this.api.delete(
        `/api/v1/schedule/${scheduleId}${forceDelete ? '?force_delete=true' : ''}`
      );

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Delete schedule error:', error);
      if (axios.isAxiosError(error)) {
        return {
          success: false,
          error: error.response?.data?.detail || '스케줄 삭제에 실패했습니다',
        };
      }
      
      return {
        success: false,
        error: '스케줄 삭제에 실패했습니다',
      };
    }
  }

  async deleteAllCancelledSchedules(userNickname: string): Promise<ApiResponse> {
    try {
      const response = await this.api.delete(`/api/v1/schedule/cancelled/${userNickname}`);

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Delete all cancelled schedules error:', error);
      if (axios.isAxiosError(error)) {
        return {
          success: false,
          error: error.response?.data?.detail || '취소된 스케줄 일괄 삭제에 실패했습니다',
        };
      }
      
      return {
        success: false,
        error: '취소된 스케줄 일괄 삭제에 실패했습니다',
      };
    }
  }

  async updateScheduleStatus(scheduleId: number, action: 'pause' | 'resume'): Promise<ApiResponse> {
    try {
      const response = await this.api.patch(`/api/v1/schedule/${scheduleId}/status`, {
        action: action,
      });

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Update schedule status error:', error);
      if (axios.isAxiosError(error)) {
        return {
          success: false,
          error: error.response?.data?.detail || '스케줄 상태 변경에 실패했습니다',
        };
      }
      
      return {
        success: false,
        error: '스케줄 상태 변경에 실패했습니다',
      };
    }
  }
}

export default new ApiService();