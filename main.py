import pygame
import random
import os
import math
import numpy as np
import asyncio

pygame.init()


HEIGHT = 720
WIDTH = 1280
FPS = 120

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("froggy")
clock = pygame.time.Clock()

#game var
wave = 1
mosquitoes_ded = 0
instructions = False

# movement vars
velocity = 0.0
accel = 750
max_speed = 450
friction = 0.85

# frog sprite 
frog_w = 60
frog_h = 40
frog_x = WIDTH // 2 - frog_w // 2
frog_y = HEIGHT - frog_h - 30
frog_rect = pygame.Rect(frog_x, frog_y, frog_w, frog_h)

# tongue vars
tongue_l = 0
tongue_speed = 3200
tongue_max = 650
tongue_shooting = False
tongue_retracting = False

# game vars
bullets_rem = 8
shake_dur = 0
shake_mag = 0
pending_shake = False

# effects
slowdown_t = 0
slowdown_active = False
orig_speed = max_speed
orig_tongue = tongue_speed

speedup_t = 0
speedup_active = False

nausea_t = 0

# wave 
wave_transition = False
wave_transition_x = -WIDTH
wave_transition_speed = 2500
wave_completed = False

# loading assets
frog_img = "assets/frog/frog seperate images/"

tongue_mid = pygame.image.load("assets/tongue/tongue-base.png").convert_alpha()

tongue_tip = pygame.image.load("assets/tongue/tongue-tip.png")

font = "assets/m6x11-font.ttf"
game_font = pygame.font.Font(font, 28)

# sfx
pygame.mixer.set_num_channels(32)

crazy = pygame.mixer.Sound("assets/sfx/crazy.wav")
crazy.set_volume(1.0)

boom = pygame.mixer.Sound("assets/sfx/screenshake.wav")
boom.set_volume(1.0)
boom_delay = 0
boom_to_play = None

tongue_sound = pygame.mixer.Sound("assets/sfx/tongue.wav")
tongue_sound.set_volume(0.3)

mosquito_buzz = pygame.mixer.Sound("assets/sfx/mosquito_buzz.mp3")
mosquito_buzz.set_volume(1.0)

intro_jingle = pygame.mixer.Sound("assets/sfx/bgm/Intro Jingle.wav")
intro_jingle.set_volume(1)
intro_jingle.play()

while pygame.mixer.get_busy():
    pygame.time.wait(100)

bgm = random.choice(["Map.wav", "Mercury.wav", "Venus.wav"])
pygame.mixer.music.load(f"assets/sfx/bgm/{bgm}")
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1)

# animating frog
frog_no = 8
frog_frames = [
    pygame.image.load(f"{frog_img}froggy_{i}.png").convert_alpha()
    for i in range(1, frog_no + 1)
]

frame_ind = 0
frame_time = 0
anim_speed = 0.1


if tongue_l > 0:
    tongue_x = frog_rect.centerx - tongue_mid.get_width() // 2
    tongue_y = frog_rect.top + frog_h // 4 - tongue_l

    middle_len = max(0, tongue_l - tongue_tip.get_height())
    if middle_len > 0:
        stretched_mid = pygame.transform.scale(tongue_mid, (tongue_mid.get_width(), middle_len))
        screen.blit(stretched_mid, (tongue_x, tongue_y))

        tip_y = tongue_y + middle_len
        screen.blit(tongue_tip, (tongue_x, tip_y))

