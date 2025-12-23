import pygame
import json
import os
import random

# ================== KONFIGURACJA ==================
WIDTH, HEIGHT = 950, 700
BG_COLOR = (30, 30, 30)
TEXT_COLOR = (240, 240, 240)
BTN_COLOR = (70, 70, 200)
BTN_HOVER = (100, 100, 240)
INPUT_BG = (50, 50, 50)
FONT_SIZE = 24
DATA_FILE = "quiz_data.json"


# ================== DANE ==================
def load_data():
    if not os.path.exists(DATA_FILE):
        data = {
            "Podstawy": [{"question": "Ile to 2+2?", "options": ["4", "5", "6", "7"], "correct": 0}],
            "Technologia": [
                {"question": "Jaki język programowania obsługuje Pygame?", "options": ["C++", "Python", "Java", "Ruby"],
                 "correct": 1}],
            "Nauka": [
                {"question": "Która planeta jest najbliżej Słońca?", "options": ["Ziemia", "Mars", "Merkury", "Wenus"],
                 "correct": 2}]
        }
        save_data(data)
        return data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ================== FUNKCJE POMOCNICZE ==================
def wrap_text(text, font, max_width):
    words = text.split(' ')
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        w, _ = font.size(test_line)
        if w < max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))
    return lines


# ================== UI ELEMENTY ==================
class Button:
    def __init__(self, x, y, width, text, font, padding=12, data=None):
        self.x, self.y, self.width, self.font = x, y, width, font
        self.padding = padding
        self.text_lines = wrap_text(text, font, width - (padding * 2))
        self.line_height = font.get_linesize()
        self.height = (len(self.text_lines) * self.line_height) + (padding * 2)
        self.rect = pygame.Rect(x, y, width, self.height)
        self.data = data

    def draw(self, screen, mouse_pos):
        color = BTN_HOVER if self.rect.collidepoint(mouse_pos) else BTN_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        for i, line in enumerate(self.text_lines):
            txt_surf = self.font.render(line, True, TEXT_COLOR)
            screen.blit(txt_surf, (self.x + self.padding, self.y + self.padding + i * self.line_height))

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)


class InputBox:
    def __init__(self, rect, placeholder=""):
        self.rect = pygame.Rect(rect)
        self.text = ""
        self.active = False
        self.placeholder = placeholder

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if self.active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE: self.text = self.text[:-1]
            elif event.type == pygame.TEXTINPUT:
                self.text += event.text

    def draw(self, screen, font):
        color = (100, 100, 255) if self.active else (80, 80, 80)
        pygame.draw.rect(screen, color, self.rect, border_radius=5, width=2)
        txt = font.render(self.text if self.text else self.placeholder, True,
                          TEXT_COLOR if self.text else (130, 130, 130))
        screen.blit(txt, (self.rect.x + 10, self.rect.y + 10))


# ================== WIDOKI ==================

