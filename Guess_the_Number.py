
import json
import math
import random
import sys
from array import array
from datetime import date
from pathlib import Path
import ctypes

import pygame

if sys.platform == "win32":
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("GuessTheNumber.Game")
    except (OSError, AttributeError):
        pass

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

BASE_WIDTH = 800
BASE_HEIGHT = 600
MIN_WINDOW_WIDTH = 400
MIN_WINDOW_HEIGHT = 300

window_surface = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Guess the Number")

clock = pygame.time.Clock()
BASE_DIR = Path(__file__).resolve().parent
SFX_DIR = BASE_DIR / "assets" / "sfx"
IMAGE_DIR = BASE_DIR / "assets" / "images"
ICON_DIR = BASE_DIR / "assets" / "icons"
SAVE_FILE = BASE_DIR / "save_data.json"

try:
    pygame.mixer.init()
    SOUND_ENABLED = True
except pygame.error:
    SOUND_ENABLED = False

MUSIC_FILE = SFX_DIR / "background_music.wav"
MUSIC_LOADED = False
current_music_track = None


def play_theme_music(theme_name):
    global current_music_track, MUSIC_LOADED
    if not SOUND_ENABLED:
        return
    slug = theme_name.lower().replace(" ", "_")
    candidate = SFX_DIR / f"background_music_{slug}.wav"
    target = candidate if candidate.exists() else MUSIC_FILE
    if not target.exists():
        return
    target_str = str(target)
    if target_str == current_music_track:
        return
    try:
        pygame.mixer.music.load(target_str)
        pygame.mixer.music.set_volume(0.35)
        pygame.mixer.music.play(-1)
        current_music_track = target_str
        MUSIC_LOADED = True
    except pygame.error:
        pass


def make_tone(frequency, duration_ms, volume=0.35):
    if not SOUND_ENABLED:
        return None

    sample_rate = 44100
    sample_count = int(sample_rate * duration_ms / 1000)
    samples = array("h")
    fade_samples = max(1, int(sample_rate * 0.015))

    for i in range(sample_count):
        wave = math.sin(2 * math.pi * frequency * i / sample_rate)
        envelope = 1
        if i < fade_samples:
            envelope = i / fade_samples
        elif i > sample_count - fade_samples:
            envelope = max(0, (sample_count - i) / fade_samples)
        samples.append(int(32767 * volume * envelope * wave))

    return pygame.mixer.Sound(buffer=samples)


def play_sound(name):
    if not SOUND_ENABLED:
        return
    sound = sounds.get(name)
    if sound:
        sound.play()


def load_sound(filename, fallback):
    if not SOUND_ENABLED:
        return None

    path = SFX_DIR / filename
    if path.exists():
        try:
            return pygame.mixer.Sound(str(path))
        except pygame.error:
            pass

    return fallback


def load_image(folder, filename):
    path = folder / filename
    if not path.exists():
        return None

    try:
        return pygame.image.load(str(path)).convert_alpha()
    except pygame.error:
        return None


sounds = {
    "click": load_sound("click.wav", make_tone(520, 45, 0.22)),
    "miss": load_sound("lose.wav", make_tone(180, 130, 0.28)),
    "win": load_sound("win.wav", make_tone(760, 160, 0.32)),
    "buy": load_sound("buy.wav", make_tone(960, 120, 0.25)),
    "shop_open": load_sound("shop_open.wav", make_tone(680, 90, 0.2)),
    "achievement": load_sound("achievement.wav", make_tone(880, 220, 0.3)),
    "levelup": load_sound("levelup.wav", make_tone(1040, 260, 0.32)),
}

images = {
    "coin": load_image(IMAGE_DIR, "coin.png"),
    "logo": load_image(IMAGE_DIR, "logo.png"),
}

if images["logo"]:
    pygame.display.set_icon(images["logo"])

icons = {
    "close": load_image(ICON_DIR, "close.png"),
    "shop": load_image(ICON_DIR, "shop.png"),
    "sound_off": load_image(ICON_DIR, "sound_off.png"),
    "sound_on": load_image(ICON_DIR, "sound_on.png"),
}

GAME_MODES = {
    "Easy": {"low": 1, "high": 10, "attempts": 6, "multiplier": 1.0},
    "Medium": {"low": 1, "high": 15, "attempts": 5, "multiplier": 1.5},
    "Hard": {"low": 1, "high": 20, "attempts": 4, "multiplier": 2.2},
}
MODE_ORDER = ["Easy", "Medium", "Hard"]

RARITY_COLORS = {
    "Common": (140, 140, 140),
    "Rare": (46, 160, 90),
    "Epic": (72, 108, 224),
    "Legendary": (206, 144, 30),
}

themes = [
    {"name": "Royal", "cost": 0, "rarity": "Common",
     "base": (171, 105, 201), "accent": (102, 7, 145),
     "button": (102, 7, 145), "button_hover": (140, 40, 190)},
    {"name": "Ocean", "cost": 40, "rarity": "Common",
     "base": (45, 150, 185), "accent": (16, 82, 120),
     "button": (14, 102, 145), "button_hover": (20, 132, 176)},
    {"name": "Sunset", "cost": 75, "rarity": "Rare",
     "base": (232, 124, 74), "accent": (123, 55, 44),
     "button": (177, 73, 52), "button_hover": (211, 91, 57)},
    {"name": "Mint", "cost": 120, "rarity": "Rare",
     "base": (78, 178, 136), "accent": (19, 88, 79),
     "button": (23, 120, 98), "button_hover": (32, 150, 116)},
    {"name": "Lagoon", "cost": 180, "rarity": "Epic",
     "base": (46, 196, 182), "accent": (20, 110, 102),
     "button": (255, 107, 107), "button_hover": (255, 140, 140)},
    {"name": "Watermelon", "cost": 180, "rarity": "Epic",
     "base": (255, 89, 94), "accent": (150, 40, 45),
     "button": (138, 201, 38), "button_hover": (165, 220, 70)},
    {"name": "Pool Party", "cost": 260, "rarity": "Legendary",
     "base": (0, 191, 255), "accent": (0, 110, 160),
     "button": (255, 127, 80), "button_hover": (255, 155, 110)},
]

