import sqlite3
import os
import glob
import urllib.parse
import json
from datetime import datetime, timedelta, timezone

def get_home_dirs():
    """Returns a list of potential home directories to check."""
    dirs = [os.path.expanduser("~")]
    if os.path.exists("/home"):
        for d in os.listdir("/home"):
            dirs.append(os.path.join("/home", d))
    return list(set(dirs))

def find_chrome_path():
    """Attempts to automatically find the Chrome History database on Linux."""
    home_dirs = get_home_dirs()
    for home in home_dirs:
        paths = [
            os.path.join(home, ".config", "google-chrome", "Default", "History"),
            os.path.join(home, ".config", "chromium", "Default", "History")
        ]
        for p in paths:
            if os.path.exists(p):
                return p
    return None

def find_firefox_path():
    """Attempts to automatically find the Firefox places.sqlite database on Linux."""
    home_dirs = get_home_dirs()
    for home in home_dirs:
        profile_dir = os.path.join(home, ".mozilla", "firefox")
        if os.path.exists(profile_dir):
            search_pattern = os.path.join(profile_dir, "*.default*", "places.sqlite")
            matches = glob.glob(search_pattern)
            if matches:
                return matches[0]
            
            # Additional check for just any dir containing places.sqlite
            search_pattern_all = os.path.join(profile_dir, "*", "places.sqlite")
            matches_all = glob.glob(search_pattern_all)
            if matches_all:
                return matches_all[0]
                
    return None

def extract_search_from_url(url, timestamp, source):
    """Attempts to dynamically extract a search query parameter from a generic URL."""
    try:
        parsed = urllib.parse.urlparse(url)
        if 'search' in parsed.path or 'find' in parsed.path or 'query' in parsed.path or parsed.netloc.endswith('google.com') or parsed.netloc.endswith('bing.com'):
            query_params = urllib.parse.parse_qs(parsed.query)
            if 'q' in query_params:
                return {
                    'timestamp': timestamp,
                    'source': source,
                    'type': 'Search Query',
                    'description': f"Extracted Search Term: '{query_params['q'][0]}' | Origin: {parsed.netloc}"
                }
    except Exception:
        pass
    return None

def parse_chrome_history(db_path):
    """Parses a Chrome History SQLite database (Visits, Downloads, Searches, Cookies, Extensions)."""
    events = []
    if not os.path.exists(db_path):
        return events

    profile_dir = os.path.dirname(db_path)
    epoch_start = datetime(1601, 1, 1, tzinfo=timezone.utc)

    # LETHAL EXTENSION: Chrome Extensions
    ext_dir = os.path.join(profile_dir, "Extensions")
    if os.path.exists(ext_dir):
        for ext_id in os.listdir(ext_dir):
            ext_path = os.path.join(ext_dir, ext_id)
            if os.path.isdir(ext_path):
                for ver in os.listdir(ext_path):
                    ver_path = os.path.join(ext_path, ver)
                    manifest_path = os.path.join(ver_path, "manifest.json")
                    if os.path.exists(manifest_path):
                        try:
                            with open(manifest_path, 'r', encoding='utf-8') as f:
                                mdata = json.load(f)
                            # Handle localized names (often dictionaries or __MSG_...__) safely
                            name = mdata.get('name', 'Unknown')
                            if isinstance(name, dict): name = str(name)
                            permissions = mdata.get('permissions', [])
                            
                            stat = os.stat(ver_path)
                            timestamp = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                            events.append({
                                'timestamp': timestamp,
                                'source': 'Chrome',
                                'type': 'Browser Extension',
                                'description': f"Installation -> Ext Name: {name} | ID: {ext_id} | Permissions: {len(permissions)} requested"
                            })
                        except Exception: pass

    # LETHAL EXTENSION: Chrome Auth Cookies
    cookie_path = os.path.join(profile_dir, "Network", "Cookies")
    if not os.path.exists(cookie_path):
        cookie_path = os.path.join(profile_dir, "Cookies")
        
    if os.path.exists(cookie_path):
        try:
            c_conn = sqlite3.connect(f"file:{cookie_path}?mode=ro", uri=True)
            c_cursor = c_conn.cursor()
            c_cursor.execute("SELECT host_key, name, creation_utc FROM cookies;")
            for r in c_cursor.fetchall():
                host, name, creation_utc = r
                if creation_utc:
                    try:
                        timestamp = epoch_start + timedelta(microseconds=creation_utc)
                        events.append({
                            'timestamp': timestamp,
                            'source': 'Chrome',
                            'type': 'Auth Cookie',
                            'description': f"Session Created -> Host: {host} | Cookie Name: {name}"
                        })
                    except Exception: pass
            c_conn.close()
        except Exception as e: pass

    # CORE HISTORY
    try:
        uri_path = f"file:{db_path}?mode=ro"
        conn = sqlite3.connect(uri_path, uri=True)
        cursor = conn.cursor()

        # 1. PAGE VISITS
        query = """
            SELECT urls.url, urls.title, visits.visit_time 
            FROM urls 
            JOIN visits ON urls.id = visits.url;
        """
        cursor.execute(query)
        for row in cursor.fetchall():
            url, title, visit_time = row
            if visit_time:
                try:
                    delta = timedelta(microseconds=visit_time)
                    timestamp = epoch_start + delta
                except Exception:
                    continue

                events.append({
                    'timestamp': timestamp,
                    'source': 'Chrome',
                    'type': 'Page Visited',
                    'description': f"URL: {url} | Title: {title}"
                })
                
                search_event = extract_search_from_url(url, timestamp, 'Chrome')
                if search_event:
                    events.append(search_event)

        # 2. DOWNLOADS
        try:
            cursor.execute("SELECT current_path, target_path, start_time, total_bytes FROM downloads;")
            for row in cursor.fetchall():
                curr_path, targ_path, start_time, total_bytes = row
                if start_time:
                    try:
                        timestamp = epoch_start + timedelta(microseconds=start_time)
                        events.append({
                            'timestamp': timestamp,
                            'source': 'Chrome',
                            'type': 'Browser Download',
                            'description': f"Target Path: {targ_path} | Size: {total_bytes} bytes"
                        })
                    except Exception: pass
        except Exception: pass

        # 3. NATIVE SEARCH QUERIES
        try:
            query_search = """
                SELECT k.term, u.url, v.visit_time 
                FROM keyword_search_terms k
                JOIN urls u ON k.url_id = u.id
                JOIN visits v ON u.id = v.url;
            """
            cursor.execute(query_search)
            for row in cursor.fetchall():
                term, url, visit_time = row
                if visit_time:
                    try:
                        timestamp = epoch_start + timedelta(microseconds=visit_time)
                        events.append({
                            'timestamp': timestamp,
                            'source': 'Chrome',
                            'type': 'Search Query',
                            'description': f"Term: '{term}' | Origin Engine: {urllib.parse.urlparse(url).netloc}"
                        })
                    except Exception: pass
        except Exception: pass

        conn.close()
    except Exception as e:
        from .ui import console
        console.print(f"[danger]Error parsing Chrome DB {db_path}: {e}[/danger]")

    return events


