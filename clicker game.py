import json
import math
import random
import time
import turtle
from pathlib import Path


# here you go 

WIDTH, HEIGHT = 960, 600
SAVE_FILE = Path(__name__).resolve().with_name("clicker_save.json")

THEMES = {
    "midnight": {
        "background": "#111827", "panel": "#1F2937", "panel2": "#273449",
        "text": "#F9FAFB", "muted": "#9CA3AF", "accent": "#8B5CF6",
        "accent2": "#38BDF8", "success": "#34D399", "danger": "#FB7185",
        "gold": "#FBBF24",
    },
    "sunset": {
        "background": "#17151F", "panel": "#2B2438", "panel2": "#372C49",
        "text": "#FFF7ED", "muted": "#C4B5C9", "accent": "#FB7185",
        "accent2": "#F59E0B", "success": "#4ADE80", "danger": "#EF4444",
        "gold": "#FDE68A",
    },
    "ocean": {
        "background": "#082F49", "panel": "#164E63", "panel2": "#155E75",
        "text": "#ECFEFF", "muted": "#A5F3FC", "accent": "#22D3EE",
        "accent2": "#818CF8", "success": "#5EEAD4", "danger": "#FDA4AF",
        "gold": "#FACC15",
    },
}

screen = turtle.Screen()
screen.setup(WIDTH, HEIGHT)
screen.title("Clicker Forge")
screen.tracer(0, 0)
screen.cv.winfo_toplevel().resizable(False, False)

ui = turtle.Turtle(visible=False)
ui.speed(0)
ui.pen(speed=0)


class Game:
    def __init__(self):
        self.score = 0.0
        self.total_clicks = 0.0
        self.click_power = 1.0
        self.rebirths = 0
        self.theme_name = "midnight"
        self.shop_open = False
        self.settings_open = False
        self.upgrade_level = {"power": 0, "auto": 0, "boost": 0}
        self.fortune_ready_at = 0
        self.best_score = 0.0
        self.load()

    @property
    def rebirth_multiplier(self):
        return 1.0 + self.rebirths * 0.25

    @property
    def clicks_per_second(self):
        return self.upgrade_level["auto"] * self.rebirth_multiplier

    def upgrade_cost(self, name):
        base = {"power": 25, "auto": 100, "boost": 500}[name]
        growth = {"power": 1.65, "auto": 1.8, "boost": 2.1}[name]
        return int(base * (growth ** self.upgrade_level[name]))

    def buy(self, name):
        cost = self.upgrade_cost(name)
        if self.score < cost:
            notify(f"Need {format_number(cost)} points", "danger")
            return False
        self.score -= cost
        self.upgrade_level[name] += 1
        if name == "power":
            self.click_power += 1
        elif name == "boost":
            self.click_power *= 2
        notify("Upgrade purchased!", "success")
        save_game()
        redraw()
        return True

    def rebirth(self):
        if self.score < 1_000_000:
            notify("Reach 1M to rebirth", "danger")
            return
        self.rebirths += 1
        self.score = 0
        self.click_power = 1
        self.upgrade_level = {"power": 0, "auto": 0, "boost": 0}
        notify("Rebirth complete! Permanent bonus earned.", "gold")
        save_game()
        redraw()

    def fortune(self):
        now = time.time()
        if now < self.fortune_ready_at:
            remaining = int(self.fortune_ready_at - now)
            notify(f"Fortune wheel: {remaining}s", "danger")
            return
        self.fortune_ready_at = now + 30
        roll = random.randint(1, 100)
        if roll <= 45:
            gain = max(10, int(self.score * 0.10))
            self.score += gain
            notify(f"Lucky! +{format_number(gain)}", "success")
        elif roll <= 80:
            gain = max(25, int(self.click_power * 5))
            self.click_power += gain
            notify(f"Power surge! +{gain} per click", "gold")
        else:
            penalty = int(self.score * 0.05)
            self.score = max(0, self.score - penalty)
            notify(f"A small loss: -{format_number(penalty)}", "danger")
        save_game()
        redraw()

    def save(self):
        data = {
            "score": self.score,
            "total_clicks": self.total_clicks,
            "click_power": self.click_power,
            "rebirths": self.rebirths,
            "theme_name": self.theme_name,
            "upgrade_level": self.upgrade_level,
            "fortune_ready_at": self.fortune_ready_at,
            "best_score": self.best_score,
        }
        try:
            SAVE_FILE.write_text(json.dumps(data), encoding="utf-8")
        except OSError:
            pass

    def load(self):
        try:
            data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
            self.score = float(data.get("score", 0))
            self.total_clicks = float(data.get("total_clicks", 0))
            self.click_power = float(data.get("click_power", 1))
            self.rebirths = int(data.get("rebirths", 0))
            self.theme_name = data.get("theme_name", "midnight")
            if self.theme_name not in THEMES:
                self.theme_name = "midnight"
            self.upgrade_level = data.get("upgrade_level", {"power": 0, "auto": 0, "boost": 0})
            self.fortune_ready_at = float(data.get("fortune_ready_at", 0))
            self.best_score = float(data.get("best_score", 0))
        except (OSError, json.JSONDecodeError, TypeError):
            pass


