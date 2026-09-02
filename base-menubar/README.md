# base-menubar

macOS menu bar widget for [Base](../README.md). Shows your WHOOP recovery, sleep, strain, and forecast at a glance — always visible, never in the way.

## What it shows

- Recovery score with color-coded zone (green/yellow/red) in the menu bar
- Click to expand: HRV, resting HR, SpO2, sleep breakdown, strain, workouts
- 3-day recovery forecast (if recovery-forecast is running)
- Auto-refreshes every 5 minutes

## Dependencies

- **whoop-core** (required) — must be running on `:9120`
- **recovery-forecast** (optional) — if running on `:9122`, shows the forecast section

## Setup

### Option 1: Open in Xcode

```bash
open base-menubar/Base.xcodeproj
```

Hit **Cmd+R** to build and run. The app appears in your menu bar (not the Dock — it's set to `LSUIElement = YES`).

### Option 2: Build from command line

```bash
cd base-menubar
xcodebuild -scheme Base -configuration Release build
```

## Usage

- The menu bar shows a heart icon + your recovery percentage
- Click it to see the full dashboard
- Click **Refresh** to fetch latest data
- Click **Quit** to close

## Adding to Login Items

To start Base automatically when you log in:

1. Open **System Settings** → **General** → **Login Items**
2. Click **+** and select the Base app

## Architecture

- Pure SwiftUI with `MenuBarExtra`
- Polls `localhost:9120/today` for WHOOP data
- Polls `localhost:9122/predict` for forecast (optional)
- No data storage — everything is fetched from the local services
- Hidden from Dock (`LSUIElement = YES`)
