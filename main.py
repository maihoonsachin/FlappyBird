import random
import sqlite3

import pygame


class Bird(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.flap_speed = 4
        self.velocity = -self.flap_speed
        self.gravity = 0.3
        self.max_speed = 7
        self.image = pygame.image.load("graphics/bird.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (bird_size, bird_size))
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3))
        self.mask = pygame.mask.from_surface(self.image)

    def apply_gravity(self):
        self.velocity += self.gravity
        if self.velocity >= self.max_speed:
            self.velocity = self.max_speed
        self.rect.y += round(self.velocity)

    def bird_control(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            flap_channel.play(flap_sound)
            self.velocity = -self.flap_speed

    def collison_ground_or_sky(self):
        if self.rect.bottom >= ground_top + 6 or self.rect.top <= -6:
            return True
        else:
            return False

    def fall(self):
        global collided
        if collided:
            self.rect.x += 3
        if self.rect.top >= SCREEN_HEIGHT:
            global game_active
            bird.empty()
            pillars.empty()
            game_active = False

    def update(self):
        global collided
        self.apply_gravity()
        if not collided:
            self.bird_control()
        self.fall()


class Pillar(pygame.sprite.Sprite):
    def __init__(self, pillar_height, position):
        super().__init__()
        self.image = pygame.image.load("graphics/pillar1.png").convert_alpha()
        self.image = pygame.transform.scale(
            self.image,
            (pillar_width, pillar_height),
        )
        if position == "lower":
            self.rect = self.image.get_rect(bottomleft=(SCREEN_WIDTH, ground_top))
        else:
            self.image = pygame.transform.flip(self.image, 0, 1)
            self.rect = self.image.get_rect(topleft=(SCREEN_WIDTH, 0))

        self.mask = pygame.mask.from_surface(self.image)

        self.crossed_bird = False

    def pillar_move(self):
        self.rect.x -= round(pillar_speed)

    def delete_pillar(self):
        if self.rect.right < -50:
            self.kill()

    def score_update(self):
        global SCORE
        cross_point = round(SCREEN_WIDTH / 2 - bird_size / 2)
        if self.rect.right <= cross_point and not self.crossed_bird:
            point_sound.play()
            SCORE += 1
            self.crossed_bird = True

    def update(self):
        self.pillar_move()
        self.delete_pillar()
        if not collided:
            self.score_update()


class Button:
    def __init__(self, label, fg, bg, font):
        self.label = font.render(label, True, fg)
        self.label_rect = self.label.get_rect(
            center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        )
        self.bg_rect = self.label_rect.scale_by(1.3, 1.3)
        self.bg = bg

    def update(self):
        pygame.draw.rect(screen, self.bg, self.bg_rect, border_radius=7)
        screen.blit(self.label, self.label_rect)


class Input_Box:
    def __init__(self):
        self.input = ""

        self.warning = pygame.font.Font("fonts/Play-Regular.ttf", 20).render(
            "Please enter username", True, "Red"
        )
        self.warning_rect = self.warning.get_rect(
            center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40)
        )
        self.show_warning = False

    def update_text(self):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.input != "":
                    scores_db_cursor.execute(
                        "SELECT * FROM scores WHERE name = ?", (self.input,)
                    )
                    check_name = scores_db_cursor.fetchall()
                    if len(check_name) > 0:
                        # Update score only if greater than previous score
                        check_score = check_name[0][1]
                        if check_score < SCORE // 2:
                            scores_db.execute(
                                "UPDATE scores SET score=? WHERE name=?",
                                (SCORE // 2, self.input),
                            )
                        else:
                            scores_db.execute(
                                "UPDATE scores SET score=? WHERE name=?",
                                (check_score, self.input),
                            )
                    else:
                        scores_db.execute(
                            "INSERT INTO scores (name, score) VALUES(?, ?)",
                            (self.input, SCORE // 2),
                        )

                    scores_db.commit()
                    reset()
                else:
                    self.show_warning = True

            elif event.key == pygame.K_BACKSPACE:
                self.input = self.input[:-1]
            elif event.key == pygame.K_SPACE:
                return
            else:
                if len(self.input) < 20:
                    self.input += event.unicode

    def update(self):
        if self.input == "":
            self.text = font.render("Enter username", True, "Gray")
        else:
            self.text = font.render(self.input, True, "White")

        self.rect = self.text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
        text_rect_width = max(400 / 1.1, self.rect.width)
        text_rect_height = self.rect.height
        text_rect_x = (SCREEN_WIDTH - text_rect_width) / 2
        text_rect_y = (SCREEN_HEIGHT - text_rect_height) / 2 - 100
        self.text_rect = pygame.Rect(
            text_rect_x, text_rect_y, text_rect_width, text_rect_height
        )
        self.bg_rect = self.text_rect.scale_by(1.1, 1.3)

        pygame.draw.rect(screen, "Black", self.bg_rect, border_radius=7)
        screen.blit(self.text, self.text_rect)

        if self.show_warning:
            screen.blit(self.warning, self.warning_rect)


class LeaderBoard:
    def __init__(self):
        self.warning = font.render("Nothing to show", True, "Red")
        self.warning_rect = self.warning.get_rect(
            center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        )

        self.heading = font.render("LeaderBoard", True, "Black")
        self.heading_rect = self.heading.get_rect(center=(SCREEN_WIDTH / 2, 50))

    def update(self):
        screen.blit(self.heading, self.heading_rect)
        scores_db_cursor.execute("SELECT * FROM scores ORDER BY score DESC LIMIT 10")
        self.scores_data = scores_db_cursor.fetchall()
        self.scores_data.insert(0, ("Username", "Score"))

        if len(self.scores_data) > 0:
            for i in range(len(self.scores_data)):
                self.rank = font3.render(f"{i}", True, "White")
                self.username = font3.render(f"{self.scores_data[i][0]}", True, "White")
                self.score = font3.render(f"{self.scores_data[i][1]}", True, "White")

                if i == 0:
                    self.rank = font4.render("Rank", True, "Yellow")
                    self.username = font4.render(
                        f"{self.scores_data[i][0]}", True, "Yellow"
                    )
                    self.score = font4.render(
                        f"{self.scores_data[i][1]}", True, "Yellow"
                    )
                    self.rank_rect = self.rank.get_rect(
                        midtop=(75, leaderboard_icon_rect.bottom + 40)
                    )
                    self.username_rect = self.username.get_rect(
                        midtop=(SCREEN_WIDTH / 2, leaderboard_icon_rect.bottom + 40)
                    )
                    self.score_rect = self.score.get_rect(
                        midtop=(SCREEN_WIDTH - 75, leaderboard_icon_rect.bottom + 40)
                    )
                else:
                    self.rank_rect = self.rank.get_rect(
                        midtop=(75, self.rank_rect.bottom + 20)
                    )
                    self.username_rect = self.username.get_rect(
                        midtop=(SCREEN_WIDTH / 2, self.username_rect.bottom + 20)
                    )
                    self.score_rect = self.score.get_rect(
                        midtop=(SCREEN_WIDTH - 75, self.score_rect.bottom + 20)
                    )

                self.bg_rect = self.username_rect.scale_by(1.3, 1.3)
                self.bg_rect.width = SCREEN_WIDTH - 50
                self.bg_rect.x = 25
                pygame.draw.rect(screen, "Black", self.bg_rect, border_radius=7)
                screen.blit(self.rank, self.rank_rect)
                screen.blit(self.username, self.username_rect)
                screen.blit(self.score, self.score_rect)
        else:
            screen.blit(self.warning, self.warning_rect)


def collison():
    if pygame.sprite.spritecollide(bird.sprite, pillars, False):
        return True
    return False


def mask_collision(sprite1, sprite2):
    offset = (
        sprite2.rect.left - sprite1.rect.left,
        sprite2.rect.top - sprite1.rect.top,
    )
    return sprite1.mask.overlap(sprite2.mask, offset) is not None


def display_score(active):
    score_surf = font.render(f"Score: {SCORE//2}", True, "Black")
    if active:
        score_rect = score_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 50))
    else:
        score_rect = score_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
    screen.blit(score_surf, score_rect)


