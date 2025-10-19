"""
Fantasy Football Matrix Portal Display
CircuitPython 10 code for Adafruit MatrixPortal S3
"""

import time
import json
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

# Configuration from settings.toml
API_HOST = os.getenv("API_HOST", "192.168.1.100")
API_PORT = os.getenv("API_PORT", "8000")
API_URL = f"http://{API_HOST}:{API_PORT}/league/data"

DISPLAY_TIME = 5  # seconds to show each matchup
REFRESH_INTERVAL = 30  # seconds between API calls

# COLOR ORDER CONFIGURATION: Tested and confirmed for this panel
# "RGB": Standard color order (most panels)
# "RBG": Swapped green/blue - common on 64x32 2.5mm pitch (product ID 5036)
# "BGR": Swapped red/blue - some newer panel batches
COLOR_ORDER = "RGB"  # Confirmed working for this panel

# PURE single-channel colors ONLY (no multi-channel mixing due to CP10 bug)
# Multi-channel colors (like white=0xFFFFFF) cause severe aliasing
# TESTING: Use all BLUE to test stability, blank bar for away team
HOME_TEAM_COLOR = 0x0000FF  # Blue for home team
AWAY_TEAM_COLOR = 0x0000FF  # Blue for away team
WINNING_SCORE_COLOR = 0x0000FF  # Blue for winning score
LOSING_SCORE_COLOR = 0x0000FF  # Blue for losing score
WIN_BAR_HOME_COLOR = 0x0000FF  # Blue for home team's probability portion
WIN_BAR_AWAY_COLOR = 0x000000  # Black (blank) for away team's probability portion

