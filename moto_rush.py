"""
MOTO RUSH PRO — Python/Pygame Port
Requirements: pip install pygame
Run: python moto_rush.py
"""

import pygame
import random
import math
import json
import os
import sys

# ── INIT ──────────────────────────────────────────────────────────────[...]
pygame.init()
pygame.display.set_caption("MOTO RUSH PRO")

W, H = 900, 650
screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)
clock  = pygame.time.Clock()

# ── FONTS ─────────────────────────────────────────────────────────────[...]
def font(size, bold=False):
    return pygame.font.SysFont("Arial", size, bold=bold)

F_TITLE  = font(52, True)
F_MED    = font(22, True)
F_SMALL  = font(14)
F_TINY   = font(11)

# ── COLOURS ───────────────────────────────────────────────────────────[...]
GOLD    = (255, 215,   0)
ORANGE  = (255, 107,   0)
RED     = (220,  30,  30)
GREEN   = (  0, 220, 100)
BLUE    = (  0, 180, 255)
WHITE   = (255, 255, 255)
BLACK   = (  0,   0,   0)
DARK    = (  6,   8,  16)
GRAY    = (120, 120, 130)
ROAD_C  = ( 34,  34,  34)
GRASS_C = ( 13,  31,  10)
YELLOW  = (255, 230,   0)

CAR_COLORS = [
    (231,  76,  60), ( 52, 152, 219), ( 46, 204, 113),
    (243, 156,  18), (155,  89, 182), ( 26, 188, 156),
    (230, 126,  34), (236, 240, 241), (192,  57,  43),
    ( 39, 174,  96),
]

# ── SAVE / LOAD ───────────────────────────────────────────────────────[...]
SAVE_FILE = "moto_save.json"

def load_save():
    defaults = {
        "coins": 0,
        "owned": ["sport_bike"],
        "selected": "sport_bike",
        "unlocked_levels": 1,
    }
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE) as f:
                data = json.load(f)
                defaults.update(data)
        except Exception:
            pass
    return defaults

def write_save(save):
    with open(SAVE_FILE, "w") as f:
        json.dump(save, f)

SAVE = load_save()

# ── VEHICLES ──────────────────────────────────────────────────────────[...]
VEHICLES = [
    {"id": "sport_bike",  "name": "Sport Bike",  "price":    0, "max_speed": 180, "accel": 50, "color": RED,              "desc": "Starter ride"},
    {"id": "ninja_r",     "name": "Ninja R",      "price":  800, "max_speed": 220, "accel": 60, "color": BLUE,             "desc": "Track beast"},
    {"id": "chopper",     "name": "Chopper",      "price":  600, "max_speed": 170, "accel": 40, "color": ORANGE,           "desc": "Heavy cruiser"},
    {"id": "super_car",   "name": "SuperCar",     "price": 1500, "max_speed": 260, "accel": 70, "color": GOLD,             "desc": "Ultimate machine"},
    {"id": "muscle_car",  "name": "Muscle Car",   "price": 1200, "max_speed": 240, "accel": 65, "color": (200, 34,   0),   "desc": "Raw power"},
    {"id": "moto_gp",     "name": "MotoGP",       "price": 2000, "max_speed": 300, "accel": 75, "color": (200,  0, 255),   "desc": "Racing legend"},
]

# ── LEVELS ────────────────────────────────────────────────────────────[...]
LEVELS = [
    {"n": 1, "name": "City Streets",   "goal":  500, "car_speed": (30,  55), "car_rate": 90,  "max_speed": 180},
    {"n": 2, "name": "Highway Chase",  "goal": 1000, "car_speed": (40,  70), "car_rate": 75,  "max_speed": 210},
    {"n": 3, "name": "Storm Run",      "goal": 1500, "car_speed": (50,  85), "car_rate": 60,  "max_speed": 230},
    {"n": 4, "name": "Night Blitz",    "goal": 2200, "car_speed": (60, 100), "car_rate": 50,  "max_speed": 250},
    {"n": 5, "name": "Desert Fury",    "goal": 3000, "car_speed": (70, 115), "car_rate": 40,  "max_speed": 270},
    {"n": 6, "name": "ULTRA SPEED",    "goal": 4000, "car_speed": (80, 130), "car_rate": 32,  "max_speed": 300},
]

N_LANES = 5

# ── HELPERS ───────────────────────────────────────────────────────────[...]
def lerp(a, b, t):
    return a + (b - a) * t

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def draw_text(surf, text, fnt, color, cx, cy, anchor="center"):
    img = fnt.render(str(text), True, color)
    r   = img.get_rect()
    setattr(r, anchor, (cx, cy))
    surf.blit(img, r)

def draw_rect_alpha(surf, color, rect, alpha=180, radius=0):
    s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha), (0, 0, rect[2], rect[3]), border_radius=radius)
    surf.blit(s, (rect[0], rect[1]))

def draw_circle_alpha(surf, color, cx, cy, r, alpha=180):
    s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
    pygame.draw.circle(s, (*color, alpha), (r, r), r)
    surf.blit(s, (cx - r, cy - r))