def select_module(screen, font, data, title):
    back_btn = Button(375, 580, 200, "Powrót", font)
    while True:
        screen.fill(BG_COLOR)
        mouse = pygame.mouse.get_pos()
        title_txt = font.render(f"Wybierz moduł: {title}", True, (255, 200, 100))
        screen.blit(title_txt, (WIDTH // 2 - title_txt.get_width() // 2, 40))

        module_btns = []
        for i, m_name in enumerate(data.keys()):
            module_btns.append(
                Button(275, 120 + i * 100, 400, f"{m_name} ({len(data[m_name])} pyt.)", font, data=m_name))

        for b in module_btns: b.draw(screen, mouse)
        back_btn.draw(screen, mouse)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return None
            if back_btn.clicked(event): return None
            for b in module_btns:
                if b.clicked(event): return b.data


def quiz_loop(screen, font, original_questions):
    questions = list(original_questions)
    random.shuffle(questions)

    idx, score = 0, 0
    while idx < len(questions):
        q = questions[idx]
        correct_content = q["options"][q["correct"]]
        shuffled_options = list(q["options"])
        random.shuffle(shuffled_options)

        answered = False
        while not answered:
            screen.fill(BG_COLOR)
            q_lines = wrap_text(q["question"], font, 800)
            curr_y = 100
            for line in q_lines:
                screen.blit(font.render(line, True, TEXT_COLOR), (75, curr_y))
                curr_y += 30

            stats = font.render(f"Pytanie: {idx + 1}/{len(questions)}   Wynik: {score}", True, (100, 255, 100))
            screen.blit(stats, (WIDTH - 300, 20))

            ans_btns = []
            ans_y = curr_y + 40
            for opt in shuffled_options:
                btn = Button(275, ans_y, 400, opt, font, data=opt)
                ans_btns.append(btn)
                ans_y += btn.height + 15

            mouse = pygame.mouse.get_pos()
            for b in ans_btns: b.draw(screen, mouse)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT: return
                for b in ans_btns:
                    if b.clicked(event):
                        if b.data == correct_content: score += 1
                        idx += 1
                        answered = True

    screen.fill(BG_COLOR)
    final_txt = font.render(f"Koniec! Wynik końcowy: {score}/{len(questions)}", True, (255, 255, 255))
    screen.blit(final_txt, (WIDTH // 2 - final_txt.get_width() // 2, HEIGHT // 2))
    pygame.display.flip()
    pygame.time.wait(2000)


def add_question(screen, font, data, module):
    inputs = [
        InputBox((225, 80, 500, 45), "Pytanie"),
        InputBox((225, 140, 500, 45), "Opcja A"),
        InputBox((225, 200, 500, 45), "Opcja B"),
        InputBox((225, 260, 500, 45), "Opcja C"),
        InputBox((225, 320, 500, 45), "Opcja D"),
        InputBox((225, 380, 200, 45), "Poprawna (A, B, C lub D)")
    ]
    save_btn = Button(225, 460, 240, "Zapisz w " + module, font)
    back_btn = Button(485, 460, 240, "Powrót", font)
    feedback_msg, feedback_color = "", (255, 255, 255)

    while True:
        screen.fill(BG_COLOR)
        mouse = pygame.mouse.get_pos()
        for i in inputs: i.draw(screen, font)
        save_btn.draw(screen, mouse)
        back_btn.draw(screen, mouse)

        if feedback_msg:
            msg_surf = font.render(feedback_msg, True, feedback_color)
            screen.blit(msg_surf, (WIDTH // 2 - msg_surf.get_width() // 2, 550))

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return
            if back_btn.clicked(event): return
            for i in inputs: i.handle_event(event)
            if save_btn.clicked(event):
                ans = inputs[5].text.upper()
                if not all(i.text for i in inputs[:5]):
                    feedback_msg, feedback_color = "Błąd: Wypełnij wszystkie pola!", (255, 100, 100)
                elif ans not in "ABCD":
                    feedback_msg, feedback_color = "Błąd: Podaj poprawną literę (A-D)!", (255, 100, 100)
                else:
                    data[module].append({
                        "question": inputs[0].text,
                        "options": [inputs[i].text for i in range(1, 5)],
                        "correct": "ABCD".index(ans)
                    })
                    save_data(data)
                    feedback_msg, feedback_color = "Dodano pomyślnie!", (100, 255, 100)
                    for i in inputs: i.text = ""


def delete_manager(screen, font, data, module):
    while True:
        screen.fill(BG_COLOR)
        mouse = pygame.mouse.get_pos()
        if not data[module]:
            empty_txt = font.render(f"Moduł '{module}' jest pusty!", True, (255, 100, 100))
            screen.blit(empty_txt, (WIDTH // 2 - empty_txt.get_width() // 2, HEIGHT // 2))
            pygame.display.flip()
            pygame.time.wait(1500)
            return

        title_txt = font.render(f"Usuwanie z: {module}", True, (255, 200, 100))
        screen.blit(title_txt, (50, 20))

        del_btns = []
        for i, q in enumerate(data[module]):
            short_q = q["question"][:75] + "..." if len(q["question"]) > 75 else q["question"]
            del_btns.append(Button(50, 70 + i * 50, 850, short_q, font, padding=8, data=i))

        back_btn = Button(375, 620, 200, "Powrót", font)
        for b in del_btns: b.draw(screen, mouse)
        back_btn.draw(screen, mouse)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return
            if back_btn.clicked(event): return
            for b in del_btns:
                if b.clicked(event):
                    data[module].pop(b.data)
                    save_data(data)
                    break


# ================== MAIN ==================
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Mega Quiz v2.0")
    font = pygame.font.SysFont("Arial", FONT_SIZE)
    data = load_data()

    main_btns = [
        Button(375, 200, 200, "Start Quiz", font),
        Button(375, 280, 200, "Dodaj Pytanie", font),
        Button(375, 360, 200, "Usuń Pytania", font),
        Button(375, 440, 200, "Wyjście", font)
    ]

    while True:
        screen.fill(BG_COLOR)
        mouse = pygame.mouse.get_pos()
        for b in main_btns: b.draw(screen, mouse)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); return
            if main_btns[0].clicked(event):
                m = select_module(screen, font, data, "START")
                if m: quiz_loop(screen, font, data[m])
            if main_btns[1].clicked(event):
                m = select_module(screen, font, data, "DODAWANIE")
                if m: add_question(screen, font, data, m)
            if main_btns[2].clicked(event):
                m = select_module(screen, font, data, "USUWANIE")
                if m: delete_manager(screen, font, data, m)
            if main_btns[3].clicked(event): pygame.quit(); return


if __name__ == "__main__":
    main()