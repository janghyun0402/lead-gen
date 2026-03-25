import requests
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Set, Optional
import re
from collections import deque
import random

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




def extract_text_from_soup(soup: BeautifulSoup) -> str:
    """
    BeautifulSoup 객체에서 깨끗한 텍스트 콘텐츠를 추출합니다.
    (이 함수는 soup 객체를 직접 수정하므로 링크 추출 후에 호출해야 합니다.)
    """
    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.decompose()
    
    text = soup.get_text()
    
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    return text


def extract_links(soup: BeautifulSoup, current_url: str, base_domain: str) -> Dict[str, List[str]]:
    """
    페이지에서 내부 및 외부 링크를 추출합니다.
    www 유무, http/https 차이를 극복하도록 수정된 최종 버전입니다.
    """
    internal_links = set()
    external_links = set()
    
    # [수정 1] www.를 제거한 핵심 도메인을 기준으로 삼습니다.
    core_domain = base_domain.replace("www.", "")

    for link in soup.find_all('a', href=True):
        href = link['href']
        
        # mailto, tel 같은 유효하지 않은 링크는 건너뜁니다.
        if href.startswith(('mailto:', 'tel:', 'javascript:')):
            continue

        # [수정 2] #fragment를 제거하여 중복 URL을 방지합니다.
        absolute_url = urljoin(current_url, href).split('#')[0]
        
        # URL이 비어있으면 건너뜁니다.
        if not absolute_url:
            continue

        parsed_link = urlparse(absolute_url)
        
        # [수정 3] 링크의 도메인에서 www.를 제거한 후 핵심 도메인이 포함되는지 확인합니다.
        link_domain = parsed_link.netloc.replace("www.", "")
        if core_domain in link_domain:
            internal_links.add(absolute_url)
        else:
            external_links.add(absolute_url)
    
    return {
        'internal': list(internal_links),
        'external': list(external_links)
    }


async def crawl_website(url: str, max_pages: int = 15, max_depth: int = 3, delay: float = 1.0) -> Dict[str, any]:
    """
    Crawl a website and extract all text content from internal pages.
    """
    try:
        # URL이 실제로 URL 형식인지 확인 (상호명 등 잘못된 값이 들어오는 경우 방지)
        if not isinstance(url, str) or '.' not in url:
            logger.error(f"Provided url is not a valid URL string: {url!r}")
            return {'error': f"Invalid URL: {url!r}"}

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        parsed_url = urlparse(url)
        base_domain = parsed_url.netloc

        # base_domain이 비어있으면 url이 진짜 URL이 아님
        if not base_domain:
            logger.error(f"Parsed base_domain is empty. Input url: {url!r}")
            return {'error': f"Invalid URL (no domain found): {url!r}"}

        logger.info(f"Starting to crawl website: {url}")

        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        session.headers.update(headers)

        visited_urls = set()
        to_visit = deque([(url, 0)])
        pages_data = []

        while to_visit and len(visited_urls) < max_pages:
            current_url, depth = to_visit.popleft()

            # current_url이 진짜 URL인지 체크 (상호명 등 잘못 들어온 경우 방지)
            if not isinstance(current_url, str) or '.' not in current_url or current_url.strip() == "":
                logger.warning(f"Skipping invalid URL in queue: {current_url!r}")
                continue

            if current_url in visited_urls or depth > max_depth:
                continue

            try:
                logger.info(f"Crawling: {current_url} (depth: {depth})")

                response = session.get(current_url, timeout=30)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                # [중요] 링크 추출을 먼저 실행합니다.
                links = extract_links(soup, response.url, base_domain)  # response.url로 리디렉션된 최종 주소 사용

                # 그 다음에 텍스트를 추출합니다.
                page_text = extract_text_from_soup(soup)

                title = soup.find('title')
                title_text = title.get_text().strip() if title else ""

                page_data = {
                    'url': response.url,
                    'title': title_text,
                    'text': page_text,
                }

                pages_data.append(page_data)
                visited_urls.add(current_url)
                visited_urls.add(response.url)  # 리디렉션된 URL도 추가

                for link in links['internal']:
                    # link가 진짜 URL인지 체크
                    if not isinstance(link, str) or '.' not in link or link.strip() == "":
                        logger.debug(f"Skipping invalid internal link: {link!r}")
                        continue
                    if link not in visited_urls:
                        to_visit.append((link, depth + 1))

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed for {current_url}: {e}")
            except Exception as e:
                logger.warning(f"Error processing {current_url}: {e}")

            time.sleep(delay + random.uniform(0, 1))

        all_text = '\n\n'.join([page['text'] for page in pages_data])

        # all_text가 int 등 잘못된 타입이 되는 경우 방지
        if not isinstance(all_text, str):
            logger.error(f"all_text is not a string: {type(all_text)}")
            return {'error': f"all_text is not a string: {type(all_text)}"}

        result = {
            'base_url': url,
            'total_pages': len(pages_data),
            'all_text': all_text,
            'total_word_count': len(all_text.split()) if isinstance(all_text, str) else 0
        }

        logger.info(f"Completed crawling {url}: {len(pages_data)} pages, {len(all_text.split()) if isinstance(all_text, str) else 0} words")
        return result

    except Exception as e:
        logger.error(f"Error crawling website {url}: {e}")
        return {'error': str(e)}

if __name__ == "__main__":
    test_url = "https://www.eqinternational.com/"
    # max_pages 값을 늘려서 테스트
    result = crawl_website(test_url, max_pages=50, max_depth=3)

    if 'error' not in result:
        print(f"\nCrawled {result['total_pages']} pages")
        print(f"Total words: {result['total_word_count']}")
        print(f"Sample text: {result['all_text'][:500]}...")


