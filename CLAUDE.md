# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Property Management 회사 리드 자동 생성 파이프라인. Google Maps API로 PM 회사를 탐색하고, 웹사이트를 크롤링한 뒤, Gemini AI로 구조화된 정보를 추출하며, 선택적으로 browser-use(LLM 기반 브라우저 자동화)로 누락 데이터를 보완한다.

## Commands

```bash
# 의존성 설치
pip install -r requirements.txt

# CLI 실행 (단일 도시)
python run.py city "Kansas City"

# CLI 실행 (CSV 파일)
python run.py csv companies.csv

# CLI 실행 (복수 도시)
python run.py city "New York, Los Angeles, Chicago"

# FastAPI 백엔드 실행 (MongoDB 필요)
uvicorn app:app --host 0.0.0.0 --port 8000

# Gradio UI 실행
python app.py

# 테스트
python test_google_maps_api.py
python test_census_api.py
python test_crawling.py
python test_complete_pipeline.py
```

## Architecture

### Data Pipeline (순서대로)

1. **Lead Discovery** (`agent/tools.py`) — Google Maps Places API + Census Bureau API로 도시별 PM 회사 검색
2. **Web Crawling** (`agent/crawling.py`) — BFS 기반 크롤러. `max_pages=50`, `max_depth=3`. 도메인 경계 준수
3. **AI Analysis** (`agent/agent.py`) — Gemini 2.5 Pro로 크롤링 데이터에서 구조화된 JSON 추출 (소유자, 서비스, 소프트웨어, 팀 정보 등)
4. **Browser Enhancement** (`browser/test.py`) — 선택적. browser-use로 JS 렌더링 페이지에서 누락 데이터 수집. 사이트당 2-5분 소요
5. **Export** — CSV 생성 후 `outputs/` 디렉토리에 저장. 웹 모드에서는 MongoDB GridFS에 업로드

### Entry Points

- **`run.py`** — CLI 오케스트레이터. `city_mode()`, `csv_mode()`, `multi_city_mode()` 제공. `COLUMN_MAPPING` dict로 중첩 JSON → CSV 컬럼 매핑 정의
- **`app.py`** — Gradio UI. FastAPI 백엔드(`/city`, `/csv`, `/status`, `/download`)에 요청을 보내 분석 실행 및 결과 다운로드
- **`app/db.py`** — MongoDB(Motor) 비동기 드라이버. GridFS 파일 저장, 작업 추적(`running_jobs`, `jobs` 컬렉션)

### Agent Modules (`agent/`)

- **`agent.py`** — `analyze_website()`, `generate_final_report()`, `generate_email()`. Gemini API로 크롤링 결과 분석
- **`tools.py`** — `google_maps_search_pm_for_cities()`, `get_cities_by_population()`. 외부 API 호출
- **`crawling.py`** — `crawl_website()`. BeautifulSoup 기반, script/style/nav/footer 태그 제거
- **`csv_processor.py`** — `process_csv_file()`. 필수 컬럼: "Organization Name", 선택: "City"

### Key Design Decisions

- 웹 백엔드는 사용자당 동시 작업 1개로 제한 (`running_jobs` 컬렉션)
- `asyncio.to_thread()`로 CPU 집약적 크롤링을 비동기 처리
- 개별 회사 분석 실패 시 파이프라인 전체를 중단하지 않고 `analysis=None`으로 계속 진행
- browser-use 실패 시 Gemini 전용 분석으로 fallback

## Environment Variables (`.env`)

```
GOOGLE_GEMINI_API_KEY=    # Gemini 2.5 Pro
GOOGLE_MAPS_API_KEY=      # Google Places API
CENSUS_API_KEY=           # US Census Bureau API
MONGO_URI=                # MongoDB 연결 (웹 모드에서만 필요)
MONGO_DB_NAME=            # MongoDB DB 이름
```
