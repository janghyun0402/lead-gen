#!/usr/bin/env python3
"""
Property Management 홈페이지 분석 실행 스크립트

browser-use를 사용하여 PM 회사의 홈페이지에 직접 접속해서
관리하는 방의 개수와 형태를 자동으로 조사합니다.
"""

import asyncio
import json
import sys
import argparse
from typing import List, Dict, Any
from datetime import datetime

from pm_property_analyzer import analyze_pm_website, batch_analyze_pm_websites
from advanced_property_scanner import deep_scan_pm_website


class PropertyAnalysisRunner:
    """Property Management 분석 실행 클래스"""
    
    def __init__(self):
        self.results = []
    
    async def analyze_single_website(self, url: str, deep_scan: bool = False) -> Dict[str, Any]:
        """
        단일 웹사이트 분석
        
        Args:
            url: 분석할 PM 홈페이지 URL
            deep_scan: True면 고급 스캔, False면 기본 스캔
            
        Returns:
            Dict: 분석 결과
        """
        print(f"\n🔍 {'Deep scanning' if deep_scan else 'Analyzing'}: {url}")
        print("-" * 60)
        
        try:
            if deep_scan:
                result = await deep_scan_pm_website(url)
            else:
                result = await analyze_pm_website(url)
            
            # 결과 출력
            self._print_analysis_result(result)
            
            return result
            
        except Exception as e:
            error_result = {
                "url": url,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            print(f"❌ Error analyzing {url}: {e}")
            return error_result
    
    async def analyze_multiple_websites(self, urls: List[str], deep_scan: bool = False) -> List[Dict[str, Any]]:
        """
        여러 웹사이트 일괄 분석
        
        Args:
            urls: 분석할 PM 홈페이지 URL 리스트
            deep_scan: True면 고급 스캔, False면 기본 스캔
            
        Returns:
            List[Dict]: 각 URL의 분석 결과 리스트
        """
        print(f"\n🚀 Starting {'deep scan' if deep_scan else 'analysis'} of {len(urls)} websites")
        print("=" * 60)
        
        results = []
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Processing: {url}")
            result = await self.analyze_single_website(url, deep_scan)
            results.append(result)
            
            # 진행 상황 출력
            status = result.get('status', 'unknown')
            print(f"✅ Completed [{i}/{len(urls)}] - Status: {status}")
        
        self.results = results
        return results
    
    def _print_analysis_result(self, result: Dict[str, Any]) -> None:
        """분석 결과를 보기 좋게 출력"""
        print("\n📊 Analysis Result:")
        print("=" * 40)
        
        if result.get('status') == 'error':
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            return
        
        # 기본 정보
        url = result.get('url', 'Unknown')
        status = result.get('status', 'unknown')
        print(f"URL: {url}")
        print(f"Status: {status}")
        
        # 부동산 정보
        if 'property_management_info' in result:
            pm_info = result['property_management_info']
            print(f"\n🏠 Property Management Info:")
            print(f"  • Total Properties: {pm_info.get('total_properties_managed', 'Unknown')}")
            print(f"  • Property Types: {', '.join(pm_info.get('property_types', []))}")
            print(f"  • Service Areas: {', '.join(pm_info.get('service_areas', []))}")
            print(f"  • Company Size: {pm_info.get('company_size', 'Unknown')}")
            print(f"  • Confidence: {pm_info.get('confidence_level', 'Unknown')}")
        
        elif 'total_properties' in result:
            print(f"\n🏠 Property Info:")
            print(f"  • Total Properties: {result.get('total_properties', 'Unknown')}")
            print(f"  • Property Types: {', '.join(result.get('property_types', []))}")
            print(f"  • Service Areas: {', '.join(result.get('service_areas', []))}")
            print(f"  • Company Size: {result.get('company_size', 'Unknown')}")
        
        # 요약
        if 'summary' in result:
            print(f"\n📝 Summary: {result['summary']}")
        
        # 추가 정보
        if 'notes' in result:
            print(f"\n📌 Notes: {result['notes']}")
    
    def save_results(self, filename: str = None) -> str:
        """분석 결과를 JSON 파일로 저장"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"pm_analysis_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {filename}")
        return filename
    
    def print_summary(self) -> None:
        """전체 분석 결과 요약 출력"""
        if not self.results:
            print("No results to summarize.")
            return
        
        print("\n📈 Analysis Summary")
        print("=" * 50)
        
        total_analyzed = len(self.results)
        successful = len([r for r in self.results if r.get('status') == 'success'])
        failed = len([r for r in self.results if r.get('status') in ['failed', 'error']])
        
        print(f"Total websites analyzed: {total_analyzed}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        
        # 성공한 분석들의 통계
        if successful > 0:
            successful_results = [r for r in self.results if r.get('status') == 'success']
            
            # 총 부동산 개수 합계
            total_properties = 0
            property_counts = []
            
            for result in successful_results:
                if 'property_management_info' in result:
                    count = result['property_management_info'].get('total_properties_managed', 'unknown')
                else:
                    count = result.get('total_properties', 'unknown')
                
                if count != 'unknown' and str(count).isdigit():
                    total_properties += int(count)
                    property_counts.append(int(count))
            
            if property_counts:
                print(f"\n🏠 Property Statistics:")
                print(f"  • Total properties managed: {total_properties:,}")
                print(f"  • Average per company: {total_properties // len(property_counts):,}")
                print(f"  • Largest portfolio: {max(property_counts):,}")
                print(f"  • Smallest portfolio: {min(property_counts):,}")


async def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='Property Management Website Analysis Tool')
    parser.add_argument('urls', nargs='+', help='URLs to analyze')
    parser.add_argument('--deep', action='store_true', help='Perform deep scan (more thorough but slower)')
    parser.add_argument('--output', '-o', help='Output filename for results')
    parser.add_argument('--file', '-f', help='File containing URLs (one per line)')
    
    args = parser.parse_args()
    
    # URL 목록 준비
    urls = []
    if args.file:
        try:
            with open(args.file, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found.")
            sys.exit(1)
    else:
        urls = args.urls
    
    # URL 유효성 검사
    valid_urls = []
    for url in urls:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        valid_urls.append(url)
    
    if not valid_urls:
        print("Error: No valid URLs provided.")
        sys.exit(1)
    
    # 분석 실행
    runner = PropertyAnalysisRunner()
    
    try:
        if len(valid_urls) == 1:
            result = await runner.analyze_single_website(valid_urls[0], args.deep)
            runner.results = [result]
        else:
            await runner.analyze_multiple_websites(valid_urls, args.deep)
        
        # 결과 저장
        output_file = runner.save_results(args.output)
        
        # 요약 출력
        runner.print_summary()
        
        print(f"\n✅ Analysis completed! Results saved to: {output_file}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Analysis interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 예시 실행 (인수 없이 실행할 때)
    if len(sys.argv) == 1:
        print("Property Management Website Analysis Tool")
        print("=" * 50)
        print("\nUsage examples:")
        print("  python run_property_analysis.py https://example-pm.com")
        print("  python run_property_analysis.py --deep https://example-pm.com")
        print("  python run_property_analysis.py --file urls.txt")
        print("  python run_property_analysis.py url1.com url2.com url3.com")
        print("\nFor more options: python run_property_analysis.py --help")
        
        # 테스트 URL로 데모 실행
        print("\n🚀 Running demo with test URLs...")
        test_urls = [
            "https://www.cloverleafpropertymanagement.com/",
            "https://www.chandlerproperties.com/"
        ]
        
        async def demo():
            runner = PropertyAnalysisRunner()
            await runner.analyze_multiple_websites(test_urls, deep_scan=True)
            runner.save_results("demo_results.json")
            runner.print_summary()
        
        asyncio.run(demo())
    else:
        asyncio.run(main())