def start_screen():
    play_button = Button("Play", fg="White", bg="Black", font=font)

    label2 = font2.render("Press Enter to start", True, "Black")
    label2_rect = label2.get_rect(
        center=(SCREEN_WIDTH / 2, play_button.bg_rect.bottom + 30)
    )

    icon_size = 1.5 * bird_size
    icon = pygame.image.load("graphics/bird.png").convert_alpha()
    icon = pygame.transform.scale(icon, (icon_size, icon_size))
    icon_rect = icon.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3))

    screen.blit(icon, icon_rect)
    play_button.update()
    screen.blit(label2, label2_rect)

    mouse_pressed = pygame.mouse.get_pressed()
    if mouse_pressed[0]:
        if play_button.bg_rect.collidepoint(pygame.mouse.get_pos()):
            global game_active
            game_active = True


def end_screen():
    if show_leaderboard:
        leaderboard.update()
    else:
        input_box.update()
        display_score(active=False)
    screen.blit(leaderboard_icon, leaderboard_icon_rect)


def reset():
    global SCORE, HIGH_SCORE, pillar_speed, collided, game_active, high_score_surface
    bird.add(Bird())
    pillars.empty()
    SCORE = 0
    pillar_speed = 0.003 * SCREEN_WIDTH

    # Update High Score
    scores_db_cursor.execute("SELECT MAX(score) FROM scores")
    HIGH_SCORE = scores_db_cursor.fetchall()[0][0] or 0
    high_score_surface = font2.render(f"HS: {HIGH_SCORE}", True, "Black")

    collided = False
    game_active = True


