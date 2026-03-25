import asyncio
import sys
import os
import json
import csv
from pathlib import Path
from pprint import pprint
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime

# Import agent modules
from agent import csv_processor
from agent.tools import google_maps_search_pm_for_cities, google_maps_search_by_organization_name
from agent.crawling import crawl_website
from agent.agent import analyze_website, generate_final_report, generate_email
from agent.csv_processor import process_csv_file

COLUMN_MAPPING = {
    # 'Column name of csv': ['Key path in the data dictionary'],
    'Company Name': ['firm_name'],
    'Website': ['website_url'],
    'Phone': ['firm_level_data', 'phone'],
    'Owner Name': ['firm_level_data', 'owner', 'name'],
    'Owner Phone': ['firm_level_data', 'owner', 'phone'],
    'Owner Email': ['firm_level_data', 'owner', 'email'],
    'City': ['firm_level_data', 'city'],
    'State': ['firm_level_data', 'state'],
    '# Vacancies': ['firm_level_data', 'number_of_door'],
    'Software Used': ['firm_level_data', 'software_used', 'name'],
    'Portfolio Focus': ['services_and_focus', 'portfolio_focus'],
    'Services Offered': ['services_and_focus', 'services_offered'],
    'Leasing Manager Name': ['team_info', 'leasing_manager_name'],
    'Maintenance Manager Name': ['team_info', 'maintenance_manager_name'],
    'Google Rating': ['google_review', 'rating'],
    'Google Review Count': ['google_review', 'review_count'],
    'Google Review Summary': ['google_review', 'summary'],
    'LinkedIn URL': ['social_media_info', 'linkedin_url'],
    'Instagram URL': ['social_media_info', 'instagram_url'],
    'Facebook URL': ['social_media_info', 'facebook_url'],
    'Summary Report': ['summary_report'],
    'Example Email': ['example_email'],
}



# Import browser_use functions
try:
    from browser.test import main as browser_use_main
except ImportError:
    print("Warning: browser_use module not found. Browser enhancement will be disabled.")
    browser_use_main = None


def get_nested_value(data_dict, key_path, default_value='Not Found'):
    """
    키 경로(리스트)를 따라 딕셔너리의 값을 안전하게 찾아오는 헬퍼 함수.
    """
    temp_value = data_dict
    for key in key_path:
        if isinstance(temp_value, dict) and key in temp_value:
            temp_value = temp_value[key]
        else:
            return default_value
    return temp_value

