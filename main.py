#!/usr/local/bin/python
from time import strftime, sleep

from dotenv import load_dotenv
from gotify import Gotify
import os
import whois
from datetime import datetime


load_dotenv()
GOTIFY_URL = os.getenv("GOTIFY_URL")
GOTIFY_TOKEN = os.getenv("GOTIFY_TOKEN")
MONITOR_DOMAIN_001 = os.getenv("MONITOR_DOMAIN_001")


def send_alert(message, title):
    gotify = Gotify(
        base_url = GOTIFY_URL,
        app_token= GOTIFY_TOKEN,
    )
    try:
        result = gotify.create_message(
            f"{message}",
            title=f"GEA: {title}",
            priority=2,
        )
        print(f"Gotify alert sent to {GOTIFY_URL}")
        return True
    except Exception as e:
        print(f"Failed to call Gotify to: {GOTIFY_URL}.  Error is: {e}")
        return False

def get_domain_expires_days(domain):
    result = dict(date = datetime.now(), days = 0)

    try:
        print(f"Querying for domain {domain}")
        result["date"] = whois.whois(domain).expiration_date
    except Exception as e:
        print(f"Failed to call whois for: {domain}.  Error is: {e}")
        return False

    now = datetime.now()
    expires = datetime.strptime(str(result["date"]),"%Y-%m-%d %H:%M:%S")
    date_dif = expires - now
    result["days"] = date_dif.days
    return result


def main():
    SLEEP = 10  # hours
    DAYS = 10

    print(f"Starting GEA...")
    expires = get_domain_expires_days(MONITOR_DOMAIN_001)
    send_alert(
        f"Now monitoring domain {MONITOR_DOMAIN_001} which expires on {expires['days']} ;)",
        "GEA started"
    )

    while True:
        if DAYS > expires['days']:
            send_alert(
                f"NOTICE: {MONITOR_DOMAIN_001} is expiring in {expires['days']} days",
                f"{MONITOR_DOMAIN_001} Expiring"
            )
        print(f"Sleeping for {SLEEP} hours...")
        sleep(SLEEP * 60 * 60 )
        expires = get_domain_expires_days(MONITOR_DOMAIN_001)

main()
