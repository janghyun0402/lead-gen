
from dotenv import load_dotenv
import asyncio
from pydantic import BaseModel, Field
import sys
import os
from pathlib import Path


# Search for Playwright Chromium binary in both x64 and arm64 folders


base = Path.home() / ".cache/ms-playwright"
chromes = list(base.glob("chromium-*/chrome-linux*/chrome"))
if chromes:
    os.environ["BROWSER_USE_BINARY"] = str(chromes[0])
    print(f"BROWSER_USE_BINARY set to: {os.environ['BROWSER_USE_BINARY']}")
else:
    raise FileNotFoundError(
        "Playwright Chromium not found — run `playwright install chromium` first."
    )

# Force headless mode & safe flags
os.environ["BROWSER_USE_LAUNCH_ARGS"] = (
    "--headless=new --no-sandbox --disable-dev-shm-usage --disable-gpu"
)
os.environ["BROWSER_USE_LAUNCH_TIMEOUT"] = "120"  # give it more time on ARM64
os.environ["ANONYMIZED_TELEMETRY"] = "false"



# Add parent directory to path to import from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.tools import google_maps_search_pm_for_cities
from agent.crawling import crawl_website
from agent.agent import analyze_website
from browser.browser_use_prompts import BROWSER_USE_PROMPTS
import pprint
from browser.search_tool import get_urls_from_google_search
load_dotenv()

from browser_use import Agent, ChatGoogle, Controller, Browser
from browser.search_tool import tools

browser = Browser(
    executable_path=os.environ["BROWSER_USE_BINARY"],
    headless=True,
    args=[
        "--headless=new",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
    ],
)




class MissingFeatureInfo(BaseModel):
    feature_name: str = Field(description="The name of the feature being searched for")
    found_value: str = Field(description="The value found for this feature, or 'Not Found' if not available")
    reasoning: str = Field(description="Brief explanation of how the information was found or why it wasn't found")

class ExtractedData(BaseModel):
    missing_features: list[MissingFeatureInfo] = Field(description="List of missing features that were searched for")

class OwnerPhoneInfo(BaseModel):
    phone_number: str = Field(description="The phone number found for the owner")

def get_nested_value(data_dict, key_path):
    """
    Get value from nested dictionary using dot notation key.
    e.g., 'firm_level_data.owner.name' -> data_dict['firm_level_data']['owner']['name']
    """
    keys = key_path.split('.')
    value = data_dict
    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return None
    
    

    
    
    
    
    
    
###### Owner Phone Browser-Use #######
async def browser_use_owner_phone(owner_name: str, pm_name: str, company_number: str):
    """
    Use browser-use to search for the owner's phone number on the PM website.
    """
    task = f"""
    
    You are an expert in searching for information on the internet.
    Your mission is to find the owner's phone number on the PM website.

    **Goal**: Find the owner's phone number on the PM website.

    **Owner Name**: {owner_name}
    **PM Name**: {pm_name}
    **Company Number**: {company_number}
    
    
    **Workflow**:
    1. Use `get_urls_from_google_search` tool with the query: "{owner_name} {pm_name} cell phone realtor" and get URL list.
    2. Write down the URL list in todo.md file. Do not use `get_urls_from_google_search` after this step.
    2. go_to_url in listing URL one by one.
    3. Find the owner's phone number on the website.
    4. Return the phone number.
    Repeat 2~3 until you find the owner's phone number.
    
    **FINAL OUTPUT RULES (HARD)**
    You MUST output EXACTLY ONE LINE:
    - If a valid phone number is found on the page: output the phone number only.
    - If not found: output Not Found.

    STRICT FORMAT:
    - No quotes, no labels, no markdown, no explanation.
    - Examples (valid):
    +1 407-555-1234
    Not Found

    Examples (INVALID — do NOT do this):
    Phone number: +1 407-555-1234
    "Not Found"
    Not Found because ...
    
    **Rules**:
    - Do not use `google_search` tool. Only use `get_urls_from_google_search` tool.
    - Search carefully and thoroughly each website one by one.
    - If your found number is same with the company number given above, proceed to the next website. It's not the owner's phone number.
    - If you meet a log-in page or reCAPTCHA or Cloudflare problem, skip that site and go to the next website.
    - If you can't find the owner's phone number, return 'Not Found'.
    - Do not try to download any files(ex. pdf, doc, etc.) or images. Just search the website.
    """
    
    controller = Controller(output_model=OwnerPhoneInfo)
    
    llm = ChatGoogle(model="gemini-2.5-flash")
    browser = Browser(
        executable_path=os.environ["BROWSER_USE_BINARY"],
        headless=True,
        args=[
            "--headless=new",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ],
    )
    agent = Agent(task=task, llm=llm, max_history_items=15, browser=browser, tools=tools)
    history = await agent.run()
    await agent.close()

    result_json = history.final_result()
    print(f"OWNER PHONE RESULT: {result_json}")
    return result_json
    
    
    
    
    


