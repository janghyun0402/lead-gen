import requests
import os
import time
from typing import List, Dict, Optional
import logging
from dotenv import load_dotenv
from pprint import pprint
import httpx
import asyncio

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def get_cities_by_population(min_population: int = 50000, state_code: Optional[str] = None) -> List[Dict[str, any]]:
    """
    Retrieve a list of cities with population above the specified threshold using Census Bureau API.
    
    Args:
        min_population (int): Minimum population threshold (default: 50,000)
        state_code (str, optional): Specific state code (e.g., "CA", "NY"). If None, searches all states
    
    Returns:
        List[Dict]: List of city information dictionaries containing:
            - name: City name
            - population: Population count
            - state: State name
            - state_code: State code
            - place_fips: Place FIPS code
    """
    try:
        # Census API 키 확인
        api_key = os.getenv('CENSUS_API_KEY')
        if not api_key:
            logger.error("CENSUS_API_KEY environment variable is not set.")
            return []
        
        # API 엔드포인트 설정
        base_url = "https://api.census.gov/data/2020/acs/acs5"
        
        # 요청 파라미터 설정
        params = {
            "get": "NAME,B01003_001E",  # 도시명과 총 인구수
            "for": "place:*",  # 모든 place (도시)
            "key": api_key
        }
        
        # 특정 주가 지정된 경우
        if state_code:
            params["in"] = f"state:{state_code}"
        else:
            params["in"] = "state:*"  # 모든 주
        
        logger.info(f"인구수 {min_population:,}명 이상의 도시를 검색 중...")
        
        # API 요청
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # 헤더 제거 (첫 번째 행)
        data_rows = data[1:]
        
        cities = []
        for row in data_rows:
            try:
                city_name = row[0]
                population = int(row[1]) if row[1] else 0
                place_fips = row[2]  # Place FIPS 코드
                state_fips = row[3]  # State FIPS 코드
                
                # 인구수 조건 확인
                if population >= min_population:
                    # State FIPS 코드를 주 코드로 변환 (간단한 매핑)
                    state_code_map = {
                        "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA",
                        "08": "CO", "09": "CT", "10": "DE", "11": "DC", "12": "FL",
                        "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN",
                        "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME",
                        "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS",
                        "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
                        "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND",
                        "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
                        "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT",
                        "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI", "56": "WY"
                    }
                    
                    state_code_str = state_code_map.get(state_fips, state_fips)
                    
                    cities.append({
                        "name": city_name,
                        "population": population,
                        "state": state_code_str,
                        "state_code": state_code_str,
                        "place_fips": place_fips
                    })
                    
            except (ValueError, IndexError) as e:
                logger.warning(f"데이터 파싱 오류: {row}, 오류: {e}")
                continue
        
        # 인구수 기준으로 내림차순 정렬
        cities.sort(key=lambda x: x["population"], reverse=True)
        
        logger.info(f"총 {len(cities)}개의 도시를 찾았습니다.")
        return cities
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API 요청 오류: {e}")
        return []
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        return []





async def google_maps_search_pm_for_cities(cities: List[str], max_results_per_city: int = 10) -> List[Dict[str, any]]:
    """
    Search for property management firms across multiple cities and return a unified list.
    This function combines city discovery and PM firm search into one operation.
    
    Args:
        cities (List[Dict]): List of city dictionaries from get_cities_by_population()
        max_results_per_city (int): Maximum results per city (default: 10)
    
    Returns:
        List[Dict]: Unified list of all property management firms with city information
    """
    all_firms = []
    
    for city in cities:
        
        logger.info(f"Processing city: {city}")
        
        try:
            async with httpx.AsyncClient() as client:
                # Google Maps API 키 확인
                api_key = os.getenv('GOOGLE_MAPS_API_KEY')
                if not api_key:
                    logger.error("GOOGLE_MAPS_API_KEY environment variable is not set.")
                    continue
                
                # New Places API Text Search를 사용하여 부동산 관리 회사 검색
                text_search_url = "https://places.googleapis.com/v1/places:searchText"
                query = f"Top residential property management firms in {city}"
                
                headers = {
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": api_key,
                    "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.types,places.rating,places.userRatingCount,places.businessStatus"
                }
                
                payload = {
                    "textQuery": query,
                    "maxResultCount": max_results_per_city,
                    "languageCode": "en",
                    "regionCode": "US"
                }
                
                # Text Search 요청
                text_response = await client.post(text_search_url, headers=headers, json=payload, timeout=30)
                text_response.raise_for_status()
            
            text_data = text_response.json()
            
            if "places" not in text_data:
                logger.warning(f"Text search failed for {city}: No places found")
                continue
            
            results = text_data.get("places", [])
            city_firms = []
            
            # 각 결과에 대해 Place Details API 호출
            for i, result in enumerate(results[:max_results_per_city]):
                place_id = result.get("id")
                if not place_id:
                    continue
                
                try:
                    # New Places API Details를 사용하여 상세 정보 가져오기
                    details_url = f"https://places.googleapis.com/v1/places/{place_id}"
                    
                    details_headers = {
                        "Content-Type": "application/json",
                        "X-Goog-Api-Key": api_key,
                        "X-Goog-FieldMask": "id,displayName,formattedAddress,internationalPhoneNumber,websiteUri,rating,userRatingCount,businessStatus,types,priceLevel,reviews,location,googleMapsUri"
                    }
                    
                    details_response = requests.get(details_url, headers=details_headers, timeout=30)
                    details_response.raise_for_status()
                    
                    details = details_response.json()
                    
                    # 리뷰 정보 추출
                    reviews = details.get("reviews", [])
                    review_summary = []
                    for review in reviews:  # maximum 5 reviews
                        review_summary.append({
                            "rating": review.get("rating"),
                            "text": review.get("text", {}).get("text", ""),
                            "author_name": review.get("authorAttribution", {}).get("displayName", ""),
                            "relative_time_description": review.get("publishTime", "")
                        })
                    

                    
                    firm_info = {
                        "name": details.get("displayName", {}).get("text", ""),
                        "address": details.get("formattedAddress", ""),
                        "phone_number": details.get("internationalPhoneNumber", ""),
                        "website": details.get("websiteUri", ""),
                        "rating": details.get("rating", 0),
                        "user_ratings_total": details.get("userRatingCount", 0),
                        "place_id": place_id,
                        "business_status": details.get("businessStatus", ""),
                        "types": details.get("types", []),
                        "price_level": details.get("priceLevel"),
                        "reviews": review_summary,
                        "geometry": details.get("location", {}),
                        "google_maps_url": details.get("googleMapsUri", ""),
                        "city": city,
                    }
                    
                    city_firms.append(firm_info)
                    all_firms.append(firm_info)
                    logger.info(f"Found firm: {firm_info['name']} (Rating: {firm_info['rating']})")
 
                        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Request failed for place_id {place_id}: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Unexpected error for place_id {place_id}: {e}")
                    continue
            
            logger.info(f"Found {len(city_firms)} firms in {city}")
            
            # 도시 간 API 호출 제한을 위한 지연
            time.sleep(2)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Google Maps API request error for {city}: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error for {city}: {e}")
            continue
    
    logger.info(f"Total firms found across all cities: {len(all_firms)}")
    return all_firms




