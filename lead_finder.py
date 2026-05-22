import os
import re
import csv
import sys
import time
import requests

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
                
        # Remove duplicates
        seen_sites = set()
        unique_restaurants = []
        for r in restaurants:
            clean_url = r["website"].replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
            if clean_url not in seen_sites:
                seen_sites.add(clean_url)
                unique_restaurants.append(r)
                
        print(f"[+] Cleaned duplicates. Found {len(unique_restaurants)} unique restaurant websites.")
        return unique_restaurants
        
    except Exception as e:
        print(f"[!] Error querying OpenStreetMap: {e}")
        return []

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
        # Fetch the homepage
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
    print("      NORA AGENTS — TORONTO GTA RESTAURANT LEAD FINDER      ")
    print("=" * 60)
    
    # Parse limits
    limit = 20  # Safe default for quick testing
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
        
    total_leads_available = len(raw_leads)
    
    if limit is not None:
        raw_leads = raw_leads[:limit]
        print(f"[*] Applying screening limit: checking first {limit} out of {total_leads_available} available leads.")
        print("[TIP] Tip: Run 'python lead_finder.py --limit=all' to screen all restaurants or 'python lead_finder.py --limit=100' for a custom number.")
    else:
        print(f"[*] Screening all {total_leads_available} available leads in GTA.")

    # Step 2: Screen websites for chatbots
    output_file = "toronto_restaurant_leads.csv"
    fieldnames = ["Restaurant Name", "Website", "Phone", "Address", "City", "Status", "Chatbot Detected"]
    
    print("\n[*] Starting chatbot screening. This might take several minutes...")
    print(f"[*] Results will be saved to: {output_file}\n")
    
    leads_saved = 0
    total_leads = len(raw_leads)
    
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        
        for idx, lead in enumerate(raw_leads, start=1):
            name = lead["name"]
            url = lead["website"]
            phone = lead["phone"]
            addr = lead["address"]
            city = lead["city"]
            
            print(f"[{idx}/{total_leads}] Checking: {name} ({url})...", end="", flush=True)
            
            has_bot, bot_type = check_for_chatbot(url)
            
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
                print(" [OK] NO CHATBOT!")
                leads_saved += 1
                
            writer.writerow({
                "Restaurant Name": name,
                "Website": url,
                "Phone": phone,
                "Address": addr,
                "City": city,
                "Status": status,
                "Chatbot Detected": chatbot_status
            })
            
            # Short courtesy pause
            time.sleep(0.5)
            
    print("\n" + "=" * 60)
    print(f"[+] SCREENING COMPLETE!")
    print(f"[+] Total restaurants checked: {total_leads}")
    print(f"[+] Hot prospects (with website, NO chatbot) saved: {leads_saved}")
    print(f"[+] Saved leads to CSV file: {output_file}")
    print("=" * 60)
    print("\n[TIP] TIP: Open 'toronto_restaurant_leads.csv' and filter by 'Status' = 'No Chatbot (HOT PROSPECT)'.")
    print("[TIP] These are the restaurants you should pitch text chatbots to!")

if __name__ == "__main__":
    main()
