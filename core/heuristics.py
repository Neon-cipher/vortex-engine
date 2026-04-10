from collections import deque

def run_heuristics(events):
    """
    Scans a chronologically sorted list of events for known malicious heuristics.
    Returns a list of alert dictionaries.
    """
    alerts = []
    
    # Configuration
    RANSOMWARE_TIME_WINDOW_SEC = 5
    RANSOMWARE_MOD_LIMIT = 50
    SUSPICIOUS_PATHS = ['/tmp/', '/dev/shm/', '\\Temp\\', 'Downloads']
    SUSPICIOUS_EXTS = ['.exe', '.sh', '.elf', '.bat', '.ps1', '.vbs']
    SUSPICIOUS_DOMAINS = ['.onion', 'ngrok.io', 'pastebin.com', 'raw.githubusercontent.com', 'discordapp.com/attachments']

    # State tracking for sliding window
    mod_window = deque()
    ransomware_alert_triggered = False
    last_ransomware_ts = None

    for event in events:
        msg = event['description'].lower()
        evt_type = event['type']
        ts = event['timestamp']

        # RULE 1: High-Risk Domains
        if event['source'] in ['Chrome', 'Firefox']:
            for domain in SUSPICIOUS_DOMAINS:
                if domain in msg:
                    alerts.append({
                        'timestamp': ts,
                        'severity': 'HIGH',
                        'rule': 'Suspicious Browser Destination',
                        'details': f"Visited known high-risk domain fragment '{domain}' -> {event['description']}"
                    })

        # RULE 2: Suspicious Executable Paths
        if event['source'] == 'File System' and evt_type in ['File Created/Changed', 'File Accessed']:
            # A simple heuristic check
            is_suspicious_path = any(p.lower() in msg for p in SUSPICIOUS_PATHS)
            # Find if description indicates the file path ends in a bad ext
            # Format is "File: /path/to/malware.exe | SHA256: ..."
            path_part = event['description'].split(" | ")[0].lower()
            is_executable = any(path_part.endswith(e) for e in SUSPICIOUS_EXTS)
            
            if is_suspicious_path and is_executable:
                alerts.append({
                    'timestamp': ts,
                    'severity': 'HIGH',
                    'rule': 'Suspicious Executable Path',
                    'details': f"Executable interacting within world-writable/risk path -> {path_part}"
                })

        # RULE 3: Ransomware Mass-Modification (Sliding Window)
        if event['source'] == 'File System' and evt_type == 'File Modified':
            mod_window.append(ts)
            # Remove timestamps outside the window
            while mod_window and (ts - mod_window[0]).total_seconds() > RANSOMWARE_TIME_WINDOW_SEC:
                mod_window.popleft()
            
            # Re-arm ransomware specific trigger if 60 seconds have passed since last one
            if ransomware_alert_triggered and last_ransomware_ts and (ts - last_ransomware_ts).total_seconds() > 60:
                ransomware_alert_triggered = False

            if len(mod_window) >= RANSOMWARE_MOD_LIMIT and not ransomware_alert_triggered:
                alerts.append({
                    'timestamp': ts,
                    'severity': 'CRITICAL',
                    'rule': 'Ransomware Mass-Modification',
                    'details': f"Detected {len(mod_window)} file modifications within {RANSOMWARE_TIME_WINDOW_SEC} seconds."
                })
                ransomware_alert_triggered = True  # Prevent spam
                last_ransomware_ts = ts

    return alerts