async def google_maps_search_by_organization_name(organization_name: str, city: Optional[str] = None) -> Optional[Dict[str, any]]:
    """
    Search for a specific organization by name using Google Maps Places API.
    
    Args:
        organization_name (str): Name of the organization to search for
        city (Optional[str]): City name to include in search for more precise results
    
    Returns:
        Optional[Dict]: Organization information if found, None if not found
    """
    try:
        async with httpx.AsyncClient() as client:
            # Google Maps API 키 확인
            api_key = os.getenv('GOOGLE_MAPS_API_KEY')
            if not api_key:
                logger.error("GOOGLE_MAPS_API_KEY environment variable is not set.")
                return None
            
            # New Places API Text Search를 사용하여 조직 검색
            text_search_url = "https://places.googleapis.com/v1/places:searchText"
            if city:
                query = f"{organization_name} in {city}"
            else:
                query = f"{organization_name}"
            
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.types,places.rating,places.userRatingCount,places.businessStatus"
            }
            
            payload = {
                "textQuery": query,
                "maxResultCount": 5,  # 최대 5개 결과만 검색
                "languageCode": "en",
                "regionCode": "US"
            }
            
            logger.info(f"Searching for organization: {organization_name}")
            
            # Text Search 요청
            text_response = requests.post(text_search_url, headers=headers, json=payload, timeout=30)
            text_response.raise_for_status()
        
        text_data = text_response.json()
        
        if "places" not in text_data or not text_data["places"]:
            logger.warning(f"No places found for organization: {organization_name}")
            return None
        
        # 첫 번째 결과를 가장 관련성 높은 것으로 간주
        result = text_data["places"][0]
        place_id = result.get("id")
        
        if not place_id:
            logger.warning(f"No place_id found for organization: {organization_name}")
            return None
        
        # Place Details API 호출하여 상세 정보 가져오기
        details_url = f"https://places.googleapis.com/v1/places/{place_id}"
        
        details_headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "id,displayName,formattedAddress,internationalPhoneNumber,websiteUri,rating,userRatingCount,businessStatus,types,priceLevel,reviews,location,googleMapsUri"
        }
        
        details_response = requests.get(details_url, headers=details_headers, timeout=30)
        details_response.raise_for_status()
        
        details = details_response.json()
        
        # 리뷰 정보 추출
        reviews = details.get("reviews", [])
        review_summary = []
        for review in reviews:  # maximum 5 reviews
            review_summary.append({
                "rating": review.get("rating"),
                "text": review.get("text", {}).get("text", ""),
                "author_name": review.get("authorAttribution", {}).get("displayName", ""),
                "relative_time_description": review.get("publishTime", "")
            })
        
        firm_info = {
            "name": details.get("displayName", {}).get("text", ""),
            "address": details.get("formattedAddress", ""),
            "phone_number": details.get("internationalPhoneNumber", ""),
            "website": details.get("websiteUri", ""),
            "rating": details.get("rating", 0),
            "user_ratings_total": details.get("userRatingCount", 0),
            "place_id": place_id,
            "business_status": details.get("businessStatus", ""),
            "types": details.get("types", []),
            "price_level": details.get("priceLevel"),
            "reviews": review_summary,
            "geometry": details.get("location", {}),
            "google_maps_url": details.get("googleMapsUri", ""),
            "city": city if city else "Unknown",  # CSV에서 제공된 도시 정보 또는 Unknown
        }
        
        logger.info(f"Found organization: {firm_info['name']} at {firm_info['address']}")
        return firm_info
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Google Maps API request error for {organization_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error for {organization_name}: {e}")
        return None


if __name__ == "__main__":
    pprint(google_maps_search_pm_for_cities(["San Antonio"]))