async def find_unknown_features(analyze_result):
    """
    Find all features in analyze_website result that have 'Unknown' values.
    Returns list of feature paths (e.g., ['firm_level_data.owner.name', 'social_media_info.linkedin_url'])
    """
    unknown_features = []
    
    # Check below feature paths that could be Unknown
    feature_paths_to_check = [
        # Firm level data
        "firm_level_data.owner.name",
        "firm_level_data.owner.email",
        "firm_level_data.software_used.name",
        "firm_level_data.number_of_door",
        
        # Team information
        "team_info.leasing_manager_name",
        "team_info.maintenance_manager_name",
        
        # Services and focus
        "services_and_focus.services_offered",
        "services_and_focus.portfolio_focus",
        
        # Social media information
        "social_media_info.linkedin_url",
        "social_media_info.instagram_url",
        "social_media_info.facebook_url",
    ]
    for feature_path in feature_paths_to_check:
        value = get_nested_value(analyze_result, feature_path)
        if value == "Unknown" or value is None or value == "Not Found":
            unknown_features.append(feature_path)
    
    return unknown_features

async def search_missing_features(pm_url, unknown_features):
    """
    Use browser-use to search for missing features on the PM website.
    """
    if not unknown_features:
        print("No missing features to search for!")
        return {}
    
    llm = ChatGoogle(model="gemini-2.5-flash")
    controller = Controller(output_model=ExtractedData)
    
    # Build dynamic task based on missing features
    features_to_search = []
    for feature in unknown_features:
        if feature in BROWSER_USE_PROMPTS:
            features_to_search.append({
                "feature_name": feature,
                "instructions": BROWSER_USE_PROMPTS[feature]
            })
    
    if not features_to_search:
        print("No prompts available for the missing features!")
        return {}
    
    # Create dynamic task
    task = f"""
    You are an expert AI agent specializing in property management website analysis.
    Your mission is to collect information about Property Management companies from their websites to support the Sales team in their sales activities targeting PM companies.

    **Goal**: Find specific missing information from the property management company's website.

    **Target URL**: {pm_url}

    **Missing Features to Find**:
    """
    
    for i, feature_info in enumerate(features_to_search, 1):
        task += f"""
        
    {i}. **{feature_info['feature_name']}**:
       {feature_info['instructions']}
       
    """
    
    task += f"""
    ----------------------------
    **Procedure**:
    1. go_to_url {pm_url}
    2. For each missing feature above, thoroughly search the website one feature at a time using the instructions provided above.
 
    ----------------------------
    
    **Rules**:
    - Wait a moment for the webpage to load completely, and after it loads completely, then proceed to the next step.
    - Before clicking any top navigation menu item, first move the mouse over it and wait briefly to check if a dropdown menu appears.
      - If a dropdown opens, review all visible submenu items and click the most relevant one.
      - If no dropdown or submenu appears after hovering, click the main menu item directly.
    - If browser malfunctions, close the browser and restart the browser.
    - Don't proceed when log-in window appears. Just collect information from that page and go back to the previous page.
    - Navigate through pages relevant to target feature.   
    - Only report information that you can clearly see and verify on the website - if you're not certain about the information, mark it as 'Not Found'
    - Complete the search for one feature before moving to the next feature
    - If information is not found, mark as 'Not Found'
    
    ----------------------------

    **Output**: Return information for all {len(features_to_search)} features listed above.
    
    ----------------------------
    
    
    **Constraints**:
    - Close any pop-ups that may appear
    - If you can't solve reCAPTCHA 3 times in a row, stop the search and return 'Not Found'
    - Must follow the instructions and rules in each feature's prompt.
    """
    
    print(f"🔍 Searching for {len(features_to_search)} missing features...")
    print("Missing features:", [f['feature_name'] for f in features_to_search])
    
    browser = Browser(
        executable_path=os.environ["BROWSER_USE_BINARY"],
        headless=True,
        args=[
            "--headless=new",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ],
    )
    agent = Agent(task=task, llm=llm, controller=controller, max_history_items=15, browser=browser)
    history = await agent.run()
    await agent.close()
    
    result_json = history.final_result()
    screenshot_paths = history.screenshot_paths()
    print(f"HISTORY PATH: {screenshot_paths}")
    
    
    
    if result_json:
        try:
            parsed_data = ExtractedData.model_validate_json(result_json)
            
            # Convert to dictionary format
            results = {}
            for feature_info in parsed_data.missing_features:
                results[feature_info.feature_name] = feature_info.found_value
            
            print("\n--- 🤖 Browser-Use Search Results ---")
            for feature_name, value in results.items():
                print(f"{feature_name}: {value}")
            print("------------------------------------\n")
            
            return results
            
        except Exception as e:
            print(f"An error occurred while processing the results: {e}")
            print("Original data received:", result_json)
            return {}
    else:
        print("Failed to extract missing features from the website.")
        return {}

