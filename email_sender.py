import os
import re
import csv
import sys
import time
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def load_env():
    """
    Zero-dependency helper to load environment variables from a local .env file.
    """
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip('"').strip("'")

def get_email_template(restaurant_name, website, sender_name):
    """
    Returns a beautifully formatted HTML and Text cold outreach email in English.
    """
    subject = f"Quick suggestion for {restaurant_name}'s website"
    
    # Custom HTML content for maximum visual appeal
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #0a0a0c; color: #ffffff; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 24px; letter-spacing: 1px;">NORA AGENTS</h1>
            <p style="margin: 5px 0 0 0; font-size: 14px; color: #9c9c9c;">AI-Powered Restaurant Assistants</p>
        </div>
        <div style="padding: 20px; border: 1px solid #dddddd; border-top: none; border-radius: 0 0 8px 8px; background-color: #fafafa;">
            <p>Hi <strong>{restaurant_name}</strong> Team,</p>
            
            <p>I'm {sender_name}, a Toronto local and the founder of <a href="https://noraagents.com" style="color: #6366f1; text-decoration: none; font-weight: bold;">noraagents.com</a>. We help local GTA restaurants optimize their website guest experience and capture more table bookings using custom AI assistants.</p>
            
            <p>I was browsing your website (<a href="{website}" style="color: #6366f1; text-decoration: none;">{website.replace('https://', '').replace('http://', '').strip('/')}</a>) today and absolutely loved your concept and menu! However, I noticed that during peak dinner rushes or when your restaurant is closed, you don't have an automated AI assistant on your site to instantly answer guest questions and capture reservations.</p>
            
            <p>When phone lines are busy or staff are fully focused on the dining room, guests often drop off if their quick questions aren't answered instantly. We build smart, custom-trained chatbots that handle common inquiries (e.g., <i>"Do you have gluten-free options?", "Can I book a table for 4 tonight at 8 PM?", "Is there parking nearby?"</i>) and direct them straight into your existing booking system 24/7.</p>
            
            <p>I would love to design a custom chatbot trained on your menu and hours, and let you test it out on your site completely <strong>free for 7 days</strong> with zero setup fees or commitments.</p>
            
            <p>Would you be open to a quick 5-minute chat this week to see a live demo of what we can build for {restaurant_name}?</p>
            
            <p style="margin-top: 30px;">Best regards,<br>
            <strong>{sender_name}</strong><br>
            Founder, Nora Agents<br>
            <a href="https://noraagents.com" style="color: #6366f1; text-decoration: none;">noraagents.com</a></p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
Hi {restaurant_name} Team,

I'm {sender_name}, a Toronto local and the founder of noraagents.com. We help local GTA restaurants optimize their website guest experience and capture more table bookings using custom AI assistants.

I was browsing your website ({website}) today and absolutely loved your concept and menu! However, I noticed that during peak dinner rushes or when your restaurant is closed, you don't have an automated AI assistant on your site to instantly answer guest questions and capture reservations.

When phone lines are busy or staff are fully focused on the dining room, guests often drop off if their quick questions aren't answered instantly. We build smart, custom-trained chatbots that handle common inquiries (e.g., "Do you have gluten-free options?", "Can I book a table for 4 tonight at 8 PM?", "Is there parking nearby?") and direct them straight into your existing booking system 24/7.

I would love to design a custom chatbot trained on your menu and hours, and let you test it out on your site completely free for 7 days with zero setup fees or commitments.

Would you be open to a quick 5-minute chat this week to see a live demo of what we can build for {restaurant_name}?

