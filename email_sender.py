import os
import re
import csv
import sys
import time
import smtplib
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
    Returns a beautifully formatted HTML and Text cold outreach email.
    """
    subject = f"{restaurant_name} + Toronto Akşamları İçin Ufak Bir Öneri 🍕"
    
    # Custom HTML content for maximum visual appeal
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #0a0a0c; color: #ffffff; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 24px; letter-spacing: 1px;">NORA AGENTS</h1>
            <p style="margin: 5px 0 0 0; font-size: 14px; color: #9c9c9c;">Yapay Zeka Destekli Restoran Asistanları</p>
        </div>
        <div style="padding: 20px; border: 1px solid #dddddd; border-top: none; border-radius: 0 0 8px 8px; background-color: #fafafa;">
            <p>Merhaba <strong>{restaurant_name}</strong> ekibi,</p>
            
            <p>Ben {sender_name}, Toronto'da yaşıyorum ve yerel restoranların dijital dönüşüm süreçlerine ve müşteri deneyimlerine yardımcı olan <a href="https://noraagents.com" style="color: #6366f1; text-decoration: none; font-weight: bold;">noraagents.com</a>'un kurucusuyum.</p>
            
            <p>Sıcak Toronto akşamlarında restoranınızın ne kadar yoğun olabildiğini tahmin edebiliyorum. Web sitenizi (<a href="{website}" style="color: #6366f1; text-decoration: none;">{website.replace('https://', '').replace('http://', '').strip('/')}</a>) incelediğimde harika menünüz ve konseptiniz dikkatimi çekti. Ancak sitenizde, yoğun saatlerde veya restoranınız kapalıyken gelen müşteri sorularını yanıtlayıp onları masaya çekecek akıllı bir yapay zeka asistanı (Chatbot) olmadığını fark ettim.</p>
            
            <p>Telefonların sürekli çaldığı veya garsonların en yoğun olduğu anlarda, potansiyel müşterilerin anlık sorularını (<i>"Glutensiz seçeneğiniz var mı?", "Bu akşam 20:00 için yer var mı?", "Otoparkınız mevcut mu?"</i>) anında yanıtlayıp doğrudan rezervasyon kanallarınıza yönlendiren Nora Agents chatbot'larını geliştiriyoruz.</p>
            
            <p>Sizin için web sitenizin içeriğiyle ve menünüzle eğitilmiş özel bir chatbot tasarlayıp <strong>7 gün boyunca tamamen ücretsiz</strong> denemenizi sağlamak isterim. Üstelik kurulum ücreti almadan, 5 dakika içinde sitenize entegre edebiliriz.</p>
            
            <p>Bu hafta detayları konuşmak ve size özel hazırlayabileceğimiz demoyu göstermek için kısa bir telefon görüşmesi yapabilir miyiz?</p>
            
            <p style="margin-top: 30px;">Sevgiler,<br>
            <strong>{sender_name}</strong><br>
            Kurucu, Nora Agents<br>
            <a href="https://noraagents.com" style="color: #6366f1; text-decoration: none;">noraagents.com</a></p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
Merhaba {restaurant_name} ekibi,

Ben {sender_name}, Toronto'da yaşıyorum ve yerel restoranların dijital dönüşüm süreçlerine ve müşteri deneyimlerine yardımcı olan noraagents.com'un kurucusuyum.

Sıcak Toronto akşamlarında restoranınızın ne kadar yoğun olabildiğini tahmin edebiliyorum. Web sitenizi ({website}) incelediğimde harika menünüz dikkatimi çekti. Ancak sitenizde, yoğun saatlerde veya restoranınız kapalıyken gelen müşteri sorularını yanıtlayıp onları masaya çekecek akıllı bir yapay zeka asistanı (Chatbot) olmadığını fark ettim.

Telefonların sürekli çaldığı veya garsonların en yoğun olduğu anlarda, potansiyel müşterilerin anlık sorularını ("Glutensiz seçeneğiniz var mı?", "Bu akşam 20:00 için yer var mı?", "Otoparkınız mevcut mu?") anında yanıtlayıp doğrudan rezervasyon kanallarınıza yönlendiren Nora Agents chatbot'larını geliştiriyoruz.

Sizin için web sitenizin içeriğiyle ve menünüzle eğitilmiş özel bir chatbot tasarlayıp 7 gün boyunca tamamen ücretsiz denemenizi sağlamak isterim. Üstelik kurulum ücreti almadan, 5 dakika içinde sitenize entegre edebiliriz.

Bu hafta detayları konuşmak ve size özel hazırlayabileceğimiz demoyu göstermek için kısa bir telefon görüşmesi yapabilir miyiz?

Sevgiler,
{sender_name}
Kurucu, Nora Agents
noraagents.com
    """
    
    return subject, html_content, text_content

