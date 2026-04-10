from .file_analyzer import analyze_directory
from .browser_analyzer import parse_chrome_history, parse_firefox_history
from .ui import console
from rich.progress import Progress, SpinnerColumn, TextColumn

class TimelineAggregator:
    def __init__(self):
        self.events = []

    def add_directory(self, dir_path):
        """Analyzes a directory and adds events to the timeline."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[info][*] Analyzing directory:[/info] [highlight]{task.description}[/highlight]"),
            console=console,
            transient=True
        ) as progress:
            progress.add_task(dir_path, total=None)
            file_events = analyze_directory(dir_path)
            
        self.events.extend(file_events)
        console.print(f"[success][*] Added {len(file_events)} file system events from {dir_path}.[/success]")

    def add_chrome_db(self, db_path):
        """Analyzes Chrome DB and adds events to the timeline."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[info][*] Analyzing Chrome history:[/info] [highlight]{task.description}[/highlight]"),
            console=console,
            transient=True
        ) as progress:
            progress.add_task(db_path, total=None)
            chrome_events = parse_chrome_history(db_path)
            
        self.events.extend(chrome_events)
        console.print(f"[success][*] Added {len(chrome_events)} Chrome events from {db_path}.[/success]")

    def add_firefox_db(self, db_path):
        """Analyzes Firefox DB and adds events to the timeline."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[info][*] Analyzing Firefox history:[/info] [highlight]{task.description}[/highlight]"),
            console=console,
            transient=True
        ) as progress:
            progress.add_task(db_path, total=None)
            ff_events = parse_firefox_history(db_path)
            
        self.events.extend(ff_events)
        console.print(f"[success][*] Added {len(ff_events)} Firefox events from {db_path}.[/success]")

    def get_timeline(self):
        """Sorts all events chronologically and returns them."""
        if len(self.events) > 0:
            with Progress(
                SpinnerColumn(),
                TextColumn("[info][*] Sorting {task.description} total events...[/info]"),
                console=console,
                transient=True
            ) as progress:
                progress.add_task(str(len(self.events)), total=None)
                sorted_events = sorted(self.events, key=lambda x: x['timestamp'])
                return sorted_events
        return []