game = Game()
theme = THEMES[game.theme_name]
particles = []
popups = []
notification = {"text": "", "kind": "accent", "until": 0}


def format_number(value):
    value = float(value)
    units = ["", "K", "M", "B", "T", "Qa", "Qi"]
    index = 0
    while abs(value) >= 1000 and index < len(units) - 1:
        value /= 1000
        index += 1
    if abs(value) >= 100:
        return f"{value:.0f}{units[index]}"
    if abs(value) >= 10:
        return f"{value:.1f}{units[index]}"
    return f"{value:.2f}{units[index]}".rstrip("0").rstrip(".")


def notify(text, kind="accent"):
    notification["text"] = text
    notification["kind"] = kind
    notification["until"] = time.time() + 2.2


def save_game():
    game.best_score = max(game.best_score, game.score)
    game.save()


def set_theme(name):
    global theme
    game.theme_name = name
    theme = THEMES[name]
    notify(f"{name.title()} theme selected", "success")
    save_game()
    redraw()


def inside(x, y, cx, cy, width, height):
    return cx - width / 2 <= x <= cx + width / 2 and cy - height / 2 <= y <= cy + height / 2


def round_rect(x, y, width, height, fill, radius=12, outline=None):
    ui.penup()
    ui.goto(x - width / 2 + radius, y - height / 2)
    ui.pendown()
    ui.color(outline or fill, fill)
    ui.begin_fill()
    ui.goto(x + width / 2 - radius, y - height / 2)
    ui.circle(radius, 90)
    ui.goto(x + width / 2, y + height / 2 - radius)
    ui.circle(radius, 90)
    ui.goto(x - width / 2 + radius, y + height / 2)
    ui.circle(radius, 90)
    ui.goto(x - width / 2, y - height / 2 + radius)
    ui.circle(radius, 90)
    ui.goto(x - width / 2 + radius, y - height / 2)
    ui.end_fill()


def write(text, x, y, size=16, color=None, align="left", bold=False):
    ui.penup()
    ui.goto(x, y)
    ui.color(color or theme["text"])
    weight = "bold" if bold else "normal"
    ui.write(text, align=align, font=("Arial", size, weight))


