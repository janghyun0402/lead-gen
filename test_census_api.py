#!/usr/bin/env python3
"""
Census API 도구 테스트 스크립트
"""

import os
from dotenv import load_dotenv
from agent.tools import get_cities_by_population, get_top_cities_by_population, search_cities_by_name

# 환경변수 로드
load_dotenv()

def test_census_api():
    """Census API 함수들을 테스트합니다."""
    
    print("=== Census API 테스트 시작 ===\n")
    
    # API 키 확인
    api_key = os.getenv('CENSUS_API_KEY')
    if not api_key:
        print("❌ CENSUS_API_KEY 환경변수가 설정되지 않았습니다.")
        print("   .env 파일에 CENSUS_API_KEY를 설정해주세요.")
        return
    
    print(f"✅ API 키 확인됨: {api_key[:10]}...")
    
    try:
        # 테스트 1: 인구수 10만명 이상의 도시 조회 (최대 10개)
        print("\n1. 인구수 10만명 이상의 도시 조회 (상위 10개):")
        cities = get_cities_by_population(min_population=100000)
        for i, city in enumerate(cities[:10], 1):
            print(f"   {i:2d}. {city['name']}, {city['state']} - {city['population']:,}명")
        
        # 테스트 2: 상위 5개 도시 조회
        print("\n2. 상위 5개 도시 조회:")
        top_cities = get_top_cities_by_population(limit=5, min_population=100000)
        for i, city in enumerate(top_cities, 1):
            print(f"   {i}. {city['name']}, {city['state']} - {city['population']:,}명")
        
        # 테스트 3: 특정 도시 검색
        print("\n3. 'New York' 검색:")
        ny_cities = search_cities_by_name("New York", min_population=50000)
        for city in ny_cities[:5]:  # 최대 5개만 표시
            print(f"   - {city['name']}, {city['state']} - {city['population']:,}명")
        
        # 테스트 4: 캘리포니아 주 도시들
        print("\n4. 캘리포니아 주 인구수 5만명 이상 도시 (상위 5개):")
        ca_cities = get_cities_by_population(min_population=50000, state_code="CA")
        for i, city in enumerate(ca_cities[:5], 1):
            print(f"   {i}. {city['name']}, {city['state']} - {city['population']:,}명")
        
        print(f"\n✅ 테스트 완료! 총 {len(cities)}개의 도시를 찾았습니다.")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    test_census_api()
