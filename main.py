#!/usr/local/bin/python
import json
from time import sleep
from dotenv import load_dotenv
from gotify import Gotify
from datetime import datetime
import os
import whois
import threading
import http.server
import socketserver
import json


def get_domains():
    MONITOR_DOMAINS = os.getenv("MONITOR_DOMAINS")
    domain_list = MONITOR_DOMAINS.split(",")
    domains = {}
    for domain in domain_list:
        domain = domain.strip()
        domains[domain] = domain
    return domains


def send_alert(message, title):
    gotify_url = os.getenv("GOTIFY_URL")
    gotify = Gotify(
        base_url = gotify_url,
        app_token = os.getenv("GOTIFY_TOKEN"),
    )
    try:
        gotify.create_message(
            f"{message}",
            title=f"GEA: {title}",
            priority=2,
        )
        print(f"INFO: Gotify alert sent to {gotify_url}")
        return True
    except Exception as e:
        print(f"WARNING: Error in send_alert() call. Failed to call Gotify at: {gotify_url}.  Error is: {e}")
        return False


def expire_info(domain):
    result = dict(date = datetime.now(), days = 0)
    result["domain"] = domain

    try:
        print(f"INFO: Querying for domain {domain}")
        tmp_result = whois.whois(domain).expiration_date
        if isinstance(tmp_result, list) and tmp_result[0] and type(tmp_result[0]) is datetime:
            result["date"] = tmp_result[0]
        else:
            result["date"] = tmp_result
    except Exception as e:
        print(f"WARNING: Error in expire_info() call 1. Failed getting expiration date for: {domain}.  Error is: {e}")
        return False

    try:
        expires = datetime.strptime(str(result["date"]),"%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        date_dif = expires - now
        result["days"] = date_dif.days
        print(f"INFO: Domain {domain} expires in {date_dif.days} days on {result['date']}")
        return result
    except Exception as e:
        print(f"WARNING: Error in expire_info() call 2. Failed getting expiration date for: {domain}.  Error is: {e}")
        return False


def check_domains_every_n_hours(first = False):
    send_alerts = bool(os.getenv("SEND_ALERTS"))
    warn_days = int(os.getenv("WARN_DAYS"))
    domains = get_domains()

    print(f"INFO: Starting GEA loop with {len(domains)} domains: {', '.join(domains)}")

    for domain in get_domains():
        # todo: this will cache an empty result, what if we fail to get expiration data?
        cache_domain_results({'domain': domain})
        info = expire_info(domain)
        if info:
            cache_domain_results(info)
            if send_alerts and warn_days >= info['days']:
                send_alert(
                    f"NOTICE: {domain} expires in {info['days']} days",
                    f"{domain} Expiring"
                )

            if send_alerts and first:
                send_alert(
                    f"INFO: Expires in {info['days']} days",
                    f"{domain} now being monitored"
                )

    # thanks MaxCore! https://stackoverflow.com/q/39709280
    sleep_time = 12 # hours
    print(f"INFO: Sleeping for {sleep_time} hours...")
    threading.Timer(sleep_time * 60 * 60, check_domains_every_n_hours).start()


def cache_domain_results(info):
    info["cached_date"] = str(datetime.now())
    if "date" in info:
        info["date"] = str(info["date"])
    path = "./web/" + info['domain'] + ".json"
    string = json.dumps(info)
    with open(path, "w") as text_file:
        text_file.write(string)


def web_server():
    PORT = int(os.getenv("PORT"))
    domains = get_domains()
    print(f"INFO: Starting GEA webserver with {len(domains)} domains: {', '.join(domains)}")

    try:
        Handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print("INFO: serving at port", PORT)
            httpd.serve_forever()
    except Exception as e:
        print(f"WARNING: Error in web_server() call 1. Failed to start webserver.  Error is: {e}")
        return False


def main():
    load_dotenv()
    first = True
    check_domains_every_n_hours(first)
    web_server()


main()
