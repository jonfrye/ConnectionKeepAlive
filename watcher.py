"""
This tool maintains the internet connection provided by RADIUS sign-on alive.

Usage:
    python watcher.py <sign-on-url> <login>
"""

import getpass
import sys
import time
import logging
import md5
import re
import requests
import dns.resolver

def is_connection_alive(timeout=0.3):
    "Checks if the internet connection is alive by means of DNS."

    dns_resolver = dns.resolver.Resolver()
    dns_resolver.nameservers = ['8.8.8.8', '8.8.4.4', '208.67.220.220', '208.67.222.222']
    dns_resolver.timeout = timeout
    dns_resolver.lifetime = timeout

    for _ in range(1, 3):
        try:
            dns_resolver.query('google.com')
            return True
        except:
            pass
    return False

def fetch_sign_on_page(sign_on_url):
    "Fetches sign on page by the given url."
    r = requests.get(sign_on_url, timeout=30)
    if r.status_code / 100 not in [2, 3]:
        raise Exception("Unable to fetch sign on page. Response: %s %s\n%s",
                        r.status_code, r.reason, r.text)
    logging.debug("Fetched sign on page:%s\n%s", r.headers, r.text)
    return r.text

def parse_hashing_chars(sign_on_page):
    """Parses the sign on page in order to find this block:
        hexMD5('\340' + document.login.password.value + '\051\361\240\040\256\007\015\042\201\176\001\204\363\053\224\126');
    """
    regex = r"'([\\0-9]+)'\s*\+\s*document\.login\.password\.value\s*\+\s*'([\\0-9]+)'"
    m = re.search(regex, sign_on_page)
    if m is None:
        raise Exception("Unable to parse hash chars")
    prefix = m.group(1).decode('string_escape')
    suffix = m.group(2).decode('string_escape')
    return (prefix, suffix)

def connect_to_radius(sign_on_url, login, password):
    """Signs on using provided credentials.

    Returns:
        bool: True if connection was successful and False otherwise.
    """
    try:
        sign_on_page = fetch_sign_on_page(sign_on_url)
    except Exception as e:
        logging.info("Unable to fetch the sign on page. Error: %s", e)
        return False

    try:
        (md5_prefix, md5_suffix) = parse_hashing_chars(sign_on_page)
    except:
        logging.info("Unable to parse hash chars. Page:\n%s", sign_on_page)
        return False

    m = md5.new(md5_prefix + password + md5_suffix)
    password_hex_md5 = m.hexdigest()
    try:
        r = requests.post(sign_on_url, data={'username': login,
                                             'password': password_hex_md5,
                                             'dst': 'http://www.google.com',
                                             'popup': 'true'}, timeout=30)
    except Exception as e:
        logging.info("Unable to sign on. Error: %s", e)
        return False

    # NOTE: It may be needed to check r.text in the future as it is impossible to determine
    # if the connection was not established due to the wrong password.
    if r.status_code / 100 not in [2, 3]:
        logging.info("Unable to sign on. Response: %s %s\n%s", r.status_code, r.reason, r.text)
        return False
    logging.debug("Response to the login attempt:%s\n%s", r.headers, r.text)
    return True

def keep_alive_radius_connection(sign_on_url, login, password, check_interval_sec=1):
    # Monitors internet connection and trying to reconnect when it is lost.
    while True:
        if not is_connection_alive():
            logging.info("No internet connection, reconnecting...")
            if connect_to_radius(sign_on_url, login, password):
                logging.info("Connection established")
        time.sleep(check_interval_sec)

def main():
    if len(sys.argv) < 3:
        exit("Usage:\n    python watcher.py <sign-on-url> <login>")
    sign_on_url = sys.argv[1]
    login = sys.argv[2]
    password = getpass.getpass()
    # Change logging.INFO to logging.DEBUG to show server responses.
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s:%(levelname)s:%(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    logging.info("Monitoring has started")
    keep_alive_radius_connection(sign_on_url, login, password, check_interval_sec=1)

if __name__ == "__main__":
    main()