ACHIEVEMENTS = [
    {"id": "first_win", "name": "First Win", "reward": 20,
     "check": lambda: stats["wins"] >= 1},
    {"id": "streak_5", "name": "5 Win Streak", "reward": 30,
     "check": lambda: best_streak >= 5},
    {"id": "coins_100", "name": "Coin Collector", "reward": 25,
     "check": lambda: stats["coins_earned_total"] >= 100},
    {"id": "collector", "name": "Theme Collector", "reward": 50,
     "check": lambda: len(owned_themes) >= len(themes)},
    {"id": "lucky_guess", "name": "Lucky Guess", "reward": 25,
     "check": lambda: stats["fastest_win"] == 1},
    {"id": "hard_master", "name": "Hard Mode Master", "reward": 60,
     "check": lambda: stats["hard_wins"] >= 10},
]

POWERUPS = [
    {"id": "parity", "label": "Odd/Even", "cost": 15},
    {"id": "warmer", "label": "Narrow It", "cost": 20},
    {"id": "extra", "label": "+1 Attempt", "cost": 25},
]


SPIN_COST = 30
WHEEL_REWARDS = [
    {"label": "20 Coins", "type": "coins", "value": 20, "weight": 30},
    {"label": "50 Coins", "type": "coins", "value": 50, "weight": 22},
    {"label": "100 Coins", "type": "coins", "value": 100, "weight": 12},
    {"label": "Free Theme!", "type": "theme", "value": 0, "weight": 8},
    {"label": "JACKPOT! 250 Coins", "type": "coins", "value": 250, "weight": 4},
    {"label": "Nothing... unlucky!", "type": "coins", "value": 0, "weight": 24},
]

HINT_MESSAGES_HIGHER = [
    "Colder than an ice cube! Go higher.",
    "Too low, dive deeper!",
    "Freezing! Try a bigger number.",
]
HINT_MESSAGES_LOWER = [
    "Way too high! Bring it down.",
    "Scorching! Try a smaller number.",
    "Too hot, cool it off with a lower guess.",
]
NEAR_MISS_MESSAGES = [
    "Almost! So close!",
    "You're getting warmer...",
    "Just a little off!",
]


def get_hint_message(guess, secret, low, high):
    diff = abs(guess - secret)
    span = max(1, high - low)
    if diff <= max(1, span // 8):
        return random.choice(NEAR_MISS_MESSAGES)
    if guess < secret:
        return random.choice(HINT_MESSAGES_HIGHER)
    return random.choice(HINT_MESSAGES_LOWER)

def default_save():
    return {
        "coins": 0,
        "owned_themes": ["Royal"],
        "current_theme": "Royal",
        "best_streak": 0,
        "xp": 0,
        "level": 1,
        "stats": {
            "games_played": 0,
            "wins": 0,
            "losses": 0,
            "total_guesses_in_wins": 0,
            "fastest_win": None,
            "coins_earned_total": 0,
            "hard_wins": 0,
        },
        "achievements": [],
        "last_daily_date": None,
        "daily_streak": 0,
    }


def load_game():
    base = default_save()
    if not SAVE_FILE.exists():
        return base

    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)

        if not isinstance(data, dict):
            return base

        base.update({key: value for key, value in data.items() if key in base})
        saved_stats = data.get("stats", {})
        if isinstance(saved_stats, dict):
            base["stats"] = {**default_save()["stats"], **saved_stats}

        if not isinstance(base["owned_themes"], list):
            base["owned_themes"] = ["Royal"]
        if not isinstance(base["achievements"], list):
            base["achievements"] = []
        if base["current_theme"] not in {theme["name"] for theme in themes}:
            base["current_theme"] = "Royal"

        numeric_keys = ("coins", "best_streak", "xp", "level", "daily_streak")
        for key in numeric_keys:
            if not isinstance(base[key], (int, float)) or isinstance(base[key], bool):
                base[key] = default_save()[key]
        base["coins"] = max(0, int(base["coins"]))
        base["best_streak"] = max(0, int(base["best_streak"]))
        base["xp"] = max(0, int(base["xp"]))
        base["level"] = max(1, int(base["level"]))
        base["daily_streak"] = max(0, int(base["daily_streak"]))

    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return default_save()

    return base


def save_game():
    data = {
        "coins": coins,
        "owned_themes": sorted(owned_themes),
        "current_theme": themes[current_theme]["name"],
        "best_streak": best_streak,
        "xp": xp,
        "level": level,
        "stats": stats,
        "achievements": sorted(achievements_unlocked),
        "last_daily_date": last_daily_date,
        "daily_streak": daily_streak,
    }
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as handle:
            json.dump(data, handle)
    except OSError:
        pass


save_data = load_game()
coins = save_data["coins"]
owned_themes = set(save_data["owned_themes"]) | {"Royal"}
best_streak = save_data["best_streak"]
xp = save_data["xp"]
level = save_data["level"]
stats = save_data["stats"]
achievements_unlocked = set(save_data["achievements"])
last_daily_date = save_data["last_daily_date"]
daily_streak = save_data["daily_streak"]

current_theme = 0
for _idx, _t in enumerate(themes):
    if _t["name"] == save_data["current_theme"] and _t["name"] in owned_themes:
        current_theme = _idx
        break

displayed_coins = float(coins)

current_mode = "Easy"
mode_range = (GAME_MODES[current_mode]["low"], GAME_MODES[current_mode]["high"])
mode_max_attempts = GAME_MODES[current_mode]["attempts"]
round_max_attempts = mode_max_attempts

secret_number = random.randint(*mode_range)
message = f"Guess a number from {mode_range[0]} to {mode_range[1]}"
feedback_color = themes[current_theme]["base"]
flash_strength = 0
attempts = 0
win_streak = 0
last_reward = 0

show_shop = False
show_stats = False
show_wheel = False

