import argparse
import os
import sys
from datetime import datetime, timezone

from core.engine import TimelineAggregator
from reporters.json_reporter import export_to_json
from reporters.pdf_reporter import export_to_pdf
from core.ui import console
from rich.panel import Panel

def main():
    help_text = """
=============================================================================
          ██╗   ██╗ ██████╗ ██████╗ ████████╗███████╗██╗  ██╗
          ██║   ██║██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝╚██╗██╔╝
          ██║   ██║██║   ██║██████╔╝   ██║   █████╗   ╚███╔╝ 
          ╚██╗ ██╔╝██║   ██║██╔══██╗   ██║   ██╔══╝   ██╔██╗ 
           ╚████╔╝ ╚██████╔╝██║  ██║   ██║   ███████╗██╔╝ ██╗
            ╚═══╝   ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
=============================================================================
                  VORTEX: Forensic Timeline Engine
=============================================================================

EXAMPLES:
  1. Analyze a directory and automatically detect browser history on Linux:
     main.py -d /home/kali/ --chrome --firefox -o my_report

  2. Organize outputs into a simple Case folder automatically:
     main.py -d /tmp --case "Operation_Phoenix"
"""

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Digital Forensics Timeline Engine",
        epilog=help_text
    )
    
    parser.add_argument('-d', '--dir', help="Directory to analyze for file MAC times")
    parser.add_argument('-c', '--chrome', nargs='?', const='auto', help="Path to Chrome DB (leave blank to auto-detect)")
    parser.add_argument('-f', '--firefox', nargs='?', const='auto', help="Path to Firefox DB (leave blank to auto-detect)")
    parser.add_argument('--case', help="Name of a Case folder to route output into (creates if doesn't exist).")
    parser.add_argument('-o', '--output', help="Output file base name (e.g., 'report'). Overridden by --case.")

    args = parser.parse_args()

    # Print banner safely using rich
    console.print(f"[info]{help_text}[/info]", highlight=False)

    if not any([args.dir, args.chrome, args.firefox]):
        console.print("[warning][!] You must specify at least one input source (-d, -c, or -f)[/warning]")
        parser.print_help()
        sys.exit(1)

    # Resolve output path
    output_base = "timeline_report" 
    
    if args.case:
        # Create case directory
        safe_case_name = "".join([c if c.isalnum() else "_" for c in args.case])
        case_dir = os.path.join("cases", safe_case_name)
        if not os.path.exists(case_dir):
            os.makedirs(case_dir)
            
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_base = os.path.join(case_dir, f"timeline_export_{timestamp_str}")
        console.print(f"[info][*] Attaching output to Case Folder: {case_dir}/[/info]")
    elif args.output:
        output_base = args.output
    else:
        # Default fallback
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_base = f"timeline_export_{timestamp_str}"
        console.print(f"[info][*] Output will be generated as: {output_base}.[json|pdf][/info]")

    # Initialize Engine
    engine = TimelineAggregator()

    # Process Inputs
    if args.dir:
        engine.add_directory(args.dir)
    
    if args.chrome:
        if args.chrome == 'auto':
            from core.browser_analyzer import find_chrome_path
            path = find_chrome_path()
            if path:
                engine.add_chrome_db(path)
            else:
                console.print("[warning][!] Could not auto-detect Chrome DB path.[/warning]")
        else:
            engine.add_chrome_db(args.chrome)
            
    if args.firefox:
        if args.firefox == 'auto':
            from core.browser_analyzer import find_firefox_path
            path = find_firefox_path()
            if path:
                engine.add_firefox_db(path)
            else:
                console.print("[warning][!] Could not auto-detect Firefox DB path.[/warning]")
        else:
            engine.add_firefox_db(args.firefox)

    # Get Master Timeline
    timeline = engine.get_timeline()
    
    if not timeline:
        console.print("[warning][!] No events found. Exiting without writing reports.[/warning]")
        sys.exit(0)

    # Run Heuristics
    from core.heuristics import run_heuristics
    alerts = run_heuristics(timeline)
    
    if alerts:
        from rich import box
        console.bell()  # Trigger audible terminal alert
        alert_body = f"[bold red]CRITICAL:[/bold red] Detected [bold underline]{len(alerts)} suspicious anomalies[/bold underline] in timeline!\n\n"
        for alert in alerts:
            alert_body += f"-> \\[[bold red]{alert['severity']}[/bold red]] [yellow]{alert['rule']}[/yellow]: {alert['details']}\n"
        
        console.print(Panel(alert_body, title="[bold white on red] !!! HIGH PRIORITY HEURISTICS ALERT !!! [/bold white on red]", border_style="red", box=box.DOUBLE))

    # Export Reports
    if output_base.endswith('.json') or output_base.endswith('.pdf'):
        output_base = os.path.splitext(output_base)[0]

    export_to_json(timeline, alerts, f"{output_base}.json")
    export_to_pdf(timeline, alerts, f"{output_base}.pdf")
    
    console.print(f"\n[success]=====================================[/success]")
    console.print(f"[success][*] Engine execution completed successfully![/success]")
    console.print(f"[success][*] Output routed to: [bold]{output_base}.[json|pdf][/bold][/success]")
    console.print(f"[success]=====================================[/success]")

if __name__ == "__main__":
    main()
