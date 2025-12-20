import pygame
import json
import os

# ================== KONFIGURACJA ==================
WIDTH, HEIGHT = 900, 650
BG_COLOR = (30, 30, 30)
TEXT_COLOR = (240, 240, 240)
BTN_COLOR = (70, 70, 200)
BTN_HOVER = (100, 100, 240)
INPUT_BG = (50, 50, 50)
FONT_SIZE = 26
DATA_FILE = "questions.json"


# ================== DANE ==================
def load_questions():
    if not os.path.exists(DATA_FILE):
        questions = [
            {"question": "Ile to 2 + 2?", "options": ["3", "4", "5", "22"], "correct": 1},
            {"question": "Kolor nieba w słoneczny dzień to:", "options": ["zielony", "niebieski", "czerwony", "czarny"],
             "correct": 1}
        ]
        save_questions(questions)
        return questions
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_questions(questions):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)


# ================== UI ELEMENTY ==================
class Button:
    def __init__(self, rect, text, data=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.data = data  # Opcjonalne pole na ID pytania

    def draw(self, screen, font, mouse_pos):
        color = BTN_HOVER if self.rect.collidepoint(mouse_pos) else BTN_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=6)
        txt = font.render(self.text, True, TEXT_COLOR)
        screen.blit(txt, txt.get_rect(center=self.rect.center))

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
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
            elif event.type == pygame.TEXTINPUT:
                self.text += event.text

    def draw(self, screen, font):
        color = (100, 100, 255) if self.active else INPUT_BG
        pygame.draw.rect(screen, color, self.rect, border_radius=4, width=2)
        pygame.draw.rect(screen, INPUT_BG, self.rect.inflate(-4, -4), border_radius=4)

        display_text = self.text if self.text else self.placeholder
        txt_color = TEXT_COLOR if self.text else (120, 120, 120)
        txt = font.render(display_text, True, txt_color)
        screen.blit(txt, (self.rect.x + 10, self.rect.y + 10))


# ================== WIDOKI (PĘTLE) ==================

def quiz_loop(screen, font, questions):
    idx = 0
    score = 0
    clock = pygame.time.Clock()

    while idx < len(questions):
        q = questions[idx]
        buttons = [Button((250, 200 + i * 60, 400, 45), opt) for i, opt in enumerate(q["options"])]
        answered = False
        feedback = ""

        while not answered:
            screen.fill(BG_COLOR)
            q_txt = font.render(f"Pytanie {idx + 1}/{len(questions)}: {q['question']}", True, TEXT_COLOR)
            screen.blit(q_txt, (50, 100))

            mouse = pygame.mouse.get_pos()
            for b in buttons: b.draw(screen, font, mouse)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT: return
                for i, b in enumerate(buttons):
                    if b.clicked(event):
                        if i == q["correct"]:
                            score += 1
                        answered = True
                        idx += 1
            clock.tick(60)

    # Ekran końcowy
    screen.fill(BG_COLOR)
    msg = f"Koniec! Wynik: {score}/{len(questions)}"
    txt = font.render(msg, True, (100, 255, 100))
    screen.blit(txt, txt.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
    pygame.display.flip()
    pygame.time.wait(2000)


def manage_questions(screen, font, questions):
    inputs = [
        InputBox((250, 100, 500, 45), "Treść pytania"),
        InputBox((250, 160, 500, 45), "Opcja A"),
        InputBox((250, 220, 500, 45), "Opcja B"),
        InputBox((250, 280, 500, 45), "Opcja C"),
        InputBox((250, 340, 500, 45), "Opcja D"),
        InputBox((250, 400, 200, 45), "Poprawna (A, B, C lub D)")
    ]
    save_btn = Button((250, 480, 200, 50), "Zapisz")
    back_btn = Button((470, 480, 200, 50), "Powrót")
    msg = ""

    while True:
        screen.fill(BG_COLOR)
        mouse = pygame.mouse.get_pos()
        for box in inputs: box.draw(screen, font)
        save_btn.draw(screen, font, mouse)
        back_btn.draw(screen, font, mouse)

        if msg:
            m_txt = font.render(msg, True, (255, 255, 100))
            screen.blit(m_txt, (250, 550))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return
            for box in inputs: box.handle_event(event)

            if back_btn.clicked(event): return

            if save_btn.clicked(event):
                ans = inputs[5].text.upper()
                if ans in "ABCD" and all(b.text for b in inputs[:5]):
                    questions.append({
                        "question": inputs[0].text,
                        "options": [inputs[i].text for i in range(1, 5)],
                        "correct": "ABCD".index(ans)
                    })
                    save_questions(questions)
                    for b in inputs: b.text = ""
                    msg = "Dodano pomyślnie!"
                else:
                    msg = "Błąd: Wypełnij pola i podaj A-D!"


def delete_questions(screen, font, questions):
    back_btn = Button((350, 550, 200, 50), "Powrót")

    while True:
        screen.fill(BG_COLOR)
        mouse = pygame.mouse.get_pos()

        # Tworzymy listę przycisków do usuwania
        del_buttons = []
        for i, q in enumerate(questions):
            del_buttons.append(Button((50, 50 + i * 50, 800, 40), f"Usuń: {q['question'][:50]}...", i))

        for b in del_buttons: b.draw(screen, font, mouse)
        back_btn.draw(screen, font, mouse)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return
            if back_btn.clicked(event): return
            for b in del_buttons:
                if b.clicked(event):
                    questions.pop(b.data)
                    save_questions(questions)
                    break  # Przerwij, bo lista się zmieniła


# ================== MAIN ==================
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Mega Quiz Python")
    font = pygame.font.SysFont("Arial", FONT_SIZE)

    questions = load_questions()

    menu_btns = [
        Button((350, 200, 200, 60), "Start Quiz"),
        Button((350, 280, 200, 60), "Dodaj Pytanie"),
        Button((350, 360, 200, 60), "Usuń Pytanie"),
        Button((350, 440, 200, 60), "Wyjście")
    ]

    running = True
    while running:
        screen.fill(BG_COLOR)
        mouse = pygame.mouse.get_pos()

        for b in menu_btns: b.draw(screen, font, mouse)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if menu_btns[0].clicked(event): quiz_loop(screen, font, questions)
            if menu_btns[1].clicked(event): manage_questions(screen, font, questions)
            if menu_btns[2].clicked(event): delete_questions(screen, font, questions)
            if menu_btns[3].clicked(event): running = False

    pygame.quit()


if __name__ == "__main__":
    main()