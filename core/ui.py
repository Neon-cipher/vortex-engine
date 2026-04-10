from rich.console import Console
from rich.theme import Theme

# Define a professional, forensics-oriented color theme
custom_theme = Theme({
    "info": "cyan",
    "success": "bold green",
    "warning": "bold yellow",
    "danger": "bold red",
    "highlight": "magenta",
    "dim": "dim white"
})

# Global console instance to be imported across the application
console = Console(theme=custom_theme)
