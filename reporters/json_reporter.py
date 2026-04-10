import json
from datetime import datetime

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def export_to_json(events, alerts, output_path):
    """Exports the event timeline and heuristics alerts to a JSON file."""
    # Sort descending for consistency (Newest first)
    alerts = sorted(alerts, key=lambda x: x['timestamp'], reverse=True)
    events = sorted(events, key=lambda x: (x['timestamp'], x['source'], x['type'], x['description']), reverse=True)

    file_events = [e for e in events if e['source'] == 'File System']
    browser_history = [e for e in events if e['source'] in ['Chrome', 'Firefox'] and e['type'] in ['Page Visited', 'Search Query']]
    browser_cookies = [e for e in events if e['source'] in ['Chrome', 'Firefox'] and e['type'] == 'Auth Cookie']
    browser_extensions = [e for e in events if e['source'] in ['Chrome', 'Firefox'] and e['type'] == 'Browser Extension']
    browser_other = [e for e in events if e['source'] in ['Chrome', 'Firefox'] and e['type'] not in ['Page Visited', 'Search Query', 'Auth Cookie', 'Browser Extension']]

    data = {
        "metadata": {
            "total_events": len(events),
            "total_alerts": len(alerts)
        },
        "alerts": alerts,
        "timeline": {
            "file_system_events": file_events,
            "web_history_and_searches": browser_history,
            "browser_authentication_cookies": browser_cookies,
            "browser_extensions": browser_extensions,
            "other_browser_events": browser_other
        }
    }
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=CustomJSONEncoder, indent=4)
        from core.ui import console
        console.print(f"[success][*] Successfully exported JSON timeline to: {output_path}[/success]")
    except Exception as e:
        from core.ui import console
        console.print(f"[danger][!] Error exporting JSON: {e}[/danger]")
