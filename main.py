import json
import random
from pathlib import Path

import pygame


CELL_SIZE = 24
GRID_WIDTH = 30
GRID_HEIGHT = 22
SIDE_PANEL_WIDTH = 190
WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE + SIDE_PANEL_WIDTH
WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE
FPS = 60
MOVE_DELAY_MS = 105

DATA_FILE = Path(__file__).with_name("high_score.json")

BACKGROUND = (18, 22, 28)
BOARD_BG = (25, 31, 40)
GRID_LINE = (35, 42, 53)
SNAKE_HEAD = (65, 214, 122)
SNAKE_BODY = (39, 174, 96)
FOOD = (239, 91, 91)
TEXT = (235, 240, 245)
MUTED_TEXT = (148, 163, 184)
PANEL_BG = (30, 38, 49)
ACCENT = (96, 165, 250)


def load_high_score() -> int:
    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return 0

    score = data.get("high_score", 0)
    return score if isinstance(score, int) and score >= 0 else 0


def save_high_score(score: int) -> None:
    DATA_FILE.write_text(
        json.dumps({"high_score": score}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


class SnakeGame:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Змейка")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("arial", 36, bold=True)
        self.font_medium = pygame.font.SysFont("arial", 24, bold=True)
        self.font_small = pygame.font.SysFont("arial", 18)
        self.high_score = load_high_score()
        self.reset()

    def reset(self) -> None:
        start_x = GRID_WIDTH // 2
        start_y = GRID_HEIGHT // 2
        self.snake = [(start_x, start_y), (start_x - 1, start_y), (start_x - 2, start_y)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.food = self.spawn_food()
        self.score = 0
        self.game_over = False
        self.paused = False
        self.last_move_time = pygame.time.get_ticks()

    def spawn_food(self) -> tuple[int, int]:
        free_cells = [
            (x, y)
            for x in range(GRID_WIDTH)
            for y in range(GRID_HEIGHT)
            if (x, y) not in self.snake
        ]
        return random.choice(free_cells) if free_cells else (-1, -1)

    def run(self) -> None:
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()

    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_SPACE and not self.game_over:
                    self.paused = not self.paused
                if event.key == pygame.K_r and self.game_over:
                    self.reset()

                self.handle_direction_key(event.key)

        return True

    def handle_direction_key(self, key: int) -> None:
        directions = {
            pygame.K_UP: (0, -1),
            pygame.K_w: (0, -1),
            pygame.K_DOWN: (0, 1),
            pygame.K_s: (0, 1),
            pygame.K_LEFT: (-1, 0),
            pygame.K_a: (-1, 0),
            pygame.K_RIGHT: (1, 0),
            pygame.K_d: (1, 0),
        }
        new_direction = directions.get(key)
        if new_direction is None:
            return

        if (new_direction[0] * -1, new_direction[1] * -1) != self.direction:
            self.next_direction = new_direction

    def update(self) -> None:
        if self.game_over or self.paused:
            return

        now = pygame.time.get_ticks()
        if now - self.last_move_time < MOVE_DELAY_MS:
            return

        self.last_move_time = now
        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        hit_wall = not (0 <= new_head[0] < GRID_WIDTH and 0 <= new_head[1] < GRID_HEIGHT)
        snake_body = self.snake if new_head == self.food else self.snake[:-1]
        hit_self = new_head in snake_body
        if hit_wall or hit_self:
            self.finish_game()
            return

        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.score += 10
            if self.score > self.high_score:
                self.high_score = self.score
                save_high_score(self.high_score)
            self.food = self.spawn_food()
        else:
            self.snake.pop()

    def finish_game(self) -> None:
        self.game_over = True
        if self.score > self.high_score:
            self.high_score = self.score
            save_high_score(self.high_score)

    def draw(self) -> None:
        self.screen.fill(BACKGROUND)
        self.draw_board()
        self.draw_side_panel()

        if self.paused:
            self.draw_center_message("Пауза", "Пробел - продолжить")
        elif self.game_over:
            self.draw_center_message("Игра окончена", "R - заново, Esc - выход")

        pygame.display.flip()

    def draw_board(self) -> None:
        board_rect = pygame.Rect(0, 0, GRID_WIDTH * CELL_SIZE, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, BOARD_BG, board_rect)

        for x in range(0, board_rect.width, CELL_SIZE):
            pygame.draw.line(self.screen, GRID_LINE, (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, CELL_SIZE):
            pygame.draw.line(self.screen, GRID_LINE, (0, y), (board_rect.width, y))

        self.draw_cell(self.food, FOOD, radius=8)
        for index, cell in enumerate(self.snake):
            color = SNAKE_HEAD if index == 0 else SNAKE_BODY
            self.draw_cell(cell, color, radius=6)

    def draw_cell(self, cell: tuple[int, int], color: tuple[int, int, int], radius: int) -> None:
        if cell == (-1, -1):
            return

        x, y = cell
        rect = pygame.Rect(
            x * CELL_SIZE + 2,
            y * CELL_SIZE + 2,
            CELL_SIZE - 4,
            CELL_SIZE - 4,
        )
        pygame.draw.rect(self.screen, color, rect, border_radius=radius)

    def draw_side_panel(self) -> None:
        panel_x = GRID_WIDTH * CELL_SIZE
        panel_rect = pygame.Rect(panel_x, 0, SIDE_PANEL_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, PANEL_BG, panel_rect)

        self.draw_text("Змейка", self.font_large, TEXT, panel_x + 24, 28)
        self.draw_text("Счет", self.font_small, MUTED_TEXT, panel_x + 24, 96)
        self.draw_text(str(self.score), self.font_medium, TEXT, panel_x + 24, 120)
        self.draw_text("Рекорд", self.font_small, MUTED_TEXT, panel_x + 24, 172)
        self.draw_text(str(self.high_score), self.font_medium, ACCENT, panel_x + 24, 196)

        controls_y = 284
        controls = [
            "Стрелки / WASD",
            "Пробел - пауза",
            "R - рестарт",
            "Esc - выход",
        ]
        self.draw_text("Управление", self.font_small, MUTED_TEXT, panel_x + 24, controls_y)
        for index, line in enumerate(controls):
            self.draw_text(line, self.font_small, TEXT, panel_x + 24, controls_y + 34 + index * 28)

    def draw_center_message(self, title: str, subtitle: str) -> None:
        board_width = GRID_WIDTH * CELL_SIZE
        overlay = pygame.Surface((board_width, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        title_surface = self.font_large.render(title, True, TEXT)
        subtitle_surface = self.font_small.render(subtitle, True, MUTED_TEXT)
        title_rect = title_surface.get_rect(center=(board_width // 2, WINDOW_HEIGHT // 2 - 22))
        subtitle_rect = subtitle_surface.get_rect(center=(board_width // 2, WINDOW_HEIGHT // 2 + 24))
        self.screen.blit(title_surface, title_rect)
        self.screen.blit(subtitle_surface, subtitle_rect)

    def draw_text(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        x: int,
        y: int,
    ) -> None:
        self.screen.blit(font.render(text, True, color), (x, y))


if __name__ == "__main__":
    SnakeGame().run()
