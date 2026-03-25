# 🚀 Complete Lead Generation Pipeline

이 `run.py` 파일은 전체 Lead Generation 파이프라인을 실행하는 통합 스크립트입니다.

## 🔄 전체 프로세스 파이프라인

1. **Google Maps 검색** → PM 회사 정보 수집
2. **웹사이트 크롤링** → 회사 웹사이트 데이터 수집  
3. **AI 분석** → Gemini를 사용한 구조화된 데이터 추출
4. **Browser-Use 강화** → 누락된 정보 추가 수집 (선택사항)
5. **결과 저장** → JSON 형태로 최종 결과 저장

## 🚀 사용법

### City 모드 (도시 기반 검색)
```bash
python run.py city <city_name> [max_results] [max_pages] [max_depth] [--no-browser]
```

**예시:**
```bash
# 기본 설정으로 Kansas City 검색
python run.py city "Kansas City"

# 상세 설정으로 검색 (최대 5개 회사, 30페이지 크롤링, 깊이 2, 브라우저 강화 사용)
python run.py city "San Antonio" 5 30 2

# 브라우저 강화 없이 검색
python run.py city "Dallas" 10 50 3 --no-browser
```

### CSV 모드 (CSV 파일 기반 검색)
```bash
python run.py csv <csv_file_path> [max_pages] [max_depth] [--no-browser]
```

**예시:**
```bash
# 기본 설정으로 CSV 파일 처리
python run.py csv companies.csv

# 상세 설정으로 처리 (50페이지 크롤링, 깊이 3, 브라우저 강화 사용)
python run.py csv companies.csv 50 3

# 브라우저 강화 없이 처리
python run.py csv companies.csv 30 2 --no-browser
```

## 📊 CSV 파일 형식

CSV 파일은 다음 컬럼을 포함해야 합니다:

| 컬럼명 | 필수여부 | 설명 |
|--------|----------|------|
| `Organization Name` | **필수** | 검색할 회사명 |
| `City` | 선택사항 | 검색 정확도 향상을 위한 도시명 |
| 기타 컬럼 | 선택사항 | 추가 메타데이터 |

**예시 CSV:**
```csv
Organization Name,City,Additional Info
"ABC Property Management","San Antonio","Sample company 1"
"XYZ Residential Services","Dallas","Sample company 2"
"CloverLeaf Property Management","San Antonio","Sample company 3"
```

## 🎯 주요 기능

### ✅ **완전한 파이프라인**
- Google Maps 검색 → 크롤링 → AI 분석 → Browser 강화까지 한 번에 실행

### ✅ **유연한 설정**
- 처리할 회사 수, 크롤링 페이지 수, 깊이 등 모든 설정 조정 가능
- Browser-use 강화 기능 on/off 선택 가능

### ✅ **에러 핸들링**
- 개별 회사 처리 실패 시에도 다른 회사들은 계속 처리
- 상세한 에러 로그 및 요약 제공

### ✅ **결과 저장**
- JSON 형태로 구조화된 결과 자동 저장
- 파일명: `city_analysis_{city_name}.json` 또는 `csv_analysis_{filename}.json`

### ✅ **진행상황 추적**
- 각 단계별 진행상황 실시간 표시
- 처리 완료 후 상세한 요약 제공

## 🔧 매개변수 설명

| 매개변수 | 기본값 | 설명 |
|----------|--------|------|
| `max_results` | 10 | 도시당 처리할 최대 회사 수 (City 모드만) |
| `max_pages` | 50 | 회사당 크롤링할 최대 페이지 수 |
| `max_depth` | 3 | 크롤링 최대 깊이 |
| `--no-browser` | False | Browser-use 강화 기능 비활성화 |

## 📋 출력 결과

### 콘솔 출력
- 실시간 진행상황 표시
- 각 단계별 성공/실패 로그  
- 최종 요약 (성공/실패 개수, 샘플 결과 등)

### JSON 파일
구조화된 분석 결과가 JSON 형태로 저장되며, 다음 정보를 포함합니다:

```json
{
  "firm_name": "회사명",
  "website_url": "웹사이트 URL",
  "firm_level_data": {
    "owner": {"name": "소유자명", "phone": "전화번호", "email": "이메일"},
    "city": "도시",
    "state": "주",
    "software_used": {"name": "사용 소프트웨어"}
  },
  "team_info": {
    "has_leasing_manager": true,
    "leasing_manager_name": "임대 매니저명"
  },
  "services_and_focus": {
    "services_offered": ["SFR", "Multifamily"],
    "portfolio_focus": ["Luxury"]
  },
  "social_media_info": {
    "linkedin_url": "LinkedIn URL",
    "instagram_url": "Instagram URL"
  },
  "google_review": {
    "rating": 4.5,
    "review_count": 150
  }
}
```

## ⚠️ 주의사항

1. **API 키 설정**: `.env` 파일에 필요한 API 키들이 설정되어 있어야 합니다
   - `GOOGLE_MAPS_API_KEY`
   - `GOOGLE_GEMINI_API_KEY`

2. **Browser-use 의존성**: Browser-use 기능을 사용하려면 관련 모듈이 설치되어 있어야 합니다

3. **처리 시간**: 브라우저 강화 기능을 사용하면 처리 시간이 상당히 늘어날 수 있습니다

4. **Rate Limiting**: Google Maps API 호출 제한을 고려하여 대량 처리 시 주의하세요
