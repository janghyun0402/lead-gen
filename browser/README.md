# Property Management Website Analysis with Browser-Use

browser-use를 활용하여 Property Management 회사의 홈페이지에 직접 접속해서 관리하는 방의 개수와 형태를 자동으로 조사하는 도구입니다.

## 🚀 주요 기능

- **자동 웹사이트 탐색**: LLM이 브라우저를 직접 조작하여 홈페이지 탐색
- **부동산 정보 수집**: 관리하는 방의 개수, 유형, 서비스 지역 등 자동 추출
- **다단계 분석**: 기본 스캔과 고급 스캔 옵션 제공
- **기존 시스템 통합**: Google Maps 데이터와 쉽게 통합 가능
- **배치 처리**: 여러 웹사이트 동시 분석

## 📁 파일 구조

```
browser_use/
├── test.py                      # 기본 browser-use 테스트
├── pm_property_analyzer.py      # 기본 PM 분석 도구
├── advanced_property_scanner.py # 고급 PM 분석 도구
├── run_property_analysis.py     # 실행 스크립트
├── integration_helper.py        # 기존 agent와 통합용 헬퍼
└── README.md                    # 이 파일
```

## 🛠️ 설치 및 설정

### 1. 필요한 패키지 설치
```bash
pip install browser-use
pip install python-dotenv
```

### 2. 환경 변수 설정
`.env` 파일에 Google API 키 설정:
```
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 3. Browser-use 설정
browser-use는 자동으로 브라우저를 설치하고 설정합니다.

## 🎯 사용 방법

### 1. 기본 사용법

#### 단일 웹사이트 분석
```python
from pm_property_analyzer import analyze_pm_website

# 기본 분석
result = await analyze_pm_website("https://example-pm.com")
print(result)
```

#### 고급 분석 (더 정확하고 상세함)
```python
from advanced_property_scanner import deep_scan_pm_website

# 고급 분석
result = await deep_scan_pm_website("https://example-pm.com")
print(result)
```

### 2. 명령줄 실행

#### 기본 분석
```bash
python run_property_analysis.py https://example-pm.com
```

#### 고급 분석
```bash
python run_property_analysis.py --deep https://example-pm.com
```

#### 여러 웹사이트 분석
```bash
python run_property_analysis.py url1.com url2.com url3.com
```

#### URL 파일에서 읽어서 분석
```bash
python run_property_analysis.py --file urls.txt
```

### 3. 기존 agent와 통합

```python
from integration_helper import enhance_google_maps_data, quick_analyze_pm

# Google Maps 데이터에 부동산 분석 추가
enhanced_data = enhance_google_maps_data(google_maps_data, deep_scan=True)

