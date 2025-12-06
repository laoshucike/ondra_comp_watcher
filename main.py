import sys
from playwright.sync_api import sync_playwright

def check_stock():
    url = "https://www.lasportivausa.com/ondra-comp.html"
    target_size = "40"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print(f"Checking {url}...")
        page.goto(url)
        page.wait_for_load_state("networkidle")

        try:
            # 1. Click the 'Size' Dropdown
            # We try the standard text first, then the generic class
            try:
                page.get_by_text("Size", exact=True).click()
            except:
                page.locator(".super-attribute-select").first.click()
            
            # 2. Select Size 40
            page.get_by_text(target_size, exact=True).click()
            
            # 3. Wait 2 seconds for the "Add to Cart" button to refresh
            page.wait_for_timeout(2000)
            
            # 4. Take a screenshot for proof
            page.screenshot(path="proof.png")
            
            # 5. Check the text
            content = page.content()
            
            if "Add to Cart" in content:
                print("!!! IN STOCK - TRIGGERING ALERT !!!")
                # This 'exit(1)' tells GitHub the script FAILED.
                # GitHub will send you a "Workflow Failed" email immediately.
                sys.exit(1) 
            else:
                print(f"Verified: Size {target_size} is out of stock.")
                
        except Exception as e:
            # If the script crashes for a real reason (like the site is down),
            # we also want to know, so we let it fail.
            print(f"Error checking stock: {e}")
            raise e
            
        browser.close()

if __name__ == "__main__":
    check_stock()