wheel_spinning = False
wheel_timer = 0
wheel_result = None
wheel_display_label = "Give it a spin!"

button_scale = 1.0
input_text = ""
active = False

popup_queue = []
particles = []
bubbles = [
    {
        "x": random.uniform(0, BASE_WIDTH),
        "y": random.uniform(0, BASE_HEIGHT),
        "r": random.uniform(4, 11),
        "speed": random.uniform(0.25, 0.7),
        "phase": random.uniform(0, math.pi * 2),
    }
    for _ in range(14)
]
frame_count = 0

FONT_CACHE = {}
IMAGE_CACHE = {}

play_theme_music(themes[current_theme]["name"])


def get_font(base_size, scale):
    size = max(10, int(round(base_size * scale)))
    key = (base_size, size)
    font_obj = FONT_CACHE.get(key)
    if font_obj is None:
        font_obj = pygame.font.Font(None, size)
        FONT_CACHE[key] = font_obj
    return font_obj


def get_scaled_image(image, base_size, scale):
    if image is None:
        return None
    size = max(6, int(round(base_size * scale)))
    key = (id(image), size)
    scaled = IMAGE_CACHE.get(key)
    if scaled is None:
        scaled = pygame.transform.smoothscale(image, (size, size))
        IMAGE_CACHE[key] = scaled
    return scaled


def to_rect(x, y, w, h, layout):
    return pygame.Rect(
        int(x * layout["sx"]),
        int(y * layout["sy"]),
        int(w * layout["sx"]),
        int(h * layout["sy"]),
    )


def to_point(x, y, layout):
    return (int(x * layout["sx"]), int(y * layout["sy"]))


def xp_needed_for_level(lv):
    return 100 + (lv - 1) * 40


def reward_for_streak(streak):
    multiplier = GAME_MODES[current_mode]["multiplier"]
    base_reward = 10 + max(0, streak - 1) * 5
    return int(round(base_reward * multiplier))


def queue_popup(title, subtitle, duration=170):
    popup_queue.append({"title": title, "subtitle": subtitle, "timer": duration})


def gain_xp(amount):
    global xp, level, coins
    xp += amount
    needed = xp_needed_for_level(level)
    leveled = False
    while xp >= needed:
        xp -= needed
        level += 1
        coins += 25
        stats["coins_earned_total"] += 25
        leveled = True
        needed = xp_needed_for_level(level)
    if leveled:
        queue_popup("Level Up!", f"Now level {level} (+25 coins)")
        play_sound("levelup")


def check_achievements():
    global coins
    for ach in ACHIEVEMENTS:
        if ach["id"] in achievements_unlocked:
            continue
        try:
            unlocked = ach["check"]()
        except Exception:
            unlocked = False
        if unlocked:
            achievements_unlocked.add(ach["id"])
            coins += ach["reward"]
            stats["coins_earned_total"] += ach["reward"]
            queue_popup(f"Achievement: {ach['name']}", f"+{ach['reward']} coins")
            play_sound("achievement")


def claim_daily_reward():
    global coins, daily_streak, last_daily_date
    today = date.today()
    today_str = today.isoformat()
    if last_daily_date == today_str:
        return
    if last_daily_date:
        try:
            prev = date.fromisoformat(last_daily_date)
            daily_streak = daily_streak + 1 if (today - prev).days == 1 else 1
        except ValueError:
            daily_streak = 1
    else:
        daily_streak = 1
    reward = min(100, 20 + (daily_streak - 1) * 15)
    coins += reward
    stats["coins_earned_total"] += reward
    last_daily_date = today_str
    queue_popup("Daily Reward!", f"+{reward} coins (Day {daily_streak})")
    play_sound("buy")
    save_game()


def spawn_win_particles(base_x, base_y, reward):
    for _ in range(12):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.5, 4.0)
        particles.append({
            "kind": "coin", "x": base_x, "y": base_y,
            "vx": math.cos(angle) * speed, "vy": math.sin(angle) * speed - 3,
            "life": 40, "max_life": 40,
        })
    particles.append({
        "kind": "text", "x": base_x, "y": base_y, "vy": -1.2,
        "life": 55, "max_life": 55, "text": f"+{reward}", "color": (255, 215, 0),
    })


def update_particles():
    for p in particles[:]:
        if p["kind"] == "coin":
            p["vy"] += 0.15
            p["x"] += p["vx"]
            p["y"] += p["vy"]
        else:
            p["y"] += p["vy"]
        p["life"] -= 1
        if p["life"] <= 0:
            particles.remove(p)


def draw_alpha_circle(color, center, radius, alpha):
    if radius <= 0:
        return
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(surf, (*color, max(0, min(255, alpha))), (radius, radius), radius)
    window_surface.blit(surf, (center[0] - radius, center[1] - radius))


def draw_alpha_text(text, font_obj, color, center, alpha):
    surf = font_obj.render(text, True, color).convert_alpha()
    surf.set_alpha(max(0, min(255, alpha)))
    rect = surf.get_rect(center=center)
    window_surface.blit(surf, rect)


def draw_particles(layout):
    for p in particles:
        alpha = int(255 * p["life"] / p["max_life"])
        point = to_point(p["x"], p["y"], layout)
        if p["kind"] == "coin":
            radius = max(2, int(5 * layout["s"]))
            draw_alpha_circle((255, 215, 0), point, radius, alpha)
        else:
            draw_alpha_text(p["text"], layout["fonts"]["small"], p["color"], point, alpha)


def update_bubbles():
    for b in bubbles:
        b["y"] -= b["speed"]
        b["x"] += math.sin(frame_count * 0.02 + b["phase"]) * 0.25
        if b["y"] < -15:
            b["y"] = BASE_HEIGHT + 15
            b["x"] = random.uniform(0, BASE_WIDTH)


def draw_bubbles(layout):
    for b in bubbles:
        point = to_point(b["x"], b["y"], layout)
        radius = max(1, int(b["r"] * layout["s"]))
        draw_alpha_circle((255, 255, 255), point, radius, 50)


