#!/usr/bin/env python3
"""
Website crawling 테스트 스크립트
"""

import os
from dotenv import load_dotenv
from agent.tools import get_complete_pm_leads, get_top_cities_by_population
from agent.crawling import crawl_website

# 환경변수 로드
load_dotenv()

def test_crawling():
    """Website crawling 함수들을 테스트합니다."""
    
    print("=== Website Crawling 테스트 시작 ===\n")
    
    try:
        # 테스트 1: 단일 웹사이트 크롤링
        print("1. 단일 웹사이트 크롤링 테스트:")
        test_url = "https://example.com"
        result = crawl_website(test_url, max_pages=5, max_depth=2)
        
        print(f"   크롤링된 페이지 수: {result['total_pages']}")
        print(f"   총 단어 수: {result['total_word_count']}")
        print(f"   내부 링크 수: {len(result['internal_links'])}")
        print(f"   외부 링크 수: {len(result['external_links'])}")
        print(f"   샘플 텍스트: {result['all_text'][:200]}...")
        
        # 테스트 2: PM 회사 통합 파이프라인 테스트
        print(f"\n2. PM 회사 통합 파이프라인 테스트:")
        print("   (주의: 이 테스트는 실제 API 호출을 수행합니다)")
        
        # 작은 규모로 테스트
        cities = get_top_cities_by_population(limit=2, min_population=1000000)
        print(f"   테스트 도시: {[city['name'] for city in cities]}")
        
        # 통합 파이프라인 실행
        leads = get_complete_pm_leads(
            cities=cities,
            max_firms_per_city=2,  # 도시당 최대 2개 회사
            max_pages_per_site=5   # 사이트당 최대 5페이지
        )
        
        print(f"\n   생성된 리드 수: {len(leads)}")
        
        # 결과 요약
        for i, lead in enumerate(leads[:3], 1):  # 처음 3개만 표시
            print(f"\n   리드 {i}: {lead['name']}")
            print(f"      도시: {lead['city']}, {lead['state']}")
            print(f"      평점: {lead['rating']}/5")
            print(f"      웹사이트: {lead['website']}")
            print(f"      웹사이트 크롤링: {'완료' if lead.get('website_crawled') else '실패'}")
            
            if lead.get('website_crawled'):
                crawled_data = lead.get('crawled_data', {})
                print(f"      크롤링된 페이지: {crawled_data.get('total_pages', 0)}개")
                print(f"      웹사이트 단어 수: {crawled_data.get('total_word_count', 0)}개")
                print(f"      샘플 텍스트: {crawled_data.get('all_text', '')[:100]}...")
        
        print(f"\n✅ 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_crawling()
