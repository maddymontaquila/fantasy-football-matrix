"""
Fantasy Football Matrix Portal Display
CircuitPython 10 code for Adafruit MatrixPortal S3
"""

import time
import wifi
import socketpool
import ssl
import adafruit_requests
import displayio
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect
import terminalio
import os
import board
import neopixel

# API Configuration
API_HOST = os.getenv("API_HOST", "192.168.1.100")
API_PORT = os.getenv("API_PORT", "8000")
API_URL = f"http://{API_HOST}:{API_PORT}/league/data"

# Display Configuration
DISPLAY_TIME = 5  # seconds per matchup
SUMMARY_DISPLAY_TIME = 5  # seconds for summary screen
REFRESH_INTERVAL = 30  # seconds between API calls
COLOR_ORDER = "RGB"  # RGB/RBG/BGR depending on panel type

# Neon color sets for 6 matchups (home, away)
MATCHUP_COLORS = [
    (0x00FFFF, 0xFF1493),  # Cyan vs Deep Pink
    (0xFFFF00, 0x0000FF),  # Yellow vs Blue
    (0xFF00FF, 0x00FFFF),  # Magenta vs Cyan
    (0xFF69B4, 0x1E90FF),  # Hot Pink vs Dodger Blue
    (0xFFD700, 0x8B00FF),  # Gold vs Electric Purple
    (0xFFA500, 0x00CED1),  # Orange vs Turquoise
]

WINNING_SCORE_COLOR = 0x00FF00  # Green
LOSING_SCORE_COLOR = 0xFFFFFF   # White

# Summary screen colors
MEDIAN_TITLE_COLOR = 0xFF69B4   # Hot Pink
LIVE_LABEL_COLOR = 0x00FF00     # Green
LIVE_VALUE_COLOR = 0xFFFFFF     # White
PROJ_LABEL_COLOR = 0x00FFFF     # Cyan
PROJ_VALUE_COLOR = 0xFFFFFF     # White