def start_spin():
    global coins, wheel_spinning, wheel_timer, wheel_result, wheel_display_label
    if coins < SPIN_COST or wheel_spinning:
        return
    coins -= SPIN_COST
    wheel_spinning = True
    wheel_timer = 90
    weights = [r["weight"] for r in WHEEL_REWARDS]
    wheel_result = random.choices(WHEEL_REWARDS, weights=weights, k=1)[0]
    wheel_display_label = "..."
    play_sound("shop_open")
    save_game()


def finish_spin():
    global wheel_spinning, coins, wheel_display_label
    wheel_spinning = False
    reward = wheel_result
    wheel_display_label = reward["label"]
    if reward["type"] == "coins" and reward["value"] > 0:
        coins += reward["value"]
        stats["coins_earned_total"] += reward["value"]
    elif reward["type"] == "theme":
        unowned = [t for t in themes if t["name"] not in owned_themes]
        if unowned:
            pick = random.choice(unowned)
            owned_themes.add(pick["name"])
            wheel_display_label = f"Free Theme: {pick['name']}!"
        else:
            coins += 50
            stats["coins_earned_total"] += 50
            wheel_display_label = "All themes owned! +50 coins"
    play_sound("win" if reward["type"] == "theme" or reward.get("value", 0) >= 100 else "click")
    check_achievements()
    save_game()


def use_powerup(pid):
    global coins, message, round_max_attempts
    cfg = next(p for p in POWERUPS if p["id"] == pid)
    if coins < cfg["cost"] or show_shop or show_stats or show_wheel:
        return
    coins -= cfg["cost"]
    play_sound("buy")
    if pid == "parity":
        parity = "even" if secret_number % 2 == 0 else "odd"
        message = f"Power-up: the number is {parity}!"
    elif pid == "warmer":
        low, high = mode_range
        window = min(5, high - low)
        start = max(low, min(secret_number - random.randint(1, 3), high - window))
        end = min(high, start + window)
        message = f"Power-up: it's between {start} and {end}!"
    elif pid == "extra":
        round_max_attempts += 1
        message = "Power-up: +1 attempt added!"
    save_game()


def compute_layout():
    w, h = window_surface.get_size()
    sx = w / BASE_WIDTH
    sy = h / BASE_HEIGHT
    s = min(sx, sy)

    layout = {"w": w, "h": h, "sx": sx, "sy": sy, "s": s}

    layout["input_box"] = to_rect(250, 258, 300, 50, layout)
    layout["guess_button"] = to_rect(325, 358, 150, 50, layout)

    layout["wheel_button"] = to_rect(470, 16, 70, 40, layout)
    layout["stats_button"] = to_rect(548, 16, 70, 40, layout)
    layout["shop_button"] = to_rect(626, 16, 70, 40, layout)
    layout["sound_button"] = to_rect(704, 16, 40, 40, layout)

    layout["mode_buttons"] = {
        "Easy": to_rect(250, 205, 90, 34, layout),
        "Medium": to_rect(350, 205, 90, 34, layout),
        "Hard": to_rect(450, 205, 90, 34, layout),
    }

    layout["daily_button"] = to_rect(270, 168, 260, 30, layout)
    layout["xp_bar"] = to_rect(20, 172, 220, 12, layout)

    layout["powerup_buttons"] = {
        "parity": to_rect(170, 470, 150, 40, layout),
        "warmer": to_rect(325, 470, 150, 40, layout),
        "extra": to_rect(480, 470, 150, 40, layout),
    }

    layout["shop_panel"] = to_rect(110, 40, 580, 530, layout)
    layout["shop_close"] = to_rect(628, 55, 32, 32, layout)

    layout["stats_panel"] = to_rect(150, 90, 500, 380, layout)
    layout["stats_close"] = to_rect(588, 105, 32, 32, layout)

    layout["wheel_panel"] = to_rect(200, 140, 400, 300, layout)
    layout["wheel_close"] = to_rect(538, 155, 32, 32, layout)
    layout["spin_button"] = to_rect(300, 370, 200, 50, layout)

    layout["fonts"] = {
        "small": get_font(28, s),
        "tiny": get_font(22, s),
        "normal": get_font(40, s),
        "big": get_font(54, s),
        "title": get_font(78, s),
    }

    return layout


def draw_text(text, used_font, color, center=None, topleft=None):
    surface = used_font.render(text, True, color)
    rect = surface.get_rect()
    if center:
        rect.center = center
    if topleft:
        rect.topleft = topleft
    window_surface.blit(surface, rect)
    return rect


def draw_button(rect, text, used_font, base_color, hover_color, layout, disabled=False):
    mouse_pos = pygame.mouse.get_pos()
    hovering = rect.collidepoint(mouse_pos) and not disabled
    color = (96, 92, 104) if disabled else hover_color if hovering else base_color
    border_radius = max(2, int(8 * layout["s"]))
    pygame.draw.rect(window_surface, color, rect, border_radius=border_radius)
    pygame.draw.rect(window_surface, (255, 255, 255), rect, max(1, int(2 * layout["s"])), border_radius=border_radius)
    draw_text(text, used_font, (255, 255, 255), center=rect.center)
    return hovering


def draw_icon_button(rect, icon, icon_base_size, fallback_text, base_color, hover_color, layout, disabled=False):
    mouse_pos = pygame.mouse.get_pos()
    hovering = rect.collidepoint(mouse_pos) and not disabled
    color = (96, 92, 104) if disabled else hover_color if hovering else base_color
    border_radius = max(2, int(8 * layout["s"]))
    pygame.draw.rect(window_surface, color, rect, border_radius=border_radius)
    pygame.draw.rect(window_surface, (255, 255, 255), rect, max(1, int(2 * layout["s"])), border_radius=border_radius)

    scaled_icon = get_scaled_image(icon, icon_base_size, layout["s"])
    if scaled_icon:
        icon_rect = scaled_icon.get_rect(center=rect.center)
        window_surface.blit(scaled_icon, icon_rect)
    else:
        draw_text(fallback_text, layout["fonts"]["small"], (255, 255, 255), center=rect.center)

    return hovering


