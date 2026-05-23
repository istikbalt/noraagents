import os
import re
import csv
import sys
import time
import requests
from urllib.parse import urljoin

def get_gta_restaurants():
    """
    Fetches restaurants in the Greater Toronto Area (GTA) from the OpenStreetMap Overpass API.
    Returns a list of dicts with name, website, phone, and city.
    """
    print("[*] Connecting to OpenStreetMap Overpass API...")
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    query = """
    [out:json][timeout:180];
    area["name"="Toronto"]->.toronto;
    area["name"="Mississauga"]->.mississauga;
    area["name"="Brampton"]->.brampton;
    area["name"="Markham"]->.markham;
    area["name"="Vaughan"]->.vaughan;
    area["name"="Richmond Hill"]->.richmond_hill;
    area["name"="Oakville"]->.oakville;
    (
      node["amenity"="restaurant"]["website"](area.toronto);
      way["amenity"="restaurant"]["website"](area.toronto);
      node["amenity"="restaurant"]["website"](area.mississauga);
      way["amenity"="restaurant"]["website"](area.mississauga);
      node["amenity"="restaurant"]["website"](area.brampton);
      way["amenity"="restaurant"]["website"](area.brampton);
      node["amenity"="restaurant"]["website"](area.markham);
      way["amenity"="restaurant"]["website"](area.markham);
      node["amenity"="restaurant"]["website"](area.vaughan);
      way["amenity"="restaurant"]["website"](area.vaughan);
      node["amenity"="restaurant"]["website"](area.richmond_hill);
      way["amenity"="restaurant"]["website"](area.richmond_hill);
      node["amenity"="restaurant"]["website"](area.oakville);
      way["amenity"="restaurant"]["website"](area.oakville);
    );
    out tags;
    """
    
    headers = {
        'User-Agent': 'NoraAgentsLeadFinder/1.0'
    }
    try:
        response = requests.get(overpass_url, params={'data': query}, headers=headers, timeout=120)
        if response.status_code != 200:
            print(f"[!] Overpass API returned status code {response.status_code}")
            return []
            
        data = response.json()
        elements = data.get("elements", [])
        print(f"[+] Successfully fetched {len(elements)} restaurants with websites from OpenStreetMap!")
        
        restaurants = []
        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name", "Unnamed Restaurant")
            website = tags.get("website", "").strip()
            
            # Normalize website URL
            if website and not website.startswith("http"):
                website = "http://" + website
                
            phone = tags.get("phone", tags.get("contact:phone", "N/A"))
            street = tags.get("addr:street", "")
            housenumber = tags.get("addr:housenumber", "")
            city = tags.get("addr:city", "GTA")
            
            address = f"{housenumber} {street}".strip() if street else "N/A"
            
            if website:
                restaurants.append({
                    "name": name,
                    "website": website,
                    "phone": phone,
                    "address": address,
                    "city": city
                })
                
        # Remove duplicates within fetched elements
        seen_sites = set()
        unique_restaurants = []
        for r in restaurants:
            clean_url = r["website"].replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
            if clean_url not in seen_sites:
                seen_sites.add(clean_url)
                unique_restaurants.append(r)
                
        print(f"[+] Cleaned duplicates. Found {len(unique_restaurants)} unique restaurant websites in GTA.")
        return unique_restaurants
        
    except Exception as e:
        print(f"[!] Error querying OpenStreetMap: {e}")
        return []