# cralwed_results -> browser_results 로 업데이트 하는 함수.
# browser_results 는 flat 한 형태로 저장되어 있고, 최종 리턴하는 포맷은 nested 한 형태로 리턴해야 한다.
async def update_analysis_with_browser_results(analyze_result, browser_results):
    """
    Update the analyze_website result with findings from browser-use.
    """
    updated_result = analyze_result.copy()
    
    for feature_path, found_value in browser_results.items():
        # Update the nested dictionary regardless of value (including 'Not Found')
        keys = feature_path.split('.')
        current = updated_result
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value (including 'Not Found')
        current[keys[-1]] = found_value
    
    return updated_result

async def main(after_crawl_results: dict):
    """
    Main function to demonstrate the integration.
    This would normally be called after analyze_website() returns results.
    """
    
    pm_url = after_crawl_results["website_url"]
    
    # Find which features are Unknown
    unknown_features = await find_unknown_features(after_crawl_results)
    print(f"Found {len(unknown_features)} unknown features: {unknown_features}")
    
    if unknown_features:
        # Use browser-use to search for missing features
        browser_results = await search_missing_features(pm_url, unknown_features)
        print(f"BROWSER_RESULT: {browser_results}")
        
        # Update the original analysis with browser-use findings
        final_result = await update_analysis_with_browser_results(after_crawl_results, browser_results)
        print(f"FINAL_RESULT: {final_result}")
        
        
        if final_result["firm_level_data"]["owner"]["name"] != "Not Found":
            owner_phone = await browser_use_owner_phone(final_result["firm_level_data"]["owner"]["name"], final_result["firm_name"], final_result["firm_level_data"]["phone"])
            print(f"OWNER PHONE: {owner_phone}")
            final_result["firm_level_data"]["owner"]["phone"] = owner_phone
        else:
            final_result["firm_level_data"]["owner"]["phone"] = "Not Found"
            print("Owner name not found - SKIP phone search")
        
        
        print("\n🎯 Final Updated Analysis:")
        print("="*50)
        import json
        print(json.dumps(final_result, indent=2))
        
        return final_result
    else:
        print("No unknown features found - analysis is complete!")
        return None




if __name__ == "__main__":
    example_analyze_result = {'extra_indicators': {'advertises_24_7_maintenance': True, 'is_hiring': True},
 'firm_level_data': {'city': 'Overland Park', 'phone': '+1 913-359-5659',
                     'owner': {'email': 'contact@scudore.com',
                               'evidence': "Found 'Author Brittney Orellano "
                                           "Co-Founder + COO' on a blog post "
                                           'within the website text.',
                               'name': 'Brittney Orellano',
                               'phone': '+1 913-359-5659'},
                     'software_used': {'evidence': 'The website mentions '
                                                   "'Owner Portal' and "
                                                   "'Resident Portal' but does "
                                                   'not name the specific '
                                                   'software provider.',
                                       'name': 'Unknown'},
                     'state': 'KS'},
 'firm_name': 'SCUDO Real Estate + Property Management',
 'google_review': {'rating': 4.3,
                   'review_count': 191,
                   'summary': 'Reviews are mixed. Positive feedback highlights '
                              'good communication and responsiveness for both '
                              'owners and tenants. Negative reviews cite '
                              'issues with poor quality and overpriced '
                              'maintenance, unannounced maintenance visits, '
                              'and frustrating communication with the '
                              'company.'},
 'services_and_focus': {'portfolio_focus': ['Luxury'],
                        'services_offered': ['SFR',
                                             'Multifamily',
                                             'Real Estate Sales']},
 'social_media_info': {'facebook_url': 'Unknown',
                       'instagram_url': 'Unknown',
                       'linkedin_url': 'Unknown'},
 'team_info': {'has_leasing_manager': True,
               'has_maintenance_manager': True,
               'leasing_manager_name': 'Unknown',
               'maintenance_manager_name': 'Unknown'},
 'website_url': 'https://www.scudore.com/'}
    
    
    asyncio.run(main(example_analyze_result))

# if __name__ == "__main__":
#     result = asyncio.run(browser_use_owner_phone("Jennifer Olson Spadine", "Guardian Property Management", "+1 651-287-2011"))
#     print(f"RESULT: {result}")