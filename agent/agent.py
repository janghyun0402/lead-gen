import os
import json
import requests
from dotenv import load_dotenv
from agent.crawling import crawl_website
from pprint import pprint
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

MODEL = "gemini-2.5-pro"

import google.generativeai as genai

async def call_gemini_api(prompt: str, model: str = MODEL) -> str:
    """
    Call Google Gemini API using the official google-generativeai Python SDK.

    Args:
        prompt (str): The prompt to send to the model
        model (str): Model name (default: "gemini-2.5-pro")

    Returns:
        str: Response from the model
    """
    api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_GEMINI_API_KEY environment variable is not set")

    genai.configure(api_key=api_key)

    try:
        generation_config = {
            "temperature": 0.7,
            "top_k": 40,
            "top_p": 0.95,
            "max_output_tokens": 8192,
        }
        model_obj = genai.GenerativeModel(model, generation_config=generation_config)
        response = model_obj.generate_content(prompt)
        # The SDK returns a response object with .text property
        if hasattr(response, "text") and response.text:
            return response.text
        else:
            raise ValueError("No response generated from Gemini API")
    except Exception as e:
        raise Exception(f"Error calling Gemini API: {e}")



async def extract_conditions_from_natural_language(user_input: str) -> dict:
    """
    Extract search conditions from natural language input using Gemini.
    
    Args:
        user_input (str): Natural language input from user
    
    Returns:
        dict: Extracted conditions
    """
    prompt = f"""
    You are a lead generation assistant. Extract search conditions from the following user input for finding property management companies.
    
    User input: "{user_input}"
    
    Please extract and return ONLY a JSON object with the following structure:
    {{
        "min_population": <number or null>,
        "state_code": "<state_code or null>",
        "max_cities": <number or 10>,
        "max_firms_per_city": <number or 10>,
        "max_pages_per_site": <number or 30>
    }}
    
    Rules:
    - If no population mentioned, use 50000 as default
    - If no state mentioned, use null
    - If no city limit mentioned, use 10
    - If no firm limit mentioned, use 10
    - If no page limit mentioned, use 30
    - Return ONLY the JSON object, no other text
    """
    
    try:
        response = await call_gemini_api(prompt)
        # Clean up response to extract JSON
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        if response.endswith('```'):
            response = response[:-3]
        
        conditions = json.loads(response)
        return conditions
    except Exception as e:
        print(f"Error extracting conditions: {e}")
        # Return default conditions if extraction fails
        return {
            "min_population": 50000,
            "state_code": None,
            "max_cities": 10,
            "max_firms_per_city": 10,
            "max_pages_per_site": 30
        }


