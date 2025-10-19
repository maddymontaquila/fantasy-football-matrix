"""
Test if BLUE channel only works on half the screen
"""
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_display_text import label
import terminalio
import time

COLOR_ORDER = "RGB"

print(f"Testing BLUE on different parts of screen with order: {COLOR_ORDER}")

# Initialize display
matrixportal = MatrixPortal(
    width=64,
    height=32,
    bit_depth=4,
    color_order=COLOR_ORDER,
    status_neopixel=None,
)

matrixportal.display.brightness = 0.8
group = matrixportal.display.root_group

# All BLUE text at different positions
# Top of screen
label1 = label.Label(
    terminalio.FONT,
    text="BLUE1",
    color=0x0000FF,
    x=2, y=4
)
group.append(label1)

# Quarter screen
label2 = label.Label(
    terminalio.FONT,
    text="BLUE2",
    color=0x0000FF,
    x=2, y=10
)
group.append(label2)

# Half screen
label3 = label.Label(
    terminalio.FONT,
    text="BLUE3",
    color=0x0000FF,
    x=2, y=16
)
group.append(label3)

# Three-quarter screen
label4 = label.Label(
    terminalio.FONT,
    text="BLUE4",
    color=0x0000FF,
    x=2, y=22
)
group.append(label4)

# Bottom of screen
label5 = label.Label(
    terminalio.FONT,
    text="BLUE5",
    color=0x0000FF,
    x=2, y=28
)
group.append(label5)

print("\nShowing 5 BLUE labels at different Y positions:")
print("  BLUE1 at y=4")
print("  BLUE2 at y=10")
print("  BLUE3 at y=16 (middle)")
print("  BLUE4 at y=22")
print("  BLUE5 at y=28")
print("\nCheck if blue appears on all of them or only some!")

while True:
    time.sleep(1)
