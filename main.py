
import pygame
import cv2
import numpy as np
import random
import math
import os

# ==========================================
# 1. INITIALIZATION
# ==========================================

pygame.init()

# Original image ratio: 35:54
W, H = 630, 972

FPS = 60

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Medusa - Digital Painting")

clock = pygame.time.Clock()

BG = (4, 4, 12)

random.seed(7)
np.random.seed(7)

# ==========================================
# 2. IMAGE SETTINGS
# ==========================================

IMAGE_PATH = "medusa.jpg"

if not os.path.exists(IMAGE_PATH):
    raise FileNotFoundError(
        "medusa.jpg not found! Put it beside main.py."
    )

original = cv2.imread(IMAGE_PATH)

if original is None:
    raise ValueError("Unable to load medusa.jpg")

# ==========================================
# 3. PRESERVE ORIGINAL IMAGE
# ==========================================

# Resize without cropping or stretching
original = cv2.resize(
    original,
    (W, H),
    interpolation=cv2.INTER_AREA
)

# Slight color enhancement
hsv = cv2.cvtColor(
    original,
    cv2.COLOR_BGR2HSV
)

h, s, v = cv2.split(hsv)

s = np.clip(
    s.astype(np.float32) * 1.08,
    0, 255
).astype(np.uint8)

hsv = cv2.merge((h, s, v))

enhanced = cv2.cvtColor(
    hsv,
    cv2.COLOR_HSV2BGR
)

# Preserve the original painting details
rgb = cv2.cvtColor(
    enhanced,
    cv2.COLOR_BGR2RGB
)

painting_surface = pygame.surfarray.make_surface(
    rgb.swapaxes(0, 1)
)

# ==========================================
# 4. CREATE SKETCH EDGES
# ==========================================

gray = cv2.cvtColor(
    original,
    cv2.COLOR_BGR2GRAY
)

smooth = cv2.bilateralFilter(
    gray,
    9,
    75,
    75
)

edges = cv2.Canny(
    smooth,
    35,
    110
)

# Make sketch lines slightly thicker
kernel = np.ones(
    (2, 2),
    np.uint8
)

edges = cv2.dilate(
    edges,
    kernel,
    iterations=1
)

# ==========================================
# 5. ANIMATION SETTINGS
# ==========================================

TRACE_START = 0.2
TRACE_SPREAD = 8.5

FILL_START = 7.0
FILL_END = 13.0

SHIMMER_START = 13.4
SHIMMER_DUR = 2.4

TEXT_START = 16.0

FADE_START = 23.0
DURATION = 25.0

TWINKLES = 35

QUOTE = (
    "They Called It A Punishment,"
    "\nBut She Called It Freedom."
)

# Center focus point
FOCUS_REL = (0.50, 0.42)

# Turquoise drawing colors (RGB)
STOPS = [
    (100, 255, 210),
    (40, 235, 175),
    (40, 195, 230),
    (100, 160, 255),
    (180, 255, 240)
]

# ==========================================
# 6. EASING FUNCTIONS
# ==========================================

def ease_in_out(x):

    x = max(0, min(1, x))

    if x < 0.5:
        return 4 * x ** 3

    return 1 - ((-2 * x + 2) ** 3) / 2


def ease_sine(x):

    x = max(0, min(1, x))

    return (1 - math.cos(math.pi * x)) / 2


def ease_out(x):

    x = max(0, min(1, x))

    return 1 - (1 - x) ** 3


# ==========================================
# 7. COLOR PALETTE
# ==========================================

def palette(t):

    t = max(0, min(1, t))

    pos = t * (len(STOPS) - 1)

    i = min(
        int(pos),
        len(STOPS) - 2
    )

    f = pos - i

    a = np.array(
        STOPS[i],
        dtype=float
    )

    b = np.array(
        STOPS[i + 1],
        dtype=float
    )

    result = a + (b - a) * f

    return tuple(
        np.clip(result, 0, 255).astype(int)
    )


