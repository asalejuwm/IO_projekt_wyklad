import pygame
import json
import os
import random
import math

# ================== KONFIGURACJA ==================
WIDTH, HEIGHT = 950, 850
BG_COLOR = (30, 30, 30)
TEXT_COLOR = (240, 240, 240)
BTN_COLOR = (70, 70, 200)
BTN_HOVER = (100, 100, 240)
BTN_LOCKED = (50, 50, 80)
INPUT_BG = (50, 50, 50)
FONT_SIZE = 22
DATA_FILE = "quiz_data.json"
USERS_FILE = "users.json"


# ================== DANE I LOGIKA ==================
def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_level(xp):
    if xp <= 0: return 1
    return int((xp / 100) ** (1 / 1.5)) + 1


ACHIEVEMENTS_DEF = {
    "add_q": {"name": "Architekt", "desc": "Dodano pierwsze własne pytanie"},
    "top5": {"name": "Elita", "desc": "Zajęcie miejsca w rankingu TOP 5"},
    "perfection_Podstawy": {"name": "Mistrz Podstaw", "desc": "100% poprawnych w Podstawach"},
    "perfection_Technologia": {"name": "Cyber-mózg", "desc": "100% poprawnych w Technologii"},
    "perfection_Nauka": {"name": "Eksplorator", "desc": "100% poprawnych w Nauce"},
    "correct_25": {"name": "Mędrzec", "desc": "25 łącznych poprawnych odpowiedzi"},
    "wrong_10": {"name": "Uczeń błędów", "desc": "Udzielenie 10 błędnych odpowiedzi"},
    "first_quiz": {"name": "Pierwsze kroki", "desc": "Ukończenie pierwszego quizu"}
}


def check_achievement(username, users, ach_id):
    if ach_id not in users[username]["achievements"]:
        users[username]["achievements"].append(ach_id)
        save_json(USERS_FILE, users)
        return True
    return False


def truncate_text(text, font, max_width):
    if font.size(text)[0] <= max_width: return text
    while font.size(text + "...")[0] > max_width and len(text) > 0: text = text[:-1]
    return text + "..."


def wrap_text(text, font, max_width):
    words = text.split(' ')
    lines, current_line = [], []
    for word in words:
        test_line = ' '.join(current_line + [word])
        if font.size(test_line)[0] < max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))
    return lines


# ================== UI ELEMENTY ==================
class Button:
    def __init__(self, x, y, width, text, font, padding=12, data=None, locked=False):
        self.x, self.y, self.width, self.font = x, y, width, font
        self.padding = padding
        self.text_lines = wrap_text(text, font, width - (padding * 2))
        self.line_height = font.get_linesize()
        self.height = (len(self.text_lines) * self.line_height) + (padding * 2)
        self.rect = pygame.Rect(x, y, width, self.height)
        self.data = data
        self.locked = locked

    def draw(self, screen, mouse_pos):
        color = BTN_LOCKED if self.locked else (BTN_HOVER if self.rect.collidepoint(mouse_pos) else BTN_COLOR)
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        for i, line in enumerate(self.text_lines):
            c = (140, 140, 140) if self.locked else TEXT_COLOR
            screen.blit(self.font.render(line, True, c),
                        (self.x + self.padding, self.y + self.padding + i * self.line_height))

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(
            event.pos) and not self.locked


class InputBox:
    def __init__(self, rect, placeholder="", password=False):
        self.rect = pygame.Rect(rect);
        self.text = "";
        self.active = False
        self.placeholder = placeholder;
        self.password = password

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN: self.active = self.rect.collidepoint(event.pos)
        if self.active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE: self.text = self.text[:-1]
            elif event.type == pygame.TEXTINPUT:
                self.text += event.text

    def draw(self, screen, font):
        color = (100, 100, 255) if self.active else (80, 80, 80)
        pygame.draw.rect(screen, color, self.rect, border_radius=5, width=2)
        display = "*" * len(self.text) if self.password else self.text
        txt = font.render(display if self.text else self.placeholder, True,
                          TEXT_COLOR if self.text else (130, 130, 130))
        screen.blit(txt, (self.rect.x + 10, self.rect.y + 10))


class Checkbox:
    def __init__(self, x, y, label):
        self.rect = pygame.Rect(x, y, 25, 25);
        self.checked = False;
        self.label = label

    def draw(self, screen, font):
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2)
        if self.checked: pygame.draw.rect(screen, (100, 255, 100), self.rect.inflate(-8, -8))
        screen.blit(font.render(self.label, True, TEXT_COLOR), (self.rect.right + 10, self.rect.y))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.checked = not self.checked


# ================== WIDOKI TABELARYCZNE ==================