class FantasyMatrixDisplay:
    def __init__(self):
        """Initialize the MatrixPortal and display"""
        print("Initializing Fantasy Football Matrix Display...")
        print(f"Using color order: {COLOR_ORDER}")

        # Initialize MatrixPortal with proper color_order parameter
        # This handles pin swapping automatically for different panel types
        self.matrixportal = MatrixPortal(
            width=64,
            height=32,
            bit_depth=2,  # Use 2 for stable multi-channel colors (bit_depth=4 breaks mixed colors)
            color_order=COLOR_ORDER,  # Handles G/B swap for 64x32 2.5mm panels
            status_neopixel=None,
        )

        # Set up network requests separately
        pool = socketpool.SocketPool(wifi.radio)
        self.requests = adafruit_requests.Session(pool, ssl.create_default_context())

        # Display setup - use MatrixPortal's display and root_group
        self.display = self.matrixportal.display
        self.display.brightness = 0.8
        self.group = self.display.root_group

        # Data storage
        self.matchups = []
        self.current_matchup_index = 0
        self.last_api_call = 0

        print("Matrix Portal initialized!")
    
    def connect_wifi(self, ssid, password):
        """Connect to WiFi network"""
        print(f"Connecting to WiFi: {ssid}")
        try:
            wifi.radio.connect(ssid, password)
            print(f"Connected! IP: {wifi.radio.ipv4_address}")
            return True
        except Exception as e:
            print(f"WiFi connection failed: {e}")
            return False
    
    def fetch_matchups(self):
        """Fetch fresh matchup data from API"""
        try:
            print(f"Fetching data from: {API_URL}")
            response = self.requests.get(API_URL, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.matchups = data["matchups"]
                print(f"Fetched {len(self.matchups)} matchups for Week {data['week']}")
                return True
            else:
                print(f"API error: {response.status_code}")
                return False

        except Exception as e:
            print(f"Network error: {e}")
            return False
        finally:
            response.close() if 'response' in locals() else None
    
    def create_matchup_display(self, matchup):
        """Create display elements for a single matchup"""
        home = matchup["home_team"]
        away = matchup["away_team"]

        # Round probabilities
        home_prob = round(matchup["home_win_probability"] * 100)
        away_prob = 100 - home_prob

        # Use pure single-channel colors only (CP10 multi-channel bug)
        matchup_idx = matchup["matchup_index"]
        home_color = HOME_TEAM_COLOR  # Red
        away_color = AWAY_TEAM_COLOR  # Red (TESTING)

        print(f"Matchup {matchup_idx}: TESTING - All BLUE to test stability")

        # Line 2: Scores - home (left), away (right)
        # Green for winning score, white for losing score (single-channel colors only)
        home_score_val = home['current_score']
        away_score_val = away['current_score']

        if home_score_val > away_score_val:
            home_score_color = WINNING_SCORE_COLOR  # Green (winning)
            away_score_color = LOSING_SCORE_COLOR   # Red (losing)
        elif away_score_val > home_score_val:
            home_score_color = LOSING_SCORE_COLOR   # Red (losing)
            away_score_color = WINNING_SCORE_COLOR  # Green (winning)
        else:
            # Tied - both red
            home_score_color = LOSING_SCORE_COLOR
            away_score_color = LOSING_SCORE_COLOR

        # Line 3: Win probability bar (visual split bar)
        bar_width = 64  # Full width of display
        bar_height = 4  # Roughly text height
        bar_y = 24  # Slightly higher to center better

        # Calculate split based on probabilities
        home_bar_width = int((home_prob / 100) * bar_width)
        away_bar_width = bar_width - home_bar_width
        
        # Bar colors match team colors (pure single-channel only)
        home_bar_color = WIN_BAR_HOME_COLOR  # Red
        away_bar_color = WIN_BAR_AWAY_COLOR  # Blue

        # Create a new group for this matchup to avoid display timing issues
        new_group = displayio.Group()
        
        # Line 1: Team abbreviations - home (left), away (right)
        home_team = label.Label(
            terminalio.FONT,
            text=home["team_abbrev"],
            color=home_color,
            x=0, y=6
        )
        new_group.append(home_team)

        # Calculate right alignment for away team
        away_x = max(0, 64 - (len(away["team_abbrev"]) * 6))
        away_team = label.Label(
            terminalio.FONT,
            text=away["team_abbrev"],
            color=away_color,
            x=away_x, y=6
        )
        new_group.append(away_team)

        # Add home score
        home_score_text = f"{home_score_val:.1f}"
        home_score = label.Label(
            terminalio.FONT,
            text=home_score_text,
            color=home_score_color,
            x=0, y=16
        )
        new_group.append(home_score)

        # Add away score
        away_score_text = f"{away_score_val:.1f}"
        away_score_x = max(0, 64 - (len(away_score_text) * 6))
        away_score = label.Label(
            terminalio.FONT,
            text=away_score_text,
            color=away_score_color,
            x=away_score_x, y=16
        )
        new_group.append(away_score)

        # Home team probability bar (left side)
        home_prob_bar = Rect(
            x=0,
            y=bar_y,
            width=home_bar_width,
            height=bar_height,
            fill=home_bar_color
        )
        new_group.append(home_prob_bar)

        # Away team probability bar (right side)
        away_prob_bar = Rect(
            x=home_bar_width,
            y=bar_y,
            width=away_bar_width,
            height=bar_height,
            fill=away_bar_color
        )
        new_group.append(away_prob_bar)

        # Atomically swap the display group to avoid flicker/color changes
        self.display.root_group = new_group
        self.group = new_group

        print(f"Displaying: {home['team_abbrev']} vs {away['team_abbrev']} ({home_prob}%-{away_prob}%)")
    
    def run(self, wifi_ssid, wifi_password):
        """Main display loop"""
        # Connect to WiFi
        if not self.connect_wifi(wifi_ssid, wifi_password):
            print("ERROR: Cannot continue without WiFi")
            return

        # Initial data fetch
        if not self.fetch_matchups():
            print("ERROR: Cannot continue without initial data")
            return

        print("Starting display loop...")
        
        while True:
            try:
                # Display current matchup if we have data
                if self.matchups:
                    matchup = self.matchups[self.current_matchup_index]
                    self.create_matchup_display(matchup)

                    # Wait before showing next matchup
                    time.sleep(DISPLAY_TIME)

                    # Move to next matchup
                    self.current_matchup_index = (self.current_matchup_index + 1) % len(self.matchups)
                    
                    # Only refresh data after completing a full cycle through all matchups
                    if self.current_matchup_index == 0:
                        current_time = time.monotonic()
                        if current_time - self.last_api_call > REFRESH_INTERVAL:
                            print("Refreshing data after full cycle...")
                            if self.fetch_matchups():
                                self.last_api_call = current_time
                else:
                    print("No matchup data, retrying...")
                    time.sleep(5)

            except Exception as e:
                print(f"Display error: {e}")
                time.sleep(5)


# Main execution
if __name__ == "__main__":
    # Create and run display
    display = FantasyMatrixDisplay()
    
    # Get WiFi credentials from settings.toml
    WIFI_SSID = os.getenv("CIRCUITPY_WIFI_SSID")
    WIFI_PASSWORD = os.getenv("CIRCUITPY_WIFI_PASSWORD")
    
    if not WIFI_SSID or not WIFI_PASSWORD:
        print("ERROR: WiFi credentials not found in settings.toml")
        print("Please update settings.toml with your WiFi info")
    else:
        display.run(WIFI_SSID, WIFI_PASSWORD)