# ==========================================
# 8. EXTRACT CONTOURS
# ==========================================

contours, _ = cv2.findContours(
    edges,
    cv2.RETR_LIST,
    cv2.CHAIN_APPROX_NONE
)

focus_x = int(W * FOCUS_REL[0])
focus_y = int(H * FOCUS_REL[1])

segments = []

SEG_LEN = 100

for contour in contours:

    points = contour.reshape(-1, 2)

    if len(points) < 5:
        continue

    for i in range(
        0,
        len(points) - 1,
        SEG_LEN
    ):

        part = points[i:i + SEG_LEN]

        if len(part) < 2:
            continue

        center = np.mean(
            part,
            axis=0
        )

        distance = math.sqrt(
            (center[0] - focus_x) ** 2 +
            (center[1] - focus_y) ** 2
        )

        segments.append({

            "points": part,

            "distance": distance

        })

# Reveal from the center outward
segments.sort(
    key=lambda item: item["distance"]
)

# ==========================================
# 9. SKETCH LAYER
# ==========================================

sketch_layer = pygame.Surface(
    (W, H),
    pygame.SRCALPHA
)

last_reveal_count = 0

# ==========================================
# 10. SPARKLES
# ==========================================

stars = []

for i in range(TWINKLES):

    stars.append({

        "x": random.randint(15, W - 15),

        "y": random.randint(15, H - 15),

        "phase": random.uniform(
            0,
            math.pi * 2
        ),

        "size": random.randint(1, 2)

    })


# ==========================================
# 11. DRAW SKETCH SEGMENTS
# ==========================================

def draw_segment(surface, segment):

    points = segment["points"]

    if len(points) < 2:
        return

    color = palette(
        segment["distance"] /
        math.sqrt(W ** 2 + H ** 2)
    )

    pygame_points = [
        (int(p[0]), int(p[1]))
        for p in points
    ]

    pygame.draw.lines(
        surface,
        color,
        False,
        pygame_points,
        1
    )


# ==========================================
# 12. SPARKLE ANIMATION
# ==========================================

def draw_stars(surface, elapsed):

    for star in stars:

        brightness = (
            math.sin(
                elapsed * 3 + star["phase"]
            ) + 1
        ) / 2

        brightness = int(
            90 + brightness * 150
        )

        color = (
            brightness // 2,
            brightness,
            brightness
        )

        pygame.draw.circle(
            surface,
            color,
            (star["x"], star["y"]),
            star["size"]
        )


# ==========================================
# 13. QUOTE ANIMATION
# ==========================================

def draw_quote(surface, elapsed):

    if elapsed < TEXT_START:
        return

    font = pygame.font.SysFont(
        "serif",
        19,
        italic=True
    )

    lines = QUOTE.split("\n")

    progress = min(
        1,
        (elapsed - TEXT_START) / 2.5
    )

    alpha = int(
        230 * ease_out(progress)
    )

    # Subtle dark background behind text
    overlay = pygame.Surface(
        (W, 65),
        pygame.SRCALPHA
    )

    overlay.fill(
        (0, 0, 0, 75)
    )

    overlay.set_alpha(alpha)

    surface.blit(
        overlay,
        (0, H - 75)
    )

    for i, line in enumerate(lines):

        text_surface = font.render(
            line,
            True,
            (170, 255, 230)
        )

        text_surface.set_alpha(alpha)

        rect = text_surface.get_rect(
            center=(
                W // 2,
                H - 49 + i * 22
            )
        )

        surface.blit(
            text_surface,
            rect
        )


# ==========================================
# 14. MAIN ANIMATION
# ==========================================

def reset_animation():

    global start_ticks
    global last_reveal_count

    start_ticks = pygame.time.get_ticks()

    last_reveal_count = 0

    sketch_layer.fill(
        (0, 0, 0, 0)
    )


start_ticks = pygame.time.get_ticks()