def draw_coin_text(text, x, y, layout):
    coin = get_scaled_image(images.get("coin"), 26, layout["s"])
    point = to_point(x, y - 2, layout)
    if coin:
        icon_rect = coin.get_rect(topleft=point)
        window_surface.blit(coin, icon_rect)
        draw_text(text, layout["fonts"]["small"], (255, 255, 255), topleft=(point[0] + coin.get_width() + 8, point[1] + 2))
    else:
        draw_text(f"Coins: {text}", layout["fonts"]["small"], (255, 255, 255), topleft=to_point(x, y, layout))


def draw_xp_bar(layout, theme):
    needed = xp_needed_for_level(level)
    ratio = min(1.0, xp / needed) if needed > 0 else 0
    bar_rect = layout["xp_bar"]
    border_radius = max(1, int(6 * layout["s"]))
    pygame.draw.rect(window_surface, (255, 255, 255), bar_rect, border_radius=border_radius)
    fill_rect = pygame.Rect(bar_rect.x, bar_rect.y, int(bar_rect.width * ratio), bar_rect.height)
    if fill_rect.width > 0:
        pygame.draw.rect(window_surface, (255, 215, 0), fill_rect, border_radius=border_radius)
    pygame.draw.rect(window_surface, theme["accent"], bar_rect, max(1, int(2 * layout["s"])), border_radius=border_radius)
    draw_text(f"Lv {level}", layout["fonts"]["tiny"], (255, 255, 255), topleft=(bar_rect.x, bar_rect.y - int(20 * layout["s"])))


def draw_daily_banner(layout, daily_available):
    if not daily_available:
        return
    rect = layout["daily_button"]
    reward_preview = min(100, 20 + daily_streak * 15)
    border_radius = max(2, int(8 * layout["s"]))
    pygame.draw.rect(window_surface, (255, 215, 0), rect, border_radius=border_radius)
    pygame.draw.rect(window_surface, (120, 80, 0), rect, max(1, int(2 * layout["s"])), border_radius=border_radius)
    draw_text(f"Claim Daily Reward (+{reward_preview}c)", layout["fonts"]["tiny"], (60, 40, 0), center=rect.center)


def draw_powerups(layout, theme):
    for pid, rect in layout["powerup_buttons"].items():
        cfg = next(p for p in POWERUPS if p["id"] == pid)
        disabled = coins < cfg["cost"]
        draw_button(rect, f"{cfg['label']} ({cfg['cost']}c)", layout["fonts"]["tiny"], theme["button"], theme["button_hover"], layout, disabled)


def draw_popup(layout):
    if not popup_queue:
        return
    popup = popup_queue[0]
    card = to_rect(220, 20, 360, 64, layout)
    border_radius = max(2, int(10 * layout["s"]))
    surf = pygame.Surface((card.width, card.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (30, 25, 40, 235), (0, 0, card.width, card.height), border_radius=border_radius)
    pygame.draw.rect(surf, (255, 215, 0, 255), (0, 0, card.width, card.height), max(1, int(3 * layout["s"])), border_radius=border_radius)
    window_surface.blit(surf, card.topleft)
    draw_text(popup["title"], layout["fonts"]["small"], (255, 255, 255), center=(card.centerx, card.centery - 12))
    draw_text(popup["subtitle"], layout["fonts"]["tiny"], (255, 215, 0), center=(card.centerx, card.centery + 14))
    popup["timer"] -= 1
    if popup["timer"] <= 0:
        popup_queue.pop(0)


def shop_row_rect(index, layout):
    y = 140 + index * 54
    return to_rect(126, y, 548, 48, layout)


def shop_action_rect(index, layout):
    y = 140 + index * 54
    return to_rect(560, y + 6, 96, 36, layout)


def shop_swatch_rect(index, layout):
    y = 140 + index * 54
    return to_rect(140, y + 7, 34, 34, layout)


def draw_shop(layout):
    overlay = pygame.Surface((layout["w"], layout["h"]), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 110))
    window_surface.blit(overlay, (0, 0))

    panel = layout["shop_panel"]
    border_radius = max(2, int(8 * layout["s"]))
    pygame.draw.rect(window_surface, (250, 248, 255), panel, border_radius=border_radius)
    pygame.draw.rect(window_surface, (48, 33, 58), panel, max(1, int(3 * layout["s"])), border_radius=border_radius)
    draw_text("Shop", layout["fonts"]["big"], (48, 33, 58), topleft=to_point(140, 50, layout))

    coin = get_scaled_image(images.get("coin"), 24, layout["s"])
    coin_point = to_point(140, 90, layout)
    if coin:
        window_surface.blit(coin, coin.get_rect(topleft=coin_point))
        draw_text(str(coins), layout["fonts"]["small"], (48, 33, 58),
                  topleft=(coin_point[0] + coin.get_width() + 8, coin_point[1] + 2))
    else:
        draw_text(f"Coins: {coins}", layout["fonts"]["small"], (48, 33, 58), topleft=coin_point)

    draw_icon_button(layout["shop_close"], icons.get("close"), 20, "X", (160, 45, 65), (194, 62, 80), layout)

    unowned_themes = [t for t in themes if t["name"] not in owned_themes]
    featured = max(unowned_themes, key=lambda t: t["cost"]) if unowned_themes else None

    for index, theme_option in enumerate(themes):
        row_rect = shop_row_rect(index, layout)
        owned = theme_option["name"] in owned_themes
        selected = index == current_theme
        can_buy = coins >= theme_option["cost"]

        pygame.draw.rect(window_surface, (236, 232, 244), row_rect, border_radius=border_radius)
        if selected:
            pygame.draw.rect(window_surface, (48, 33, 58), row_rect, max(1, int(3 * layout["s"])), border_radius=border_radius)

        swatch = shop_swatch_rect(index, layout)
        pygame.draw.rect(window_surface, theme_option["base"], swatch, border_radius=max(1, int(5 * layout["s"])))
        pygame.draw.rect(window_surface, theme_option["accent"], swatch, max(1, int(3 * layout["s"])), border_radius=max(1, int(5 * layout["s"])))

        name_pos = (swatch.right + int(10 * layout["s"]), row_rect.y + int(5 * layout["s"]))
        draw_text(theme_option["name"], layout["fonts"]["small"], (48, 33, 58), topleft=name_pos)

        rarity = theme_option["rarity"]
        rarity_color = RARITY_COLORS.get(rarity, (100, 100, 100))
        rarity_pos = (swatch.right + int(10 * layout["s"]), row_rect.y + int(26 * layout["s"]))
        draw_text(rarity, layout["fonts"]["tiny"], rarity_color, topleft=rarity_pos)

        label = "Selected" if selected else "Use" if owned else f"Buy {theme_option['cost']}"
        disabled = selected or (not owned and not can_buy)
        action_rect = shop_action_rect(index, layout)
        draw_button(action_rect, label, layout["fonts"]["tiny"], theme_option["button"], theme_option["button_hover"], layout, disabled)

        if featured and theme_option["name"] == featured["name"]:
            draw_text("Featured", layout["fonts"]["tiny"], (206, 144, 30),
                       topleft=(action_rect.x, action_rect.y - int(16 * layout["s"])))


