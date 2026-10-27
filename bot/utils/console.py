from rich.console import Console
from rich.text import Text

console = Console(log_time_format=lambda dt: Text(f"[{dt:%H:%M:%S}.{dt.microsecond // 1000:03d}]"))
connecting = console.status("Connecting to Discord...")