def show_achievements(screen, font, username, users):
    back_btn = Button(375, 750, 200, "Powrót", font)
    # Kolumny dla tabeli achievementów
    COL_STATUS = 100
    COL_NAME = 200
    COL_DESC = 450

    while True:
        screen.fill(BG_COLOR);
        mouse = pygame.mouse.get_pos()
        title = font.render(f"OSIĄGNIĘCIA UŻYTKOWNIKA: {username}", True, (255, 215, 0))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

        # Nagłówki tabeli
        h1 = font.render("Status", True, (150, 150, 150))
        h2 = font.render("Nazwa", True, (150, 150, 150))
        h3 = font.render("Wymaganie", True, (150, 150, 150))
        screen.blit(h1, (COL_STATUS, 100))
        screen.blit(h2, (COL_NAME, 100))
        screen.blit(h3, (COL_DESC, 100))
        pygame.draw.line(screen, (100, 100, 100), (80, 130), (870, 130), 2)

        y_off = 150
        for ach_id, info in ACHIEVEMENTS_DEF.items():
            has_it = ach_id in users[username]["achievements"]
            color = (100, 255, 100) if has_it else (100, 100, 100)

            status_txt = "[ V ]" if has_it else "[   ]"
            s_surf = font.render(status_txt, True, color)
            n_surf = font.render(info["name"], True, color)
            d_surf = font.render(truncate_text(info["desc"], font, 400), True, (180, 180, 180))

            screen.blit(s_surf, (COL_STATUS, y_off))
            screen.blit(n_surf, (COL_NAME, y_off))
            screen.blit(d_surf, (COL_DESC, y_off))
            y_off += 40

        back_btn.draw(screen, mouse);
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if back_btn.clicked(event): return