class FantasyMatrixDisplay:
    def __init__(self):
        """Initialize the MatrixPortal and display"""
        print("Initializing Fantasy Football Matrix Display...")
        print(f"Using color order: {COLOR_ORDER}")

        self.matrixportal = MatrixPortal(
            width=64,
            height=32,
            bit_depth=4,
            color_order=COLOR_ORDER,
            status_neopixel=None,
        )

        # Set up status NeoPixel for network activity indication
        self.status_pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2)
        self.status_pixel.fill(0x000000)  # Start off

        pool = socketpool.SocketPool(wifi.radio)
        self.requests = adafruit_requests.Session(pool, ssl.create_default_context())

        self.display = self.matrixportal.display
        self.display.brightness = 0.8
        self.group = self.display.root_group

        self.matchups = []
        self.current_matchup_index = 0
        self.last_api_call = 0
        self.projected_median = 0.0

        print("Matrix Portal initialized!")
    
    def connect_wifi(self, ssid, password):
        """Connect to WiFi network"""
        print(f"Connecting to WiFi: {ssid}")
        self.status_pixel.fill(0xFFFF00)  # Yellow while connecting
        try:
            wifi.radio.connect(ssid, password)
            print(f"Connected! IP: {wifi.radio.ipv4_address}")
            self.status_pixel.fill(0x00FF00)  # Green on success
            time.sleep(0.5)
            self.status_pixel.fill(0x000000)  # Turn off
            return True
        except Exception as e:
            print(f"WiFi connection failed: {e}")
            self.status_pixel.fill(0xFF0000)  # Red on error
            time.sleep(1)
            self.status_pixel.fill(0x000000)
            return False
    
    def fetch_matchups(self):
        """Fetch fresh matchup data from API"""
        self.status_pixel.fill(0x0000FF)  # Blue while fetching
        try:
            print(f"Fetching data from: {API_URL}")
            response = self.requests.get(API_URL, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.matchups = data["matchups"]
                self.projected_median = data.get("projected_median", 0.0)
                print(f"Fetched {len(self.matchups)} matchups for Week {data['week']}")
                self.status_pixel.fill(0x00FF00)  # Green flash on success
                time.sleep(0.3)
                self.status_pixel.fill(0x000000)
                return True
            else:
                print(f"API error: {response.status_code}")
                self.status_pixel.fill(0xFF0000)  # Red on error
                time.sleep(0.5)
                self.status_pixel.fill(0x000000)
                return False

        except Exception as e:
            print(f"Network error: {e}")
            self.status_pixel.fill(0xFF0000)  # Red on error
            time.sleep(0.5)
            self.status_pixel.fill(0x000000)
            return False
        finally:
            response.close() if 'response' in locals() else None
    
    def create_matchup_display(self, matchup):
        """Create display elements for a single matchup"""
        home = matchup["home_team"]
        away = matchup["away_team"]
        home_prob = round(matchup["home_win_probability"] * 100)
        
        # Get colors for this matchup
        matchup_idx = matchup.get("matchup_index", 0) % len(MATCHUP_COLORS)
        home_color, away_color = MATCHUP_COLORS[matchup_idx]

        # Determine score colors based on who's winning
        home_score_val = home['current_score']
        away_score_val = away['current_score']
        
        if home_score_val > away_score_val:
            home_score_color, away_score_color = WINNING_SCORE_COLOR, LOSING_SCORE_COLOR
        elif away_score_val > home_score_val:
            home_score_color, away_score_color = LOSING_SCORE_COLOR, WINNING_SCORE_COLOR
        else:
            home_score_color = away_score_color = LOSING_SCORE_COLOR

        # Calculate probability bar dimensions
        bar_width = 64
        bar_height = 4
        bar_y = 24
        home_bar_width = int((home_prob / 100) * bar_width)

        # Create display group
        new_group = displayio.Group()

        # Team names
        new_group.append(label.Label(
            terminalio.FONT,
            text=home["team_abbrev"],
            color=home_color,
            x=0, y=6
        ))
        
        away_x = max(0, 64 - (len(away["team_abbrev"]) * 6))
        new_group.append(label.Label(
            terminalio.FONT,
            text=away["team_abbrev"],
            color=away_color,
            x=away_x, y=6
        ))

        # Scores
        home_score_text = f"{home_score_val:.1f}"
        new_group.append(label.Label(
            terminalio.FONT,
            text=home_score_text,
            color=home_score_color,
            x=0, y=16
        ))

        away_score_text = f"{away_score_val:.1f}"
        away_score_x = max(0, 64 - (len(away_score_text) * 6))
        new_group.append(label.Label(
            terminalio.FONT,
            text=away_score_text,
            color=away_score_color,
            x=away_score_x, y=16
        ))

        # Probability bars
        new_group.append(Rect(
            x=0, y=bar_y,
            width=home_bar_width,
            height=bar_height,
            fill=home_color
        ))
        
        new_group.append(Rect(
            x=home_bar_width, y=bar_y,
            width=bar_width - home_bar_width,
            height=bar_height,
            fill=away_color
        ))

        self.display.root_group = new_group
        self.group = new_group

        print(f"Displaying: {home['team_abbrev']} vs {away['team_abbrev']} ({home_prob}%-{100-home_prob}%)")
    
    def create_summary_display(self):
        """Create summary screen with live vs projected median"""
        # Calculate live median from all teams
        all_scores = []
        
        for matchup in self.matchups:
            home = matchup["home_team"]
            away = matchup["away_team"]
            all_scores.append(home['current_score'])
            all_scores.append(away['current_score'])
        
        # Calculate live median
        sorted_scores = sorted(all_scores)
        n = len(sorted_scores)
        live_median = sorted_scores[n // 2] if n % 2 else (sorted_scores[n // 2 - 1] + sorted_scores[n // 2]) / 2
        
        # Create display group
        new_group = displayio.Group()
        
        # Title: MEDIAN (centered at top)
        title_text = "MEDIAN"
        title_x = (64 - (len(title_text) * 6)) // 2
        new_group.append(label.Label(
            terminalio.FONT,
            text=title_text,
            color=MEDIAN_TITLE_COLOR,
            x=title_x, y=6
        ))
        
        # LIVE: xx.x
        live_text = f"LIVE: {live_median:.1f}"
        live_x = (64 - (len(live_text) * 6)) // 2
        new_group.append(label.Label(
            terminalio.FONT,
            text="LIVE:",
            color=LIVE_LABEL_COLOR,
            x=live_x, y=16
        ))
        new_group.append(label.Label(
            terminalio.FONT,
            text=f"{live_median:.1f}",
            color=LIVE_VALUE_COLOR,
            x=live_x + 30, y=16
        ))
        
        # PROJ: xx.x
        proj_text = f"PROJ: {self.projected_median:.1f}"
        proj_x = (64 - (len(proj_text) * 6)) // 2 + 1  # Add 1 pixel offset
        new_group.append(label.Label(
            terminalio.FONT,
            text="PROJ:",
            color=PROJ_LABEL_COLOR,
            x=proj_x, y=26
        ))
        new_group.append(label.Label(
            terminalio.FONT,
            text=f"{self.projected_median:.1f}",
            color=PROJ_VALUE_COLOR,
            x=proj_x + 30, y=26
        ))
        
        self.display.root_group = new_group
        self.group = new_group
        
        print(f"Summary: Live Median={live_median:.1f}, Projected Median={self.projected_median:.1f}")
    
    def run(self, wifi_ssid, wifi_password):
        """Main display loop"""
        if not self.connect_wifi(wifi_ssid, wifi_password):
            print("ERROR: Cannot continue without WiFi")
            return

        if not self.fetch_matchups():
            print("ERROR: Cannot continue without initial data")
            return

        print("Starting display loop...")
        
        while True:
            try:
                if self.matchups:
                    # Check if we should show summary screen
                    if self.current_matchup_index >= len(self.matchups):
                        self.create_summary_display()
                        time.sleep(SUMMARY_DISPLAY_TIME)
                        self.current_matchup_index = 0
                        
                        # Refresh data after summary
                        current_time = time.monotonic()
                        if current_time - self.last_api_call > REFRESH_INTERVAL:
                            print("Refreshing data...")
                            if self.fetch_matchups():
                                self.last_api_call = current_time
                    else:
                        # Show matchup
                        matchup = self.matchups[self.current_matchup_index]
                        self.create_matchup_display(matchup)
                        time.sleep(DISPLAY_TIME)
                        self.current_matchup_index += 1
                else:
                    print("No matchup data, retrying...")
                    time.sleep(5)

            except Exception as e:
                print(f"Display error: {e}")
                time.sleep(5)


if __name__ == "__main__":
    display = FantasyMatrixDisplay()
    
    WIFI_SSID = os.getenv("CIRCUITPY_WIFI_SSID")
    WIFI_PASSWORD = os.getenv("CIRCUITPY_WIFI_PASSWORD")
    
    if not WIFI_SSID or not WIFI_PASSWORD:
        print("ERROR: WiFi credentials not found in settings.toml")
        print("Please update settings.toml with your WiFi info")
    else:
        display.run(WIFI_SSID, WIFI_PASSWORD)