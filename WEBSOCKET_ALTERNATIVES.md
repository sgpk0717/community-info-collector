# WebSocket vs 대안 방안 비교

## 현재 WebSocket 방식의 문제점

### 1. 개발 환경 문제
- **네트워크 의존성**: 로컬 IP 주소 하드코딩으로 인한 네트워크 변경 시 오류
- **연결 불안정**: 모바일 네트워크 환경에서 WebSocket 연결 끊김 빈발
- **디버깅 복잡성**: 실시간 연결 상태 추적 어려움

### 2. 운영 환경에서의 한계
- **프록시/로드밸런서**: Nginx, CloudFlare 등에서 WebSocket 설정 복잡
- **스케일링**: 여러 서버 인스턴스 간 WebSocket 세션 공유 어려움
- **모바일 앱**: 백그라운드 모드에서 연결 유지 불가
- **배터리 소모**: 지속적인 연결로 인한 배터리 드레인

## 추천 대안: Polling 방식

### 1. 단순 폴링 (Simple Polling)
```typescript
// 진행률을 주기적으로 확인
const pollProgress = async (sessionId: string) => {
  const response = await fetch(`/api/v1/progress/${sessionId}`);
  const progress = await response.json();
  return progress;
};

// 2초마다 체크
const progressInterval = setInterval(async () => {
  const progress = await pollProgress(sessionId);
  updateUI(progress);
  
  if (progress.percentage === 100) {
    clearInterval(progressInterval);
  }
}, 2000);
```

### 2. 장점
- **안정성**: HTTP 요청 기반으로 네트워크 이슈에 강함
- **단순성**: 복잡한 연결 관리 불필요
- **호환성**: 모든 네트워크 환경에서 동작
- **디버깅**: 일반적인 API 요청과 동일하게 디버깅 가능

### 3. 성능 최적화
- **백오프 전략**: 진행률이 변경되지 않으면 폴링 간격 증가
- **조건부 폴링**: 분석 중일 때만 폴링 활성화
- **캐싱**: 동일한 진행률은 캐시하여 불필요한 UI 업데이트 방지

## 제안: Hybrid 방식

### 1. 기본은 Polling, 빠른 업데이트가 필요한 경우만 WebSocket
```typescript
class ProgressTracker {
  private useWebSocket: boolean = false;
  
  async startTracking(sessionId: string) {
    // WebSocket 연결 시도
    try {
      await this.connectWebSocket(sessionId);
      this.useWebSocket = true;
    } catch (error) {
      // 실패 시 Polling으로 fallback
      console.log('WebSocket 실패, Polling 모드로 전환');
      this.startPolling(sessionId);
    }
  }
}
```

### 2. 점진적 개선
1. **1단계**: WebSocket 제거하고 Polling으로 변경
2. **2단계**: 안정성 확인 후 필요시 Server-Sent Events (SSE) 도입
3. **3단계**: 대규모 서비스 시 Redis Pub/Sub + Polling 조합

## 즉시 적용 방안

현재 문제를 빠르게 해결하려면:

1. **WebSocket 비활성화**: 진행률 UI를 단순 스피너로 변경
2. **완료 알림**: 분석 완료 시 Push Notification 또는 일반 알림
3. **결과 확인**: 보고서 탭에서 새로운 보고서 확인

이렇게 하면 현재 에러 없이 안정적으로 동작하며, 나중에 점진적으로 개선할 수 있습니다.