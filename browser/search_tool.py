from browser_use import Tools
import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

tools = Tools()

@tools.action(description="Search Google to get result URLs")
def get_urls_from_google_search(query: str) -> str:
    """Search Google to get result URLs"""
    
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    engine_id = os.getenv('GOOGLE_CSE_ID')
    
    if not api_key or not engine_id:
        return "오류: GOOGLE_API_KEY 또는 GOOGLE_CSE_ID가 설정되지 않았습니다."
    
    try:
        # Google Custom Search 서비스 객체를 생성합니다.
        service = build("customsearch", "v1", developerKey=api_key)
        
        # API를 호출하여 검색 결과를 가져옵니다. num=10으로 상위 10개를 요청합니다.
        result = service.cse().list(
            q=query,
            cx=engine_id,
            num=7
        ).execute()

        # 결과에서 'items' 키가 있는지 확인하고, 각 항목의 'link'를 추출합니다.
        search_items = result.get("items", [])
        if not search_items:
            return f"'{query}'에 대한 검색 결과가 없습니다."
            
        urls = [item['link'] for item in search_items]
        formatted_string = "\n".join(f"{i}. {url}" for i, url in enumerate(urls, 1))
        return formatted_string

    except HttpError as e:
        # API 관련 에러 처리 (잘못된 API 키, CSE ID 등)
        return f"API 오류가 발생했습니다: {e.reason}"
    except Exception as e:
        # 기타 예외 처리
        return f"알 수 없는 오류가 발생했습니다: {e}"
 
 
import asyncio
if __name__ == "__main__":
# 비동기 함수를 실행하기 위한 진입점을 만듭니다.
    async def main():
        query = "property management companies in Kansas City"
        # 데코레이터에 의해 변환된 함수이므로 await로 호출해야 합니다.
        results = await get_urls_from_google_search(query=query)
        print(results)

    # asyncio.run()으로 main 비동기 함수를 실행합니다.
    asyncio.run(main())