def main():
    print("=" * 60)
    print("        NORA AGENTS - COLD OUTREACH EMAIL SENDER        ")
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
        print("[!] HATA: SMTP_EMAIL ve SMTP_PASSWORD cevre degiskenleri .env dosyasinda bulunamadi!")
        print("[!] Lutfen bir '.env' dosyasi olusturun ve bilgilerinizi doldurun.")
        print("[TIP] Ornek format:")
        print("    SMTP_HOST=smtp.gmail.com")
        print("    SMTP_PORT=587")
        print("    SMTP_EMAIL=your-email@gmail.com")
        print("    SMTP_PASSWORD=your-app-password")
        print("    SMTP_FROM_NAME=Istikbal")
        return
        
    leads_file = "toronto_restaurant_leads.csv"
    if not os.path.exists(leads_file):
        print(f"[!] HATA: '{leads_file}' bulunamadi. Lutfen once lead finder scriptini calistirin.")
        return
        
    # Read hot prospects
    prospects = []
    with open(leads_file, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row.get("Status") == "No Chatbot (HOT PROSPECT)":
                emails_str = row.get("Email", "N/A")
                if emails_str and emails_str != "N/A":
                    # Split comma-separated emails and clean them
                    emails = [e.strip() for e in emails_str.split(",") if "@" in e]
                    # Filter out Wix Sentry / false positive emails
                    clean_emails = []
                    for e in emails:
                        if not any(x in e.lower() for x in ["sentry", "wixpress", "example.com", "mysite.com", "domain.com", "localoria.com"]):
                            clean_emails.append(e)
                            
                    if clean_emails:
                        prospects.append({
                            "name": row["Restaurant Name"],
                            "website": row["Website"],
                            "emails": clean_emails
                        })
                        
    if not prospects:
        print("[!] Gonderim yapilabilecek e-postali hicbir sicak aday bulunamadi.")
        return
        
    print(f"[+] Toplam {len(prospects)} adet restoran sicak adayi e-postalariyla hazirlandi.")
    print("[*] Gonderime baslamak icin onay bekleniyor...")
    
    # Dry run check
    dry_run = True
    if len(sys.argv) > 1 and "--send" in sys.argv:
        dry_run = False
        print("[WARNING] DIKKAT: Canli gonderim modu aktif! E-postalar gercek adreslere gonderilecek.")
    else:
        print("[INFO] MOD: DRY-RUN (Simulasyon). E-postalar gonderilmeyecek, sadece taslaklar yazdirilacak.")
        print("[TIP] Gercek gonderim icin: 'python email_sender.py --send' komutunu kullanin.")
        
    print("\n" + "-" * 50)
    
    try:
        # Establish connection if not in dry-run
        server = None
        if not dry_run:
            print("[*] SMTP sunucusuna baglaniliyor...")
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_email, smtp_password)
            print("[+] SMTP baglantisi ve giris basarili!\n")
            
        success_count = 0
        for idx, prospect in enumerate(prospects, start=1):
            name = prospect["name"]
            web = prospect["website"]
            target_emails = prospect["emails"]
            
            subject, html, text = get_email_template(name, web, sender_name)
            
            print(f"[{idx}/{len(prospects)}] Restoran: {name}")
            print(f"    Alicilar: {', '.join(target_emails)}")
            print(f"    Konu: {subject}")
            
            if dry_run:
                print("    [SIMULATION] E-posta basariyla taslak olarak olusturuldu.")
            else:
                try:
                    # Create MIME message
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = subject
                    msg["From"] = f"{sender_name} <{smtp_email}>"
                    msg["To"] = target_emails[0] # Primary recipient
                    if len(target_emails) > 1:
                        msg["Cc"] = ", ".join(target_emails[1:])
                        
                    msg.attach(MIMEText(text, "plain", "utf-8"))
                    msg.attach(MIMEText(html, "html", "utf-8"))
                    
                    # Combine all recipients for SMTP sending
                    all_recipients = target_emails
                    
                    server.sendmail(smtp_email, all_recipients, msg.as_string())
                    print("    [OK] E-posta basariyla gonderildi!")
                    success_count += 1
                    
                    # Anti-spam delay between emails
                    time.sleep(3)
                except Exception as ex:
                    print(f"    [FAIL] Gonderim hatasi: {ex}")
                    
            print("-" * 50)
            
        if server:
            server.quit()
            
        print("\n" + "=" * 60)
        if dry_run:
            print(f"[+] SIMULASYON TAMAMLANDI! {len(prospects)} adet taslak basariyla incelendi.")
            print("[TIP] Gercek gonderime hazir oldugunuzda '.env' dosyanizi doldurun ve:")
            print("      'python email_sender.py --send' komutunu calistirin.")
        else:
            print(f"[+] GONDERIM TAMAMLANDI! Basariyla Gonderilen: {success_count} / {len(prospects)}")
        print("=" * 60)
        
    except Exception as e:
        print(f"[!] SMTP Baglanti hatasi: {e}")
        if server:
            try:
                server.quit()
            except Exception:
                pass

if __name__ == "__main__":
    main()
