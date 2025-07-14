#!/usr/local/bin/python
from time import strftime, sleep

from dotenv import load_dotenv
from gotify import Gotify
import os
import whois
from datetime import datetime


def get_domains():
    MONITOR_DOMAINS = os.getenv("MONITOR_DOMAINS")
    domain_list = MONITOR_DOMAINS.split(",")
    domains = {}
    for domain in domain_list:
        domains[domain] = {}
        domains[domain]["days"] = 0
    return domains


def send_alert(message, title):
    gotify_url = os.getenv("GOTIFY_URL")
    gotify = Gotify(
        base_url = gotify_url,
        app_token = os.getenv("GOTIFY_TOKEN"),
    )
    try:
        result = gotify.create_message(
            f"{message}",
            title=f"GEA: {title}",
            priority=2,
        )
        print(f"INFO: Gotify alert sent to {gotify_url}")
        return True
    except Exception as e:
        print(f"WARNING: Error in send_alert() call. Failed to call Gotify at: {gotify_url}.  Error is: {e}")
        return False


def expires_days(domain):
    result = dict(date = datetime.now(), days = 0)

    try:
        print(f"INFO: Querying for domain {domain}")
        result["date"] = whois.whois(domain).expiration_date
    except Exception as e:
        print(f"WARNING: Failed to call whois for: {domain}.  Error is: {e}")
        return False

    now = datetime.now()
    try:
        expires = datetime.strptime(str(result["date"]),"%Y-%m-%d %H:%M:%S")
        date_dif = expires - now
        result["days"] = date_dif.days
        print(f"INFO: Domain {domain} expires in {date_dif.days} days on {result['date']}")
        return result
    except Exception as e:
        print(f"WARNING: Error in expires_days() call. Failed getting expiration date for: {domain}.  Error is: {e}")
        return False


def main():
    load_dotenv()
    warn_days = int(os.getenv("WARN_DAYS"))
    sleep_time = 12  # hours
    domains = get_domains()

    print(f"INFO: Starting GEA with {len(domains)} domains: {', '.join(domains)}")

    while True:
        for domain in get_domains():
            domains[domain] = expires_days(domain)
            if domains[domain] and warn_days > domains[domain]["days"]:
                send_alert(
                    f"NOTICE: {domain} is expiring in {domains[domain]['days']} days",
                    f"{domain} Expiring"
                )
            elif domains[domain]:
                print(f"INFO: {domain} is not expiring for {domains[domain]['days']} days")

        print(f"INFO: Sleeping for {sleep_time} hours...")
        sleep(sleep_time * 60 * 60 )


main()