async def analyze_website(google_data: dict, crawled_data: dict, company_name: str = "Not Found", location: str = "Not Found") -> dict:
    """
    Analyze crawled website content using Gemini.
    
    Args:
        crawled_data (dict): Crawled website data from crawl_website()
        company_name (str): Company name for context
        location (str): Company location for context
    
    Returns:
        dict: Analysis results with extracted information
    """
    
    # Crawling 과정에서 오류 발생 시 그냥 빈 문자열로 처리
    
    if not crawled_data:
        website_text = ""
    else:
        website_text = crawled_data.get('all_text', '')
    
    prompt = f"""
    You are an expert real estate market analyst. Your task is to analyze the provided Google Maps data and the full text from a property management company's website. Synthesize information from BOTH sources to extract the required data points as accurately as possible.

    **Data from Google Maps:**
    {google_data}

    **Website Content:**
    {website_text}

    ---

    Please extract the information and return **ONLY a valid JSON object** with the exact structure below.

    **Rules:**
    - Analyze both `google_data` and `website_text` to fill the fields.
    - Especially, check **social network links** in the Website Content such as LinkedIn, Instagram, Facebook.
    - For boolean fields, use `true` or `false`. For numerical fields, use numbers or `null`.
    - If information cannot be found in the provided texts, use `Not Found` for strings/numbers, empty arrays `[]` for lists, and `false` for booleans.
    - Do not invent or infer information that isn't present.
    - The "evidence" fields should contain a brief quote or description of how you found the information.
    - Return ONLY the JSON object and nothing else.

    ```json
    {{
    "firm_name": "string",   // From google_data or website
    "website_url": "string", // From google_data
    "firm_level_data": {{
        "phone": "string | Not Found",  // From google_data "internationalPhoneNumber"
        "owner": {{
        "name": "string | Not Found",   // Search for titles like Owner, Founder, CEO, President, Principal. Do not use Google Reviews's reviewer name. Only use the website's information.
        "phone": "string | Not Found",  // Owner's cell phone number (CEO, President, Principal etc.). Do not use same number with google_data "internationalPhoneNumber" (Company's phone number).
        "email": "string | Not Found",
        "evidence": "string | Not Found" // e.g., "Found 'John Doe, Founder' on the About Us page."
        }},
        "city": "string", // From google_data
        "state": "string", // From google_data
    }},
    "team_info": {{
        "leasing_manager_name": "string | Not Found",
        "maintenance_manager_name": "string | Not Found"
    }},
    "services_and_focus": {{
        "services_offered": ["string"], | "Not Found" // (e.g., "SFR", "Multifamily", "HOA")
        "portfolio_focus": ["string"] | "Not Found" // (e.g., "Luxury", "Affordable", "Student")
    }},
    "social_media_info": {{
        "linkedin_url": "string | Not Found",
        "instagram_url": "string | Not Found",
        "facebook_url": "string | Not Found"
    }},
    "extra_indicators": {{
        "advertises_24_7_maintenance": "boolean",
        "is_hiring": "boolean"          // Look for a 'Careers' page or hiring-related text.
    }},
    "google_review": {{     // from google_data
        "rating": "number",
        "summary": "string",
        "review_count": "number"
    }},
    }}```
    """
    
    try:
        response = await call_gemini_api(prompt)
        # Clean up response to extract JSON
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        if response.endswith('```'):
            response = response[:-3]
        
        analysis = json.loads(response)
        
        # Ensure all required fields are present
        if 'social_media_info' not in analysis:
            analysis['social_media_info'] = {
                "linkedin_url": "Not Found",
                "instagram_url": "Not Found",
                "facebook_url": "Not Found"
            }
        else:
            # Ensure all SNS fields are present within social_media_info
            sns_fields = ['linkedin_url', 'instagram_url', 'facebook_url']
            for field in sns_fields:
                if field not in analysis['social_media_info']:
                    analysis['social_media_info'][field] = "Not Found"
        
        return analysis
        
    except Exception as e:
        print(f"Error analyzing {company_name}: {e}")
        return {
            "firm_name": company_name,
            "website_url": google_data.get('website', 'Not Found'),
            "firm_level_data": {
                "owner": {"name": "Not Found", "phone": "Not Found", "email": "Not Found", "evidence": "Not Found"},
                "city": google_data.get('city', location),
                "state": google_data.get('state', 'Not Found'),
                "software_used": {"name": "Not Found", "evidence": "Not Found"}
            },
            "team_info": {
                "leasing_manager_name": "Not Found",
                "maintenance_manager_name": "Not Found"
            },
            "services_and_focus": {
                "services_offered": [],
                "portfolio_focus": []
            },
            "social_media_info": {
                "linkedin_url": "Not Found",
                "instagram_url": "Not Found", 
                "facebook_url": "Not Found"
            },
            "extra_indicators": {
                "advertises_24_7_maintenance": False,
                "is_hiring": False
            },
            "google_review": {
                "rating": google_data.get('rating', 0),
                "summary": "Summary failed",
                "review_count": google_data.get('user_ratings_total', 0)
            }
        }
        
        

async def generate_final_report(analysis: dict) -> str:
    """
    Generate a final analysis report from the analysis results.
    """
    prompt = f"""
    
    # Mission
    You are a capable sales analyst at a B2B SaaS company. Based on the provided JSON data, your mission is to create a "Sales Analysis Report" that contains the essential information our sales team needs before approaching a prospect (a property management firm).

    # Context
    - The audience for this report is a sales team member with no prior knowledge of this prospect.
    - The goal is to enable them to quickly understand the prospect's situation and provide concrete strategies and ideas on how to approach them.
    - The tone should be concise, clear, and action-oriented.

    # Instructions
    Analyze the JSON data below and generate a 'Sales Analysis Report' according to the following structure.

    ---
    ## 🏢 Sales Analysis Report: [firm_name]

    ### 1. Executive Summary
    - Define the company in one sentence (including its size, location, and specialty).
    - Summarize the two most important features to note from a sales perspective.

    ### 2. Key Contact
    - State the name, title, and contact information.
    - Emphasize that this person is the key decision-maker.

    ### 3. Sales Opportunities & Angles
    - **Software:** Mention their current software (`software_used`), and specifically leverage the 'uncertain evidence' to connect how our product can provide better data and certainty.
    - **Portfolio Focus:** Connect the features of our product that are specialized for "Student Housing" (`portfolio_focus`) to suggest that a customized proposal is possible.
    - **Leverage Strengths:** Use the high Google Review score and keywords like "prompt maintenance" and "smooth communication" (`google_review`) to build the logic that our product is the best partner to further enhance their strengths.
    - **Limitation of Scale:** Given their small number of doors (`number_of_door`), present a strategy that emphasizes how even small businesses can easily adopt our product to maximize operational efficiency.

    ### 4. Conversation Starters
    - Suggest two personalized icebreaker sentences that can be used in a first email or phone call.
    - Example: A way to start the conversation by mentioning a point of praise that repeatedly appears in their Google Reviews.

    ### 5. Reference Info
    - Asset types managed (`services_offered`)
    - Number of doors (`number_of_door`)
    - Social media link (`facebook_url`)

    ---

    # Lead Data
    {analysis}

    ---
    """
    try:
        response = await call_gemini_api(prompt)
        return response
    except Exception as e:
        print(f"Error generating final report: {e}")
        return "Error generating final report"
    