def draw_stats(layout):
    overlay = pygame.Surface((layout["w"], layout["h"]), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 110))
    window_surface.blit(overlay, (0, 0))

    panel = layout["stats_panel"]
    border_radius = max(2, int(8 * layout["s"]))
    pygame.draw.rect(window_surface, (250, 248, 255), panel, border_radius=border_radius)
    pygame.draw.rect(window_surface, (48, 33, 58), panel, max(1, int(3 * layout["s"])), border_radius=border_radius)
    draw_text("Statistics", layout["fonts"]["big"], (48, 33, 58),
               topleft=(panel.x + int(24 * layout["s"]), panel.y + int(16 * layout["s"])))
    draw_icon_button(layout["stats_close"], icons.get("close"), 20, "X", (160, 45, 65), (194, 62, 80), layout)

    wins = stats["wins"]
    losses = stats["losses"]
    avg_guesses = (stats["total_guesses_in_wins"] / wins) if wins else None
    fastest = stats["fastest_win"]

    lines = [
        f"Games Played: {stats['games_played']}",
        f"Wins: {wins}   Losses: {losses}",
        f"Best Streak: {best_streak}",
        f"Average Guesses to Win: {avg_guesses:.1f}" if avg_guesses is not None else "Average Guesses to Win: -",
        f"Fastest Win: {fastest} guess(es)" if fastest is not None else "Fastest Win: -",
        f"Total Coins Earned: {stats['coins_earned_total']}",
        f"Level {level}  (XP {xp}/{xp_needed_for_level(level)})",
        f"Hard Mode Wins: {stats['hard_wins']}",
        f"Achievements: {len(achievements_unlocked)}/{len(ACHIEVEMENTS)}",
        f"Daily Streak: {daily_streak} day(s)",
    ]
    start_y = panel.y + int(70 * layout["s"])
    line_gap = int(30 * layout["s"])
    for i, line in enumerate(lines):
        draw_text(line, layout["fonts"]["tiny"], (48, 33, 58),
                  topleft=(panel.x + int(24 * layout["s"]), start_y + i * line_gap))


def draw_wheel(layout):
    overlay = pygame.Surface((layout["w"], layout["h"]), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 130))
    window_surface.blit(overlay, (0, 0))

    panel = layout["wheel_panel"]
    border_radius = max(2, int(8 * layout["s"]))
    pygame.draw.rect(window_surface, (250, 248, 255), panel, border_radius=border_radius)
    pygame.draw.rect(window_surface, (48, 33, 58), panel, max(1, int(3 * layout["s"])), border_radius=border_radius)
    draw_icon_button(layout["wheel_close"], icons.get("close"), 20, "X", (160, 45, 65), (194, 62, 80), layout)

    draw_text("Lucky Wheel", layout["fonts"]["big"], (48, 33, 58), center=(panel.centerx, panel.y + int(50 * layout["s"])))
    draw_text(f"Spin cost: {SPIN_COST} coins", layout["fonts"]["tiny"], (48, 33, 58), center=(panel.centerx, panel.y + int(90 * layout["s"])))
    draw_text(wheel_display_label, layout["fonts"]["normal"], (102, 7, 145), center=(panel.centerx, panel.y + int(160 * layout["s"])))

    spin_button = layout["spin_button"]
    disabled = wheel_spinning or coins < SPIN_COST
    draw_button(spin_button, "Spinning..." if wheel_spinning else "SPIN", layout["fonts"]["small"], (102, 7, 145), (140, 40, 190), layout, disabled)