running = True

while running:

    clock.tick(FPS)

    # ======================================
    # EVENTS
    # ======================================

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:

                running = False

            if event.key == pygame.K_r:

                reset_animation()

    # ======================================
    # TIMER
    # ======================================

    elapsed = (
        pygame.time.get_ticks() - start_ticks
    ) / 1000

    screen.fill(BG)

    # ======================================
    # 1. SKETCH REVEAL
    # ======================================

    if elapsed >= TRACE_START:

        progress = min(
            1,
            (elapsed - TRACE_START) /
            TRACE_SPREAD
        )

        reveal_count = int(
            len(segments) *
            ease_in_out(progress)
        )

        # Draw only new segments
        for i in range(
            last_reveal_count,
            reveal_count
        ):

            draw_segment(
                sketch_layer,
                segments[i]
            )

        last_reveal_count = reveal_count

    # ======================================
    # 2. ORIGINAL COLOR PAINTING REVEAL
    # ======================================

    if elapsed < FILL_START:

        fill_alpha = 0

    else:

        fill_progress = min(
            1,
            (elapsed - FILL_START) /
            (FILL_END - FILL_START)
        )

        fill_alpha = int(
            255 * ease_sine(fill_progress)
        )

    # Draw the original full-color painting
    if fill_alpha > 0:

        color_layer = painting_surface.copy()

        color_layer.set_alpha(
            fill_alpha
        )

        screen.blit(
            color_layer,
            (0, 0)
        )

    # ======================================
    # 3. REMOVE GREEN / CYAN SKETCH LINES
    # ======================================

    if elapsed < FILL_START:

        sketch_alpha = 255

    elif elapsed < FILL_END:

        fade_progress = (
            (elapsed - FILL_START) /
            (FILL_END - FILL_START)
        )

        sketch_alpha = int(
            255 * (
                1 - ease_sine(fade_progress)
            )
        )

    else:

        sketch_alpha = 0

    # Draw sketch only while visible
    if sketch_alpha > 0:

        sketch_display = sketch_layer.copy()

        sketch_display.set_alpha(
            sketch_alpha
        )

        screen.blit(
            sketch_display,
            (0, 0)
        )

    # ======================================
    # 4. SHIMMER EFFECT
    # ======================================

    if (
        SHIMMER_START <= elapsed <=
        SHIMMER_START + SHIMMER_DUR
    ):

        shimmer_progress = (
            elapsed - SHIMMER_START
        ) / SHIMMER_DUR

        shimmer_x = int(
            -100 + (W + 200) *
            shimmer_progress
        )

        shimmer_layer = pygame.Surface(
            (W, H),
            pygame.SRCALPHA
        )

        pygame.draw.line(
            shimmer_layer,
            (120, 255, 220, 65),
            (shimmer_x, 0),
            (shimmer_x - 200, H),
            30
        )

        screen.blit(
            shimmer_layer,
            (0, 0)
        )

    # ======================================
    # 5. SPARKLES
    # ======================================

    if elapsed >= FILL_END:

        draw_stars(
            screen,
            elapsed
        )

    # ======================================
    # 6. QUOTE
    # ======================================

    draw_quote(
        screen,
        elapsed
    )

    # ======================================
    # 7. FADE OUT
    # ======================================

    if elapsed >= FADE_START:

        fade_progress = min(
            1,
            (elapsed - FADE_START) / 2
        )

        fade = pygame.Surface(
            (W, H)
        )

        fade.fill((0, 0, 0))

        fade.set_alpha(
            int(255 * fade_progress)
        )

        screen.blit(
            fade,
            (0, 0)
        )

    # ======================================
    # 8. UPDATE DISPLAY
    # ======================================

    pygame.display.flip()

    # ======================================
    # 9. RESTART AFTER 25 SECONDS
    # ======================================

    if elapsed >= DURATION:

        reset_animation()


pygame.quit()
