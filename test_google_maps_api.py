#!/usr/bin/env python3
"""
Google Maps API 도구 테스트 스크립트
"""

import os
from dotenv import load_dotenv
from agent.tools import search_pm_firms_for_cities, get_top_cities_by_population

# 환경변수 로드
load_dotenv()

def test_google_maps_api():
    """Google Maps API 함수들을 테스트합니다."""
    
    print("=== Google Maps API 테스트 시작 ===\n")
    
    # API 키 확인
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("❌ GOOGLE_MAPS_API_KEY 환경변수가 설정되지 않았습니다.")
        print("   .env 파일에 GOOGLE_MAPS_API_KEY를 설정해주세요.")
        return
    
    print(f"✅ Google Maps API 키 확인됨: {api_key[:10]}...")
    
    try:
        # 테스트: 통합 함수로 여러 도시에서 PM 회사 검색
        print(f"\n1. 상위 3개 도시에서 부동산 관리 회사 검색 (새로운 Places API):")
        top_cities = get_top_cities_by_population(limit=3, min_population=500000)
        
        all_firms = search_pm_firms_for_cities(top_cities, max_results_per_city=3)
        
        # 도시별로 그룹화하여 표시
        cities_dict = {}
        for firm in all_firms:
            city = firm['city']
            if city not in cities_dict:
                cities_dict[city] = []
            cities_dict[city].append(firm)
        
        for city_name, city_firms in cities_dict.items():
            print(f"\n   📍 {city_name} ({city_firms[0]['city_population']:,}명):")
            for firm in city_firms:
                print(f"      - {firm['name']} (평점: {firm['rating']}/5, 리뷰: {firm['user_ratings_total']}개)")
                print(f"        주소: {firm['address']}")
                print(f"        전화: {firm['phone_number']}")
                print(f"        웹사이트: {firm['website']}")
                print(f"        Google Maps: {firm['google_maps_url']}")
        
        print(f"\n✅ 테스트 완료! 총 {len(all_firms)}개의 회사를 찾았습니다.")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    test_google_maps_api()
