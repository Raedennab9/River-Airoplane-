
"""
airplane_shooter_advanced.py
Advanced 2‑D airplane shooter with river, parallax clouds, power‑ups, difficulty ramp,
particles, screen shake, pause/restart, and minimal state machine.
Compatible with pygame (<=3.12) and pygame‑ce (3.13+).

Controls:
- Move: Arrow keys or WASD
- Shoot: Space
- Pause/Resume: P
- Quit: Esc
- Restart (Game Over): R
"""
from __future__ import annotations
import asyncio
import math, random, sys
from pathlib import Path
from typing import Tuple, Optional
import pygame

# --------------- Config ----------------
WIDTH, HEIGHT = 800, 600
FPS = 60

# Speeds & timing (pixels/sec & seconds)
PLAYER_SPEED = 300
BULLET_SPEED = -720
ENEMY_MIN_SPEED = 140
ENEMY_MAX_SPEED = 360
SCROLL_SPEED = 120

SPAWN_BASE_INTERVAL = 0.9  # seconds (will decrease with difficulty)
DIFFICULTY_ACCEL = 0.0006  # lower = slower ramp (affects spawn rate)
ENEMY_SPEED_BONUS = 12     # added *sqrt(t) over time

# Player
PLAYER_MAX_HP = 3
INVINCIBILITY_TIME = 1.0    # seconds after hit
FIRE_COOLDOWN = 0.22        # seconds between shots (base)

# Power‑ups
POWERUP_DURATION = 8.0
POWERUP_DROP_PROB = 0.12  # 12% chance per enemy destroyed
RAPIDFIRE_COOLDOWN = 0.08
SPREAD_ANGLE = 0.28  # radians offset for side bullets

# Colors
FOREST = (24, 68, 30)
FOREST_DARK = (18, 54, 24)
WATER = (22, 98, 160)
WATER_LIGHT = (35, 140, 210)
SHORE = (210, 210, 190)
SKY_TEXT = (245, 245, 245)
UI_YELLOW = (250, 230, 90)
UI_RED = (220, 60, 60)
UI_GREEN = (60, 200, 120)
UI_BLUE = (70, 140, 220)
UI_GREY = (180, 180, 185)

SCRIPT_DIR = Path(__file__).resolve().parent
ASSET_CANDIDATES = (
    Path(__file__).resolve().with_suffix('') / "assets",
    SCRIPT_DIR / "assets",
)
ASSETS_DIR = next((path for path in ASSET_CANDIDATES if path.is_dir()), ASSET_CANDIDATES[-1])

# --------------- Helpers ----------------
def load_image(name: str, size=None) -> Optional[pygame.Surface]:
    p = ASSETS_DIR / name
    if not p.exists(): return None
    try:
        img = pygame.image.load(str(p)).convert_alpha()
        if size is not None: img = pygame.transform.smoothscale(img, size)
        return img
    except Exception:
        return None

def load_sound(name: str) -> Optional[pygame.mixer.Sound]:
    p = ASSETS_DIR / name
    if not p.exists(): return None
    try:
        return pygame.mixer.Sound(str(p))
    except Exception:
        return None

def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

# --------------- Background ----------------
RIVER_BASE_WIDTH = 360
RIVER_WIDTH_VARIATION = 70
RIVER_AMPLITUDE = 120
RIVER_FREQ = 0.0065
RIVER_SEGMENT_H = 8

