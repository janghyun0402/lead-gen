# Browser-use prompts for finding missing features from analyze_website results

BROWSER_USE_PROMPTS = {
    "firm_level_data.owner.name": """
    Navigate to the website and find information about the company owner, founder, CEO, president, or principal.
    
    Process:
    1. **Navigate to the About Us or Team page:** Look for a link or button labeled "About Us" or "Team" and click it to navigate to the appropriate page.
    2. **Find the Owner's Name:** Look for the person's name who is listed as the owner, founder, CEO, president, or principal.
    
    Rules:
    - Must return the full name of the person including both first and last name.
    - Must return one name who is most likely to be the owner, founder, CEO, president, or principal.
    """,
    

    
    "firm_level_data.owner.email": """
    Find the direct email address of the company owner, founder, CEO, or principal.
    
    Process:
    1. **Navigate to the Contact page:** Look for a link or button labeled "Contact" or something similar and click it to navigate to the appropriate page.
    2. **Find the Owner's Email:** Look for the person's email address who is listed as the owner, founder, CEO, president, or principal.
    
    Rules:
    - Must return the full email address including the domain name.
    - Must return one email address who is most likely to be the owner, founder, CEO, president, or principal.
    """,
    
    "firm_level_data.software_used.name": """
    
    Find what property management software this company uses by investigating their tenant portal.

    Process:
    1.  **Find the Portal Link:** Search the website for a link that leads to a tenant or resident portal. Look for button or link text like "Tenant Portal", "Resident Login", "Pay Rent", "Tenant Login", "Renter Login" or similar phrases.
    2.  **Click and Navigate:** Click this link to open the portal login page.
    3.  **Analyze the URL:** Once the new page loads, carefully examine its full URL (the web address). The software name is often part of the domain name (e.g., yourpropertymanager.**appfolio**.com).
    4.  **Identify the Software:** Look for common property management software names within the URL, such as:
        - Appfolio
        - Buildium
        - Rentvine
        - Yardi
        - Propertyware
        - RentManager
        - Entrata
        - ResMan

    Fallback (if the above fails):
    - Check the website's footer for mentions of software partners.

    Return the name of the software if found.
    
    """,
    
    "firm_level_data.number_of_door": """
    Find the **total number of doors** this property management company manages.

    Look for:
    - "Rental Search", "Properties", "Listings", "Vacancies" or similar pages.

    Counting Process:
    1.  **Load All Properties on the Page:**
        - First, scroll to the bottom of the page.
        - Then, find and click any "View More," "Load More," or similar buttons. Repeat this until no new properties are loaded on the current page.
    2.  **Navigate Through All Pages:**
        - After counting all properties on the current page, look for pagination links (e.g., "Next," ">," or page numbers like 2, 3, ...).
        - Click to the next page and repeat Step 1 (scrolling and clicking "View More").
        - Continue this process until you have reached and counted the properties on the very last page.
    3.  **Count the Doors:**
        - Sum up the **total number of individual properties** (NOT number of pages) one by one found across all pages.

    Rules:
    - **Only count the doors with their prices.**
    - **If the page provides the number of doors (e.g., "Showing 46 of 46 results."), use that number directly.**
    - Do not apply any filters to the listings.

    Return the total number of doors found.
    """,
    
    "team_info.leasing_manager_name": """
    Find the name of the leasing manager or leasing specialist.
    Look for:
    - Team/Staff page
    - Contact page with staff directory
    - About Us page with team members
    Find the specific person responsible for leasing.
    """,
    
    "team_info.maintenance_manager_name": """
    Find the name of the maintenance manager or maintenance coordinator.
    Look for:
    - Team/Staff page
    - Contact page with staff directory
    - About Us page with team members
    Find the specific person responsible for maintenance.
    """,
    
    "services_and_focus.services_offered": """
    Find what types of property management services this company offers.
    Look for:
    - Sizes of properties they manage
    - Prices of properties they manage
    Common services: SFR (Single Family Residential), Multifamily, HOA (Homeowners Association), Commercial, Student Housing
    Return a list of service types they offer.
    """,
    
    "services_and_focus.portfolio_focus": """
    Determine what type of properties or market segment the company focuses on.
    Look for:
    - Portfolio page
    - Property listings to see what types they manage
    - About Us page describing their specialty
    - Marketing language about their focus
    Common focuses: Luxury, Affordable, Student, Senior, Corporate, Vacation Rentals
    Return a list of their portfolio focus areas.
    """,
    
    "social_media_info.linkedin_url": """
    
    Find the company's LinkedIn profile URL by clicking its icon.

    **Action Plan:**
    1.  **Find the Icon:** Locate the LinkedIn logo or icon, which is most likely in the website's footer or header.
    2.  **Click and Capture URL:** Click the icon. A new page will open, which might be a login screen. **Immediately capture the full URL of this new page.** This URL is the answer.


    Return the captured URL.
    
    """,
    
    "social_media_info.instagram_url": """
    
    Find the company's Instagram profile URL by clicking its icon.

    **Action Plan:**
    1.  **Find the Icon:** Locate the Instagram logo or icon, which is most likely in the website's footer or header.
    2.  **Click and Capture URL:** Click the icon. A new page will open, which might be a login screen. **Immediately capture the full URL of this new page.** This URL is the answer.

    Return the captured URL.
    
    """,
    
    "social_media_info.facebook_url": """
    
    Find the company's Facebook profile URL by clicking its icon.

    **Action Plan:**
    1.  **Find the Icon:** Locate the Facebook logo or icon, which is most likely in the website's footer or header.
    2.  **Click and Capture URL:** Click the icon. A new page will open, which might be a login screen. **Immediately capture the full URL of this new page.** This URL is the answer.


    Return the captured URL.
    
    """
}