def draw_header():
    round_rect(0, 255, 920, 75, theme["panel"])
    write("CLICKER", -430, 262, 12, theme["accent2"], bold=True)
    write("FORGE", -430, 238, 28, theme["text"], bold=True)

    write("SCORE", -100, 268, 11, theme["muted"], align="center", bold=True)
    write(format_number(game.score), -100, 235, 30, theme["text"], align="center", bold=True)

    write("PER CLICK", 110, 268, 11, theme["muted"], align="center", bold=True)
    write(format_number(game.click_power), 110, 240, 20, theme["accent2"], align="center", bold=True)

    write("PER SECOND", 260, 268, 11, theme["muted"], align="center", bold=True)
    write(format_number(game.clicks_per_second), 260, 240, 20, theme["success"], align="center", bold=True)


def draw_click_area():
    round_rect(-170, -25, 480, 430, theme["panel"])

    # Ambient rings
    ui.penup()
    ui.goto(-170, -25)
    ui.dot(214, theme["panel2"])
    ui.goto(-170, -25)
    ui.dot(194, theme["accent"])
    ui.goto(-170, -25)
    ui.dot(174, theme["accent2"])
    ui.goto(-170, -25)
    ui.dot(154, theme["background"])

    write("FORGE", -170, -10, 24, theme["text"], align="center", bold=True)
    write("tap to produce", -170, -38, 12, theme["muted"], align="center")

    write(f"+{format_number(game.click_power)}", -170, 42, 18, theme["gold"], align="center", bold=True)

    round_rect(-170, -215, 200, 42, theme["panel2"])
    fortune_text = "FORTUNE WHEEL"
    remaining = int(game.fortune_ready_at - time.time())
    if remaining > 0:
        fortune_text = f"READY IN {remaining}s"
    write(fortune_text, -170, -226, 12, theme["gold"], align="center", bold=True)


def draw_side_buttons():
    round_rect(205, 118, 220, 74, theme["accent"], outline=theme["accent"])
    write("UPGRADES", 205, 111, 16, theme["text"], align="center", bold=True)
    write("Shop & boosts", 205, 87, 10, theme["text"], align="center")

    round_rect(205, 28, 220, 74, theme["panel2"])
    write("REBIRTH", 205, 21, 16, theme["gold"], align="center", bold=True)
    write("1M required", 205, -3, 10, theme["muted"], align="center")

    round_rect(205, -62, 220, 74, theme["panel2"])
    write("THEMES", 205, -69, 16, theme["text"], align="center", bold=True)
    write("Customize", 205, -93, 10, theme["muted"], align="center")


def shop_card(name, title, subtitle, cost, y, accent):
    affordable = game.score >= cost
    bg = theme["panel2"] if affordable else theme["panel"]
    round_rect(205, y, 220, 86, bg, outline=accent if affordable else theme["panel2"])
    write(title, 125, y + 20, 13, accent if affordable else theme["muted"], bold=True)
    write(subtitle, 125, y - 3, 10, theme["muted"])
    write(format_number(cost), 205, y - 29, 11, theme["gold"], align="center", bold=True)
    level = game.upgrade_level[name]
    write(f"LV. {level}", 300, y + 20, 10, theme["muted"], align="right")


def draw_shop():
    round_rect(205, -20, 220, 340, theme["panel"])
    write("UPGRADES", 205, 128, 17, theme["text"], align="center", bold=True)

    shop_card("power", "Power Click", "+1 per tap", game.upgrade_cost("power"), 55, theme["accent2"])
    shop_card("auto", "Auto Forge", "+1 point / sec", game.upgrade_cost("auto"), -42, theme["success"])
    shop_card("boost", "Core Amplifier", "Double tap power", game.upgrade_cost("boost"), -139, theme["gold"])


def draw_settings():
    round_rect(205, -20, 220, 340, theme["panel"])
    write("THEMES", 205, 128, 17, theme["text"], align="center", bold=True)

    y_positions = [55, -42, -139]
    for (name, colors), y in zip(THEMES.items(), y_positions):
        selected = name == game.theme_name
        round_rect(205, y, 220, 86, theme["panel2"], outline=colors["accent"] if selected else theme["panel"])
        ui.penup()
        ui.goto(150, y)
        ui.dot(32, colors["accent"])
        ui.goto(150, y)
        ui.dot(20, colors["panel"])
        write(name.title(), 125, y - 5, 13, theme["text"], bold=True)