def find_emails_on_website(url):
    """
    Scrapes the homepage and common subpages (contact, about, etc.) of a website
    to find email addresses.
    Returns a string of unique emails separated by commas, or "N/A" if none found.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    emails = set()
    
    # Standard email regex pattern
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    try:
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            html = response.text
            found = re.findall(email_pattern, html)
            for email in found:
                email_lower = email.lower()
                # Exclude static assets or image files that match regex incorrectly
                if not any(email_lower.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.css', '.js']):
                    emails.add(email.strip())
            
            # Find links that might be contact or about pages
            contact_links = []
            href_patterns = [r'href=["\']([^"\']*(?:contact|about|info|reach|connect)[^"\']*)["\']']
            for pattern in href_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    if match.startswith('http'):
                        contact_links.append(match)
                    elif match.startswith('/'):
                        contact_links.append(urljoin(url, match))
            
            # De-duplicate contact links and limit to top 3 to keep it fast
            contact_links = list(set(contact_links))[:3]
            
            # If no contact links detected, try guessing standard paths
            if not contact_links:
                for path in ['contact', 'contact-us', 'about', 'about-us', 'info']:
                    contact_links.append(urljoin(url, path))
            
            # Fetch contact pages to scan for emails
            for link in contact_links:
                try:
                    res = requests.get(link, headers=headers, timeout=8, allow_redirects=True)
                    if res.status_code == 200:
                        found_sub = re.findall(email_pattern, res.text)
                        for email in found_sub:
                            email_lower = email.lower()
                            if not any(email_lower.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.css', '.js']):
                                emails.add(email.strip())
                except Exception:
                    continue
                    
    except Exception:
        pass
        
    if emails:
        return ", ".join(sorted(list(emails)))
    return "N/A"

def check_for_chatbot(url):
    """
    Pings the website and checks the HTML content for popular chatbot signatures.
    Returns (has_chatbot, chatbot_name_or_empty)
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # Common chatbot widget script signatures
    chatbot_signatures = {
        r"stammer\.ai": "Stammer.ai",
        r"chatbubble\.js": "Stammer.ai / Generic Bubble",
        r"tidio\.co": "Tidio",
        r"code\.tidio\.co": "Tidio",
        r"js\.intercomcdn\.com": "Intercom",
        r"widget\.intercom\.io": "Intercom",
        r"drift\.com": "Drift",
        r"embed\.tawk\.to": "Tawk.to",
        r"crisp\.chat": "Crisp",
        r"client\.crisp\.chat": "Crisp",
        r"js-agent\.newrelic\.com": "New Relic",
        r"js\.hs-scripts\.com": "HubSpot Chat",
        r"chatbase\.co/embed": "Chatbase",
        r"botpress\.cloud": "Botpress",
        r"voiceflow\.com": "Voiceflow",
        r"window\.chatbase": "Chatbase",
        r"livechatinc\.com": "LiveChat",
        r"chat\.js": "Generic Chat",
        r"chatbot": "Generic Chat",
        r"embed\.tawk": "Tawk.to"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=12, allow_redirects=True)
        if response.status_code != 200:
            return False, "Unreachable (Status Code)"
            
        html = response.text.lower()
        
        # Scan for signatures
        for pattern, name in chatbot_signatures.items():
            if re.search(pattern.lower(), html):
                return True, name
                
        return False, ""
        
    except requests.exceptions.Timeout:
        return False, "Timeout"
    except requests.exceptions.RequestException:
        return False, "Connection Error"
    except Exception as e:
        return False, f"Error: {str(e)[:30]}"