Best regards,
{sender_name}
Founder, Nora Agents
noraagents.com
    """
    
    return subject, html_content, text_content

def update_csv_status(leads_file, restaurant_name, status, sent_date):
    """
    Safely updates the sent status and date of a restaurant in the local CSV file.
    """
    rows = []
    headers = []
    
    # Read entire file
    with open(leads_file, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        headers = next(reader)
        
        # Ensure Sent_Status and Sent_Date are in headers
        if "Sent_Status" not in headers:
            headers.append("Sent_Status")
        if "Sent_Date" not in headers:
            headers.append("Sent_Date")
            
        status_idx = headers.index("Sent_Status")
        date_idx = headers.index("Sent_Date")
        
        for row in reader:
            # Pad row if it has fewer elements than headers
            while len(row) < len(headers):
                row.append("")
                
            # If matches, update
            # Column index 0 is Restaurant Name in lead_finder output
            if row[0].strip() == restaurant_name.strip():
                row[status_idx] = status
                row[date_idx] = sent_date
            rows.append(row)
            
    # Write back to file
    with open(leads_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)

def main():
    print("=" * 60)
    print("        NORA AGENTS - COLD OUTREACH EMAIL SENDER        ")
    print("        (With Smart State Tracking & Spam Throttling)    ")
    print("=" * 60)
    
    load_env()
    
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    try:
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    except ValueError:
        smtp_port = 587
        
    smtp_email = os.environ.get("SMTP_EMAIL", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    sender_name = os.environ.get("SMTP_FROM_NAME", "Istikbal")
    
    # Validation check
    if not smtp_email or not smtp_password:
        print("[!] ERROR: SMTP_EMAIL and SMTP_PASSWORD missing in .env!")
        return
        
    leads_file = "toronto_restaurant_leads.csv"
    if not os.path.exists(leads_file):
        print(f"[!] ERROR: '{leads_file}' not found.")
        return
        
    # Read custom limits from command line arguments
    # Usage: python email_sender.py --send --limit 50
    limit = 99999
    for arg in sys.argv:
        if "--limit" in arg:
            try:
                limit = int(sys.argv[sys.argv.index(arg) + 1])
                print(f"[INFO] Campaign limit set to: {limit} emails")
            except Exception:
                pass
                
    # Read hot prospects from CSV, filtering out already sent ones and garbage emails
    prospects = []
    total_already_sent = 0
    
    with open(leads_file, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        
        # Check if headers exist
        fieldnames = reader.fieldnames
        has_sent_column = "Sent_Status" in fieldnames if fieldnames else False
        
        for row in reader:
            # Count if already sent successfully
            if has_sent_column and row.get("Sent_Status") == "SENT":
                total_already_sent += 1
                continue
                
            if row.get("Status") == "No Chatbot (HOT PROSPECT)":
                emails_str = row.get("Email", "N/A")
                if emails_str and emails_str != "N/A":
                    # Split comma-separated emails and clean them
                    emails = [e.strip() for e in emails_str.split(",") if "@" in e]
                    
                    # Filter out Wix templates / Sentries / mock placeholders
                    clean_emails = []
                    for e in emails:
                        e_low = e.lower()
                        garbage_signatures = [
                            "sentry", "wixpress", "example.com", "mysite.com", 
                            "domain.com", "localoria.com", "your@email.com", 
                            "yourdomain.com", "email.com", "xxx@xxx.com"
                        ]
                        if not any(x in e_low for x in garbage_signatures):
                            clean_emails.append(e)
                            
                    if clean_emails:
                        prospects.append({
                            "name": row["Restaurant Name"],
                            "website": row["Website"],
                            "emails": clean_emails
                        })
                        
    print(f"[+] Total cold emails sent in this campaign so far: {total_already_sent} / 1500")
    
    if total_already_sent >= 1500:
        print("=" * 60)
        print("[+] CAMPAIGN TARGET REACHED! 1500 cold emails have been successfully sent.")
        print("[+] Automatically stopping nightly campaign. Evaluation time!")
        print("=" * 60)
        return
        
    if not prospects:
        print("[+] STATUS: No new unsent prospects found. Campaign complete!")
        return
        
    # Apply limit
    active_prospects = prospects[:limit]
    print(f"[+] Total prospects available: {len(prospects)}")
    print(f"[+] Active prospects selected for this run: {len(active_prospects)}")
    
    # Dry run check
    dry_run = True
    if len(sys.argv) > 1 and "--send" in sys.argv:
        dry_run = False
        print("[WARNING] LIVE SEND MODE IS ACTIVE! Sending actual emails.")
    else:
        print("[INFO] MODE: DRY-RUN (Simulation). Add '--send' to send live.")
        
    print("\n" + "-" * 50)
    
    try:
        # Establish connection if not in dry-run
        server = None
        if not dry_run:
            print("[*] Connecting to SMTP server...")
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_email, smtp_password)
            print("[+] SMTP Connection and login successful!\n")
            
        success_count = 0
        for idx, prospect in enumerate(active_prospects, start=1):
            name = prospect["name"]
            web = prospect["website"]
            target_emails = prospect["emails"]
            
            subject, html, text = get_email_template(name, web, sender_name)
            
            print(f"[{idx}/{len(active_prospects)}] Restaurant: {name}")
            print(f"    Recipients: {', '.join(target_emails)}")
            print(f"    Subject: {subject}")
            
            if dry_run:
                print("    [SIMULATION] Email draft created successfully.")
            else:
                try:
                    # Create MIME message
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = subject
                    msg["From"] = f"{sender_name} <{smtp_email}>"
                    msg["To"] = target_emails[0]
                    if len(target_emails) > 1:
                        msg["Cc"] = ", ".join(target_emails[1:])
                        
                    msg.attach(MIMEText(text, "plain", "utf-8"))
                    msg.attach(MIMEText(html, "html", "utf-8"))
                    
                    # Combine all recipients for SMTP
                    all_recipients = target_emails
                    
                    server.sendmail(smtp_email, all_recipients, msg.as_string())
                    print("    [OK] Email sent successfully!")
                    
                    # Save state tracking live to CSV!
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    update_csv_status(leads_file, name, "SENT", now_str)
                    print("    [STATE] CSV updated to SENT.")
                    
                    success_count += 1
                    
                    # Anti-spam delay between emails
                    time.sleep(4)
                except Exception as ex:
                    print(f"    [FAIL] Sending error: {ex}")
                    
            print("-" * 50)
            
        if server:
            server.quit()
            
        print("\n" + "=" * 60)
        if dry_run:
            print(f"[+] SIMULATION COMPLETE! Ready to send {len(active_prospects)} emails.")
        else:
            print(f"[+] SEND COMPLETE! Successfully sent: {success_count} / {len(active_prospects)}")
        print("=" * 60)
        
    except Exception as e:
        print(f"[!] SMTP Error occurred: {e}")
        if server:
            try:
                server.quit()
            except Exception:
                pass

if __name__ == "__main__":
    main()
