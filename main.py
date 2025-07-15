#!/usr/local/bin/python
from time import sleep
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
        tmp_result = whois.whois(domain).expiration_date
        if isinstance(tmp_result, list) and  tmp_result[0] and type(tmp_result[0]) is datetime:
            result["date"] = tmp_result[0]
        else:
            result["date"] = tmp_result
    except Exception as e:
        print(f"WARNING: Error in expires_days() call 1. Failed getting expiration date for: {domain}.  Error is: {e}")
        return False

    try:
        expires = datetime.strptime(str(result["date"]),"%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        date_dif = expires - now
        result["days"] = date_dif.days
        print(f"INFO: Domain {domain} expires in {date_dif.days} days on {result['date']}")
        return result
    except Exception as e:
        print(f"WARNING: Error in expires_days() call 2. Failed getting expiration date for: {domain}.  Error is: {e}")
        return False


def main():
    load_dotenv()
    warn_days = int(os.getenv("WARN_DAYS"))
    sleep_time = 12  # hours
    domains = get_domains()
    first = True

    print(f"INFO: Starting GEA with {len(domains)} domains: {', '.join(domains)}")

    while True:
        for domain in get_domains():
            domains[domain] = expires_days(domain)
            if domains[domain]:
                if warn_days >= domains[domain]["days"]:
                    send_alert(
                        f"NOTICE: {domain} is expiring in {domains[domain]['days']} days",
                        f"{domain} Expiring"
                    )
                else:
                    print(f"INFO: {domain} is not expiring for {domains[domain]['days']} days")

                if first:
                    send_alert(
                        f"INFO: {domain} is now being monitored! It expires in {domains[domain]['days']} days",
                        f"{domain} now being monitored"
                    )

        print(f"INFO: Sleeping for {sleep_time} hours...")
        sleep(sleep_time * 60 * 60 )
        first = False


main()