class RiverBackground:
    def __init__(self, width, height):
        self.width = width; self.height = height
        self.scroll_h = height * 3
        self.surface = pygame.Surface((width, self.scroll_h)).convert()
        self.offset = 0
        self._render()

    def _cx(self, y): # center x of river
        return self.width/2 + RIVER_AMPLITUDE*math.sin(RIVER_FREQ*y) + 0.35*RIVER_AMPLITUDE*math.sin(RIVER_FREQ*0.53*y + 1.7)
    def _hw(self, y): # half width
        return (RIVER_BASE_WIDTH + RIVER_WIDTH_VARIATION*math.sin(RIVER_FREQ*0.77*y + 2.4))/2

    def _render(self):
        s = self.surface
        s.fill(FOREST)
        for _ in range(250):
            x = random.randint(0, self.width); y = random.randint(0, self.scroll_h)
            r = random.randint(6, 26)
            pygame.draw.circle(s, FOREST_DARK, (x,y), r)
        y = 0; L=[]; R=[]
        while y <= self.scroll_h + RIVER_SEGMENT_H:
            cx = self._cx(y); hw = self._hw(y)
            L.append((cx - hw, y)); R.append((cx + hw, y)); y += RIVER_SEGMENT_H
        for i in range(len(L)-1):
            pygame.draw.polygon(s, WATER, [L[i], R[i], R[i+1], L[i+1]])
        pygame.draw.lines(s, SHORE, False, L, 3)
        pygame.draw.lines(s, SHORE, False, R, 3)
        for _ in range(220):
            ry = random.randint(0, self.scroll_h - 1)
            cx = self._cx(ry); hw = self._hw(ry) * random.uniform(0.2, 0.9)
            x1 = int(cx - hw + random.uniform(-12, 12))
            x2 = int(cx + hw + random.uniform(-12, 12))
            pygame.draw.line(s, WATER_LIGHT, (x1, ry), (x2, ry), 1)

    def update(self, dt):
        self.offset = (self.offset + SCROLL_SPEED*dt) % self.scroll_h

    def draw(self, screen, ox=0, oy=0):
        y1 = int(self.offset); h1 = min(self.scroll_h - y1, HEIGHT)
        screen.blit(self.surface, (ox, oy), area=pygame.Rect(0, y1, WIDTH, h1))
        if h1 < HEIGHT:
            h2 = HEIGHT - h1
            screen.blit(self.surface, (ox, oy+h1), area=pygame.Rect(0, 0, WIDTH, h2))

class CloudLayer:
    def __init__(self, speed, density, alpha=150):
        self.speed = speed
        self.clouds = []
        for _ in range(density):
            x = random.randint(0, WIDTH); y = random.randint(0, HEIGHT)
            w = random.randint(80, 180); h = random.randint(30, 60)
            self.clouds.append([x,y,w,h])
        self.surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.surface.set_alpha(alpha)
        self._render()

    def _render(self):
        s = self.surface
        s.fill((0,0,0,0))
        for x,y,w,h in self.clouds:
            pygame.draw.ellipse(s, (220,220,230,220), (x,y,w,h))

    def update(self, dt):
        for c in self.clouds:
            c[0] -= self.speed*dt
            if c[0] + c[2] < -10:
                c[0] = WIDTH + random.randint(0, 120)
                c[1] = random.randint(0, HEIGHT//2)
        self._render()

    def draw(self, screen, ox=0, oy=0):
        screen.blit(self.surface, (ox, oy))

# --------------- Sprites ----------------
def jet_surface(size=(64,52)):
    w,h = size
    s = pygame.Surface((w,h), pygame.SRCALPHA)
    body = (200,200,210); accent=(90,120,180)
    pygame.draw.polygon(s, body, [(w*0.5,0),(w*0.62,h*0.25),(w*0.62,h*0.70),(w*0.5,h),(w*0.38,h*0.70),(w*0.38,h*0.25)])
    pygame.draw.polygon(s, accent, [(w*0.5,h*0.08),(w*0.56,h*0.30),(w*0.56,h*0.46),(w*0.5,h*0.54),(w*0.44,h*0.46),(w*0.44,h*0.30)])
    pygame.draw.polygon(s, body, [(w*0.10,h*0.48),(w*0.36,h*0.46),(w*0.36,h*0.62),(w*0.14,h*0.72)])
    pygame.draw.polygon(s, body, [(w*0.90,h*0.48),(w*0.64,h*0.46),(w*0.64,h*0.62),(w*0.86,h*0.72)])
    pygame.draw.polygon(s, body, [(w*0.34,h*0.70),(w*0.46,h*0.78),(w*0.42,h*0.96),(w*0.28,h*0.84)])
    pygame.draw.polygon(s, body, [(w*0.66,h*0.70),(w*0.54,h*0.78),(w*0.58,h*0.96),(w*0.72,h*0.84)])
    pygame.draw.polygon(s, (30,30,40), [(w*0.5,0),(w*0.62,h*0.25),(w*0.62,h*0.70),(w*0.5,h),(w*0.38,h*0.70),(w*0.38,h*0.25)],2)
    return s

def heli_surface(size=(56,44)):
    w,h=size; s=pygame.Surface((w,h), pygame.SRCALPHA); body=(170,40,50); glass=(50,120,170); dark=(30,30,30)
    pygame.draw.ellipse(s, body, (w*0.18,h*0.28,w*0.64,h*0.44))
    pygame.draw.ellipse(s, glass, (w*0.48,h*0.34,w*0.18,h*0.18))
    pygame.draw.rect(s, body, (w*0.10,h*0.38,w*0.14,h*0.08))
    pygame.draw.line(s, dark, (w*0.26,h*0.76),(w*0.70,h*0.76),3)
    pygame.draw.line(s, dark, (w*0.30,h*0.70),(w*0.30,h*0.76),3)
    pygame.draw.line(s, dark, (w*0.66,h*0.70),(w*0.66,h*0.76),3)
    pygame.draw.circle(s, dark, (int(w*0.50), int(h*0.28)), 4)
    pygame.draw.line(s, dark, (w*0.08,h*0.22),(w*0.92,h*0.22),3); return s

def boat_surface(size=(60,36)):
    w,h=size; s=pygame.Surface((w,h), pygame.SRCALPHA); hull=(180,180,190); deck=(90,100,120); stripe=(220,30,30)
    pygame.draw.polygon(s, hull, [(w*0.50,0),(w*0.90,h*0.40),(w*0.50,h),(w*0.10,h*0.40)])
    pygame.draw.polygon(s, deck, [(w*0.38,h*0.14),(w*0.70,h*0.40),(w*0.50,h*0.72),(w*0.28,h*0.40)])
    pygame.draw.line(s, stripe, (w*0.20,h*0.48),(w*0.80,h*0.48),3)
    pygame.draw.polygon(s, (40,40,40), [(w*0.50,0),(w*0.90,h*0.40),(w*0.50,h),(w*0.10,h*0.40)],2); return s

# Sounds (optional)
SHOT_SND = None
EXPLO_SND = None
PUP_SND = None
HIT_SND = None

# ------------ Entities ------------
class Particle(pygame.sprite.Sprite):
    def __init__(self, pos, vel, life=0.35, color=(255,220,120)):
        super().__init__()
        self.image = pygame.Surface((3,3), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (1,1), 1)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(self.rect.center)
        self.vx, self.vy = vel
        self.life = life
    def update(self, dt):
        self.life -= dt
        if self.life <= 0: self.kill()
        self.pos.x += self.vx*dt
        self.pos.y += self.vy*dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))

