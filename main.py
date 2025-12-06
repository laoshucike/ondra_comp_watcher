import sys
import json
import requests
from bs4 import BeautifulSoup

def check_stock():
    url = "https://www.lasportivausa.com/ondra-comp.html"
    target_size_label = "40" # The size you want to track
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    print(f"Fetching {url}...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Failed to load page (Status code {response.status_code})")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the Magento configuration script containing product data
    scripts = soup.find_all('script', type='text/x-magento-init')
    
    stock_data = None
    
    for script in scripts:
        if 'jsonConfig' in script.string:
            try:
                # The script string is a JSON object
                data = json.loads(script.string)
                # Navigate down to the jsonConfig object
                stock_data = data['[data-role=swatch-options]']['Magento_Swatches/js/swatch-renderer']['jsonConfig']
                break
            except (KeyError, json.JSONDecodeError, TypeError):
                continue

    if not stock_data:
        print("Error: Could not find stock data in page source. The website structure might have changed.")
        return

    # --- Step 1: Find the internal ID for Size 40 ---
    # The 'attributes' dictionary holds the mapping of ID to Label
    # We look for attribute code 'size' (ID 187 is standard for this site)
    size_attribute = stock_data['attributes'].get('187') 
    
    if not size_attribute:
        # Fallback: Search all attributes if '187' changes
        for attr in stock_data['attributes'].values():
            if attr['code'] == 'size':
                size_attribute = attr
                break
    
    target_id = None
    # Iterate through options to find the ID that matches "40"
    for option in size_attribute['options']:
        # We check if "40" is in the label (e.g., "40 (7.5M / 8.5W)")
        if option['label'].startswith(target_size_label + " "):
            target_id = option['id']
            print(f"Found ID for Size {target_size_label}: {target_id}")
            break
            
    if not target_id:
        print(f"Error: Size '{target_size_label}' not found in product options.")
        return

    # --- Step 2: Check Stock Status ---
    # The 'salable' object lists IDs that are currently purchasable (In Stock)
    # We check if our target_id is inside that list
    salable_items = stock_data.get('salable', {}).get('187', [])
    
    is_in_stock = False
    if target_id in salable_items:
        is_in_stock = True

    # --- Step 3: Trigger Alert or Log Status ---
    if is_in_stock:
        print("!!! IN STOCK - TRIGGERING ALERT !!!")
        print(f"Go buy it here: {url}")
        # Exit with error code 1 to force GitHub Actions to mark the run as "Failed"
        # This triggers the email notification to you.
        sys.exit(1) 
    else:
        print(f"Verified: Size {target_size_label} (ID {target_id}) is OUT of stock.")
        
        # Verification: Print ALL available sizes so you can confirm the data is real
        in_stock_labels = []
        for option in size_attribute['options']:
            if option['id'] in salable_items:
                in_stock_labels.append(option['label'])
        
        if in_stock_labels:
            print(f"Currently available sizes ({len(in_stock_labels)} total): {', '.join(in_stock_labels)}")
        else:
            print("Stock Status: NO SIZES are currently available.")

if __name__ == "__main__":
    check_stock()
