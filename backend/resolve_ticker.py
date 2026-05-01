import requests
import functools

# @functools.lru_cache ensures we only download this file ONCE per application run.
# Subsequent calls will instantly load the data from RAM.
@functools.lru_cache(maxsize=1)
def get_sec_ticker_mapping():
    print("[+] Fetching live ticker mapping from SEC...")
    url = "https://www.sec.gov/files/company_tickers.json"
    
    # CRITICAL: The SEC requires a valid User-Agent for this API call too!
    headers = {"User-Agent": "John Doe john.doe@example.com"} 
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"[-] Failed to fetch SEC tickers. Status Code: {response.status_code}")
        return {}


# Keep your existing get_sec_ticker_mapping() function here
def search_companies_for_dropdown(query: str, limit: int = 5):
    """
    Returns a list of matching companies for the frontend dropdown.
    """
    if not query or len(query) < 2:
        return []

    query_lower = query.lower().strip()
    sec_data = get_sec_ticker_mapping()
    
    matches = []
    for key, data in sec_data.items():
        if query_lower in data['title'].lower() or query_lower == data['ticker'].lower():
            matches.append({
                "name": data['title'],
                "ticker": data['ticker'],
                "label": f"{data['title']} ({data['ticker']})" # For the UI
            })
            
    # Sort by name length so shorter, exact matches float to the top
    matches.sort(key=lambda x: len(x['name']))
    return matches[:limit] # Only return top 5 to keep the frontend snappy