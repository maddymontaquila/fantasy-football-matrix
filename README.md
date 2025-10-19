# Fantasy Football Matrix Display

Live fantasy football matchup display on a 64x32 RGB LED matrix using Adafruit MatrixPortal S3 and ESPN Fantasy API.

![Display shows team matchups with scores and win probabilities]

## Features

- 🏈 **Live scoring** - Real-time scores during games
- 📊 **Win probability** - Calculated from current scores + projections
- 🔄 **Auto-cycling** - Rotates through all matchups every 5 seconds
- 📡 **Auto-refresh** - Updates data every 30 seconds
- 🎨 **Single-color display** - Works around CircuitPython 10 color mixing limitations
- ⚡ **WiFi enabled** - Fetches data from local API server

## Hardware Required

- [Adafruit MatrixPortal S3](https://www.adafruit.com/product/5778)
- [64x32 RGB LED Matrix Panel](https://www.adafruit.com/product/2278) (HUB75 compatible)
- USB-C cable for power
- 5V power supply (recommended for brightness)

## Quick Start

### 1. Set up the API Server

```bash
cd fantasy-football-api
cp .env.example .env
# Edit .env with your ESPN league ID and credentials
uv run uvicorn api:app --host 0.0.0.0 --port 8000
```

### 2. Set up the Matrix Display

1. Install [CircuitPython 10](https://circuitpython.org/board/adafruit_matrixportal_s3/) on your MatrixPortal S3
2. Install required libraries:
   ```bash
   pip3 install circup
   circup install adafruit_matrixportal adafruit_requests adafruit_connection_manager adafruit_display_shapes
   ```
3. Copy files to CIRCUITPY drive:
   - `matrix-portal/code.py` → `CIRCUITPY/code.py`
   - `matrix-portal/settings.toml` → `CIRCUITPY/settings.toml`
4. Edit `settings.toml` with your WiFi credentials and API server IP

### 3. Run

The display will automatically start when powered on, connecting to WiFi and fetching matchup data.

## Project Structure

```
fantasy-football-matrix/
├── fantasy-football-api/     # FastAPI server for ESPN data
│   ├── api.py               # Main API implementation
│   ├── .env.example         # Environment variables template
│   └── pyproject.toml       # Python dependencies
├── matrix-portal/           # CircuitPython code for LED matrix
│   ├── code.py             # Main display code
│   ├── settings.toml       # WiFi and API configuration
│   └── README.md           # Detailed setup instructions
└── README.md               # This file
```

## API Endpoints

- `GET /league/data` - All current week matchups with live scores
- `GET /health` - Health check

## Display Layout

```
+------------------+
|JB  vs  ZWW       | ← Team abbreviations (blue)
|87.3    92.1      | ← Scores (green=winning, blue=losing)
|████████░░░░░░░░░| ← Win probability bar (blue=home team %)
+------------------+
```

## Known Issues & Workarounds

### CircuitPython 10 Color Mixing Bug

**Issue**: Multi-channel colors (like white=0xFFFFFF, cyan=0x00FFFF) cause severe aliasing on RGB matrices in CircuitPython 10.

**Workaround**: Code uses only pure single-channel colors:
- Blue (0x0000FF) for text
- Green (0x00FF00) for winning scores
- Black (0x000000) for blank sections

This is a CircuitPython 10 regression and should be reported to Adafruit.

## Configuration

### API (`fantasy-football-api/.env`)
```bash
ESPN_LEAGUE_ID=your_league_id
ESPN_YEAR=2025
ESPN_SWID=your_swid_cookie     # For private leagues
ESPN_S2=your_espn_s2_cookie    # For private leagues
```

### Matrix Display (`matrix-portal/settings.toml`)
```toml
CIRCUITPY_WIFI_SSID = "YourWiFiName"
CIRCUITPY_WIFI_PASSWORD = "YourPassword"
API_HOST = "192.168.1.XXX"  # Your computer's IP
API_PORT = "8000"
```

## Finding Your ESPN League ID

1. Go to your ESPN Fantasy Football league
2. Look at the URL: `https://fantasy.espn.com/football/league?leagueId=XXXXXXX`
3. The number after `leagueId=` is your league ID

## Development

### API Server
```bash
cd fantasy-football-api
uv run uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
curl http://localhost:8000/league/data
```

## Troubleshooting

**WiFi won't connect**: Check SSID/password in `settings.toml`

**API errors**: Verify your computer's IP and that the API server is running

**Blank display**: Check CircuitPython libraries are installed with `circup`

**Color issues**: Use only single-channel colors due to CP10 bug

## License

MIT

## Credits

Built with:
- [CircuitPython](https://circuitpython.org/) by Adafruit
- [espn-api](https://github.com/cwendt94/espn-api) for ESPN Fantasy data
- [FastAPI](https://fastapi.tiangolo.com/) for the API server