pygame.init()
clock = pygame.time.Clock()
running = True

scores_db = sqlite3.connect("scores.db")
scores_db_cursor = scores_db.cursor()

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

SCORE = 0
scores_db_cursor.execute("SELECT MAX(score) FROM scores")
HIGH_SCORE = scores_db_cursor.fetchall()[0][0] or 0

sky_height = 0.8 * SCREEN_HEIGHT

min_pillar_heigth = round(0.1 * sky_height)
max_pillar_height = round(0.55 * sky_height)

min_pillar_gap = round(0.45 * sky_height)
max_pillar_gap = round(0.5 * sky_height)

bird_size = round(0.25 * min_pillar_gap)

pillar_width = round(0.06 * SCREEN_WIDTH)

pillar_speed = 0.003 * SCREEN_WIDTH

# Game sounds
flap_channel = pygame.mixer.Channel(0)
flap_sound = pygame.mixer.Sound("audio/flap.mp3")
flap_sound.set_volume(0.5)
collison_sound = pygame.mixer.Sound("audio/hit.mp3")
point_sound = pygame.mixer.Sound("audio/point.mp3")

game_active = False
collided = False

# Groups
bird = pygame.sprite.GroupSingle()
bird.add(Bird())

pillars = pygame.sprite.Group()

# Background
sky_surface = pygame.image.load("graphics/Sky.png").convert()
sky_surface = pygame.transform.scale(sky_surface, (SCREEN_WIDTH, sky_height))
sky_rect = sky_surface.get_rect(top=0)

ground_top = sky_rect.bottom
ground_surface = pygame.image.load("graphics/ground.png").convert()
ground_surface = pygame.transform.scale(
    ground_surface, (SCREEN_WIDTH, SCREEN_HEIGHT - sky_height)
)
ground_rect = ground_surface.get_rect(top=ground_top)

# Text Font
font = pygame.font.Font("fonts/Play-Regular.ttf", 50)
font2 = pygame.font.Font("fonts/Play-Regular.ttf", 35)
font3 = pygame.font.Font("fonts/Play-Regular.ttf", 30)
font4 = pygame.font.Font("fonts/Play-Bold.ttf", 30)

# High Score Surface
high_score_surface = font2.render(f"HS: {HIGH_SCORE}", True, "Black")
high_score_rect = high_score_surface.get_rect(
    bottomright=(SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20)
)

# LeaderBoard
leaderboard_icon = pygame.image.load("graphics/leaderboard.png")
leaderboard_icon = pygame.transform.scale(leaderboard_icon, (50, 50))
leaderboard_icon_rect = leaderboard_icon.get_rect(topright=(SCREEN_WIDTH - 20, 20))
leaderboard = LeaderBoard()
show_leaderboard = False


# Name input
input_box = Input_Box()

# Pillar timer
pillar_timer = pygame.USEREVENT + 1
pygame.time.set_timer(pillar_timer, 1500)

# Game Loop

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_active:
            input_box = Input_Box()
            if event.type == pillar_timer:
                lower_pillar_height = random.uniform(
                    min_pillar_heigth, max_pillar_height
                )
                pillar_gap = random.uniform(min_pillar_gap, max_pillar_gap)
                pillars.add(Pillar(lower_pillar_height, "lower"))
                pillars.add(
                    Pillar(SCREEN_HEIGHT - lower_pillar_height - pillar_gap, "upper")
                )
        else:
            if collided:
                if not show_leaderboard:
                    input_box.update_text()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if leaderboard_icon_rect.collidepoint(pygame.mouse.get_pos()):
                        show_leaderboard = not show_leaderboard
            else:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        reset()

    score_surf = font.render(f"Score: {SCORE//2}", True, "Black")
    active_score_rect = score_surf.get_rect(
        center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 50)
    )
    inactive_score_rect = score_surf.get_rect(
        center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    )

    screen.blit(sky_surface, (0, 0))
    screen.blit(ground_surface, ground_rect)

    if game_active:
        screen.blit(high_score_surface, high_score_rect)

        pillars.draw(screen)
        pillars.update()

        bird.draw(screen)
        bird.update()

        if not collided:
            # if collison() or bird.sprite.collison_ground_or_sky():
            #     collison_sound.play()
            #     bird.sprite.velocity = -7
            #     collided = True
            #     pillar_speed = 0

            if (
                pygame.sprite.spritecollide(
                    bird.sprite, pillars, False, collided=mask_collision
                )
                or bird.sprite.collison_ground_or_sky()
            ):
                collison_sound.play()
                bird.sprite.velocity = -7
                collided = True
                pillar_speed = 0

        display_score(active=True)

    else:
        if collided:
            end_screen()
        else:
            start_screen()

    pygame.display.update()
    clock.tick(60)

pygame.quit()
