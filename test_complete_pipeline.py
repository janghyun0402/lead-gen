#!/usr/bin/env python3
"""
Complete lead generation pipeline 테스트 스크립트
"""

import os
from dotenv import load_dotenv
from agent.tools import generate_leads_from_natural_language
from agent import extract_conditions_from_natural_language, analyze_crawled_websites

# 환경변수 로드
load_dotenv()

def test_complete_pipeline():
    """Complete lead generation pipeline을 테스트합니다."""
    
    print("=== Complete Lead Generation Pipeline 테스트 ===\n")
    
    # API 키 확인
    gemini_key = os.getenv('GOOGLE_GEMINI_API_KEY')
    census_key = os.getenv('CENSUS_API_KEY')
    maps_key = os.getenv('GOOGLE_MAPS_API_KEY')
    
    if not gemini_key:
        print("❌ GOOGLE_GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
        return
    if not census_key:
        print("❌ CENSUS_API_KEY 환경변수가 설정되지 않았습니다.")
        return
    if not maps_key:
        print("❌ GOOGLE_MAPS_API_KEY 환경변수가 설정되지 않았습니다.")
        return
    
    print("✅ 모든 API 키 확인됨")
    
    try:
        # 테스트 1: 자연어 조건 추출 테스트
        print("\n1. 자연어 조건 추출 테스트:")
        test_inputs = [
            "인구 10만명 이상의 캘리포니아 도시에서 PM 회사 찾아줘",
            "텍사스에서 인구 5만명 이상 도시의 부동산 관리 회사 5개씩 찾아줘",
            "뉴욕에서 상위 3개 도시의 PM 회사들 웹사이트 분석해줘"
        ]
        
        for i, test_input in enumerate(test_inputs, 1):
            print(f"\n   테스트 {i}: {test_input}")
            conditions = extract_conditions_from_natural_language(test_input)
            print(f"   추출된 조건: {conditions}")
        
        # 테스트 2: 완전한 파이프라인 테스트 (작은 규모)
        print(f"\n2. 완전한 파이프라인 테스트:")
        print("   (주의: 이 테스트는 실제 API 호출을 수행합니다)")
        
        # 작은 규모로 테스트
        user_input = "캘리포니아에서 인구 50만명 이상 도시 2개, PM 회사 2개씩 찾아줘"
        print(f"   사용자 입력: {user_input}")
        
        leads = generate_leads_from_natural_language(user_input)
        
        print(f"\n   생성된 리드 수: {len(leads)}")
        
        # 결과 요약
        for i, lead in enumerate(leads[:3], 1):  # 처음 3개만 표시
            print(f"\n   리드 {i}: {lead['name']}")
            print(f"      도시: {lead['city']}, {lead['state']}")
            print(f"      평점: {lead['rating']}/5")
            print(f"      웹사이트: {lead['website']}")
            print(f"      웹사이트 크롤링: {'완료' if lead.get('website_crawled') else '실패'}")
            
            # LLM 분석 결과 표시
            if lead.get('llm_analysis'):
                analysis = lead['llm_analysis']
                print(f"      LLM 분석:")
                print(f"        서비스: {analysis.get('services', [])[:3]}")  # 최대 3개
                print(f"        회사 규모: {analysis.get('company_size', 'unknown')}")
                print(f"        요약: {analysis.get('summary', 'N/A')}")
                
                contact_info = analysis.get('contact_info', {})
                if contact_info.get('emails'):
                    print(f"        이메일: {contact_info['emails'][:2]}")  # 최대 2개
                if contact_info.get('phones'):
                    print(f"        전화번호: {contact_info['phones'][:2]}")  # 최대 2개
        
        print(f"\n✅ 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_pipeline()