def draw_notification():
    if time.time() >= notification["until"]:
        return
    color = theme.get(notification["kind"], theme["accent"])
    round_rect(0, -260, 520, 48, theme["panel2"], outline=color)
    write(notification["text"], 0, -272, 13, color, align="center", bold=True)


def draw_footer():
    write(f"REBIRTHS {game.rebirths}  •  BEST {format_number(game.best_score)}", 450, -272, 10, theme["muted"], align="right")


def redraw():
    ui.clear()
    screen.bgcolor(theme["background"])
    draw_header()
    draw_click_area()
    if game.shop_open:
        draw_shop()
    elif game.settings_open:
        draw_settings()
    else:
        draw_side_buttons()

    for popup in popups:
        write(popup["text"], popup["x"], popup["y"], 15, theme["gold"], align="center", bold=True)
    for particle in particles:
        ui.penup()
        ui.goto(particle["x"], particle["y"])
        ui.dot(particle["size"], particle["color"])

    draw_notification()
    draw_footer()
    screen.update()


def create_particles(x, y):
    for _ in range(12):
        angle = random.random() * math.tau
        speed = random.uniform(25, 85)
        particles.append({
            "x": x, "y": y,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "size": random.randint(5, 10),
            "life": 0.55,
            "color": random.choice([theme["accent"], theme["accent2"], theme["gold"]]),
        })


def animate():
    dt = 0.05
    changed = False

    if game.clicks_per_second > 0:
        game.score += game.clicks_per_second * dt
        game.best_score = max(game.best_score, game.score)

    for particle in particles[:]:
        particle["x"] += particle["vx"] * dt
        particle["y"] += particle["vy"] * dt
        particle["vy"] -= 55 * dt
        particle["life"] -= dt
        if particle["life"] <= 0:
            particles.remove(particle)
            changed = True

    for popup in popups[:]:
        popup["y"] += 38 * dt
        popup["life"] -= dt
        if popup["life"] <= 0:
            popups.remove(popup)
            changed = True

    redraw()
    screen.ontimer(animate, 50)


def clicked(x, y):
    if math.hypot(x - -170, y - -25) < 87:
        game.score += game.click_power
        game.total_clicks += 1
        game.best_score = max(game.best_score, game.score)
        create_particles(x, y)
        popups.append({"text": f"+{format_number(game.click_power)}", "x": x, "y": y, "life": 0.7})
        save_game()
        redraw()
        return

    if inside(x, y, -170, -215, 200, 42):
        game.fortune()
        return

    if not game.shop_open and not game.settings_open:
        if inside(x, y, 205, 118, 220, 74):
            game.shop_open = True
            game.settings_open = False
            redraw()
        elif inside(x, y, 205, 28, 220, 74):
            game.rebirth()
        elif inside(x, y, 205, -62, 220, 74):
            game.settings_open = True
            game.shop_open = False
            redraw()
        return

    if game.shop_open:
        if inside(x, y, 205, 55, 220, 86):
            game.buy("power")
        elif inside(x, y, 205, -42, 220, 86):
            game.buy("auto")
        elif inside(x, y, 205, -139, 220, 86):
            game.buy("boost")
        else:
            game.shop_open = False
            redraw()

    elif game.settings_open:
        for (name, _), cy in zip(THEMES.items(), [55, -42, -139]):
            if inside(x, y, 205, cy, 220, 86):
                set_theme(name)
                break
        else:
            game.settings_open = False
            redraw()


def on_close():
    save_game()


screen.onscreenclick(clicked)
screen.onkeypress(lambda: save_game(), "Escape")
screen.listen()
screen.getcanvas().bind("<Destroy>", lambda event: on_close())

redraw()
screen.ontimer(animate, 50)
screen.mainloop()
