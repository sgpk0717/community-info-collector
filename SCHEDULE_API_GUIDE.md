# 스케줄링 API 가이드

## 개요

Community Info Collector의 스케줄링 시스템은 사용자가 설정한 키워드에 대해 주기적으로 자동 보고서를 생성하고 푸시 알림을 발송합니다.

## 주요 기능

1. **자동 보고서 생성**: 설정된 주기마다 커뮤니티 정보를 수집하고 분석
2. **푸시 알림**: 보고서 생성 완료 시 모바일 앱으로 알림 발송
3. **총 보고 횟수 제한**: 원하는 횟수만큼만 보고서 생성
4. **다중 스케줄 관리**: 여러 키워드에 대해 동시에 스케줄 실행
5. **스케줄 제어**: 일시정지, 재개, 취소 기능

## API 엔드포인트

### 1. 사용자 등록

새 사용자를 등록하거나 기존 사용자 정보를 반환합니다.

```http
POST /api/v1/schedule/users
Content-Type: application/json

{
    "device_id": "unique-device-id",
    "name": "사용자명",
    "push_token": "FCM-push-token"
}
```

**응답:**
```json
{
    "id": 1,
    "device_id": "unique-device-id",
    "name": "사용자명",
    "push_token": "FCM-push-token",
    "created_at": "2025-01-09T10:00:00"
}
```

### 2. 스케줄 생성

새로운 스케줄을 생성합니다.

```http
POST /api/v1/schedule/schedules?device_id=unique-device-id
Content-Type: application/json

{
    "keyword": "Tesla 2025",
    "interval_minutes": 360,
    "report_length": "moderate",
    "total_reports": 10
}
```

**파라미터 설명:**
- `keyword`: 검색할 키워드
- `interval_minutes`: 실행 주기 (분 단위) - 60, 360, 720, 1440
- `report_length`: 보고서 길이 - "simple", "moderate", "detailed"
- `total_reports`: 총 생성할 보고서 수

**응답:**
```json
{
    "id": 1,
    "user_id": 1,
    "keyword": "Tesla 2025",
    "interval_minutes": 360,
    "report_length": "moderate",
    "total_reports": 10,
    "completed_reports": 0,
    "status": "active",
    "next_run": "2025-01-09T16:00:00",
    "last_run": null,
    "created_at": "2025-01-09T10:00:00",
    "updated_at": "2025-01-09T10:00:00"
}
```

### 3. 스케줄 목록 조회

사용자의 모든 스케줄을 조회합니다.

```http
GET /api/v1/schedule/schedules?device_id=unique-device-id&status=active
```

**쿼리 파라미터:**
- `device_id`: 사용자 디바이스 ID (필수)
- `status`: 필터링할 상태 (선택) - "active", "paused", "completed", "cancelled"

### 4. 스케줄 상태 변경

#### 스케줄 일시정지
```http
POST /api/v1/schedule/schedules/{schedule_id}/pause
```

#### 스케줄 재개
```http
POST /api/v1/schedule/schedules/{schedule_id}/resume
```

#### 스케줄 취소
```http
DELETE /api/v1/schedule/schedules/{schedule_id}
```

### 5. 알림 관리

#### 알림 목록 조회
```http
GET /api/v1/schedule/notifications?device_id=unique-device-id&unread_only=true
```

#### 알림 읽음 처리
```http
PUT /api/v1/schedule/notifications/{notification_id}/read
```

## 워크플로우 예시

### 1. 사용자 등록 및 스케줄 생성

```python
import requests

# 1. 사용자 등록
user_response = requests.post(
    "http://localhost:8000/api/v1/schedule/users",
    json={
        "device_id": "device123",
        "name": "홍길동",
        "push_token": "fcm-token-xyz"
    }
)
user_data = user_response.json()

# 2. 스케줄 생성
schedule_response = requests.post(
    f"http://localhost:8000/api/v1/schedule/schedules?device_id=device123",
    json={
        "keyword": "Apple stock forecast",
        "interval_minutes": 360,  # 6시간마다
        "report_length": "moderate",
        "total_reports": 20  # 총 20개 보고서 (5일간)
    }
)
schedule_data = schedule_response.json()
print(f"스케줄 ID: {schedule_data['id']}")
```

### 2. 스케줄 상태 확인 및 관리

```python
# 활성 스케줄 조회
schedules_response = requests.get(
    "http://localhost:8000/api/v1/schedule/schedules",
    params={"device_id": "device123", "status": "active"}
)
active_schedules = schedules_response.json()

# 첫 번째 스케줄 일시정지
if active_schedules:
    schedule_id = active_schedules[0]['id']
    pause_response = requests.post(
        f"http://localhost:8000/api/v1/schedule/schedules/{schedule_id}/pause"
    )
```

## 보고서 길이별 특징

### Simple (간단)
- 약 800자 내외
- 핵심 요약 및 주요 포인트 3가지
- 빠른 정보 파악에 적합

### Moderate (보통)
- 약 1,500자 내외
- 요약, 주요 발견사항, 트렌드 분석, 인사이트 포함
- 일반적인 분석 용도에 적합

### Detailed (상세)
- 약 3,000자 내외
- 종합 요약, 상세 분석, 감정 분석, 시사점 포함
- 심층적인 분석이 필요한 경우에 적합

## 푸시 알림 설정

푸시 알림을 받으려면 다음 설정이 필요합니다:

1. **서버 설정**
   - Firebase 프로젝트 생성
   - FCM 서비스 계정 키 다운로드
   - 환경변수 설정:
     ```
     FCM_PROJECT_ID=your-project-id
     FCM_CREDENTIALS_PATH=/path/to/service-account-key.json
     ```

2. **앱 설정**
   - Firebase SDK 통합
   - 푸시 알림 권한 요청
   - FCM 토큰을 서버에 등록

## 주의사항

1. **API 제한**
   - 동일 키워드로 중복 스케줄 생성 방지
   - 사용자당 최대 10개 활성 스케줄 제한

2. **보고서 생성**
   - 서버 부하를 고려하여 최소 주기는 60분으로 제한
   - 보고서 생성 실패 시 자동 재시도

3. **데이터 보존**
   - 완료/취소된 스케줄은 30일간 보관 후 자동 삭제
   - 생성된 보고서는 영구 보관