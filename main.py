import sys
import json
import re
import requests
from bs4 import BeautifulSoup

def check_stock():
    url = "https://www.lasportivausa.com/ondra-comp.html"
    target_size_label = "40" # The size you want (must match the label in the dropdown)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    print(f"Fetching {url}...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Failed to load page (Status code {response.status_code})")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # We are looking for the script that contains "jsonConfig"
    # This script contains all the product data (IDs, Labels, Stock status)
    scripts = soup.find_all('script', type='text/x-magento-init')
    
    stock_data = None
    
    for script in scripts:
        if 'jsonConfig' in script.string:
            try:
                # The script string is a JSON object, but we need to parse it carefully
                data = json.loads(script.string)
                # Navigate down to the jsonConfig object
                # Structure: [data-role=swatch-options] -> Magento_Swatches/js/swatch-renderer -> jsonConfig
                stock_data = data['[data-role=swatch-options]']['Magento_Swatches/js/swatch-renderer']['jsonConfig']
                break
            except (KeyError, json.JSONDecodeError):
                continue

    if not stock_data:
        print("Error: Could not find stock data in page source.")
        return

    # --- Step 1: Find the ID for Size 40 ---
    # The 'attributes' dictionary holds the mapping of ID to Label
    # We look for attribute code 'size' (ID 187 in your source)
    size_attribute = stock_data['attributes'].get('187') # 187 is the standard ID for 'size' on this site
    
    if not size_attribute:
        # Fallback: Search all attributes if '187' changes
        for attr in stock_data['attributes'].values():
            if attr['code'] == 'size':
                size_attribute = attr
                break
    
    target_id = None
    for option in size_attribute['options']:
        # We check if "40" is in the label (e.g., "40 (7.5M / 8.5W)")
        if option['label'].startswith(target_size_label + " "):
            target_id = option['id']
            print(f"Found ID for Size {target_size_label}: {target_id}")
            break
            
    if not target_id:
        print(f"Error: Size {target_size_label} not found in product options.")
        return

    # --- Step 2: Check Stock Status ---
    # The 'salable' object lists IDs that are currently purchasable
    # We check if our target_id is inside the list for attribute 187
    
    # Note: 'salable' key contains the IN STOCK items
    salable_items = stock_data.get('salable', {}).get('187', [])
    
    # In your source, salable is a dict where keys are attribute IDs and values are lists of product IDs
    # But sometimes Magento formats it differently. Let's check the index.
    
    # Looking at your source: "index" maps Product ID -> Attribute Option ID
    # "salable" maps Attribute ID -> List of Attribute Option IDs that are in stock
    
    is_in_stock = False
    
    # Method A: Check 'salable' list
    if target_id in salable_items:
        is_in_stock = True
    
    # Method B: Double check via the specific 'optionPrices' or 'index' if Salable is ambiguous
    # (Method A is usually sufficient for Magento 2)

    if is_in_stock:
        print("!!! IN STOCK - TRIGGERING ALERT !!!")
        sys.exit(1) # Fail the workflow to send email
    else:
        print(f"Verified: Size {target_size_label} (ID {target_id}) is OUT of stock.")
        # Debug: Print what IS in stock to prove it works
        in_stock_labels = []
        for option in size_attribute['options']:
            if option['id'] in salable_items:
                in_stock_labels.append(option['label'])
        print(f"Currently available sizes: {', '.join(in_stock_labels[:5])}...")

if __name__ == "__main__":
    check_stock()