# ── PARTICLE ──────────────────────────────────────────────────────────[...]
class Particle:
    def __init__(self, x, y, vx, vy, color, radius, life):
        self.x, self.y   = x, y
        self.vx, self.vy = vx, vy
        self.color       = color
        self.r           = radius
        self.life        = life
        self.max_life    = life

    def update(self, dt):
        self.x  += self.vx * dt
        self.y  += self.vy * dt
        self.vy += 300 * dt          # gravity
        self.life -= dt
        return self.life > 0

    def draw(self, surf):
        ratio = self.life / self.max_life
        alpha = int(ratio * 220)
        r = max(1, int(self.r * ratio))
        draw_circle_alpha(surf, self.color, int(self.x), int(self.y), r, alpha)

# ── TRAFFIC CAR ───────────────────────────────────────────────────────[...]
class TrafficCar:
    TYPES = ["car", "truck"]  # Only cars and trucks

    def __init__(self, lane, lane_x, speed):
        self.lane   = lane
        self.x      = lane_x
        self.y      = -140.0
        self.vy     = speed
        self.color  = random.choice(CAR_COLORS)
        self.kind   = random.choice(self.TYPES)
        self.passed = False
        self.w      = {"car": 38, "truck": 56}[self.kind]
        self.h      = {"car": 80, "truck":110}[self.kind]

    def update(self, dt, player_speed):
        self.y += (player_speed - self.vy) * dt * 2.8

    def draw(self, surf, scale=1.0):
        cx, cy = int(self.x), int(self.y)
        w, h   = int(self.w * scale), int(self.h * scale)
        col    = self.color
        
        # Shadow
        draw_circle_alpha(surf, BLACK, cx+3, cy+6, int(w//3 * scale), int(80 * scale))
        
        # Body
        body = pygame.Rect(cx - w//2, cy - h//2, w, h)
        pygame.draw.rect(surf, col, body, border_radius=max(2, int(5*scale)))
        
        # Roof
        roof_w, roof_h = int(w * 0.65), int(h * 0.42)
        roof = pygame.Rect(cx - roof_w//2, cy - h//2 - roof_h + int(4*scale), roof_w, roof_h)
        dark = tuple(max(0, c - 60) for c in col)
        pygame.draw.rect(surf, dark, roof, border_radius=max(2, int(4*scale)))
        
        # Windshield
        ws = pygame.Rect(cx - roof_w//2 + int(4*scale), cy - h//2 - roof_h + int(8*scale), roof_w - int(8*scale), roof_h - int(10*scale))
        pygame.draw.rect(surf, (100, 170, 220), ws, border_radius=max(1, int(3*scale)))
        
        # Headlights
        hl_size_x = max(3, int(10*scale))
        hl_size_y = max(2, int(6*scale))
        pygame.draw.ellipse(surf, (255, 240, 180), (cx - w//2 + int(3*scale), cy - h//2 + int(4*scale), hl_size_x, hl_size_y))
        pygame.draw.ellipse(surf, (255, 240, 180), (cx + w//2 - int(13*scale), cy - h//2 + int(4*scale), hl_size_x, hl_size_y))
        
        # Tail lights
        pygame.draw.ellipse(surf, (220, 40, 20), (cx - w//2 + int(3*scale), cy + h//2 - int(10*scale), hl_size_x, hl_size_y))
        pygame.draw.ellipse(surf, (220, 40, 20), (cx + w//2 - int(13*scale), cy + h//2 - int(10*scale), hl_size_x, hl_size_y))
        
        # Outline
        pygame.draw.rect(surf, tuple(max(0, c-80) for c in col), body, max(1, int(1*scale)), border_radius=max(2, int(5*scale)))

# ── COIN ──────────────────────────────────────────────────────────────[...]
class Coin:
    def __init__(self, lane, lane_x):
        self.lane = lane
        self.x    = lane_x
        self.y    = -60.0
        self.spin = random.random() * math.pi * 2
        self.bob  = random.random() * math.pi * 2
        self.collected = False

    def update(self, dt, player_speed):
        self.y   += (player_speed * 0.4 - 10) * dt * 2.8 + 80 * dt
        self.spin += 3 * dt
        self.bob  += 2 * dt

    def draw(self, surf, scale=1.0):
        cx = int(self.x)
        cy = int(self.y + math.sin(self.bob) * 4)
        squish = abs(math.cos(self.spin))
        r = int(14 * scale)
        
        # Glow
        draw_circle_alpha(surf, GOLD, cx, cy, int(r * 2.2), int(50 * scale))
        
        # Outer ring
        w_half = max(2, int(r * squish))
        rect = pygame.Rect(cx - w_half, cy - r, w_half * 2, r * 2)
        pygame.draw.ellipse(surf, (184, 134, 11), rect)
        
        inner = pygame.Rect(cx - max(1, int(w_half*0.85)), cy - int(r*0.85), max(2, int(w_half*1.7)), int(r*1.7))
        pygame.draw.ellipse(surf, GOLD, inner)
        
        if squish > 0.3 and scale > 0.5:
            label = F_TINY.render("$", True, (100, 60, 0))
            surf.blit(label, label.get_rect(center=(cx, cy)))

# ── PLAYER ────────────────────────────────────────────────────────────[...]
class Player:
    def __init__(self, lanes, veh):
        self.lanes      = lanes
        self.lane       = 2
        self.target_lane= 2
        self.x          = float(lanes[2])
        self.speed      = 30.0
        self.max_speed  = float(veh["max_speed"])
        self.accel      = float(veh["accel"])
        self.tilt       = 0.0
        self.wheel_spin = 0.0
        self.color      = veh["color"]

    def update(self, dt, keys):
        # Speed - SLOWER acceleration when pressing W/UP
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.speed = min(self.max_speed, self.speed + self.accel * dt)
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.speed = max(0, self.speed - 150 * dt)
        else:
            # Natural deceleration when no keys pressed
            self.speed = max(20, self.speed - 30 * dt)

        # Lane steering - player moves left/right but STAYS IN PLACE vertically
        tx = self.lanes[self.target_lane]
        diff = tx - self.x
        self.x += diff * 9 * dt
        self.tilt += (diff * 0.012 - self.tilt) * 9 * dt
        self.wheel_spin += self.speed * dt * 0.18

    def draw(self, surf):
        cx = int(self.x)
        cy = H - 110  # Player ALWAYS stays at bottom
        col = self.color
        lean = int(self.tilt * 28)

        # Shadow
        draw_circle_alpha(surf, BLACK, cx + lean//3 + 2, cy + 8, 32, 90)

        # Rear wheel
        pygame.draw.circle(surf, (15, 15, 15), (cx - 30 + lean//4, cy), 18)
        pygame.draw.circle(surf, (60, 60, 60), (cx - 30 + lean//4, cy), 18, 3)
        pygame.draw.circle(surf, (80, 80, 80), (cx - 30 + lean//4, cy), 10, 2)

        # Front wheel
        pygame.draw.circle(surf, (15, 15, 15), (cx + 34 + lean//3, cy - 14), 13)
        pygame.draw.circle(surf, (60, 60, 60), (cx + 34 + lean//3, cy - 14), 13, 2)

        # Frame
        pygame.draw.line(surf, (25, 25, 25), (cx - 28 + lean//4, cy - 4),
                         (cx + lean//2, cy - 55), 7)
        pygame.draw.line(surf, (25, 25, 25), (cx + lean//2, cy - 55),
                         (cx + 34 + lean//3, cy - 14), 5)

        # Body / fairing
        body = pygame.Rect(cx + lean - 18, cy - 90, 36, 42)
        dark = tuple(max(0, c - 60) for c in col)
        pygame.draw.rect(surf, dark, body, border_radius=5)
        inner = pygame.Rect(cx + lean - 16, cy - 88, 32, 38)
        pygame.draw.rect(surf, col, inner, border_radius=5)
        # Stripe
        stripe = pygame.Rect(cx + lean - 16, cy - 88, 32, 7)
        pygame.draw.rect(surf, (255, 255, 255, 40), stripe, border_radius=2)

        # Lower fairing
        lf = pygame.Rect(cx + lean - 14, cy - 50, 28, 22)
        pygame.draw.rect(surf, dark, lf, border_radius=4)

        # Headlight
        pygame.draw.ellipse(surf, (255, 240, 180),
                            (cx + lean + 12, cy - 87, 12, 8))
        draw_circle_alpha(surf, (255, 240, 180), cx + lean + 18, cy - 83, 18, 50)

        # Rider body
        pygame.draw.rect(surf, (20, 20, 60),
                         (cx + lean - 10, cy - 85, 22, 38), border_radius=4)
        pygame.draw.rect(surf, col,
                         (cx + lean - 10, cy - 85, 22, 6), border_radius=2)

        # Helmet
        pygame.draw.circle(surf, col, (cx + lean, cy - 94), 14)
        # Visor
        pygame.draw.arc(surf, (100, 160, 220, 180),
                        (cx + lean - 11, cy - 105, 22, 22),
                        math.radians(200), math.radians(340), 5)
        pygame.draw.circle(surf, tuple(max(0, c-80) for c in col),
                           (cx + lean, cy - 94), 14, 2)

        # Legs
        pygame.draw.rect(surf, (15, 15, 50),
                         (cx + lean - 12, cy - 48, 10, 26), border_radius=3)
        pygame.draw.rect(surf, (15, 15, 50),
                         (cx + lean + 2, cy - 48, 10, 26), border_radius=3)

# ── ROAD DRAWING ──────────────────────────────────────────────────────[...]
def draw_road(surf, lanes, road_offset, mark_offset):
    rl, rr = int(W * 0.06), int(W * 0.94)
    vy = H // 2

    # Sky gradient with subtle animation
    for y in range(vy):
        t = y / vy
        r = int(lerp(8, 20, t))
        g = int(lerp(12, 30, t))
        b = int(lerp(22, 50, t))
        surf.fill((r, g, b), (0, y, W, 1))

    # Stars with twinkling
    for i in range(100):
        sx = (i * 173 + 7) % W
        sy = (i * 97 + 13) % vy
        br = int(180 + 50 * math.sin(road_offset * 0.01 + i)) if i % 3 == 0 else int(100 + 30 * math.sin(road_offset * 0.01 + i))
        surf.fill((br, br, br), (sx, sy, 2, 2))

    # Moon with enhanced glow
    moon_x, moon_y = int(W * 0.82), int(H * 0.07)
    pygame.draw.circle(surf, (255, 255, 220), (moon_x, moon_y), 18)
    draw_circle_alpha(surf, (255, 240, 180), moon_x, moon_y, 45, 80)
    draw_circle_alpha(surf, (255, 220, 100), moon_x, moon_y, 65, 40)

    # Grass
    surf.fill(GRASS_C, (0, vy, W, H - vy))

    # Road trapezoid
    road_pts = [
        (int(W * 0.28), vy),
        (int(W * 0.72), vy),
        (rr, H),
        (rl, H),
    ]
    pygame.draw.polygon(surf, ROAD_C, road_pts)

    # Edge lines with glow
    pygame.draw.line(surf, WHITE, (int(W*0.28), vy), (rl, H), 4)
    pygame.draw.line(surf, WHITE, (int(W*0.72), vy), (rr, H), 4)
    draw_circle_alpha(surf, WHITE, int(W*0.28), vy, 8, 100)
    draw_circle_alpha(surf, WHITE, rl, H, 8, 100)
    draw_circle_alpha(surf, WHITE, int(W*0.72), vy, 8, 100)
    draw_circle_alpha(surf, WHITE, rr, H, 8, 100)

    # Lane dashes with enhanced appearance
    for li in range(1, N_LANES):
        t = li / (N_LANES + 1)
        tx = int(W*0.28 + W*0.44 * t)
        bx = int(rl + (rr - rl) * t)
        steps = 18
        for s in range(steps):
            frac = (s / steps + mark_offset / 70) % 1
            y1 = int(vy + frac * (H - vy))
            y2 = int(vy + ((s + 0.5) / steps + mark_offset / 70) % 1 * (H - vy))
            x1 = int(lerp(tx, bx, frac))
            x2 = int(lerp(tx, bx, (frac + 0.04) % 1))
            if y1 < y2:
                pygame.draw.line(surf, (220, 220, 220), (x1, y1), (x2, y2), 3)

    # Streetlights with enhanced glow
    for i in range(8):
        frac = ((i / 8) + road_offset / H * 0.5) % 1
        py   = int(vy + frac * (H - vy))
        sc   = lerp(0.05, 1, frac)
        lx   = int(W * 0.28 - sc * (W * 0.22))
        rx   = int(W * 0.72 + sc * (W * 0.20))
        pole_h = int(50 * sc)
        
        # Poles
        pygame.draw.line(surf, (70, 70, 80), (lx, py), (lx, py - pole_h), max(2, int(3*sc)))
        pygame.draw.line(surf, (70, 70, 80), (rx, py), (rx, py - pole_h), max(2, int(3*sc)))
        
        if sc > 0.3:
            # Enhanced glow
            draw_circle_alpha(surf, (255, 240, 180), lx, py - pole_h, int(40*sc), int(sc*180))
            draw_circle_alpha(surf, (255, 220, 100), lx, py - pole_h, int(50*sc), int(sc*100))
            draw_circle_alpha(surf, (255, 240, 180), rx, py - pole_h, int(40*sc), int(sc*180))
            draw_circle_alpha(surf, (255, 220, 100), rx, py - pole_h, int(50*sc), int(sc*100))
            
            # Light color
            pygame.draw.circle(surf, (255, 245, 200), (lx, py - pole_h), max(3, int(8*sc)), 1)
            pygame.draw.circle(surf, (255, 245, 200), (rx, py - pole_h), max(3, int(8*sc)), 1)

# ── HUD ───────────────────────────────────────────────────────────────[...]
def draw_hud(surf, score, coins, dist, level_obj, speed, max_speed):
    # Score box with glow
    draw_rect_alpha(surf, (0, 0, 0), (8, 8, 110, 50), 180, 8)
    pygame.draw.rect(surf, (100, 80, 0), (8, 8, 110, 50), 2, border_radius=8)
    draw_circle_alpha(surf, GOLD, 20, 20, 20, 40)
    draw_text(surf, "SCORE", F_TINY, GOLD, 63, 18)
    draw_text(surf, str(score), F_MED, WHITE, 63, 38)

    # Level bar with enhanced visuals
    goal = level_obj["goal"]
    pct  = clamp(dist / goal, 0, 1)
    bar_x, bar_y, bar_w, bar_h = W//2 - 100, 10, 200, 10
    draw_rect_alpha(surf, (30, 30, 30), (bar_x, bar_y, bar_w, bar_h), 220, 5)
    pygame.draw.rect(surf, (60, 60, 80), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=5)
    if pct > 0:
        fill_col = (int(lerp(0, 255, pct)), int(lerp(200, 100, pct)), 0)
        pygame.draw.rect(surf, fill_col,
                         (bar_x, bar_y, int(bar_w * pct), bar_h), border_radius=4)
        # Glow on progress bar
        draw_circle_alpha(surf, fill_col, int(bar_x + bar_w * pct), int(bar_y + bar_h//2), 15, 80)
    draw_text(surf, f"LVL {level_obj['n']}  {level_obj['name'].upper()}", F_TINY, GOLD, W//2, 26)
    draw_text(surf, f"{int(dist)}m / {goal}m", F_TINY, (180, 180, 180), W//2, 38)

    # Coins box with glow
    draw_rect_alpha(surf, (0, 0, 0), (W - 118, 8, 110, 50), 180, 8)
    pygame.draw.rect(surf, (100, 80, 0), (W - 118, 8, 110, 50), 2, border_radius=8)
    draw_circle_alpha(surf, GOLD, W - 55, 20, 20, 40)
    draw_text(surf, "COINS", F_TINY, GOLD, W - 63, 18)
    draw_text(surf, f"$ {coins}", F_MED, GOLD, W - 63, 38)

    # Speedo arc (bottom-right) with enhanced style
    sx, sy, sr = W - 65, H - 65, 52
    draw_circle_alpha(surf, (10, 12, 20), sx, sy, sr, 220)
    pygame.draw.circle(surf, (80, 70, 20), (sx, sy), sr, 3)
    pct_s = clamp(speed / max_speed, 0, 1)
    start_a = math.radians(225)
    end_a   = math.radians(225 - 270 * pct_s)
    # Draw arc segments
    steps = max(2, int(30 * pct_s))
    for i in range(steps):
        a1 = start_a - (start_a - end_a) * (i / steps)
        a2 = start_a - (start_a - end_a) * ((i+1) / steps)
        t  = i / steps
        c  = (int(lerp(0, 255, t)), int(lerp(200, 50, t)), 0)
        x1 = sx + int(math.cos(-a1) * (sr - 8))
        y1 = sy + int(math.sin(-a1) * (sr - 8))
        x2 = sx + int(math.cos(-a2) * (sr - 8))
        y2 = sy + int(math.sin(-a2) * (sr - 8))
        pygame.draw.line(surf, c, (x1, y1), (x2, y2), 6)
    draw_text(surf, f"{int(speed)}", F_MED, WHITE, sx, sy - 4)
    draw_text(surf, "km/h", F_TINY, GRAY, sx, sy + 14)

# ── SCREENS ───────────────────────────────────────────────────────────[...]
def draw_gradient_bg(surf, top=(5, 8, 16), bot=(10, 4, 20)):
    for y in range(H):
        t = y / H
        r = int(lerp(top[0], bot[0], t))
        g = int(lerp(top[1], bot[1], t))
        b = int(lerp(top[2], bot[2], t))
        surf.fill((r, g, b), (0, y, W, 1))

def main_menu(surf, menu_t):
    draw_gradient_bg(surf, (5, 4, 18), (18, 8, 4))
    # Animated road line
    dash_offset = menu_t * 60
    for i in range(20):
        dx = (i * 55 - dash_offset) % W
        pygame.draw.line(surf, (80, 60, 10), (int(dx), H//2 + 60), (int(dx + 35), H//2 + 60), 4)

    # Title
    draw_text(surf, "MOTO", F_TITLE, WHITE, W//2, H//2 - 160)
    draw_text(surf, "RUSH PRO", F_TITLE, GOLD, W//2, H//2 - 100)
    draw_text(surf, "ULTIMATE STREET RACING", F_SMALL, (180, 140, 40), W//2, H//2 - 60)

    # Animated mini bike
    bx = int(W//2 + math.sin(menu_t * 1.2) * 40)
    by = H//2 + 10
    pygame.draw.circle(surf, (25, 25, 25), (bx - 28, by + 14), 14)
    pygame.draw.circle(surf, (25, 25, 25), (bx + 32, by + 14), 10)
    pygame.draw.rect(surf, RED, (bx - 16, by - 20, 30, 28), border_radius=5)
    pygame.draw.circle(surf, RED, (bx + 2, by - 38), 12)
    pygame.draw.arc(surf, (100, 160, 220), (bx - 8, by - 47, 20, 18),
                    math.radians(200), math.radians(340), 4)
    # Speed lines
    for l in range(4):
        lx = int((bx - 80 - (l*45 + menu_t*100) % 120))
        ly = by - 10 + l * 8
        pygame.draw.line(surf, (255, 180, 0), (lx, ly), (lx + 30, ly), 3)

    # Buttons
    buttons = [
        ("  START RIDING  [ENTER]", H//2 + 80,  GOLD,  (80, 50, 0)),
        ("    GARAGE  [G]",          H//2 + 135, WHITE, (30, 30, 60)),
        ("    QUIT  [ESC]",          H//2 + 185, (200, 80, 80), (50, 15, 15)),
    ]
    for label, by2, col, bg in buttons:
        draw_rect_alpha(surf, bg, (W//2 - 130, by2 - 20, 260, 42), 220, 8)
        pygame.draw.rect(surf, col, (W//2 - 130, by2 - 20, 260, 42), 2, border_radius=8)
        draw_text(surf, label, F_MED, col, W//2, by2 + 1)

    draw_text(surf, "↑↓ Gas/Brake   ←→ Change Lane   ESC Pause", F_TINY, (80, 80, 100), W//2, H - 18)

def garage_screen(surf, selected_id, total_coins):
    draw_gradient_bg(surf, (5, 3, 18), (10, 5, 25))
    draw_text(surf, "GARAGE", F_TITLE, GOLD, W//2, 44)
    draw_text(surf, f"Your Coins: $ {total_coins}", F_MED, GOLD, W//2, 90)

    cols  = 3
    card_w, card_h = 230, 140
    pad   = 20
    total_w = cols * card_w + (cols - 1) * pad
    start_x = (W - total_w) // 2

    btn_rects = []
    for i, v in enumerate(VEHICLES):
        col_i = i % cols
        row_i = i // cols
        cx2 = start_x + col_i * (card_w + pad)
        cy2 = 125 + row_i * (card_h + pad)
        owned = v["id"] in SAVE["owned"]
        sel   = v["id"] == selected_id
        bg    = (40, 30, 0) if sel else (15, 15, 30)
        border_col = GOLD if sel else ((0, 180, 80) if owned else (80, 80, 120))
        draw_rect_alpha(surf, bg, (cx2, cy2, card_w, card_h), 230, 10)
        pygame.draw.rect(surf, border_col, (cx2, cy2, card_w, card_h), 3 if sel else 2, border_radius=10)
        if sel:
            draw_circle_alpha(surf, GOLD, cx2 + card_w//2, cy2 + card_h//2, card_w//2 + 15, 60)
        # Vehicle icon (coloured circle)
        pygame.draw.circle(surf, v["color"], (cx2 + 36, cy2 + card_h//2 - 10), 24)
        pygame.draw.circle(surf, (255, 255, 255), (cx2 + 36, cy2 + card_h//2 - 10), 24, 2)
        draw_text(surf, v["name"], F_MED, WHITE, cx2 + 130, cy2 + 22)
        draw_text(surf, v["desc"], F_TINY, GRAY, cx2 + 130, cy2 + 44)
        draw_text(surf, f"Spd:{v['max_speed']}  Acc:{v['accel']}", F_TINY, (160,160,180), cx2+130, cy2+62)
        if owned:
            status = "SELECTED" if sel else "OWNED"
            s_col  = GOLD if sel else GREEN
            draw_text(surf, status, F_SMALL, s_col, cx2 + 130, cy2 + 88)
        else:
            draw_text(surf, f"$ {v['price']}", F_MED, GOLD, cx2 + 130, cy2 + 80)
            if total_coins >= v["price"]:
                draw_text(surf, "[BUY - ENTER]", F_TINY, GREEN, cx2 + 130, cy2 + 104)
            else:
                draw_text(surf, "LOCKED", F_TINY, RED, cx2 + 130, cy2 + 104)
        btn_rects.append((pygame.Rect(cx2, cy2, card_w, card_h), v))

    draw_text(surf, "↑↓ Navigate   ENTER Select/Buy   ESC Back", F_TINY, (80, 80, 100), W//2, H - 18)
    return btn_rects

def result_screen(surf, win, score, earned_coins, dist, top_speed, level_n, next_exists):
    draw_gradient_bg(surf, (4, 3, 14), (14, 4, 4) if not win else (4, 14, 4))
    title = "LEVEL COMPLETE!" if win else "CRASHED!"
    col   = GOLD if win else RED
    draw_text(surf, title, F_TITLE, col, W//2, H//2 - 160)
    draw_text(surf, f"Level {level_n}", F_MED, WHITE, W//2, H//2 - 110)

    stats = [
        ("SCORE",      str(score)),
        ("COINS EARN", f"+{earned_coins}"),
        ("DISTANCE",   f"{int(dist)}m"),
        ("TOP SPEED",  f"{int(top_speed)} km/h"),
    ]
    for i, (lbl, val) in enumerate(stats):
        bx2 = W//2 - 200 + (i % 2) * 210
        by2 = H//2 - 60 + (i // 2) * 75
        draw_rect_alpha(surf, (20, 20, 40), (bx2, by2, 190, 60), 220, 8)
        pygame.draw.rect(surf, (80, 80, 120), (bx2, by2, 190, 60), 2, border_radius=8)
        draw_text(surf, lbl, F_TINY, GOLD, bx2 + 95, by2 + 14)
        draw_text(surf, val, F_MED,  WHITE, bx2 + 95, by2 + 38)

    if win and next_exists:
        draw_text(surf, "ENTER — Next Level", F_MED, GREEN, W//2, H//2 + 100)
    elif not win:
        draw_text(surf, "ENTER — Retry", F_MED, ORANGE, W//2, H//2 + 100)
    draw_text(surf, "ESC — Main Menu", F_SMALL, (160, 160, 180), W//2, H//2 + 132)

def pause_screen(surf):
    draw_rect_alpha(surf, (0, 0, 0), (0, 0, W, H), 180)
    draw_text(surf, "PAUSED", F_TITLE, GOLD, W//2, H//2 - 50)
    draw_text(surf, "ESC — Resume    Q — Quit to Menu", F_MED, WHITE, W//2, H//2 + 10)

# ── POPUP MESSAGES ────────────────────────────────────────────────────[...]
class Popup:
    def __init__(self):
        self.messages = []

    def add(self, text, color=GOLD, duration=0.8):
        self.messages.append({"text": text, "color": color, "t": duration, "max_t": duration})

    def update(self, dt):
        self.messages = [m for m in self.messages if m["t"] > 0]
        for m in self.messages:
            m["t"] -= dt

    def draw(self, surf):
        for i, m in enumerate(self.messages):
            ratio = m["t"] / m["max_t"]
            alpha = int(ratio * 255)
            y2    = int(H * 0.35 - i * 34)
            img   = F_MED.render(m["text"], True, m["color"])
            img.set_alpha(alpha)
            surf.blit(img, img.get_rect(center=(W//2, y2)))

# ════════════════════════════════════════════════════════════════════
# GAME STATE MACHINE
# ════════════════════════════════════════════════════════════════════
STATE_MENU    = "menu"
STATE_PLAY    = "play"
STATE_PAUSE   = "pause"
STATE_RESULT  = "result"
STATE_GARAGE  = "garage"

class Game:
    def __init__(self):
        self.state       = STATE_MENU
        self.menu_t      = 0.0
        self.level_n     = 1
        self.popup       = Popup()
        self.garage_sel  = 0     # cursor index in garage

        # Play vars
        self.score       = 0
        self.session_coins = 0
        self.dist        = 0.0
        self.top_speed   = 0.0
        self.frame_n     = 0
        self.near_combo  = 0
        self.combo_timer = 0.0
        self.road_off    = 0.0
        self.mark_off    = 0.0
        self.shake       = 0.0
        self.win         = False

        self.player      = None
        self.lanes       = []
        self.traffic     = []
        self.coins_list  = []
        self.particles   = []

    def get_vehicle(self):
        sel = SAVE["selected"]
        return next((v for v in VEHICLES if v["id"] == sel), VEHICLES[0])

    def get_level(self):
        return LEVELS[self.level_n - 1]

    def start_level(self, n):
        self.level_n       = n
        self.score         = 0
        self.session_coins = 0
        self.dist          = 0.0
        self.top_speed     = 0.0
        self.frame_n       = 0
        self.near_combo    = 0
        self.combo_timer   = 0.0
        self.road_off      = 0.0
        self.mark_off      = 0.0
        self.shake         = 0.0
        self.win           = False
        self.traffic.clear()
        self.coins_list.clear()
        self.particles.clear()

        self.lanes = [int(W * (0.20 + i * 0.15)) for i in range(N_LANES)]
        self.player = Player(self.lanes, self.get_vehicle())
        self.state  = STATE_PLAY

    def spawn_car(self):
        lvl = self.get_level()
        lo, hi = lvl["car_speed"]
        lane = random.randint(0, N_LANES - 1)
        speed = random.uniform(lo, hi)
        self.traffic.append(TrafficCar(lane, self.lanes[lane], speed))

    def spawn_coin(self):
        lane = random.randint(0, N_LANES - 1)
        self.coins_list.append(Coin(lane, self.lanes[lane]))

    def add_sparks(self, x, y, count=10):
        for _ in range(count):
            self.particles.append(Particle(
                x, y,
                random.uniform(-200, 200),
                random.uniform(-300, -50),
                random.choice([GOLD, ORANGE, RED, WHITE]),
                random.uniform(3, 7),
                random.uniform(0.5, 1.2)
            ))

    # ── UPDATE ──────────────────────────────────────────────────────────[...]
    def update(self, dt, events, keys_pressed):
        self.menu_t += dt

        if self.state == STATE_MENU:
            for e in events:
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_RETURN:  self.start_level(self.level_n)
                    if e.key == pygame.K_g:        self.state = STATE_GARAGE
                    if e.key == pygame.K_ESCAPE:   return False

        elif self.state == STATE_GARAGE:
            for e in events:
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        self.state = STATE_MENU
                    elif e.key == pygame.K_UP:
                        self.garage_sel = (self.garage_sel - 1) % len(VEHICLES)
                    elif e.key == pygame.K_DOWN:
                        self.garage_sel = (self.garage_sel + 1) % len(VEHICLES)
                    elif e.key == pygame.K_RETURN:
                        v = VEHICLES[self.garage_sel]
                        if v["id"] in SAVE["owned"]:
                            SAVE["selected"] = v["id"]
                            write_save(SAVE)
                        elif SAVE["coins"] >= v["price"]:
                            SAVE["coins"] -= v["price"]
                            SAVE["owned"].append(v["id"])
                            SAVE["selected"] = v["id"]
                            write_save(SAVE)
                        else:
                            self.popup.add("NOT ENOUGH COINS!", RED)

        elif self.state == STATE_PAUSE:
            for e in events:
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:  self.state = STATE_PLAY
                    if e.key == pygame.K_q:       self.state = STATE_MENU

        elif self.state == STATE_RESULT:
            for e in events:
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_RETURN:
                        if self.win and self.level_n < len(LEVELS):
                            self.start_level(self.level_n + 1)
                        elif not self.win:
                            self.start_level(self.level_n)
                        else:
                            self.state = STATE_MENU
                    if e.key == pygame.K_ESCAPE:
                        self.state = STATE_MENU

        elif self.state == STATE_PLAY:
            for e in events:
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    self.state = STATE_PAUSE

            p   = self.player
            lvl = self.get_level()

            # Input: lane change
            for e in events:
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_LEFT, pygame.K_a):
                        p.target_lane = max(0, p.target_lane - 1)
                    if e.key in (pygame.K_RIGHT, pygame.K_d):
                        p.target_lane = min(N_LANES - 1, p.target_lane + 1)

            p.update(dt, keys_pressed)
            if p.speed > self.top_speed:
                self.top_speed = p.speed

            # Road scroll
            self.road_off = (self.road_off + p.speed * dt * 2.0) % H
            self.mark_off = (self.mark_off + p.speed * dt * 2.5) % 70
            self.dist     += p.speed * dt
            self.score    += int(p.speed * dt * 0.2)
            self.frame_n  += 1

            if self.shake > 0:
                self.shake -= dt * 200

            # Level complete
            if self.dist >= lvl["goal"]:
                self._level_complete()
                return True

            # Spawn - REDUCED coin spawn rate (was 20, now 40 means half as many)
            car_rate = max(24, lvl["car_rate"] - p.speed * 0.15)
            if self.frame_n % max(1, int(car_rate)) == 0:
                self.spawn_car()
            if self.frame_n % max(1, int(max(40, 110 - p.speed * 0.1))) == 0:  # Reduced coin spawn
                self.spawn_coin()

            # Traffic update + collision + near-miss
            player_lane = round((p.x - self.lanes[0]) /
                                max(1, self.lanes[-1] - self.lanes[0]) * (N_LANES - 1))
            player_lane = clamp(player_lane, 0, N_LANES - 1)
            py = H - 110

            for car in self.traffic[:]:
                car.update(dt, p.speed)
                # Near miss window
                if not car.passed and H * 0.45 < car.y < H * 0.78:
                    dx = abs(self.lanes[car.lane] - p.x)
                    if W * 0.11 < dx < W * 0.24:
                        self._near_miss()
                        car.passed = True
                if not car.passed and car.y > H * 0.85:
                    car.passed = True
                    self.score += 60
                # Collision
                if car.lane == player_lane and py - 30 < car.y < py + 40:
                    self._crash()
                    return True
                if car.y > H + 150:
                    self.traffic.remove(car)

            # Coins
            for coin in self.coins_list[:]:
                coin.update(dt, p.speed)
                if not coin.collected and coin.lane == player_lane and abs(coin.y - py) < 40:
                    coin.collected = True
                    earn = 10 + self.level_n * 5
                    self.session_coins += earn
                    self.score         += earn * 2
                    self.popup.add(f"+{earn} $", GOLD)
                    self.add_sparks(self.lanes[coin.lane], int(coin.y), 8)
                if coin.collected or coin.y > H + 80:
                    self.coins_list.remove(coin)

            # Particles
            self.particles = [p2 for p2 in self.particles if p2.update(dt)]

            # Combo decay
            if self.combo_timer > 0:
                self.combo_timer -= dt
                if self.combo_timer <= 0:
                    self.near_combo = 0

        self.popup.update(dt)
        return True

    def _near_miss(self):
        self.near_combo  += 1
        self.combo_timer  = 3.0
        bonus = 50 * self.near_combo
        self.score += bonus
        tag = f"x{self.near_combo} " if self.near_combo > 1 else ""
        self.popup.add(f"{tag}NEAR MISS! +{bonus}", RED)
        self.shake = 5

    def _crash(self):
        self.add_sparks(int(self.player.x), H - 110, 50)
        SAVE["coins"] += self.session_coins
        write_save(SAVE)
        self.state = STATE_RESULT
        self.win   = False

    def _level_complete(self):
        SAVE["coins"] += self.session_coins
        if self.level_n >= SAVE["unlocked_levels"] and self.level_n < len(LEVELS):
            SAVE["unlocked_levels"] = self.level_n + 1
        write_save(SAVE)
        self.state = STATE_RESULT
        self.win   = True

    # ── DRAW ────────────────────────────────────────────────────────────[...]
    def draw(self, surf):
        surf.fill(DARK)

        if self.state == STATE_MENU:
            main_menu(surf, self.menu_t)

        elif self.state == STATE_GARAGE:
            btn_rects = garage_screen(surf, SAVE["selected"], SAVE["coins"])
            # Highlight garage cursor
            if 0 <= self.garage_sel < len(btn_rects):
                r, _ = btn_rects[self.garage_sel]
                pygame.draw.rect(surf, GOLD, r, 2, border_radius=8)

        elif self.state in (STATE_PLAY, STATE_PAUSE):
            # Road
            ox = int((self.shake * (0.5 - 0.5)) * 6) if self.shake > 0 else 0
            oy = int(math.sin(self.menu_t * 40) * min(self.shake, 4)) if self.shake > 0 else 0
            shifted = surf.copy() if (ox or oy) else None

            draw_road(surf, self.lanes, self.road_off, self.mark_off)

            # Coins (back-to-front) - STAY IN LANE
            for c in sorted(self.coins_list, key=lambda c: c.y):
                if not c.collected and c.y > H * 0.45:
                    depth = clamp((c.y - H*0.45) / (H - H*0.45), 0.1, 1)
                    scale = depth * 0.85
                    c.draw(surf, scale=scale)

            # Traffic (back-to-front) - STAY IN LANE
            for car in sorted(self.traffic, key=lambda c: c.y):
                if car.y > H * 0.42:
                    depth = clamp((car.y - H*0.42) / (H - H*0.42), 0.1, 1)
                    sc2   = clamp(depth * 0.88, 0.18, 1)
                    car.draw(surf, scale=sc2)

            # Particles
            for p2 in self.particles:
                p2.draw(surf)

            # Player
            if self.player:
                self.player.draw(surf)

            # HUD
            total_coins = SAVE["coins"] + self.session_coins
            draw_hud(surf, self.score, total_coins, self.dist,
                     self.get_level(), self.player.speed, self.player.max_speed)

            if self.state == STATE_PAUSE:
                pause_screen(surf)

        elif self.state == STATE_RESULT:
            # Still show road in background
            draw_road(surf, self.lanes, self.road_off, self.mark_off)
            result_screen(surf, self.win, self.score, self.session_coins,
                          self.dist, self.top_speed, self.level_n,
                          self.level_n < len(LEVELS))

        self.popup.draw(surf)


# ════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ════════════════════════════════════════════════════════════════════
def main():
    global W, H, screen
    game = Game()
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        dt = min(dt, 0.05)

        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.VIDEORESIZE:
                W, H = e.w, e.h
                screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)

        keys = pygame.key.get_pressed()
        if not game.update(dt, events, keys):
            running = False

        game.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