# 단일 웹사이트 빠른 분석
property_info = quick_analyze_pm("https://example-pm.com")
```

## 📊 분석 결과 구조

### 기본 분석 결과
```json
{
  "url": "https://example-pm.com",
  "status": "success",
  "total_properties": "500",
  "property_types": ["아파트", "단독주택", "콘도미니엄"],
  "service_areas": ["Austin", "San Antonio", "Houston"],
  "company_size": "중규모 (200-500개)",
  "confidence_level": "high",
  "summary": "총 500개의 부동산을 관리 | 주요 유형: 아파트, 단독주택 | 서비스 지역: Austin, San Antonio"
}
```

### 고급 분석 결과
```json
{
  "url": "https://example-pm.com",
  "status": "success",
  "analysis_timestamp": "2025-09-11 15:30:45",
  "property_management_info": {
    "total_properties_managed": "500",
    "property_types": ["아파트", "단독주택", "콘도미니엄"],
    "service_areas": ["Austin", "San Antonio"],
    "company_size": "중규모 (200-500개)",
    "confidence_level": "high"
  },
  "detailed_findings": {
    "basic_info": { /* 홈페이지 기본 정보 */ },
    "portfolio_info": { /* 포트폴리오 페이지 정보 */ },
    "company_info": { /* 회사 정보 페이지 */ },
    "service_info": { /* 서비스 페이지 정보 */ }
  },
  "summary": "총 500개의 부동산을 관리 | 주요 유형: 아파트, 단독주택 | 서비스 지역: Austin, San Antonio"
}
```

## 🔍 분석하는 정보

### 1. 부동산 규모
- 총 관리 부동산/방의 개수
- 연도별 성장 추이
- 현재 관리 중인 부동산 수

### 2. 부동산 유형
- 아파트 (Apartments)
- 단독주택 (Single Family Homes)
- 콘도미니엄 (Condominiums)
- 타운하우스 (Townhouses)
- 상업용 부동산 (Commercial Properties)

### 3. 서비스 지역
- 주로 관리하는 도시/지역
- 서비스 지역 범위
- 지역별 부동산 분포

### 4. 회사 정보
- 회사 규모 (소규모/중규모/대규모)
- 직원 수
- 설립 연도
- 주요 서비스

## ⚡ 성능 및 제한사항

### 성능
- **기본 분석**: 30-60초/웹사이트
- **고급 분석**: 2-5분/웹사이트
- **배치 처리**: 동시에 여러 웹사이트 처리 가능

### 제한사항
- JavaScript로 동적 로딩되는 콘텐츠는 제한적
- 로그인이 필요한 페이지는 분석 불가
- 일부 웹사이트는 접근 제한 가능

## 🛡️ 에러 처리

### 일반적인 에러
- **Invalid URL**: 잘못된 URL 형식
- **Website not accessible**: 웹사이트 접근 불가
- **Analysis failed**: 분석 과정에서 오류 발생

### 에러 대응
```python
try:
    result = await analyze_pm_website(url)
    if result.get('status') == 'success':
        print("Analysis successful!")
    else:
        print(f"Analysis failed: {result.get('error')}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## 📈 사용 예시

### 1. Google Maps 데이터와 통합
```python
# Google Maps에서 PM 회사 데이터 수집
google_maps_data = get_google_maps_pm_companies()

# 부동산 분석 정보 추가
enhanced_data = enhance_google_maps_data(google_maps_data, deep_scan=True)

# Google Sheets에 업로드
from agent.upload_sheet import upload_analysis_results_to_sheets
upload_analysis_results_to_sheets(enhanced_data)
```

### 2. 배치 분석 및 통계
```python
urls = [
    "https://pm1.com",
    "https://pm2.com", 
    "https://pm3.com"
]

# 배치 분석
results = await batch_analyze_pm_websites(urls, deep_scan=True)

# 통계 생성
summary = create_property_summary(results)
print(f"Total properties managed: {summary['total_properties_managed']:,}")
```

## 🔧 커스터마이징

### 분석 태스크 수정
`pm_property_analyzer.py`의 `_create_analysis_task()` 함수를 수정하여 분석할 정보를 커스터마이징할 수 있습니다.

### 새로운 부동산 유형 추가
`advanced_property_scanner.py`의 `property_type_keywords` 딕셔너리에 새로운 유형을 추가할 수 있습니다.

## 📞 문제 해결

### 1. 브라우저 관련 문제
- browser-use가 자동으로 브라우저를 설치하지만, 수동 설치가 필요한 경우도 있습니다.
- Chrome/Chromium이 설치되어 있는지 확인하세요.

### 2. API 키 문제
- Google Gemini API 키가 올바르게 설정되었는지 확인하세요.
- API 할당량이 남아있는지 확인하세요.

### 3. 웹사이트 접근 문제
- 일부 웹사이트는 봇 차단이 있을 수 있습니다.
- User-Agent나 다른 헤더를 수정해야 할 수도 있습니다.

---

이 도구를 사용하여 Property Management 회사들의 부동산 포트폴리오를 자동으로 분석하고, 리드 생성에 활용하세요! 🏠📊