# mosquitoes
class Mosquito:
    def __init__(self):
        self.width = 72
        self.height = 72
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.velox = random.uniform(-250, 250)
        self.veloy = random.uniform(-250, 250)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.type = random.choices(
            ["red", "yellow", "blue"],
            weights=[70, 5, 8],
            k=1
            )[0]
        
        self.frame_delay = 0.12
        self.frame_timer = 0
        self.frame_ind = 0
        self.direction = "down"

        self.channel = pygame.mixer.find_channel()
        if self.channel:
            self.channel.set_volume(0.3)
            self.channel.play(mosquito_buzz, loops=-1)
    
    def stop_sound(self):
        if self.channel:
            self.channel.stop()
    
    def update(self, t):
        self.x += self.velox * t
        self.y += self.veloy * t
        self.rect.center = (int(self.x), int(self.y))

        if self.x < 0:
            self.x = 0
            self.velox *= -1
        if self.x > WIDTH:
            self.x = WIDTH
            self.velox *= -1
        
        if self.y < 0:
            self.y = 0
            self.veloy *= -1
        if self.y > HEIGHT:
            self.y = HEIGHT
            self.veloy *= -1

        if abs(self.velox) > abs(self.veloy):
            if self.velox > 0:
                self.direction = "right"
            else:
                self.direction = "left"
        else:
            if self.veloy < 0:
                self.direction = "up"
            else:
                self.direction = "down"
            
        if self.channel:
            pan = self.x / WIDTH
            self.channel.set_volume(1.3 * (1 - pan), 1.3 * pan)

        self.frame_timer += t
        if self.frame_timer > self.frame_delay:
            self.frame_timer = 0
            self.frame_ind = (self.frame_ind + 1) %  len(mosquito_frames[self.direction])

    def draw(self, screen):
        frame = mosquito_frames[self.direction][self.frame_ind]
        screen.blit(frame, (int(self.x - self.width // 2), int(self.y - self.height // 2)))

        if self.type == "blue":
            bar = (0, 191, 255)
        elif self.type == "yellow":
            bar = (255, 215, 0)
        else:
            bar = None

        if bar:
            bar_h = 4
            bar_w = 20
            bar_x = int(self.x - bar_w // 2)
            bar_y = int(self.y - self.height // 2 + 15)

            pygame.draw.rect(screen, bar, (bar_x, bar_y, bar_w, bar_h), border_radius=2)

mosquitoes = []

for _ in range(random.randint(1, 15)):
    mosquitoes.append(Mosquito())

# requirment to kill to go to next wave
mosquitoes_req = len(mosquitoes)

class Bullets():
    def __init__(self):
        self.x = frog_rect.centerx
        self.y = frog_rect.top
        self.speed = 500
        self.width = 20
        self.height = 25
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
    
    def update(self, t):
        self.y -= self.speed * t
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, surf):
        radius = self.width // 2
        pygame.draw.circle(surf, (255, 255, 255), (int(self.x), int(self.y)), radius)

bullets = []

def img_aspect(img, max_w, max_h):
    iw, ih = img.get_size()
    scale = min(max_w / iw, max_h / ih)
    new_size = (int(iw * scale), int(ih * scale))
    return pygame.transform.scale(img, new_size)

def load_direction_frames(base_folder, direction, size=(72, 72)):
    dir_path = os.path.join(base_folder, direction)
    files = sorted([f for f in os.listdir(dir_path) if f.endswith(".png")])
    return [
        pygame.transform.scale(pygame.image.load(os.path.join(dir_path, f)).convert_alpha(), size)
        for f in files
    ]

def sinwaves(surf, time, amp, wavelen, speed):
    w, h = surf.get_size()
    result = pygame.Surface((w, h), pygame.SRCALPHA)
    strip_h = 4

    for y in range(0, h, strip_h):
        offset = int(amp * math.sin(2 * math.pi * (y / wavelen) + speed  * time))
        rect = pygame.Rect(0, y, w, strip_h)

        result.blit(surf, (offset, y), rect)
    return result


def frenzy(surf, intensity=180, cycle_speed = 5.0):
    array_rgb = pygame.surfarray.array3d(surf)
    array_alpha = pygame.surfarray.array_alpha(surf)
    mask = array_alpha > 0
    t = pygame.time.get_ticks() / 1000.0

    red = (np.sin(cycle_speed * t) * 127  + 128).astype(np.uint8)
    green = (np.sin(cycle_speed * t + 2) * 127 + 128).astype(np.uint8)    
    blue = (np.sin(cycle_speed * t + 4) * 127 + 128).astype(np.uint8)

    # cast the colors over thge image
    array_rgb[..., 0][mask] = (array_rgb[..., 0][mask] * 0.2 + red * 0.8).astype(np.uint8)
    array_rgb[..., 1][mask] = (array_rgb[..., 1][mask] * 0.2 + green * 0.8).astype(np.uint8)
    array_rgb[..., 2][mask] = (array_rgb[..., 2][mask] * 0.2 + blue * 0.8).astype(np.uint8)

    surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    pygame.surfarray.blit_array(surf, array_rgb)
    pygame.surfarray.pixels_alpha(surf)[:] = array_alpha
    return surf

def progress_bar(surf, x, y, w, h, progress, bg_clr =(30, 30, 30), fill_clr= (220, 40, 40), border_clr= (10, 10, 10), radius=7, outline=3):

    pygame.draw.rect(surf, border_clr, (x - outline, y - outline, w + 2 *outline, h+2 * outline), border_radius=radius + outline)
    pygame.draw.rect(surf, bg_clr, (x, y, w, h), border_radius=radius)

    fill_w = int(w * min(max(progress, 0), 1))
    if fill_w > 0:
        pygame.draw.rect(surf, fill_clr, (x, y, fill_w, h), border_radius=radius)

bg_color = (
    random.randint(150, 255),
    random.randint(150, 255),
    random.randint(150, 255)
)

def show_instructions(surf):

    lines = [
        "instructions:",
        "- use A and D keys to move the frog left and right.",
        "- press SPACE to shoot the tongue.",
        "- Press S to shoot bullets (you only have a limited amount!).",
        "- eat mosquitoes with tongue or kill them with the bullets to progress waves.",
        "- blue mosquitoes slow you down.",
        "- yelow mosquitoes speed you up.",
        "- press I to toggle these instructions.",
        "- enjoy!"
    ]

    card_w = 680
    card_h = 320
    card_x = (WIDTH - card_w) // 2 
    card_y = (HEIGHT - card_h) // 2
    
    bg = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
    bg.fill((37, 40, 46, 150))
    surf.blit(bg, (card_x, card_y))

    padding = 20
    for i, line in enumerate(lines):
        text_surf = game_font.render(line, True, (255, 255, 255))
        surf.blit(text_surf, (card_x + padding, card_y + padding + i * 30))


mosquito_frames = {}
for direction in ["up", "down", "left", "right"]:
    mosquito_frames[direction] = load_direction_frames("assets/mosquito", direction)

visual_prog = 0
running = True
while running:

    t = clock.tick(FPS) / 1000

    temp_surf = pygame.Surface((WIDTH, HEIGHT))
    temp_surf.fill((bg_color))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                if bullets_rem > 0:
                    bullets_rem -= 1
                    bullets.append(Bullets())
            
            if event.key == pygame.K_i:
                instructions = not instructions
                    
            if event.key == pygame.K_SPACE:
                if not tongue_shooting and not tongue_retracting:
                    tongue_shooting = True
                    tongue_sound.play()

    keys = pygame.key.get_pressed()
    move = 0
    if keys[pygame.K_a]:
        move -= 1
    if keys[pygame.K_d]:
        move += 1

    velocity += move * accel * t

    # friciton when no input
    if move == 0:
        velocity *= (1 -(1 - friction) * t)

    if velocity > max_speed:  
        velocity = max_speed
    if velocity < -max_speed:
        velocity = -max_speed
        
    frog_rect.centerx += velocity * t

    if frog_rect.left < 0:
        frog_rect.left = 0
        velocity = 0
    if frog_rect.right > WIDTH:
        frog_rect.right = WIDTH
        velocity = 0

    if tongue_shooting:
        tongue_l += tongue_speed * t
        if tongue_l >= tongue_max:
            tongue_l = tongue_max
            tongue_shooting = False
            tongue_retracting = True
    elif tongue_retracting:
        tongue_l -= tongue_speed * t
        if tongue_l <= 0:
            tongue_l = 0
            tongue_retracting = False

    frame_time += t
    if frame_time > anim_speed:
        frame_time = 0
        frame_ind = (frame_ind + 1) % frog_no

    frog_scaled = img_aspect(frog_frames[frame_ind], frog_w * 1.5, frog_h * 1.5)
    if speedup_active:
        frenzy_frog = frenzy(frog_scaled)
        frog_scaled_rect = frenzy_frog.get_rect(center = frog_rect.center)
        temp_surf.blit(frenzy_frog, frog_scaled_rect)
    else:
        # made the center of the scaled img's rect to the same the the frog_rect, so no offsetting between the tongue happens
        frog_scaled_rect = frog_scaled.get_rect(center = frog_rect.center)
        temp_surf.blit(frog_scaled, frog_scaled_rect)

    # drawing mosquitoes
    for mosquito in mosquitoes:
        mosquito.update(t)
        mosquito.draw(temp_surf)

    # draw bullets
    for bullet in bullets:
        bullet.update(t)
        bullet.draw(temp_surf)
    
    for bullet in bullets[:]:
        for mosquito in mosquitoes[:]:
            if bullet.rect.colliderect(mosquito.rect):
                mosquito.stop_sound()
                mosquitoes.remove(mosquito)
                mosquitoes_ded += 1
                bullets.remove(bullet)

                if mosquitoes_ded >= mosquitoes_req:
                    wave += 1
                    mosquitoes_ded = 0

                    max_speed += 20
                    tongue_max += 15
                    bullets_rem = 5 + (wave * 2)

                    mosquitoes.clear()
                    for _ in range(random.randint(5, 20)):
                        mosquitoes.append(Mosquito()) 

                    mosquitoes_req = len(mosquitoes)

    if instructions:
        show_instructions(temp_surf)    

    if slowdown_active:
        slowdown_t -= t
        if slowdown_t <= 0:
            slowdown_active = False
            max_speed = orig_speed
            tongue_speed = orig_tongue
    if speedup_active:
        speedup_t -= t
        if speedup_t <= 0:
            speedup_active = False
            max_speed = orig_speed
            tongue_speed = orig_tongue

    # drawing tongue, might make a seperate func
    if tongue_l > 0:
        tongue_w = 45
        tongue_x = frog_scaled_rect.centerx - (tongue_w // 2)
        tongue_y = (frog_scaled_rect.top + 18) + int(frog_h * 1.5) // 4 - tongue_l
        tongue_rect = pygame.Rect(tongue_x, tongue_y, tongue_w, tongue_l)

        for mosquito in mosquitoes[:]:
                if tongue_rect.colliderect(mosquito.rect):
                        if mosquito.type == "blue":
                            shake_dur = 0.3
                            shake_mag = 15
                            pending_shake = True
                            speedup_active = False
                            speedup_t = 0
                            slowdown_t = 15
                            slowdown_active = True
                            nausea_t = 1.5
                            max_speed = orig_speed // 1.5
                            tongue_speed = orig_tongue // 1.5
                        elif mosquito.type == "yellow":
                            slowdown_active = False
                            slowdown_t = 0
                            speedup_t = 15
                            speedup_active = True
                            max_speed = orig_speed * 1.5
                            tongue_speed = orig_tongue * 1.5
                            shake_dur = 0.3
                            shake_mag = 15
                            crazy.play()
                            boom.play()

                        mosquitoes_ded += 1
                        mosquito.stop_sound()
                        mosquitoes.remove(mosquito)


                        if mosquitoes_ded >= mosquitoes_req:
                            wave += 1
                            mosquitoes_ded = 0
                            max_speed += 20
                            tongue_max += 15
                            bullets_rem = 5 + (wave * 2)

                            mosquitoes.clear()
                            for _ in range(random.randint(5, 20)):
                                mosquitoes.append(Mosquito())
                            
                            mosquitoes_req = len(mosquitoes)

        mid_len = max(0, tongue_l - tongue_tip.get_height())
        mid_h = tongue_mid.get_height()
        covered = 0

        scaled_mid = pygame.transform.scale(tongue_mid, (tongue_w, mid_h))

        while covered < mid_len:
            part_h = min(mid_h, mid_len - covered)
            part = scaled_mid.subsurface((0, 0, tongue_w, part_h))
            temp_surf.blit(part, (tongue_x, tongue_y + covered))
            covered += part_h
        
        tip_img = pygame.transform.scale(tongue_tip, (tongue_w, tongue_tip.get_height()))
        tip_y = tongue_y - tip_img.get_height()
        temp_surf.blit(tip_img, (tongue_x, tip_y))
    
    # idk why this is working with two if statements of the same thing, but i am going to eave it as is.

    if nausea_t > 0:
        shake_x = 0
        shake_y = 0
        nausea_t -= t
        if nausea_t <= 0 and pending_shake:
            boom.play()
            pending_shake = False
    elif shake_dur > 0:
        shake_dur -= t
        shake_x = random.randint(-shake_mag, shake_mag)
        shake_y = random.randint(-shake_mag, shake_mag)
    else:
        shake_x = 0
        shake_y = 0

    # text
    box_x, box_y = 14, 14
    box_w, box_h = 320, 140
    bar_x = box_x + 12
    bar_y = box_y + 72
    bar_w = 260
    bar_h = 22

    # progress bar
    if mosquitoes_req > 0:
        progress = mosquitoes_ded / mosquitoes_req
    else:
        progress = 0

    visual_prog += (progress - visual_prog) * 0.15

    if slowdown_active:
        fill = (55, 160, 255)
    elif speedup_active and not slowdown_active:
        fill = (255, 230, 50)
    else:
        fill = (220, 40, 40)

    text_bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    pygame.draw.rect(text_bg, (20, 30, 30, 150), (0, 0, box_w, box_h), border_radius=18)
    temp_surf.blit(text_bg, (box_x, box_y))

    bullet_text = game_font.render(f"only {bullets_rem} bullets left!", True, (255, 255, 255))
    temp_surf.blit(bullet_text, (box_x + 12, box_y + 8))

    wave_text = game_font.render(f"you're on wave {wave}, noob", True, (255, 255, 255))
    temp_surf.blit(wave_text, (box_x + 12, box_y + 36))

    progress_bar(temp_surf, bar_x, bar_y, bar_w, bar_h, visual_prog, bg_clr=(37, 40, 46), fill_clr=fill, border_clr=(10, 10, 10), radius=8, outline=3)  

    instructions_text = game_font.render(f"press I to see instructions", True, (255, 255, 255))
    temp_surf.blit(instructions_text, (box_x + 12, bar_y + bar_h + 12))


    effect_y = 120

    if nausea_t > 0:
        shake_x = shake_y = 0
        time_now = pygame.time.get_ticks() / 1000
        wavy_surf = sinwaves(temp_surf, time_now, amp=8, wavelen=80, speed=4)
        screen.blit(wavy_surf, (0, 0))

        nausea_t -= t
        if nausea_t <= 0 and pending_shake:
            boom.play()
            pending_shake = False

    elif slowdown_active:
        shift = 5
        wave_surface = pygame.transform.smoothscale(temp_surf, (WIDTH + shift, HEIGHT + shift))
        screen.blit(wave_surface, (-shift // 2 + shake_x, -shift // 2 + shake_y))

    elif shake_dur > 0:
        shake_dur -= t
        shake_x = random.randint(-shake_mag, shake_mag)
        shake_y = random.randint(-shake_mag, shake_mag)
        screen.blit(temp_surf, (shake_x, shake_y))

    else:
        screen.blit(temp_surf, (0, 0))

    pygame.display.flip()

pygame.quit()

## Attribution for sfx
# Sound Effect: vocal male crazy 2 deep
# Download from https://tunetank.com