def show_leaderboard(screen, font, users):
    back_btn = Button(375, 650, 200, "Powrót", font)
    sorted_users = sorted(users.items(), key=lambda x: x[1]['xp'], reverse=True)[:5]
    COL_RANK = 200
    COL_NICK = 300
    COL_XP = 600

    while True:
        screen.fill(BG_COLOR);
        mouse = pygame.mouse.get_pos()
        t = font.render("RANKING TOP 5", True, (255, 215, 0));
        screen.blit(t, (WIDTH // 2 - t.get_width() // 2, 50))

        h1 = font.render("Poz.", True, (150, 150, 150))
        h2 = font.render("Użytkownik", True, (150, 150, 150))
        h3 = font.render("Punkty XP", True, (150, 150, 150))
        screen.blit(h1, (COL_RANK, 120))
        screen.blit(h2, (COL_NICK, 120))
        screen.blit(h3, (COL_XP, 120))
        pygame.draw.line(screen, (180, 180, 180), (180, 150), (750, 150), 2)

        for i, (name, stats) in enumerate(sorted_users):
            r_s = font.render(f"{i + 1}.", True, TEXT_COLOR)
            n_s = font.render(truncate_text(name, font, 250), True, TEXT_COLOR)
            x_s = font.render(str(stats['xp']), True, (100, 255, 100))
            screen.blit(r_s, (COL_RANK, 170 + i * 50))
            screen.blit(n_s, (COL_NICK, 170 + i * 50))
            screen.blit(x_s, (COL_XP, 170 + i * 50))

        back_btn.draw(screen, mouse);
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if back_btn.clicked(event): return


# ================== MODYFIKACJA PYTAŃ ==================

def add_question_screen(screen, font, data, module, username, users):
    inputs = [InputBox((225, 80, 500, 45), "Treść pytania"), InputBox((225, 140, 500, 45), "Opcja A"),
              InputBox((225, 200, 500, 45), "Opcja B"), InputBox((225, 260, 500, 45), "Opcja C"),
              InputBox((225, 320, 500, 45), "Opcja D"), InputBox((225, 380, 200, 45), "Poprawna (A-D)")]
    save_btn = Button(225, 460, 240, "Zapisz pytanie", font)
    back_btn = Button(485, 460, 240, "Powrót", font)
    msg = ""

    while True:
        screen.fill(BG_COLOR);
        mouse = pygame.mouse.get_pos()
        for i in inputs: i.draw(screen, font)
        save_btn.draw(screen, mouse);
        back_btn.draw(screen, mouse)
        if msg: screen.blit(font.render(msg, True, (100, 255, 100)), (WIDTH // 2 - 50, 550))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if back_btn.clicked(event): return
            for i in inputs: i.handle_event(event)
            if save_btn.clicked(event):
                ans = inputs[5].text.upper()
                if all(i.text for i in inputs[:5]) and ans in "ABCD":
                    data[module].append({"question": inputs[0].text, "options": [inputs[i].text for i in range(1, 5)],
                                         "correct": "ABCD".index(ans)})
                    save_json(DATA_FILE, data)
                    check_achievement(username, users, "add_q")
                    msg = "Dodano pomyślnie!"
                    for i in inputs: i.text = ""


# ================== QUIZ I LOGIKA ODBLOKOWANIA ==================

def quiz_loop(screen, font, module_name, quiz_data, username, users):
    questions = list(quiz_data[module_name])
    random.shuffle(questions)
    idx, score, total = 0, 0, len(questions)

    while idx < total:
        q = questions[idx]
        correct_content = q["options"][q["correct"]]
        shuffled_opts = list(q["options"]);
        random.shuffle(shuffled_opts)
        answered = False
        while not answered:
            screen.fill(BG_COLOR)
            stats = font.render(f"{username} | Pytanie: {idx + 1}/{total} | Wynik: {score}", True, (100, 255, 100))
            screen.blit(stats, (20, 20))
            curr_y = 120
            for line in wrap_text(q["question"], font, 800):
                screen.blit(font.render(line, True, TEXT_COLOR), (75, curr_y));
                curr_y += 35
            ans_btns = []
            for opt in shuffled_opts:
                btn = Button(275, curr_y + 40, 400, opt, font, data=opt)
                ans_btns.append(btn);
                curr_y += btn.height + 15
            mouse = pygame.mouse.get_pos()
            for b in ans_btns: b.draw(screen, mouse)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); exit()
                for b in ans_btns:
                    if b.clicked(event):
                        correct = b.data == correct_content
                        users[username]["xp"] += 15 if correct else 5
                        if correct:
                            score += 1
                            users[username]["stats_correct"] += 1
                        else:
                            users[username]["stats_wrong"] += 1
                        idx += 1;
                        answered = True;
                        save_json(USERS_FILE, users)

    if users[username]["stats_correct"] >= 25: check_achievement(username, users, "correct_25")
    if users[username]["stats_wrong"] >= 10: check_achievement(username, users, "wrong_10")
    check_achievement(username, users, "first_quiz")

    unlocked_msg = ""
    if score == total:
        check_achievement(username, users, f"perfection_{module_name}")
        module_list = list(quiz_data.keys())
        if module_name in module_list:
            current_idx = module_list.index(module_name)
            if current_idx + 1 < len(module_list):
                next_mod = module_list[current_idx + 1]
                if next_mod not in users[username]["unlocked"]:
                    users[username]["unlocked"].append(next_mod)
                    unlocked_msg = f"BRAWO! ODBLOKOWANO: {next_mod}"
                    save_json(USERS_FILE, users)

    screen.fill(BG_COLOR)
    res_t = font.render(f"KONIEC! WYNIK: {score}/{total}", True, (255, 255, 255))
    screen.blit(res_t, (WIDTH // 2 - res_t.get_width() // 2, HEIGHT // 2))
    if unlocked_msg:
        u_t = font.render(unlocked_msg, True, (100, 255, 100))
        screen.blit(u_t, (WIDTH // 2 - u_t.get_width() // 2, HEIGHT // 2 + 50))
    pygame.display.flip();
    pygame.time.wait(3000)


# ================== LOGOWANIE I REJESTRACJA ==================

def auth_screen(screen, font, users, quiz_data):
    mode = "login";
    u_box = InputBox((325, 250, 300, 45), "Username")
    p_box = InputBox((325, 310, 300, 45), "Password", password=True)
    mod_check = Checkbox(325, 370, "Moderator")
    btn_action = Button(325, 420, 300, "Zaloguj", font)
    btn_switch = Button(325, 480, 300, "Zmień na Rejestrację", font)
    feedback = ""

    while True:
        screen.fill(BG_COLOR);
        mouse = pygame.mouse.get_pos()
        title_txt = "LOGOWANIE" if mode == "login" else "REJESTRACJA"
        screen.blit(font.render(title_txt, True, (255, 200, 100)), (WIDTH // 2 - 70, 150))
        u_box.draw(screen, font);
        p_box.draw(screen, font)
        if mode == "register": mod_check.draw(screen, font)
        btn_action.draw(screen, mouse);
        btn_switch.draw(screen, mouse)
        if feedback:
            f_s = font.render(feedback, True, (255, 100, 100))
            screen.blit(f_s, (WIDTH // 2 - f_s.get_width() // 2, 550))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            u_box.handle_event(event);
            p_box.handle_event(event)
            if mode == "register": mod_check.handle_event(event)
            if btn_switch.clicked(event):
                mode = "register" if mode == "login" else "login"
                btn_action = Button(325, 420, 300, "Zaloguj" if mode == "login" else "Zarejestruj", font)
                btn_switch = Button(325, 480, 300, "Zmień na Rejestrację" if mode == "login" else "Zmień na Logowanie",
                                    font)
                feedback = ""
            if btn_action.clicked(event):
                u, p = u_box.text, p_box.text
                if mode == "register":
                    if u and p and u not in users:
                        first_mod = list(quiz_data.keys())[0] if quiz_data else ""
                        users[u] = {"pw": p, "is_mod": mod_check.checked, "xp": 0, "unlocked": [first_mod],
                                    "achievements": [], "stats_correct": 0, "stats_wrong": 0}
                        save_json(USERS_FILE, users);
                        mode = "login"
                        feedback = "Konto założone! Zaloguj się."
                    else:
                        feedback = "Błąd rejestracji!"
                else:
                    if u in users and users[u]["pw"] == p:
                        # Naprawa starych kont
                        changed = False
                        for key, val in {"achievements": [], "unlocked": [list(quiz_data.keys())[0]],
                                         "stats_correct": 0, "stats_wrong": 0}.items():
                            if key not in users[u]: users[u][key] = val; changed = True
                        if changed: save_json(USERS_FILE, users)
                        return u
                    else:
                        feedback = "Błędny login lub hasło!"


def select_module_screen(screen, font, data, user_unlocked, is_mod):
    back_btn = Button(375, 750, 200, "Powrót", font)
    while True:
        screen.fill(BG_COLOR);
        mouse = pygame.mouse.get_pos()
        m_btns = []
        for i, m_name in enumerate(data.keys()):
            locked = (m_name not in user_unlocked) and not is_mod
            m_btns.append(
                Button(275, 120 + i * 90, 400, f"{m_name} {'[ZABLOKOWANE]' if locked else ''}", font, data=m_name,
                       locked=locked))
        for b in m_btns: b.draw(screen, mouse)
        back_btn.draw(screen, mouse);
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if back_btn.clicked(event): return None
            for b in m_btns:
                if b.clicked(event): return b.data


def delete_manager_screen(screen, font, data, module):
    while True:
        screen.fill(BG_COLOR);
        mouse = pygame.mouse.get_pos()
        if not data[module]: return
        btns = []
        for i, q in enumerate(data[module]):
            txt = truncate_text(q["question"], font, 700)
            btns.append(Button(100, 70 + i * 55, 750, txt, font, padding=8, data=i))
        back = Button(375, 750, 200, "Powrót", font)
        for b in btns: b.draw(screen, mouse)
        back.draw(screen, mouse);
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if back.clicked(event): return
            for b in btns:
                if b.clicked(event):
                    data[module].pop(b.data);
                    save_json(DATA_FILE, data);
                    break


# ================== MAIN ==================

def main():
    pygame.init();
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    font = pygame.font.SysFont("Arial", FONT_SIZE)
    quiz_data = load_json(DATA_FILE, {"Podstawy": [], "Technologia": [], "Nauka": []})
    users = load_json(USERS_FILE, {})

    while True:
        curr_u = auth_screen(screen, font, users, quiz_data)

        while True:
            is_mod = users[curr_u]["is_mod"]
            screen.fill(BG_COLOR);
            mouse = pygame.mouse.get_pos()
            lvl = get_level(users[curr_u]["xp"])
            screen.blit(font.render(f"Gracz: {curr_u} | LVL: {lvl} | XP: {users[curr_u]['xp']}", True, (200, 200, 100)),
                        (20, 20))

            main_btns = [
                Button(375, 150, 200, "Start Quiz", font, data="start"),
                Button(375, 230, 200, "Dodaj Pytanie", font, data="add"),
                Button(375, 310, 200, "Usuń Pytania", font, data="del", locked=not is_mod),
                Button(375, 390, 200, "Achievements", font, data="ach"),
                Button(375, 470, 200, "Ranking", font, data="rank"),
                Button(375, 550, 200, "Wyloguj", font, data="logout")
            ]
            for b in main_btns: b.draw(screen, mouse)
            pygame.display.flip()

            act = None
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); exit()
                for b in main_btns:
                    if b.clicked(event): act = b.data

            if act == "start":
                m = select_module_screen(screen, font, quiz_data, users[curr_u]["unlocked"], is_mod)
                if m: quiz_loop(screen, font, m, quiz_data, curr_u, users)
            elif act == "add":
                m = select_module_screen(screen, font, quiz_data, users[curr_u]["unlocked"], is_mod)
                if m: add_question_screen(screen, font, quiz_data, m, curr_u, users)
            elif act == "del":
                m = select_module_screen(screen, font, quiz_data, users[curr_u]["unlocked"], is_mod)
                if m: delete_manager_screen(screen, font, quiz_data, m)
            elif act == "ach":
                show_achievements(screen, font, curr_u, users)
            elif act == "rank":
                show_leaderboard(screen, font, users)
            elif act == "logout":
                break


if __name__ == "__main__":
    main()