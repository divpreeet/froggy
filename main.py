import pygame
import random

pygame.init()

HEIGHT = 720
WIDTH = 1280
FPS = 120

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("froggy")
clock = pygame.time.Clock()


# movement vars
velocity = 0.0
accel = 750
max_speed = 600
friction = 0.85

# frog sprite (as a rect for now)
frog_w = 60
frog_h = 40
frog_x = WIDTH // 2 - frog_w // 2
frog_y = HEIGHT - frog_h - 30
frog_rect = pygame.Rect(frog_x, frog_y, frog_w, frog_h)

# tongue vars
tongue_l = 0
tongue_speed = 4000
tongue_max = 650
tongue_shooting = False
tongue_retracting = False

# loading assets
frog_img = "assets/frog/frog seperate images/"

tongue_mid = pygame.image.load("assets/tongue/tongue-base.png").convert_alpha()

tongue_tip = pygame.image.load("assets/tongue/tongue-tip.png")

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
        self.width = 20
        self.height = 20
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.velox = random.randint(-100, 100)
        self.veloy = random.randint(-100, 100)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
    
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

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 0, 0), self.rect)

mosquitoes = []

for _ in range(random.randint(1, 15)):
    mosquitoes.append(Mosquito())


def img_aspect(img, max_w, max_h):
    iw, ih = img.get_size()
    scale = min(max_w / iw, max_h / ih)
    new_size = (int(iw * scale), int(ih * scale))
    return pygame.transform.scale(img, new_size)


mosquito = Mosquito()
running = True
while running:

    t = clock.tick(FPS) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if not tongue_shooting and not tongue_retracting:
                    tongue_shooting = True

    keys = pygame.key.get_pressed()
    move = 0
    if keys[pygame.K_LEFT]:
        move -= 1
    if keys[pygame.K_RIGHT]:
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

    screen.fill((0, 0, 0))
    frog_scaled = img_aspect(frog_frames[frame_ind], frog_w * 1.5, frog_h * 1.5)
    # made the center of the scaled img's rect to the same the the frog_rect, so no offsetting between the tongue happens
    frog_scaled_rect = frog_scaled.get_rect(center = frog_rect.center)
    screen.blit(frog_scaled, frog_scaled_rect)

    # drawing mosquitoes
    for mosquito in mosquitoes:
        mosquito.update(t)
        mosquito.draw(screen)

    # drawing tongue, might make a seperate func
    if tongue_l > 0:
        tongue_w = 45
        tongue_x = frog_scaled_rect.centerx - (tongue_w // 2)
        tongue_y = (frog_scaled_rect.top + 18) + int(frog_h * 1.5) // 4 - tongue_l

        mid_len = max(0, tongue_l - tongue_tip.get_height())
        mid_h = tongue_mid.get_height()
        covered = 0

        scaled_mid = pygame.transform.scale(tongue_mid, (tongue_w, mid_h))

        while covered < mid_len:
            part_h = min(mid_h, mid_len - covered)
            part = scaled_mid.subsurface((0, 0, tongue_w, part_h))
            screen.blit(part, (tongue_x, tongue_y + covered))
            covered += part_h

        tip_img = pygame.transform.scale(tongue_tip, (tongue_w, tongue_tip.get_height()))
        tip_y = tongue_y - tip_img.get_height()
        screen.blit(tip_img, (tongue_x, tip_y))


    pygame.display.flip()

pygame.quit()