running = True
while running:
    theme = themes[current_theme]
    frame_count += 1

    daily_available = last_daily_date != date.today().isoformat()

    events = pygame.event.get()

    for event in events:
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.VIDEORESIZE:
            new_width = max(MIN_WINDOW_WIDTH, event.w)
            new_height = max(MIN_WINDOW_HEIGHT, event.h)
            window_surface = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)

    layout = compute_layout()

    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN:
            event_pos = event.pos

            if show_shop:
                if layout["shop_close"].collidepoint(event_pos):
                    show_shop = False
                    play_sound("click")
                else:
                    for index, theme_option in enumerate(themes):
                        action_rect = shop_action_rect(index, layout)
                        owned = theme_option["name"] in owned_themes
                        if action_rect.collidepoint(event_pos):
                            if owned:
                                if index != current_theme:
                                    current_theme = index
                                    play_theme_music(theme_option["name"])
                                    play_sound("click")
                            elif coins >= theme_option["cost"]:
                                coins -= theme_option["cost"]
                                owned_themes.add(theme_option["name"])
                                current_theme = index
                                message = f"Equipped {theme_option['name']} theme"
                                play_theme_music(theme_option["name"])
                                play_sound("buy")
                                check_achievements()
                            save_game()
                continue

            if show_stats:
                if layout["stats_close"].collidepoint(event_pos):
                    show_stats = False
                    play_sound("click")
                continue

            if show_wheel:
                if layout["wheel_close"].collidepoint(event_pos):
                    show_wheel = False
                    play_sound("click")
                elif layout["spin_button"].collidepoint(event_pos):
                    start_spin()
                continue

            active = layout["input_box"].collidepoint(event_pos)

            clicked_mode = None
            for mode_name, rect in layout["mode_buttons"].items():
                if rect.collidepoint(event_pos):
                    clicked_mode = mode_name
                    break

            if clicked_mode and clicked_mode != current_mode:
                current_mode = clicked_mode
                mode_range = (GAME_MODES[current_mode]["low"], GAME_MODES[current_mode]["high"])
                mode_max_attempts = GAME_MODES[current_mode]["attempts"]
                round_max_attempts = mode_max_attempts
                win_streak = 0
                attempts = 0
                input_text = ""
                secret_number = random.randint(*mode_range)
                message = f"{current_mode} mode: guess {mode_range[0]}-{mode_range[1]}"
                feedback_color = theme["base"]
                flash_strength = 0
                play_sound("click")
            elif layout["daily_button"].collidepoint(event_pos) and daily_available:
                claim_daily_reward()
            elif layout["sound_button"].collidepoint(event_pos):
                SOUND_ENABLED = not SOUND_ENABLED
                if MUSIC_LOADED:
                    if SOUND_ENABLED:
                        pygame.mixer.music.unpause()
                    else:
                        pygame.mixer.music.pause()
                play_sound("click")
            elif layout["shop_button"].collidepoint(event_pos):
                show_shop = True
                play_sound("shop_open")
            elif layout["stats_button"].collidepoint(event_pos):
                show_stats = True
                play_sound("click")
            elif layout["wheel_button"].collidepoint(event_pos):
                show_wheel = True
                play_sound("shop_open")
            elif layout["guess_button"].collidepoint(event_pos):
                low, high = mode_range
                if not input_text.isdigit():
                    message = "Type a number first"
                    feedback_color = (201, 20, 20)
                    flash_strength = 180
                    play_sound("miss")
                elif int(input_text) < low or int(input_text) > high:
                    message = f"Pick a number from {low} to {high}"
                    feedback_color = (201, 20, 20)
                    flash_strength = 180
                    play_sound("miss")
                    input_text = ""
                else:
                    guess = int(input_text)
                    attempts += 1
                    if guess == secret_number:
                        win_streak += 1
                        best_streak = max(best_streak, win_streak)
                        last_reward = reward_for_streak(win_streak)
                        coins += last_reward
                        stats["coins_earned_total"] += last_reward
                        stats["wins"] += 1
                        stats["games_played"] += 1
                        stats["total_guesses_in_wins"] += attempts
                        if stats["fastest_win"] is None or attempts < stats["fastest_win"]:
                            stats["fastest_win"] = attempts
                        if current_mode == "Hard":
                            stats["hard_wins"] += 1
                        gain_xp(10 + win_streak * 2)
                        message = f"You win! +{last_reward} coins"
                        feedback_color = (124, 227, 50)
                        flash_strength = 255
                        spawn_win_particles(BASE_WIDTH / 2, 430, last_reward)
                        play_sound("win")
                        attempts = 0
                        round_max_attempts = mode_max_attempts
                        secret_number = random.randint(low, high)
                        check_achievements()
                    else:
                        last_reward = 0
                        feedback_color = (201, 20, 20)
                        flash_strength = 255
                        play_sound("miss")
                        if attempts >= round_max_attempts:
                            win_streak = 0
                            stats["losses"] += 1
                            stats["games_played"] += 1
                            message = f"You lose! The number was {secret_number}"
                            attempts = 0
                            round_max_attempts = mode_max_attempts
                            secret_number = random.randint(low, high)
                        else:
                            remaining = round_max_attempts - attempts
                            hint = get_hint_message(guess, secret_number, low, high)
                            message = f"{hint} ({remaining} left)"
                    input_text = ""
                    save_game()
            else:
                for pid, rect in layout["powerup_buttons"].items():
                    if rect.collidepoint(event_pos):
                        use_powerup(pid)
                        break

        if event.type == pygame.KEYDOWN:
            any_modal_open = show_shop or show_stats or show_wheel
            if event.key == pygame.K_ESCAPE and any_modal_open:
                show_shop = show_stats = show_wheel = False
                play_sound("click")
            elif event.key == pygame.K_RETURN and active and not any_modal_open:
                low, high = mode_range
                if not input_text.isdigit():
                    message = "Type a number first"
                    feedback_color = (201, 20, 20)
                    flash_strength = 180
                    play_sound("miss")
                elif int(input_text) < low or int(input_text) > high:
                    message = f"Pick a number from {low} to {high}"
                    feedback_color = (201, 20, 20)
                    flash_strength = 180
                    play_sound("miss")
                    input_text = ""
                else:
                    guess = int(input_text)
                    attempts += 1
                    if guess == secret_number:
                        win_streak += 1
                        best_streak = max(best_streak, win_streak)
                        last_reward = reward_for_streak(win_streak)
                        coins += last_reward
                        stats["coins_earned_total"] += last_reward
                        stats["wins"] += 1
                        stats["games_played"] += 1
                        stats["total_guesses_in_wins"] += attempts
                        if stats["fastest_win"] is None or attempts < stats["fastest_win"]:
                            stats["fastest_win"] = attempts
                        if current_mode == "Hard":
                            stats["hard_wins"] += 1
                        gain_xp(10 + win_streak * 2)
                        message = f"You win! +{last_reward} coins"
                        feedback_color = (124, 227, 50)
                        flash_strength = 255
                        spawn_win_particles(BASE_WIDTH / 2, 430, last_reward)
                        play_sound("win")
                        attempts = 0
                        round_max_attempts = mode_max_attempts
                        secret_number = random.randint(low, high)
                        check_achievements()
                    else:
                        last_reward = 0
                        feedback_color = (201, 20, 20)
                        flash_strength = 255
                        play_sound("miss")
                        if attempts >= round_max_attempts:
                            win_streak = 0
                            stats["losses"] += 1
                            stats["games_played"] += 1
                            message = f"You lose! The number was {secret_number}"
                            attempts = 0
                            round_max_attempts = mode_max_attempts
                            secret_number = random.randint(low, high)
                        else:
                            remaining = round_max_attempts - attempts
                            hint = get_hint_message(guess, secret_number, low, high)
                            message = f"{hint} ({remaining} left)"
                    input_text = ""
                    save_game()
            elif active and not any_modal_open:
                if event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.unicode.isdigit() and len(input_text) < 2:
                    input_text += event.unicode

    if wheel_spinning:
        wheel_timer -= 1
        if wheel_timer % 4 == 0:
            wheel_display_label = random.choice(WHEEL_REWARDS)["label"]
        if wheel_timer <= 0:
            finish_spin()

    update_bubbles()
    update_particles()
    displayed_coins += (coins - displayed_coins) * 0.15
    if abs(coins - displayed_coins) < 0.5:
        displayed_coins = float(coins)

    base_color = theme["base"]
    mouse_pos = pygame.mouse.get_pos()
    hovering = layout["guess_button"].collidepoint(mouse_pos)

    if flash_strength > 0:
        color = (
            int((base_color[0] * (255 - flash_strength) + feedback_color[0] * flash_strength) / 255),
            int((base_color[1] * (255 - flash_strength) + feedback_color[1] * flash_strength) / 255),
            int((base_color[2] * (255 - flash_strength) + feedback_color[2] * flash_strength) / 255),
        )
        flash_strength -= 5
    else:
        color = base_color

    window_surface.fill(color)
    draw_bubbles(layout)

    fonts = layout["fonts"]

    title_text = fonts["title"].render("GUESS THE NUMBER", True, theme["accent"])
    title_rect = title_text.get_rect(center=to_point(BASE_WIDTH // 2, 100, layout))
    window_surface.blit(title_text, title_rect)

    draw_text(f"{mode_range[0]} - {mode_range[1]}", fonts["small"], (255, 255, 255), center=to_point(BASE_WIDTH // 2, 140, layout))

    draw_daily_banner(layout, daily_available)

    for mode_name, rect in layout["mode_buttons"].items():
        selected = mode_name == current_mode
        draw_button(rect, mode_name, fonts["tiny"], theme["button"], theme["button_hover"], layout)
        if selected:
            mode_border_radius = max(2, int(8 * layout["s"]))
            pygame.draw.rect(window_surface, (255, 255, 255), rect, max(2, int(4 * layout["s"])), border_radius=mode_border_radius)

    draw_coin_text(str(int(round(displayed_coins))), 20, 20, layout)
    stat_cards = [
        (f"Streak: {win_streak}", 20, 58),
        (f"Best: {best_streak}", 20, 96),
        (f"Attempts: {attempts}/{round_max_attempts}", 20, 134),
    ]
    for text, x, y in stat_cards:
        draw_text(text, fonts["small"], (255, 255, 255), topleft=to_point(x, y, layout))

    draw_xp_bar(layout, theme)

    next_reward = reward_for_streak(win_streak + 1)
    draw_text(f"Next win: +{next_reward} coins", fonts["small"], (255, 255, 255), topleft=to_point(548, 72, layout))

    input_box = layout["input_box"]
    border_radius = max(2, int(8 * layout["s"]))
    pygame.draw.rect(window_surface, (255, 255, 255), input_box, border_radius=border_radius)
    pygame.draw.rect(window_surface, theme["accent"], input_box, max(1, int(3 * layout["s"])), border_radius=border_radius)
    text_point = (input_box.x + int(12 * layout["s"]), input_box.y + int(10 * layout["s"]))
    placeholder = "" if active or input_text else "Your guess"
    if placeholder:
        draw_text(placeholder, fonts["normal"], (130, 120, 138), topleft=text_point)
    draw_text(input_text, fonts["normal"], (20, 20, 20), topleft=text_point)

    if hovering:
        button_scale += 0.02
    else:
        button_scale -= 0.02
    button_scale = max(1.0, min(button_scale, 1.1))
    guess_button = layout["guess_button"]
    scaled_width = int(guess_button.width * button_scale)
    scaled_height = int(guess_button.height * button_scale)
    draw_guess_button = pygame.Rect(
        guess_button.centerx - scaled_width // 2,
        guess_button.centery - scaled_height // 2,
        scaled_width,
        scaled_height,
    )
    draw_button(draw_guess_button, "Guess", fonts["normal"], theme["button"], theme["button_hover"], layout)

    sound_icon = icons.get("sound_on") if SOUND_ENABLED else icons.get("sound_off")
    draw_icon_button(layout["sound_button"], sound_icon, 22, "S" if SOUND_ENABLED else "M",
                      theme["button"], theme["button_hover"], layout)

    shop_button = layout["shop_button"]
    draw_button(shop_button, "Shop", fonts["tiny"], theme["button"], theme["button_hover"], layout)

    stats_button = layout["stats_button"]
    draw_button(stats_button, "Stats", fonts["tiny"], theme["button"], theme["button_hover"], layout)

    wheel_button = layout["wheel_button"]
    draw_button(wheel_button, "Spin", fonts["tiny"], theme["button"], theme["button_hover"], layout)

    draw_text(message, fonts["normal"], (255, 255, 255), center=to_point(BASE_WIDTH // 2, 430, layout))

    draw_powerups(layout, theme)
    draw_particles(layout)

    if show_shop:
        draw_shop(layout)
    if show_stats:
        draw_stats(layout)
    if show_wheel:
        draw_wheel(layout)

    draw_popup(layout)

    pygame.display.flip()
    clock.tick(60)

save_game()
pygame.quit()
sys.exit()