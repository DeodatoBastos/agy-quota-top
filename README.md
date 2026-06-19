# Antigravity CLI Quota Top

A sleek, `btop`-style terminal user interface (TUI) for monitoring your active [Google AI Pro](https://antigravity.google) quota usage directly from your local Antigravity CLI daemon.

![Screenshot](screenshot.png) *(Add your own screenshot here)*

## Features

- **Live Dashboard**: Monitors your AI Pro quota usage in real-time.
- **Auto-Discovery**: Automatically finds and connects to the active Antigravity CLI background language server via internal APIs.
- **Model Grouping**: Distinctly tracks quota limits for different model families (Gemini Models vs. Claude/GPT Models).
- **Time-to-Reset**: Calculates and displays exactly how much time is left before your quota replenishes.
- **Aesthetic TUI**: Crafted with standard `curses` using a minimal and beautiful design palette.

## Requirements

- Python 3.6+
- Antigravity CLI (`agy`) running in the background.
- Standard terminal emulator supporting 256 colors.

## Usage

Simply run the script:

```bash
./quota_top.py
```

Press `q` at any time to exit the dashboard.

## How it works

The script uses `ss` or `lsof` to locate the random port assigned to the `agy` daemon upon startup. It then queries the `/exa.language_server_pb.LanguageServerService/GetUserStatus` endpoint and extracts the `cascadeModelConfigData` to render the quota progress bars dynamically.