def create_csv_from_list(list_of_data: List[Dict], csv_filepath: str, column_mapping: Dict[str, List[str]]):
    """
    딕셔너리의 리스트를 받아 CSV 파일로 저장하는 메인 함수.
    각 딕셔너리는 CSV의 한 행이 됩니다.
    """
    if not list_of_data:
        print("Error: Input list is empty.")
        return

    # CSV 파일의 헤더는 매핑의 키(key)들로 결정됩니다.
    headers = column_mapping.keys()

    try:
        with open(csv_filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            
            # 헤더를 한 번만 작성합니다.
            writer.writeheader()
            
            # data_item == 1 row of the csv
            for data_item in list_of_data:
                row_data = {}
                for column_name, key_path in column_mapping.items():
                    value = get_nested_value(data_item, key_path)
                    
                    # Debug SNS fields
                    if column_name in ['LinkedIn URL', 'Instagram URL', 'Facebook URL'] and 'social_media_info' not in data_item:
                        print(f"[DEBUG] '{column_name}' key path {key_path} not found in data_item.")
                    if isinstance(value, list):
                        value = '|'.join(map(str, value))
                        
                    row_data[column_name] = value
                
                # 추출된 데이터로 한 행을 작성합니다.
                writer.writerow(row_data)
                
        print(f"✅ {len(list_of_data)}개의 데이터가 '{csv_filepath}' 파일로 성공적으로 저장되었습니다.")
        
    except IOError as e:
        print(f"❌ 파일 저장 중 오류가 발생했습니다: {e}")



async def city_mode(city: str, max_results_per_city: int = 10, max_pages: int = 15, max_depth: int = 3, use_browser: bool = True, progress_callback_increment = None, progress_callback_init_total = None) -> str:
    """
    Complete pipeline for city-based analysis including browser-use enhancement.
    
    Args:
        city (str): City name to search for PM companies
        max_results_per_city (int): Maximum PM companies to process per city
        max_pages (int): Maximum pages to crawl per website
        max_depth (int): Maximum crawl depth
        use_browser (bool): Whether to use browser-use for missing information
        progress_callback_increment (Callable[[int, int]]): Callback function for progress tracking
        progress_callback_init_total (Callable[[int]]): Callback function for initializing total progress
    
    Returns:
        str: Path to the generated CSV file with analysis results
    """
    print(f"🚀 Starting city-based analysis for: {city}")
    print(f"Settings: max_results={max_results_per_city}, max_pages={max_pages}, max_depth={max_depth}, browser_use={use_browser}")
    
    # Step 1: Google Maps search
    print("\n📍 Step 1: Searching Google Maps for PM companies...")
    all_google_data = await google_maps_search_pm_for_cities([city], max_results_per_city=max_results_per_city)
    
    if not all_google_data:
        print(f"❌ No property management companies found in {city}")
        return []
    
    print(f"✅ Found {len(all_google_data)} companies")
    
    results = []
    
    # Process each company
    
    # progress_callback_init_total 이 None 이면 multiple city 모드에서 호출된 것
    if progress_callback_init_total:
        progress_callback_init_total(len(all_google_data))
    
    for i, company_data in enumerate(all_google_data):
        print(f"\n{'='*60}")
        print(f"🏢 Processing company {i+1}/{len(all_google_data)}: {company_data['name']}")
        print(f"{'='*60}")
        
        try:
            # Step 2: Website crawling
            crawled_data = {}
            if company_data.get('website'):
                print(f"🕷️  Step 2: Crawling website {company_data['website']}")
                crawled_data = await crawl_website(
                    url=company_data['website'],
                    max_pages=max_pages,
                    max_depth=max_depth,
                )
                print(f"✅ Crawled {crawled_data.get('total_pages', [])} pages")
            else:
                print("⚠️  No website found for crawling")
            
            # Step 3: AI analysis
            print("🤖 Step 3: AI analysis of company data...")
            analysis = await analyze_website(
                google_data=company_data,
                crawled_data=crawled_data,
                company_name=company_data['name'],
                location=city
            )
            print("✅ AI analysis completed")
            
            # Step 4: Browser-use enhancement (if enabled and website exists)
            
            # final_analysis == crawling data 분석 결과 JSON
            final_analysis = analysis
            
            if use_browser and browser_use_main and company_data.get('website'):
                print("🌐 Step 4: Browser-use enhancement for missing information...")
                try:
                    enhanced_analysis = await browser_use_main(analysis)
                    
                    # browser_use 가 리턴하는 딕셔너리 형태의 분석 결과를 final_analysis 에 저장
                    final_analysis = enhanced_analysis if enhanced_analysis else analysis
                    print("✅ Browser-use enhancement completed")
                except Exception as e:
                    print(f"⚠️  Browser-use enhancement failed: {e}")
                    final_analysis = analysis
            else:
                if not browser_use_main:
                    print("⏭️  Step 4: Skipping browser-use enhancement (module not available)")
                else:
                    print("⏭️  Step 4: Skipping browser-use enhancement")
            
            
            result = {
                "company_index": i + 1,
                "city": city,
                "google_data": company_data,
                "crawled_data": crawled_data,
                "analysis": final_analysis,
                "error": None
            }
            
            if progress_callback_increment:
                progress_callback_increment()
            
            results.append(result)
            print(f"✅ Successfully processed {company_data['name']}")
            
        except Exception as e:
            print(f"❌ Error processing {company_data['name']}: {e}")
            
            # 자꾸 여기로 빠져서 -> results[analysis] = None 되기 때문에 이후에 에러 발생
            
            results.append({
                "company_index": i + 1,
                "city": city,
                "google_data": company_data,
                "crawled_data": {},
                "analysis": None,           # 이거 때문에 analysis가 None이 되어서 에러 발생
                "error": str(e)
            })
            
            if progress_callback_increment:
                progress_callback_increment()
    
    print(f"\n🎯 City mode completed: {len(results)} companies processed")
    
    # 최종 분석 결과에 대한 summary report 와 example email 를 생성하여 추가
    flat_results = []
    for result in results:
        if result.get('analysis'):
            analysis_data = result['analysis'].copy()
            
            # Generate summary report and email for successful analysis
            try:
                print(f"📊 Generating summary report for {analysis_data.get('firm_name', 'Unknown')}")
                summary_report = await generate_final_report(analysis_data)
                analysis_data['summary_report'] = summary_report
                
                print(f"📧 Generating example email for {analysis_data.get('firm_name', 'Unknown')}")
                example_email = await generate_email(analysis_data)
                analysis_data['example_email'] = example_email
                
            except Exception as e:
                print(f"⚠️  Error generating reports for {analysis_data.get('firm_name', 'Unknown')}: {e}")
                analysis_data['summary_report'] = 'Report generation failed'
                analysis_data['example_email'] = 'Email generation failed'
            
            flat_results.append(analysis_data)
        else:
            # Create a minimal entry for failed results
            
            # flat_results == list of dicts
            flat_results.append({
                'firm_name': result.get('google_data', {}).get('name', 'Unknown'),
                'firm_level_data': {'city': result.get('city', '')},
                'error': result.get('error', 'Processing failed'),
                'summary_report': 'N/A - Processing failed',
                'example_email': 'N/A - Processing failed'
            })
    
    # Generate CSV file
    from datetime import datetime
    import os
    
    RESULTS_DIR = "outputs"
    
    # Create outputs directory if it doesn't exist
    os.makedirs("outputs", exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_filename = f"city_analysis_{city.replace(' ', '_')}_{timestamp}.csv"
    
    full_save_path = os.path.join(RESULTS_DIR, result_filename)
    
    create_csv_from_list(flat_results, full_save_path, COLUMN_MAPPING)
    return result_filename      #파일 이름만 반환


def parse_city_list(cities_input: str) -> List[str]:
    """
    Parse comma-separated cities string into a clean list of cities.
    
    Args:
        cities_input (str): Comma-separated cities string (e.g., "New York, Los Angeles, Chicago")
    
    Returns:
        List[str]: List of clean city names
    """
    if not cities_input or not isinstance(cities_input, str):
        return []
    
    # Split by comma and clean each city name
    cities = []
    for city in cities_input.split(','):
        clean_city = city.strip()
        if clean_city:  # Only add non-empty cities
            cities.append(clean_city)
    
    print(f"📋 Parsed {len(cities)} cities: {cities}")
    return cities


def merge_csv_files(csv_file_paths: List[str], output_filename: str) -> str:
    """
    Merge multiple CSV files into a single CSV file.
    
    Args:
        csv_file_paths (List[str]): List of CSV file paths to merge
        output_filename (str): Name for the merged output file
    
    Returns:
        str: Path to the merged CSV file
    """
    if not csv_file_paths:
        print("❌ No CSV files to merge")
        return ""
    
    # Filter out empty or non-existent files
    valid_files = []
    for file_path in csv_file_paths:
        if file_path and os.path.exists(file_path):
            valid_files.append(file_path)
        else:
            print(f"⚠️  Skipping invalid file: {file_path}")
    
    if not valid_files:
        print("❌ No valid CSV files found for merging")
        return ""
    
    if len(valid_files) == 1:
        print(f"ℹ️  Only one valid file, returning: {valid_files[0]}")
        return valid_files[0]
    
    try:
        print(f"🔄 Merging {len(valid_files)} CSV files...")
        
        # Read all CSV files and combine them
        combined_df = pd.DataFrame()
        
        for i, file_path in enumerate(valid_files):
            print(f"  📂 Reading file {i+1}/{len(valid_files)}: {os.path.basename(file_path)}")
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            combined_df = pd.concat([combined_df, df], ignore_index=True)
        
        # Create output path
        RESULTS_DIR = "outputs"
        os.makedirs(RESULTS_DIR, exist_ok=True)
        merged_file_path = os.path.join(RESULTS_DIR, output_filename)
        
        # Save merged CSV
        combined_df.to_csv(merged_file_path, index=False, encoding='utf-8-sig')
        
        print(f"✅ Successfully merged {len(valid_files)} files into: {merged_file_path}")
        print(f"📊 Total records: {len(combined_df)}")
        
        return merged_file_path
        
    except Exception as e:
        print(f"❌ Error merging CSV files: {e}")
        return ""


async def multi_city_mode(cities_input: str, max_results_per_city: int = 10, max_pages: int = 15, max_depth: int = 3, use_browser: bool = True, progress_callback_increment = None, progress_callback_init_total = None) -> str:
    """
    Process multiple cities and merge results into a single CSV file.
    
    Args:
        cities_input (str): Comma-separated cities string (e.g., "New York, Los Angeles, Chicago")
        max_results_per_city (int): Maximum PM companies to process per city
        max_pages (int): Maximum pages to crawl per website
        max_depth (int): Maximum crawl depth
        use_browser (bool): Whether to use browser-use for missing information
        progress_callback (Callable[[int, int]]): Callback function for progress tracking
    Returns:
        str: Path to the merged CSV file with analysis results from all cities
    """
    print(f"🌆 Starting multi-city analysis...")
    print(f"Input: {cities_input}")
    print(f"Settings: max_results={max_results_per_city}, max_pages={max_pages}, max_depth={max_depth}, browser_use={use_browser}")
    
    # Step 1: Parse cities from input string
    city_list = parse_city_list(cities_input)
    
    if not city_list:
        print("❌ No valid cities found to process")
        return ""
    
    if len(city_list) == 1:
        print("ℹ️  Only one city detected, using single city mode")
        return await city_mode(city_list[0], max_results_per_city, max_pages, max_depth, use_browser)
    
    print(f"🎯 Processing {len(city_list)} cities: {', '.join(city_list)}")
    
    # Step 2: Process each city using existing city_mode function
    csv_file_paths = []
    successful_cities = []
    failed_cities = []
    
    total_cities = len(city_list) * max_results_per_city
    if progress_callback_init_total:
        progress_callback_init_total(total_cities)
    
    for i, city in enumerate(city_list):
        print(f"\n{'='*80}")
        print(f"🏙️  Processing city {i+1}/{len(city_list)}: {city}")
        print(f"{'='*80}")
        
        try:
            csv_filename = await city_mode(city, max_results_per_city, max_pages, max_depth, use_browser, progress_callback_increment, None)
            
            if csv_filename:
                # city_mode returns filename only, need to add full path
                csv_file_path = os.path.join("outputs", csv_filename)
                if os.path.exists(csv_file_path):
                    csv_file_paths.append(csv_file_path)
                    successful_cities.append(city)
                    print(f"✅ Successfully completed analysis for {city}")
                else:
                    failed_cities.append(city)
                    print(f"⚠️  File not found for {city}: {csv_file_path}")
            else:
                failed_cities.append(city)
                print(f"⚠️  No results generated for {city}")
                
        except Exception as e:
            failed_cities.append(city)
            print(f"❌ Error processing {city}: {e}")
    
    # Step 3: Merge all generated CSV files
    print(f"\n{'='*80}")
    print(f"📋 Multi-city Analysis Summary")
    print(f"{'='*80}")
    print(f"✅ Successful cities ({len(successful_cities)}): {', '.join(successful_cities)}")
    if failed_cities:
        print(f"❌ Failed cities ({len(failed_cities)}): {', '.join(failed_cities)}")
    
    if not csv_file_paths:
        print("❌ No CSV files generated from any city")
        return ""
    
    # Generate merged filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cities_short = "_".join([city.replace(" ", "").replace(",", "") for city in successful_cities[:3]])
    if len(successful_cities) > 3:
        cities_short += f"_and_{len(successful_cities)-3}_more"
    
    merged_filename = f"multi_city_analysis_{cities_short}_{timestamp}.csv"
    
    # Merge CSV files
    merged_csv_path = merge_csv_files(csv_file_paths, merged_filename)
    
    if merged_csv_path:
        print(f"\n🎉 Multi-city analysis completed successfully!")
        print(f"📁 Merged results saved to: {merged_csv_path}")
        return os.path.basename(merged_csv_path)  # Return filename only to match existing pattern
    else:
        print(f"\n⚠️  Multi-city analysis completed with errors")
        return ""


async def csv_mode(csv_file_path: str, max_pages: int = 50, max_depth: int = 3, use_browser: bool = True, progress_callback_increment = None, progress_callback_init_total = None) -> str:
    """
    Complete pipeline for CSV-based analysis including browser-use enhancement.
    
    Args:
        csv_file_path (str): Path to CSV file containing organization names
        max_pages (int): Maximum pages to crawl per website
        max_depth (int): Maximum crawl depth
        use_browser (bool): Whether to use browser-use for missing information
        progress_callback_increment (Callable[[int, int]]): Callback function for progress tracking
        progress_callback_init_total (Callable[[int]]): Callback function for initializing total progress
    Returns:
        str: Path to the generated CSV file with analysis results
    """
    print(f"🚀 Starting CSV-based analysis for: {csv_file_path}")
    print(f"Settings: max_pages={max_pages}, max_depth={max_depth}, browser_use={use_browser}")
    
    # Create outputs directory if it doesn't exist
    os.makedirs("outputs", exist_ok=True)
    
    if not os.path.exists(csv_file_path):
        print(f"❌ CSV file not found: {csv_file_path}")
        return None
    
    # Read CSV file first to extract organization data
    print("\n📊 Step 1: Parsing CSV file...")
    
    # 'owner_name' 컬럼 input 에 존재하면 이것까지 리턴
    organizations = process_csv_file(csv_file_path)
    
    if not organizations:
        print("❌ No organizations found in CSV file")
        return None
    
    print(f"✅ Extracted {len(organizations)} organizations from CSV")
    
    if progress_callback_init_total:
        progress_callback_init_total(len(organizations))
    
    # Process each organization through the full pipeline
    csv_results = []
    enhanced_results = []
    flat_results = []
    for i, org_data in enumerate(organizations):
        print(f"\n{'='*60}")
        print(f"🏢 Processing organization {i+1}/{len(organizations)}: {org_data['organization_name']}")
        if org_data['city']:
            print(f"   📍 City: {org_data['city']}")
        print(f"{'='*60}")
        
        try:
            # Step 1: Google Maps search
            print("📍 Step 1: Searching Google Maps...")
            google_data = await google_maps_search_by_organization_name(
                org_data['organization_name'], 
                org_data['city']
            )
            
            ## google maps search 실패한 케이스
            if not google_data:
                print(f"⚠️  No Google Maps data found for {org_data['organization_name']}")
                result = {
                    "row_number": org_data['row_number'],
                    "organization_name": org_data['organization_name'],
                    "city": org_data['city'],
                    "original_data": org_data,
                    "google_data": None,
                    "crawled_data": None,
                    "analysis": None,
                    "error": "No Google Maps data found"
                }
                csv_results.append(result)
                
                # Per-row enhancement and reporting flow
                if use_browser and browser_use_main:
                    print(f"\n{'='*60}")
                    print(f"🔍 Enhancing result {i+1}/{len(organizations)}: {result['organization_name']}")
                    print(f"{'='*60}")
                    print("⏭️  Skipping browser enhancement due to previous error")
                    enhanced_results.append(result)
                    
                    # Flatten minimal entry due to error
                    flat_results.append({
                        'firm_name': result.get('organization_name', 'Unknown'),
                        'firm_level_data': {'city': result.get('city', '')},
                        'error': result.get('error', 'Processing failed'),
                        'summary_report': 'N/A - Processing failed',
                        'example_email': 'N/A - Processing failed'
                    })
                else:
                    # No browser enhancement; flatten minimal entry
                    flat_results.append({
                        'firm_name': result.get('organization_name', 'Unknown'),
                        'firm_level_data': {'city': result.get('city', '')},
                        'error': result.get('error', 'Processing failed'),
                        'summary_report': 'N/A - Processing failed',
                        'example_email': 'N/A - Processing failed'
                    })
                if progress_callback_increment:
                    progress_callback_increment()
                continue
            
            print(f"✅ Found Google Maps data")
            
            # Step 2: Website crawling
            crawled_data = {}
            if google_data.get('website'):
                print(f"🕷️  Step 2: Crawling website {google_data['website']}")
                crawled_data = await crawl_website(
                    url=google_data['website'],
                    max_pages=max_pages,
                    max_depth=max_depth,
                )
                print(f"✅ Crawled {crawled_data.get('total_pages', [])} pages")
            else:
                print("⚠️  No website found for crawling")
            
            # Step 3: AI analysis
            print("🤖 Step 3: AI analysis...")
            analysis = await analyze_website(
                google_data=google_data,
                crawled_data=crawled_data,
                company_name=google_data.get('name', org_data['organization_name']),
                location=org_data['city'] or google_data.get('address', 'Unknown')
            )
            print("✅ AI analysis completed")
            
            # Store result
            result = {
                "row_number": org_data['row_number'],
                "organization_name": org_data['organization_name'],
                "city": org_data['city'],
                "original_data": org_data,
                "google_data": google_data,
                "crawled_data": crawled_data,
                "analysis": analysis,
                "error": None
            }
            
            csv_results.append(result)
            print(f"✅ Successfully processed {org_data['organization_name']}")
            
        except Exception as e:
            print(f"❌ Error processing {org_data['organization_name']}: {e}")
            result = {
                "row_number": org_data['row_number'],
                "organization_name": org_data['organization_name'],
                "city": org_data['city'],
                "original_data": org_data,
                "google_data": None,
                "crawled_data": None,
                "analysis": None,
                "error": str(e)
            }
            csv_results.append(result)

        # Per-row browser-use enhancement and reporting
        if use_browser and browser_use_main:
            print(f"\n{'='*60}")
            print(f"🔍 Enhancing result {i+1}/{len(csv_results)}: {result['organization_name']}")
            print(f"{'='*60}")
            
            # SKIP browser-use enhancement if there was an error in basic processing
            if result['error'] or not result['analysis']:
                print("⏭️  Skipping browser enhancement due to previous error")
                enhanced_results.append(result)
                
                # Flatten minimal entry
                flat_results.append({
                    'firm_name': result.get('organization_name', 'Unknown'),
                    'firm_level_data': {'city': result.get('city', '')},
                    'error': result.get('error', 'Processing failed'),
                    'summary_report': 'N/A - Processing failed',
                    'example_email': 'N/A - Processing failed'
                })
                if progress_callback_increment:
                    progress_callback_increment()
                continue
            
            # SKIP browser-use enhancement if no website available
            website_url = result.get('google_data', {}).get('website')
            if not website_url:
                print("⏭️  Skipping browser enhancement - no website available")
                enhanced_results.append(result)
                # Generate reports and email without enhancement
                analysis_data = result['analysis'].copy()
                try:
                    print(f"📊 Generating summary report for {analysis_data.get('firm_name', 'Unknown')}")
                    summary_report = await generate_final_report(analysis_data)
                    analysis_data['summary_report'] = summary_report
                    
                    print(f"📧 Generating example email for {analysis_data.get('firm_name', 'Unknown')}")
                    example_email = await generate_email(analysis_data)
                    analysis_data['example_email'] = example_email
                    
                except Exception as e:
                    print(f"⚠️  Error generating reports for {analysis_data.get('firm_name', 'Unknown')}: {e}")
                    analysis_data['summary_report'] = 'Report generation failed'
                    analysis_data['example_email'] = 'Email generation failed'
                flat_results.append(analysis_data)
                if progress_callback_increment:
                    progress_callback_increment()
                continue
            
            ## browser-use enhancement ###
            try:
                print("🌐 Applying browser-use enhancement...")
                
                # input csv 에서 owner_name 주어진 경우 after_crawl_results 수정
                if org_data['owner_name']:
                    result['analysis']['firm_level_data']['owner']['name'] = org_data['owner_name']
                    
                    if result['analysis']['firm_level_data']['owner']['email'] != "Not Found":
                        result['analysis']['firm_level_data']['owner']['email'] = "Not Found"
                    if result['analysis']['firm_level_data']['owner']['phone'] != "Not Found":
                        result['analysis']['firm_level_data']['owner']['phone'] = "Not Found"
                    
                
                # result['analysis'] -> after_crawl_results
                enhanced_analysis = await browser_use_main(result['analysis'])
                
                # Update the result with enhanced analysis
                enhanced_result = result.copy()
                enhanced_result['analysis'] = enhanced_analysis if enhanced_analysis else result['analysis']
                enhanced_result['browser_enhanced'] = True
                
                enhanced_results.append(enhanced_result)
                print("✅ Browser-use enhancement completed")
                
                # Generate reports and email for enhanced result
                analysis_data = enhanced_result['analysis'].copy()
                try:
                    print(f"📊 Generating summary report for {analysis_data.get('firm_name', 'Unknown')}")
                    summary_report = await generate_final_report(analysis_data)
                    analysis_data['summary_report'] = summary_report
                    
                    print(f"📧 Generating example email for {analysis_data.get('firm_name', 'Unknown')}")
                    example_email = await generate_email(analysis_data)
                    analysis_data['example_email'] = example_email
                    print(f"\n🎯 CSV mode with browser enhancement completed: {len(enhanced_results)} organizations processed")
            
                    
                except Exception as e:
                    print(f"⚠️  Error generating reports for {analysis_data.get('firm_name', 'Unknown')}: {e}")
                    analysis_data['summary_report'] = 'Report generation failed'
                    analysis_data['example_email'] = 'Email generation failed'
                flat_results.append(analysis_data)
                
            except Exception as e:
                print(f"⚠️  Browser-use enhancement failed: {e}")
                result['browser_enhanced'] = False
                enhanced_results.append(result)
                
                
            except Exception as e:
                print(f"⚠️  Browser-use enhancement failed: {e}")
                result['browser_enhanced'] = False
                enhanced_results.append(result)
                # Fallback to generating reports without enhancement
                if result.get('analysis'):
                    analysis_data = result['analysis'].copy()
                    try:
                        print(f"📊 Generating summary report for {analysis_data.get('firm_name', 'Unknown')}")
                        summary_report = await generate_final_report(analysis_data)
                        analysis_data['summary_report'] = summary_report
                        
                        print(f"📧 Generating example email for {analysis_data.get('firm_name', 'Unknown')}")
                        example_email = await generate_email(analysis_data)
                        analysis_data['example_email'] = example_email
                        
                    except Exception as e:
                        print(f"⚠️  Error generating reports for {analysis_data.get('firm_name', 'Unknown')}: {e}")
                        analysis_data['summary_report'] = 'Report generation failed'
                        analysis_data['example_email'] = 'Email generation failed'
                    flat_results.append(analysis_data)
                else:
                    flat_results.append({
                        'firm_name': result.get('organization_name', 'Unknown'),
                        'firm_level_data': {'city': result.get('city', '')},
                        'error': result.get('error', 'Processing failed'),
                        'summary_report': 'N/A - Processing failed',
                        'example_email': 'N/A - Processing failed'
                    })
        ## Fail to load browser-use enhancement ###
        else:
            print("⚠️  Browser-use module not available - proceeding without enhancement")
            if not result.get('analysis'):
                flat_results.append({
                    'firm_name': result.get('organization_name', 'Unknown'),
                    'firm_level_data': {'city': result.get('city', '')},
                    'error': result.get('error', 'Processing failed'),
                    'summary_report': 'N/A - Processing failed',
                    'example_email': 'N/A - Processing failed'
                })
            else:
                analysis_data = result['analysis'].copy()
                try:
                    print(f"📊 Generating summary report for {analysis_data.get('firm_name', 'Unknown')}")
                    summary_report = generate_final_report(analysis_data)
                    analysis_data['summary_report'] = summary_report
                    
                    print(f"📧 Generating example email for {analysis_data.get('firm_name', 'Unknown')}")
                    example_email = generate_email(analysis_data)
                    analysis_data['example_email'] = example_email
                    
                except Exception as e:
                    print(f"⚠️  Error generating reports for {analysis_data.get('firm_name', 'Unknown')}: {e}")
                    analysis_data['summary_report'] = 'Report generation failed'
                    analysis_data['example_email'] = 'Email generation failed'
                flat_results.append(analysis_data)
                
        ## 한 row 처리 완료        
        if progress_callback_increment:
            progress_callback_increment()
    
    
    print(f"\n✅ Basic processing completed: {len(csv_results)} organizations processed")
    
    # Final summary logs consistent with original flow

    
    # Generate CSV file
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_input_name = os.path.splitext(os.path.basename(csv_file_path))[0]
    csv_filename = f"outputs/csv_analysis_{csv_input_name}_{timestamp}.csv"
    
    create_csv_from_list(flat_results, csv_filename, COLUMN_MAPPING)
    return csv_filename



async def main():
    """
    Main function for testing and CLI usage.
    
    Example usage:
    - Single city: await city_mode("Milwaukee", max_results_per_city=5)
    - Multiple cities: await multi_city_mode("Milwaukee, Chicago, Detroit", max_results_per_city=3)
    - CSV processing: await csv_mode("csv_sample.csv")
    """
    
    # Example of multi-city analysis
    print("🌆 Testing multi-city mode...")
    
    # Test with multiple cities
    cities_input = "Milwaukee, Chicago"  # You can modify this for testing
    result = await multi_city_mode(
        cities_input=cities_input,
        max_results_per_city=2,  # Reduced for testing
        max_pages=10,
        max_depth=2,
        use_browser=True
    )
    
    if result:
        print(f"✅ Multi-city analysis completed! Results saved to: {result}")
    else:
        print("❌ Multi-city analysis failed")
    
    # Uncomment below for single city testing
    # await city_mode(city="Milwaukee", max_results_per_city=1, max_pages=15, max_depth=3, use_browser=True)




if __name__ == "__main__":
    asyncio.run(main())