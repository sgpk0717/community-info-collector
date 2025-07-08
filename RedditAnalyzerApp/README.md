# Reddit Analyzer App

Reddit 실시간 정보 수집 및 분석을 위한 React Native 앱입니다.

## 주요 기능

- 🔍 키워드 기반 Reddit 정보 수집 및 GPT-4 분석
- 👤 디바이스 기반 사용자 인증
- 📱 로컬 저장소에 보고서 저장
- ⏰ 주기적 자동 분석 (백그라운드 스케줄러)
- 📊 분석 보고서 관리 및 열람

## 기술 스택

- React Native 0.80.1
- TypeScript
- AsyncStorage (로컬 저장소)
- React Native Background Fetch (스케줄러)
- React Native Device Info (디바이스 정보)
- Axios (API 통신)

## 프로젝트 구조

```
RedditAnalyzerApp/
├── src/
│   ├── components/      # 재사용 가능한 컴포넌트
│   ├── screens/         # 화면 컴포넌트
│   ├── services/        # 비즈니스 로직 서비스
│   │   ├── api.service.ts        # API 통신
│   │   ├── auth.service.ts       # 사용자 인증
│   │   ├── storage.service.ts    # 로컬 저장소
│   │   └── scheduler.service.ts  # 백그라운드 작업
│   ├── types/           # TypeScript 타입 정의
│   └── utils/           # 유틸리티 함수 및 상수
├── android/             # Android 네이티브 코드
├── ios/                 # iOS 네이티브 코드
└── package.json
```

## 설치 및 실행

### 1. 의존성 설치

```bash
npm install
```

### 2. iOS 설정 (macOS만 해당)

```bash
cd ios && pod install && cd ..
```

### 3. 환경 설정

`.env.example`을 복사하여 `.env` 파일을 생성하고 API 엔드포인트를 설정합니다:

```bash
cp .env.example .env
```

### 4. 실행

Android:
```bash
npx react-native run-android
```

iOS:
```bash
npx react-native run-ios
```

## API 엔드포인트 설정

`src/utils/constants.ts` 파일에서 `API_BASE_URL`을 무료 호스팅 서비스의 URL로 변경해야 합니다.

## 백그라운드 작업 설정

### Android
- `android/app/src/main/AndroidManifest.xml`에 필요한 권한이 자동으로 추가됩니다.
- 배터리 최적화 예외 설정이 필요할 수 있습니다.

### iOS
- Background Modes 중 "Background fetch" 활성화 필요
- Info.plist에 `UIBackgroundModes` 추가 필요

## 주의사항

- 개인용 앱으로 설계되어 있으며, 마켓 배포용이 아닙니다.
- 디바이스 ID를 기반으로 사용자를 구분합니다.
- 보고서는 로컬 저장소에만 저장되며, 최대 100개까지 보관됩니다.