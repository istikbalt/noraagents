@echo off
:: ============================================================
::         NORA AGENTS - NIGHTLY AUTOMATED CAMPAIGN RUNNER
:: ============================================================
:: This script automatically harvests new leads and sends up to 100
:: cold outreach emails, updating the local state database.

cd /d "C:\Users\istik\.gemini\antigravity\scratch\noraagents"

echo [%date% %time%] ========================================== >> campaign_history.log
echo [%date% %time%] STARTING NIGHTLY CAMPAIGN RUN >> campaign_history.log

echo [*] Step 1: Harvesting 150 new restaurant leads...
python lead_finder.py --limit 150 >> campaign_history.log 2>&1

echo [*] Step 2: Sending up to 100 cold emails to unsent hot prospects...
python email_sender.py --send --limit 100 >> campaign_history.log 2>&1

echo [%date% %time%] CAMPAIGN RUN COMPLETED SUCCESSFULLY >> campaign_history.log
echo ========================================================== >> campaign_history.log

echo [+] Campaign run completed successfully! Logs saved to 'campaign_history.log'.