def parse_firefox_history(db_path):
    """Parses a Firefox places.sqlite database (Visits, Downloads, Searches, Cookies, Extensions)."""
    events = []
    if not os.path.exists(db_path):
        return events

    profile_dir = os.path.dirname(db_path)

    # LETHAL EXTENSION: Firefox Extensions (extensions.json)
    ext_json_path = os.path.join(profile_dir, "extensions.json")
    if os.path.exists(ext_json_path):
        try:
            with open(ext_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            addons = data.get('addons', [])
            for addon in addons:
                name = addon.get('defaultLocale', {}).get('name', addon.get('id', 'Unknown'))
                install_date = addon.get('installDate', 0)
                if install_date:
                    try:
                        timestamp = datetime.fromtimestamp(install_date / 1000.0, tz=timezone.utc)
                        events.append({
                            'timestamp': timestamp,
                            'source': 'Firefox',
                            'type': 'Browser Extension',
                            'description': f"Installation -> Ext Name: {name} | Type: {addon.get('type')} | Active: {addon.get('active')}"
                        })
                    except Exception: pass
        except Exception: pass

    # LETHAL EXTENSION: Firefox Auth Cookies
    cookie_path = os.path.join(profile_dir, "cookies.sqlite")
    if os.path.exists(cookie_path):
        try:
            c_conn = sqlite3.connect(f"file:{cookie_path}?mode=ro", uri=True)
            c_cursor = c_conn.cursor()
            c_cursor.execute("SELECT host, name, creationTime FROM moz_cookies;")
            for r in c_cursor.fetchall():
                host, name, creationTime = r
                if creationTime:
                    try:
                        timestamp = datetime.fromtimestamp(creationTime / 1000000.0, tz=timezone.utc)
                        events.append({
                            'timestamp': timestamp,
                            'source': 'Firefox',
                            'type': 'Auth Cookie',
                            'description': f"Session Created -> Host: {host} | Cookie Name: {name}"
                        })
                    except Exception: pass
            c_conn.close()
        except Exception: pass

    # CORE HISTORY
    try:
        uri_path = f"file:{db_path}?mode=ro"
        conn = sqlite3.connect(uri_path, uri=True)
        cursor = conn.cursor()

        # 1. PAGE VISITS
        query = """
            SELECT moz_places.url, moz_places.title, moz_historyvisits.visit_date 
            FROM moz_places 
            JOIN moz_historyvisits ON moz_places.id = moz_historyvisits.place_id;
        """
        cursor.execute(query)
        for row in cursor.fetchall():
            url, title, visit_date = row
            if visit_date:
                try:
                    timestamp = datetime.fromtimestamp(visit_date / 1000000.0, tz=timezone.utc)
                except Exception:
                    continue

                events.append({
                    'timestamp': timestamp,
                    'source': 'Firefox',
                    'type': 'Page Visited',
                    'description': f"URL: {url} | Title: {title}"
                })
                
                search_event = extract_search_from_url(url, timestamp, 'Firefox')
                if search_event:
                    events.append(search_event)

        # 2. DOWNLOADS (moz_annos)
        try:
            dl_query = """
                SELECT p.url, a.content, a.dateAdded
                FROM moz_annos a
                JOIN moz_anno_attributes attr ON a.anno_attribute_id = attr.id
                JOIN moz_places p ON a.place_id = p.id
                WHERE attr.name = 'downloads/destinationFileURI';
            """
            cursor.execute(dl_query)
            for row in cursor.fetchall():
                url, content, date_added = row
                if date_added:
                    try:
                        timestamp = datetime.fromtimestamp(date_added / 1000000.0, tz=timezone.utc)
                        events.append({
                            'timestamp': timestamp,
                            'source': 'Firefox',
                            'type': 'Browser Download',
                            'description': f"Dest URI: {content} | Origin: {url}"
                        })
                    except Exception: pass
        except Exception: pass

        conn.close()
    except Exception as e:
        from .ui import console
        console.print(f"[danger]Error parsing Firefox DB {db_path}: {e}[/danger]")

    return events
