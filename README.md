# Property Management Lead Generation 프로젝트

Property Management 회사의 홈페이지를 자동으로 분석하여 리드 정보를 수집하는 프로젝트입니다.

## 🚀 실행 방법

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. API 키 설정
`.env` 파일을 프로젝트 루트에 생성하고 다음 API 키들을 설정하세요:

```bash
GOOGLE_GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

### 3. 프로젝트 실행
```bash
cd browser_use
python test.py
```

## 📋 주요 기능

- **Google Maps API**: Property Management 회사 검색
- **웹 크롤링**: 회사 홈페이지에서 기본 정보 수집  
- **Browser-use**: LLM이 브라우저를 직접 조작하여 누락된 정보 자동 수집
- **자동 분석**: Gemini AI를 활용한 회사 정보 분석
- **Google Sheets 연동**: 분석 결과 자동 업로드

## 🔍 수집하는 정보

- 회사 소유자/창립자 정보 (이름, 연락처)
- 사용하는 Property Management 소프트웨어
- 관리하는 부동산 개수 (doors)
- 팀 구성 정보 (리싱 매니저, 유지보수 매니저)
- 제공 서비스 및 포트폴리오 포커스
- 소셜 미디어 링크

## 📁 프로젝트 구조

```
lead-gen/
├── agent/           # 기본 분석 및 크롤링 모듈
├── browser_use/     # Browser-use 기반 고급 분석
└── requirements.txt # 필요한 패키지 목록
```