async def generate_email(analysis: dict) -> str:
    """
    Generate a cold mail from the analysis results.
    """
    
    kindredpm_overview = open("agent/KindredPM_Overview.txt", "r", encoding="utf-8").read()
    sales_pitch = open("agent/SalesPitch.txt", "r", encoding="utf-8").read()
    prompt = f"""
    
    # Mission
    You are an expert B2B Sales Development Representative (SDR) specializing in the Property Management (PM) industry. Your mission is to write a highly personalized and compelling cold email to a prospect, using the provided context files.

    # Context & Persona
    - **You:** An SDR from KindredPM, offering a solution that helps PM companies streamline operations, enhance tenant communication, and improve efficiency.
    - **Audience:** The key contact at a target PM company. They are busy and will only respond to messages that are directly relevant to their problems and goals.
    - **Tone:** Professional, empathetic, concise, and value-driven. Avoid generic marketing jargon.

    # Input Files
    1.  **`Lead Data`**: A detailed report on the target PM company (size, focus, key contacts, Google Review analysis).
    2.  **`Our Service Overview`**: A comprehensive document on our service's features and benefits.
    3.  **`Key Selling Points`**: A concise text file from the sales team highlighting the top 2-3 strategic advantages we want to emphasize this quarter.

    # Instructions
    Based on all three context files, generate a personalized cold email draft following this strict structure.

    ---
    **Subject Line:** A question about [Prospect's Company Name]'s [Specific Area of Focus, e.g., student housing operations]

    **Body:**

    **Paragraph 1: The Hook (Personalized Observation)**
    - Start by acknowledging a specific, positive achievement of their company found in `Lead Data`. This is often from their positive Google Reviews. (e.g., "I was impressed to see how tenants consistently praise your team's quick maintenance response...").

    **Paragraph 2: The Pivot (Connecting a Problem to Your Solution)**
    - Analyze the "Cons" or "Negative Feedback" section of the Google Reviews in `Lead Data`.
    - **Constraint:** If, and ONLY IF, you identify a recurring problem that our service can genuinely solve, create a "pivot" sentence.
    - **If no direct problem can be solved:** Do not force it. Instead, pivot based on their strengths. (e.g., "Maintaining such a high standard for maintenance requires incredible coordination...").

    **Paragraph 3: The Value Proposition (Strategic & Relevant)**
    - This is where you present our value. **From the benefits highlighted in the `Key Selling Points` file, select the 1-2 that most directly address the problem (or strength) identified in Paragraph 2.**
    - This step is crucial for aligning our core sales strategy with the prospect's specific needs. Cross-reference with `Our Service Overview` for detailed wording.
    - **Example:** "[Your Service Name] helps by automating tenant communication for maintenance requests, a key advantage highlighted by our team, allowing residents to book available time slots directly, which reduces back-and-forth emails."

    **Paragraph 4: The Call to Action (Low-Friction)**
    - Propose a clear, easy next step. Suggest a brief, 15-minute introductory call to share a specific idea or case study.

    **Closing:**
    - Best regards,
    - Kyle
    - Sales at KindredPM
    ---
    
    
    # Lead Data
    {analysis}
    
    # Our Service Overview
    {kindredpm_overview}
    
    # Key Selling Points
    {sales_pitch}
    """
    try:
        response = await call_gemini_api(prompt)
        return response
    except Exception as e:
        print(f"Error generating cold mail: {e}")
        return "Error generating cold mail"


if __name__ == "__main__":
    # 테스트
    
    google_data = json.load(open("../from_google_maps.json"))
    crawled_data = crawl_website(
        url="http://www.cloverleafpropertymanagement.com/",
        max_pages=10,
        max_depth=5,    
    )
    analysis = analyze_website(google_data, crawled_data, "CloverLeaf Property Management", "San Antonio, TX")
    pprint(analysis)
    