def main():
    print("=" * 60)
    print("      NORA AGENTS — DATABASE-FIRST RESTAURANT LEAD FINDER      ")
    print("=" * 60)
    
    output_file = "toronto_restaurant_leads.csv"
    
    # Read existing leads to prevent duplicate scraping and preserve sent logs
    existing_websites = set()
    total_already_sent = 0
    file_exists = os.path.exists(output_file)
    headers_exist = False
    
    if file_exists:
        print("[*] Loading existing leads from database to prevent duplicate scraping...")
        try:
            with open(output_file, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames:
                    headers_exist = True
                    for row in reader:
                        web = row.get("Website", "").strip()
                        if web:
                            clean_url = web.replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
                            existing_websites.add(clean_url)
                        if row.get("Sent_Status") == "SENT":
                            total_already_sent += 1
            print(f"[+] Loaded {len(existing_websites)} existing websites from database.")
            print(f"[+] Total cold emails sent in this campaign so far: {total_already_sent} / 1500")
            if total_already_sent >= 1500:
                print("=" * 60)
                print("[+] CAMPAIGN TARGET REACHED! 1500 cold emails have been successfully sent.")
                print("[+] Stopping new scraping. Evaluation time!")
                print("=" * 60)
                return
        except Exception as e:
            print(f"[!] Warning reading existing database: {e}")
            
    # Parse screening limits
    limit = 50  # Default limit for new leads
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.startswith("--limit="):
                val = arg.split("=")[1]
                if val.lower() == "all":
                    limit = None
                else:
                    try:
                        limit = int(val)
                    except ValueError:
                        pass
            elif arg == "--limit" and len(sys.argv) > sys.argv.index(arg) + 1:
                val = sys.argv[sys.argv.index(arg) + 1]
                if val.lower() == "all":
                    limit = None
                else:
                    try:
                        limit = int(val)
                    except ValueError:
                        pass

    # Step 1: Get restaurants in GTA with websites
    raw_leads = get_gta_restaurants()
    if not raw_leads:
        print("[!] No leads found. Exiting.")
        return
        
    # Filter out already existing leads before scraping!
    new_leads = []
    for lead in raw_leads:
        clean_url = lead["website"].replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
        if clean_url not in existing_websites:
            new_leads.append(lead)
            
    print(f"[+] Out of {len(raw_leads)} fetched restaurants, {len(new_leads)} are BRAND NEW leads.")
    
    if not new_leads:
        print("[+] STATUS: All fetched leads already exist in database. No new scraping needed!")
        return
        
    if limit is not None:
        new_leads = new_leads[:limit]
        print(f"[*] Applying limit: scraping first {limit} new leads out of {len(new_leads)} available.")
    else:
        print(f"[*] Scraping all {len(new_leads)} new leads.")

    # Step 2: Screen websites for chatbots and append to database
    fieldnames = [
        "Restaurant Name", "Website", "Email", "Phone", "Address", "City", 
        "Status", "Chatbot Detected", "Sent_Status", "Sent_Date"
    ]
    
    print("\n[*] Starting chatbot screening and email harvesting for new leads...")
    print(f"[*] Results will be appended directly to: {output_file}\n")
    
    leads_saved = 0
    total_leads = len(new_leads)
    
    # Open in append mode if file exists, otherwise write mode
    write_mode = "a" if file_exists else "w"
    
    with open(output_file, mode=write_mode, newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        # If writing a brand new file, write header
        if not file_exists or not headers_exist:
            writer.writeheader()
            
        for idx, lead in enumerate(new_leads, start=1):
            name = lead["name"]
            url = lead["website"]
            phone = lead["phone"]
            addr = lead["address"]
            city = lead["city"]
            
            print(f"[{idx}/{total_leads}] Checking new: {name} ({url})...", end="", flush=True)
            
            has_bot, bot_type = check_for_chatbot(url)
            email = "N/A"
            
            if "Unreachable" in bot_type or "Timeout" in bot_type or "Connection Error" in bot_type:
                status = "Unreachable Website"
                chatbot_status = "N/A"
                print(f" [FAIL] {bot_type}")
            elif has_bot:
                status = "Has Chatbot"
                chatbot_status = bot_type
                print(f" [BOT] Yes ({bot_type})")
            else:
                status = "No Chatbot (HOT PROSPECT)"
                chatbot_status = "None"
                print(" [OK] NO CHATBOT! Hunting for email...", end="", flush=True)
                email = find_emails_on_website(url)
                print(f" Found: {email}")
                leads_saved += 1
                
            writer.writerow({
                "Restaurant Name": name,
                "Website": url,
                "Email": email,
                "Phone": phone,
                "Address": addr,
                "City": city,
                "Status": status,
                "Chatbot Detected": chatbot_status,
                "Sent_Status": "",  # Empty on new harvest
                "Sent_Date": ""     # Empty on new harvest
            })
            
            # Short courtesy pause
            time.sleep(0.5)
            
    print("\n" + "=" * 60)
    print(f"[+] HARVEST COMPLETE!")
    print(f"[+] New prospects checked: {total_leads}")
    print(f"[+] New hot prospects added: {leads_saved}")
    print(f"[+] All data saved live in: {output_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
