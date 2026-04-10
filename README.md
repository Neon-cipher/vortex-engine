<p align="center">
  <img src="vortex_hero.png" width="400" alt="VORTEX Engine Hero"/>
</p>

```text
          ██╗   ██╗ ██████╗ ██████╗ ████████╗███████╗██╗  ██╗
          ██║   ██║██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝╚██╗██╔╝
          ██║   ██║██║   ██║██████╔╝   ██║   █████╗   ╚███╔╝ 
          ╚██╗ ██╔╝██║   ██║██╔══██╗   ██║   ██╔══╝   ██╔██╗ 
           ╚████╔╝ ╚██████╔╝██║  ██║   ██║   ███████╗██╔╝ ██╗
            ╚═══╝   ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
```

# 🌪️ VORTEX: Digital Forensics Engine

VORTEX is a modular, high-performance Python-based digital forensics engine designed for automated artifact collection, normalization, and chronological correlation. This tool is built for rapid-response triage and deep-dive persistence hunting.

## 🚀 Key Features

### 🖥️ Professional Terminal UX
- **Rich Interface**: Built with the `rich` library for aesthetic console rendering.
- **Animated Progress**: Live, transient spinners visualize real-time filesystem hashing and database parsing.
- **High-Priority Alerts**: Audible terminal bells and double-thick crimson panels highlight malicious findings instantly.

### 🍱 Artifact Analysis (Lethal Mode)
- **Deep Filesystem Traversal**: Recursive SHA256 hashing and extraction of Modified, Accessed, and Created (MAC) timestamps.
- **Advanced Browser Forensics**: 
    - **Chrome & Firefox**: Natively parses `History`, `Places`, `Cookies`, and `Extensions`.
    - **Session Recovery**: Extracts Auth Cookie creation timestamps to detect AiTM transitions.
    - **Persistence Hunting**: Analyzes installed browser extensions and their associated manifest permissions.
    - **Search & Download Tracing**: Universal RegEx extraction for search queries and file drop tracing.

### 🧠 Automated Heuristics Engine
- **Ransomware Protection**: Sliding-window detection for mass file modifications.
- **Path Reputation**: Alerts on executables running from risky paths like `/tmp/` or `/dev/shm/`.
- **Domain Reputation**: Flags high-risk domain activity, including C2, Raw GitHub, and Pastebin calls.

### 📝 Premium Reporting
- **Automated PDF**: High-end formatting with cover pages, persistent footers, page numbering, and a curated Indigo/Teal color palette.
- **Machine Readable JSON**: Categorized JSON export for SEIM ingestion (Splunk, Elastic).
- **Executive Summary**: Automated threat overview presented as the first page of the report.

## 📥 Installation

Ensure you have Python 3.8+ installed.

```bash
# Clone the repository
git clone https://github.com/user/timeline_engine.git
cd timeline_engine

# Setup environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 🛠️ Usage

The engine is designed as a flat CLI for rapid response. Use flags to specify inputs; any unspecified source is automatically skipped.

```bash
# General Usage
./venv/bin/python main.py -d /home/target --chrome --firefox --case "Investigation_01"

# Help Menu
./venv/bin/python main.py --help
```

### Argument Flags:
- `-d, --dir`: Target directory for filesystem MAC time analysis.
- `-c, --chrome`: Path to Chrome DB (uses `--chrome` or `-c auto` for auto-detect).
- `-f, --firefox`: Path to Firefox DB (uses `--firefox` or `-f auto` for auto-detect).
- `--case`: Case name. Automatically routes all exports into `cases/[NAME]/`.
- `-o, --output`: Base name for output files (overridden if `--case` is used).

## 🗂️ Project Structure

```text
timeline_engine/
├── core/
│   ├── engine.py       # Master aggregator and sort logic
│   ├── file_analyzer.py # Filesystem traversal & hashing
│   ├── browser_analyzer.py # SQL parsers for Chrome/FF
│   ├── heuristics.py   # Malicious rule engine
│   └── ui.py           # Global Rich console theme
├── reporters/
│   ├── pdf_reporter.py # Premium PDF generation
│   └── json_reporter.py# Categorized JSON export
└── main.py             # CLI entry point
```

## 🛡️ Forensic Integrity
All database operations are performed on temporary copies or via `readonly` SQL connections to ensure the integrity of the original evidence artifacts remains intact.
