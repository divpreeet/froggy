import pygame

pygame.init()

HEIGHT = 720
WIDTH = 1280

# movement vars
velocity = 0.0
accel = 0.7
max_speed = 12
friction = 0.85

# frog sprite (as a rect for now)
frog_w = 60
frog_h = 40
frog_x = WIDTH // 2 - frog_w // 2
frog_y = HEIGHT - frog_h - 30
frog_rect = pygame.Rect(frog_x, frog_y, frog_w, frog_h)

# tongue vars
tongue_l = 0
tongue_speed = 40
tongue_max = 720
tongue_shooting = False
tongue_retracting = False


screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("froggy")

clock = pygame.time.Clock()

running = True
while running:
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

    velocity += move * accel  

    # friciton when no input
    if move == 0:
        velocity *= friction

    if velocity > max_speed:  
        velocity = max_speed
    if velocity < -max_speed:
        velocity = -max_speed
        
    frog_rect.x += int(velocity)

    if frog_rect.left < 0:
        frog_rect.left = 0
        velocity = 0
    if frog_rect.right > WIDTH:
        frog_rect.right = WIDTH
        velocity = 0

    if tongue_shooting:
        tongue_l += tongue_speed
        if tongue_l >= tongue_max:
            tongue_l = tongue_max
            tongue_shooting = False
            tongue_retracting = True
    elif tongue_retracting:
        tongue_l -= tongue_speed
        if tongue_l <= 0:
            tongue_l = 0
            tongue_retracting = False


    screen.fill((0, 0, 0))
    pygame.draw.rect(screen, (0, 255, 0), frog_rect)

    # drawing tongue, might make a seperate func
    if tongue_l > 0:
        tongue_start = (frog_rect.centerx, frog_rect.top + frog_h // 4)
        tongue_end = (frog_rect.centerx, frog_rect.top + frog_h // 4 - tongue_l)
        pygame.draw.line(screen, (255, 0, 0), tongue_start, tongue_end, 8)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()