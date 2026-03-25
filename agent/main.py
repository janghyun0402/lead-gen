



import pprint
from agent import analyze_website
from crawling import crawl_website
from tools import google_maps_search_pm_for_cities


if __name__ == "__main__":
    city = "Kansas City"
    all_google_data = google_maps_search_pm_for_cities([city], max_results_per_city=10)
    
    # 일단 테스트용으로 1개만 처리
    for i in range(0, 1):
        crawled_data = crawl_website(
            url=all_google_data[i]['website'],
            max_pages=50,
            max_depth=3,
        )
        analysis = analyze_website(google_data=all_google_data[i], crawled_data=crawled_data, company_name=all_google_data[i]['name'], location=city)
        pprint.pprint(analysis)
    