class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, vx=0, vy=BULLET_SPEED):
        super().__init__()
        self.image = pygame.Surface((4,12), pygame.SRCALPHA)
        pygame.draw.rect(self.image, UI_YELLOW, (0,0,4,12), border_radius=2)
        self.rect = self.image.get_rect(midbottom=pos)
        self.pos = pygame.Vector2(self.rect.center)
        self.vx, self.vy = vx, vy
    def update(self, dt):
        self.pos.x += self.vx*dt
        self.pos.y += self.vy*dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        if self.rect.bottom < 0 or self.rect.top > HEIGHT or self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()

class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, pos, vx, vy):
        super().__init__()
        self.image = pygame.Surface((4,10), pygame.SRCALPHA)
        pygame.draw.rect(self.image, UI_RED, (0,0,4,10), border_radius=2)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(self.rect.center)
        self.vx, self.vy = vx, vy
    def update(self, dt):
        self.pos.x += self.vx*dt
        self.pos.y += self.vy*dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        if self.rect.top > HEIGHT or self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()

class PowerUp(pygame.sprite.Sprite):
    TYPES = ("rapid", "spread", "shield")
    COLOR = {"rapid": UI_GREEN, "spread": UI_BLUE, "shield": UI_GREY}
    def __init__(self, pos):
        super().__init__()
        self.kind = random.choice(self.TYPES)
        self.image = pygame.Surface((20,20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.COLOR[self.kind], (10,10), 10)
        font = pygame.font.SysFont("consolas", 14, bold=True)
        letter = {"rapid":"R","spread":"S","shield":"H"}[self.kind]
        txt = font.render(letter, True, (20,20,20))
        self.image.blit(txt, txt.get_rect(center=(10,10)))
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(self.rect.center)
        self.vy = 80
    def update(self, dt):
        self.pos.y += self.vy*dt
        self.rect.centery = round(self.pos.y)
        if self.rect.top > HEIGHT: self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, style="heli", difficulty_t=0.0):
        super().__init__()
        self.style = style
        if style == "heli":
            img = load_image("enemy.png", size=(56,44))
            self.image = img if img is not None else heli_surface()
        elif style == "boat":
            self.image = boat_surface()
        else:  # "strafer"
            self.image = heli_surface()
        x = random.randrange(40, WIDTH-40)
        self.rect = self.image.get_rect(midtop=(x, -40))
        self.pos = pygame.Vector2(self.rect.topleft)
        base_speed = random.randint(ENEMY_MIN_SPEED, ENEMY_MAX_SPEED)
        self.vy = base_speed + ENEMY_SPEED_BONUS*(difficulty_t**0.5)
        self.t = 0.0
        self.shoot_cd = random.uniform(1.2, 2.2) if style != "boat" else 9999  # boats don't shoot
    def update(self, dt):
        self.t += dt
        # movement patterns
        if self.style == "heli":
            self.pos.y += self.vy*dt
            self.pos.x += 80*math.sin(self.t*2.2)*dt
        elif self.style == "strafer":
            self.pos.y += self.vy*dt
            self.pos.x += 140*math.sin(self.t*3.0)*dt
        else:  # boat
            self.pos.y += self.vy*dt
        self.rect.topleft = (round(self.pos.x), round(self.pos.y))
        if self.rect.top > HEIGHT: self.kill()
    def ready_to_shoot(self, dt) -> bool:
        self.shoot_cd -= dt
        if self.shoot_cd <= 0:
            self.shoot_cd = random.uniform(1.1, 2.0)
            return True
        return False

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        img = load_image("player.png", size=(64,52))
        self.image = img if img is not None else jet_surface()
        self.rect = self.image.get_rect(midbottom=(WIDTH//2, HEIGHT-30))
        self.pos = pygame.Vector2(self.rect.topleft)
        self.speed = PLAYER_SPEED
        self.hp = PLAYER_MAX_HP
        self.inv = 0.0
        self.shield = False
        self.fire_cd = 0.0
        self.spread = False
        self.rapid = False
        self.power_timers = {"shield":0.0, "rapid":0.0, "spread":0.0}
    def update(self, dt, keys):
        vx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        vy = (keys[pygame.K_DOWN]  or keys[pygame.K_s]) - (keys[pygame.K_UP]   or keys[pygame.K_w])
        if vx and vy:
            vx *= math.sqrt(0.5)
            vy *= math.sqrt(0.5)
        self.pos.x += vx*self.speed*dt
        self.pos.y += vy*self.speed*dt
        self.rect.topleft = (round(self.pos.x), round(self.pos.y))
        self.rect.clamp_ip(pygame.Rect(0,0,WIDTH,HEIGHT))
        self.pos.x, self.pos.y = self.rect.topleft
        self.inv = max(0.0, self.inv - dt)
        self.fire_cd = max(0.0, self.fire_cd - dt)
        # countdown powerups
        for k in list(self.power_timers.keys()):
            self.power_timers[k] = max(0.0, self.power_timers[k]-dt)
        self.shield = self.power_timers["shield"]>0
        self.rapid  = self.power_timers["rapid"]>0
        self.spread = self.power_timers["spread"]>0
    def shoot(self):
        if self.fire_cd > 0: return []
        base_cd = RAPIDFIRE_COOLDOWN if self.rapid else FIRE_COOLDOWN
        self.fire_cd = base_cd
        bullets = []
        if self.spread:
            # left / center / right
            bullets.append(Bullet(self.rect.midtop, vx=-180, vy=BULLET_SPEED))
            bullets.append(Bullet(self.rect.midtop))
            bullets.append(Bullet(self.rect.midtop, vx= 180, vy=BULLET_SPEED))
        else:
            bullets.append(Bullet(self.rect.midtop))
        return bullets
    def damage(self, amount=1):
        if self.inv>0: return False
        if self.shield:
            self.power_timers["shield"] = 0.0  # consume shield
            self.inv = 0.15
            return False
        self.hp -= amount
        self.inv = INVINCIBILITY_TIME
        return self.hp <= 0
    def apply_power(self, kind: str):
        self.power_timers[kind] = POWERUP_DURATION

# --------------- Difficulty & State ---------------
class SpawnManager:
    def __init__(self):
        self.t = 0.0
        self.spawn_accum = 0.0
    def update(self, dt):
        self.t += dt
        self.spawn_accum += dt
    def interval(self) -> float:
        return max(0.25, SPAWN_BASE_INTERVAL - DIFFICULTY_ACCEL*self.t)
    def should_spawn(self) -> bool:
        if self.spawn_accum >= self.interval():
            self.spawn_accum = 0.0
            return True
        return False
    def style(self) -> str:
        r = random.random()
        if r < 0.5: return "heli"
        elif r < 0.8: return "boat"
        else: return "strafer"

class Game:
    MENU, PLAY, PAUSE, GAMEOVER = range(4)
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.display.set_caption("Air Combat: River Run — Advanced")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        # sounds (optional)
        global SHOT_SND, EXPLO_SND, PUP_SND, HIT_SND
        SHOT_SND = load_sound("shot.wav")
        EXPLO_SND = load_sound("explosion.wav")
        PUP_SND  = load_sound("powerup.wav")
        HIT_SND  = load_sound("hit.wav")
        music = ASSETS_DIR / "music.ogg"
        if music.exists():
            try:
                pygame.mixer.music.load(str(music))
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)
            except Exception: pass
        # background & parallax
        self.bg = RiverBackground(WIDTH, HEIGHT)
        self.clouds1 = CloudLayer(speed=15, density=6, alpha=140)
        self.clouds2 = CloudLayer(speed=40, density=10, alpha=180)
        # groups
        self.all = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        # player
        self.player = Player()
        self.all.add(self.player)
        # other
        self.spawn = SpawnManager()
        self.score = 0
        self.state = self.MENU
        self.shake = 0.0

    def reset(self):
        self.all.empty()
        self.bullets.empty()
        self.enemies.empty()
        self.enemy_bullets.empty()
        self.particles.empty()
        self.powerups.empty()
        self.player = Player()
        self.all.add(self.player)
        self.spawn = SpawnManager()
        self.score = 0
        self.shake = 0.0
        self.state = self.PLAY

    async def run(self):
        while True:
            dt = min(self.clock.tick(FPS)/1000.0, 0.05)
            if not self.handle_events(): return
            if self.state == self.PLAY:
                self.update(dt)
            self.draw()
            # Yield to the browser event loop when packaged with Pygbag.
            await asyncio.sleep(0)

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT: return False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: return False
                if self.state == self.MENU and e.key == pygame.K_RETURN:
                    self.state = self.PLAY
                elif self.state == self.GAMEOVER and e.key == pygame.K_r:
                    self.reset()
                elif self.state == self.PLAY and e.key == pygame.K_p:
                    self.state = self.PAUSE
                elif self.state == self.PAUSE and e.key == pygame.K_p:
                    self.state = self.PLAY
        return True

    def fire_player_weapon(self):
        shots = self.player.shoot()
        if not shots:
            return
        self.bullets.add(shots)
        self.all.add(shots)
        if SHOT_SND:
            SHOT_SND.play()
        particles = [
            Particle(
                self.player.rect.midtop,
                (random.uniform(-30, 30), -random.uniform(120, 200)),
                life=0.2,
            )
            for _ in range(4)
        ]
        self.particles.add(particles)
        self.all.add(particles)

    def update(self, dt):
        # bg & parallax
        self.bg.update(dt); self.clouds1.update(dt); self.clouds2.update(dt)
        # player
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys)
        if keys[pygame.K_SPACE]:
            self.fire_player_weapon()
        # spawn logic
        self.spawn.update(dt)
        if self.spawn.should_spawn():
            style = self.spawn.style()
            e = Enemy(style=style, difficulty_t=self.spawn.t)
            self.enemies.add(e); self.all.add(e)
        # enemy shooting
        for e in list(self.enemies):
            if e.style != "boat" and e.ready_to_shoot(dt):
                # shoot toward player
                dx = (self.player.rect.centerx - e.rect.centerx)
                dy = (self.player.rect.centery - e.rect.centery)
                dist = max(1.0, math.hypot(dx,dy))
                vx = 0.0 + 180*dx/dist
                vy = 240*dy/dist
                b = EnemyBullet(e.rect.midbottom, vx, vy)
                self.enemy_bullets.add(b); self.all.add(b)
        # update groups
        self.bullets.update(dt); self.enemies.update(dt); self.enemy_bullets.update(dt); self.particles.update(dt); self.powerups.update(dt)
        # collisions
        hits = pygame.sprite.groupcollide(self.enemies, self.bullets, True, True)
        if hits:
            for enemy in hits.keys():
                self.score += 1
                if EXPLO_SND: EXPLO_SND.play()
                self.shake = 7.0
                # explosion particles
                explosion_particles = []
                for _ in range(16):
                    ang = random.uniform(0, math.tau); sp = random.uniform(80,220)
                    explosion_particles.append(
                        Particle(
                            enemy.rect.center,
                            (math.cos(ang)*sp, math.sin(ang)*sp),
                            life=0.5,
                            color=(255,170,60),
                        )
                    )
                self.particles.add(explosion_particles)
                self.all.add(explosion_particles)
                # power‑up drop
                if random.random() < POWERUP_DROP_PROB:
                    pu = PowerUp(enemy.rect.center)
                    self.powerups.add(pu); self.all.add(pu)
        # player collisions
        collided_enemies = pygame.sprite.spritecollide(self.player, self.enemies, dokill=True)
        collided_bullets = pygame.sprite.spritecollide(self.player, self.enemy_bullets, dokill=True)
        if (collided_enemies or collided_bullets) and self.player.inv <= 0:
            dead = self.player.damage(1)
            if HIT_SND: HIT_SND.play()
            self.shake = 10.0
            if dead:
                self.state = self.GAMEOVER
        # collect powerups
        collected = pygame.sprite.spritecollide(self.player, self.powerups, dokill=True)
        for pu in collected:
            self.player.apply_power(pu.kind)
            if PUP_SND: PUP_SND.play()

        # decay shake
        self.shake = max(0.0, self.shake - 40*dt)

    def draw_ui(self, surf):
        # score
        self.draw_text(surf, f"Score: {self.score}", 24, 10, 10)
        # hearts
        x0 = 10; y0 = 40
        for i in range(PLAYER_MAX_HP):
            col = UI_RED if i < self.player.hp else (80,80,80)
            pygame.draw.circle(surf, col, (x0 + i*22, y0), 8)
        # powerup bars
        bar_w = 140; bar_h = 8; px = WIDTH- bar_w - 12; py = 12
        self.draw_bar(surf, px, py, bar_w, bar_h, self.player.power_timers["shield"]/POWERUP_DURATION, UI_GREY, "Shield")
        self.draw_bar(surf, px, py+14, bar_w, bar_h, self.player.power_timers["rapid"]/POWERUP_DURATION, UI_GREEN, "Rapid")
        self.draw_bar(surf, px, py+28, bar_w, bar_h, self.player.power_timers["spread"]/POWERUP_DURATION, UI_BLUE, "Spread")

    def draw_bar(self, surf, x, y, w, h, frac, color, label):
        frac = clamp(frac, 0.0, 1.0)
        pygame.draw.rect(surf, (60,60,60), (x,y,w,h), border_radius=2)
        if frac>0:
            pygame.draw.rect(surf, color, (x,y,int(w*frac), h), border_radius=2)
        self.draw_text(surf, label, 14, x-58, y-2)

    def draw_text(self, surf, text, size, x, y):
        font = pygame.font.SysFont('segoeui', size, bold=True)
        rend = font.render(text, True, SKY_TEXT)
        surf.blit(rend, rend.get_rect(topleft=(x,y)))

    def draw(self):
        # render to a world surface for shake
        world = pygame.Surface((WIDTH, HEIGHT))
        self.bg.draw(world)
        self.clouds1.draw(world)
        for sprite in self.all:
            if sprite is self.player and self.player.inv > 0 and int(self.player.inv * 12) % 2 == 0:
                continue
            world.blit(sprite.image, sprite.rect)
        self.clouds2.draw(world)
        self.draw_ui(world)

        # apply shake
        ox = int(random.uniform(-self.shake, self.shake)) if self.shake>0 else 0
        oy = int(random.uniform(-self.shake, self.shake)) if self.shake>0 else 0
        self.screen.fill((0, 0, 0))
        self.screen.blit(world, (ox, oy))

        # overlays for menu/pause/gameover
        if self.state == self.MENU:
            self.draw_centered("AIR COMBAT: RIVER RUN", 48, 0, -40)
            self.draw_centered("Press ENTER to start", 28, 0, 10)
            self.draw_centered("Move: WASD/Arrows • Shoot: Space • Pause: P • Quit: Esc", 20, 0, 44)
        elif self.state == self.PAUSE:
            self.draw_centered("PAUSED", 48, 0, -10)
            self.draw_centered("Press P to resume", 24, 0, 28)
        elif self.state == self.GAMEOVER:
            self.draw_centered("MISSION FAILED", 48, 0, -20)
            self.draw_centered(f"Final Score: {self.score}", 30, 0, 20)
            self.draw_centered("Press R to restart or Esc to quit", 22, 0, 50)

        pygame.display.flip()

    def draw_centered(self, text, size, dx=0, dy=0):
        font = pygame.font.SysFont('segoeui', size, bold=True)
        rend = font.render(text, True, (255,255,255))
        rect = rend.get_rect(center=(WIDTH//2 + dx, HEIGHT//2 + dy))
        self.screen.blit(rend, rect)

async def main():
    await Game().run()

if __name__ == "__main__":
    asyncio.run(main())
