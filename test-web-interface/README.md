# Reddit 분석 테스트 인터페이스

React + TypeScript로 구축된 웹 인터페이스를 통해 GPT-4.1 분석을 테스트할 수 있습니다.

## 🚀 실행 방법

### 🎯 원클릭 실행 (권장)

#### Linux/Mac:
```bash
cd test-web-interface
./start.sh
```

#### Windows (Command Prompt):
```cmd
cd test-web-interface
start.bat
```

#### Windows (PowerShell):
```powershell
cd test-web-interface
.\start.ps1
```

#### 빠른 시작 (의존성이 이미 설치된 경우):
```cmd
cd test-web-interface
quick-start.cmd    # Windows
npm start          # 모든 OS
```

자동으로 다음 작업이 수행됩니다:
- ✅ 환경 검증 (.env 파일, Node.js)
- 📦 프론트엔드 + 백엔드 의존성 설치
- 🚀 백엔드 서버 시작 (`http://localhost:3001`)
- 🌐 프론트엔드 서버 시작 (`http://localhost:3000`)

### 🔧 수동 실행

#### 방법 1: 동시 실행
```bash
cd test-web-interface
npm run install:all    # 모든 의존성 설치
npm run start:dev       # 백엔드 + 프론트엔드 동시 실행
```

#### 방법 2: 개별 실행 (디버깅용)
```bash
# 백엔드만 실행
npm run start:backend

# 프론트엔드만 실행 (새 터미널)
npm run start:frontend
```

## 🎯 기능

### 📝 사용자 입력
- **텍스트 에어리어**: 분석할 내용 입력 (최대 5000자)
- **라디오 버튼**: 보고서 길이 선택
  - **간단히**: 1,200자 목표
  - **적당히**: 1,800자 목표 (간단히의 1.5배)
  - **상세하게**: 2,400자 목표 (간단히의 2배)

### 🔄 분석 프로세스
1. **검증 시스템**: 생성된 보고서 자동 검증
2. **재시도 로직**: 실패 시 다른 전략으로 재시도 (최대 3번)
3. **실시간 상태**: 로딩 단계별 진행 상황 표시

### 📊 결과 표시
- **메타데이터**: 글자수, 처리 시간, 생성 시간
- **결과 내용**: 포맷팅된 분석 보고서
- **액션 버튼**: 복사, 다운로드 기능

## 🔧 API 설정

`.env` 파일에 OpenAI API 키가 설정되어 있어야 합니다:

```env
OPENAI_API_KEY=sk-...
```

## 📱 반응형 디자인

- 데스크톱과 모바일 모두 지원
- 깔끔한 그라디언트 디자인
- 직관적인 사용자 인터페이스

## 🛠️ 기술 스택

### 프론트엔드
- React 18
- TypeScript
- CSS3 (Grid, Flexbox)
- Fetch API

### 백엔드
- Node.js
- Express
- OpenAI API
- CORS

## 🔍 테스트 예시

### 입력 예시
```
트럼프와 머스크의 최근 갈등에 대해 분석해주세요. 
정치적 배경과 비즈니스 영향을 포함해서 설명해주세요.
```

### 출력 예시
각 길이 설정에 따라 다른 상세도의 보고서가 생성됩니다:

- **간단히**: 핵심 포인트 위주, 1200자 내외
- **적당히**: 주요 분석 포함, 1800자 내외  
- **상세하게**: 심층 분석, 2400자 내외

## 🚨 문제 해결

### 백엔드 연결 오류
- 백엔드 서버가 실행 중인지 확인
- `http://localhost:3001/api/status`에서 상태 확인

### API 키 오류
- `.env` 파일의 `OPENAI_API_KEY` 확인
- API 키 권한 및 크레딧 확인

### 분석 실패
- 입력 내용의 길이와 품질 확인
- 네트워크 연결 상태 확인

## 📈 향후 확장 가능성

- Reddit API 연동
- 다양한 분석 모델 지원
- 결과 히스토리 저장
- 템플릿 기반 분석
- 실시간 협업 기능