import pygame
import json
import os
import random
import math
import hashlib
import re

# ================== KONFIGURACJA ==================
MIN_WIDTH, MIN_HEIGHT = 800, 600
INIT_WIDTH, INIT_HEIGHT = 950, 850
BG_COLOR = (30, 30, 30)
TEXT_COLOR = (240, 240, 240)
BTN_COLOR = (70, 70, 200)
BTN_HOVER = (100, 100, 240)
BTN_LOCKED = (50, 50, 80)
INPUT_BG = (50, 50, 50)
BASE_FONT_SIZE = 22
DATA_FILE = "quiz_data.json"
USERS_FILE = "users.json"

# Walidacja danych
MIN_USERNAME_LEN = 3
MAX_USERNAME_LEN = 20
MIN_PASSWORD_LEN = 6
MAX_PASSWORD_LEN = 50
MAX_QUESTION_LEN = 500
MAX_OPTION_LEN = 200
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]+$')


# ================== DANE I LOGIKA ==================
def hash_password(password):
    """Hashuje hasło używając SHA-256 z solą"""
    salt = "agile_scrum_quiz_2024"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()


def verify_password(password, stored_hash):
    """Weryfikuje hasło"""
    return hash_password(password) == stored_hash


def sanitize_input(text, max_length=1000):
    """Czyści i ogranicza długość tekstu"""
    if not isinstance(text, str):
        return ""
    # Usuwanie niebezpiecznych znaków
    text = text.strip()[:max_length]
    return text


def validate_username(username):
    """Waliduje nazwę użytkownika"""
    if not username or not isinstance(username, str):
        return False, "Nazwa użytkownika jest wymagana"
    if len(username) < MIN_USERNAME_LEN:
        return False, f"Nazwa użytkownika musi mieć co najmniej {MIN_USERNAME_LEN} znaki"
    if len(username) > MAX_USERNAME_LEN:
        return False, f"Nazwa użytkownika może mieć maksymalnie {MAX_USERNAME_LEN} znaków"
    if not USERNAME_PATTERN.match(username):
        return False, "Nazwa użytkownika może zawierać tylko litery, cyfry i podkreślenia"
    return True, ""


def validate_password(password):
    """Waliduje hasło"""
    if not password or not isinstance(password, str):
        return False, "Hasło jest wymagane"
    if len(password) < MIN_PASSWORD_LEN:
        return False, f"Hasło musi mieć co najmniej {MIN_PASSWORD_LEN} znaków"
    if len(password) > MAX_PASSWORD_LEN:
        return False, f"Hasło może mieć maksymalnie {MAX_PASSWORD_LEN} znaków"
    return True, ""


def load_json(path, default):
    """Bezpieczne ładowanie JSON z obsługą błędów"""
    if not os.path.exists(path):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(default, f, indent=2)
        except (IOError, OSError) as e:
            print(f"Błąd przy tworzeniu pliku {path}: {e}")
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except (json.JSONDecodeError, IOError, OSError) as e:
        print(f"Błąd przy ładowaniu {path}: {e}")
        return default


def save_json(path, data):
    """Bezpieczne zapisywanie JSON z obsługą błędów"""
    try:
        # Tworzenie backupu przed zapisem
        if os.path.exists(path):
            backup_path = path + ".backup"
            try:
                with open(path, "r", encoding="utf-8") as src:
                    with open(backup_path, "w", encoding="utf-8") as dst:
                        dst.write(src.read())
            except:
                pass
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except (IOError, OSError) as e:
        print(f"Błąd przy zapisywaniu {path}: {e}")


def get_level(xp):
    if xp <= 0: return 1
    return int((xp / 100) ** (1 / 1.5)) + 1


def migrate_user_data(users, quiz_data):
    """
    Migruje stare nazwy modułów i osiągnięć do nowych nazw.
    Stare nazwy: Podstawy, Technologia, Nauka
    Nowe nazwy: Agile_Podstawy, Scrum, Praktyki
    """
    # Mapowanie starych nazw modułów na nowe
    module_mapping = {
        "Podstawy": "Agile_Podstawy",
        "Technologia": "Scrum",
        "Nauka": "Praktyki"
    }
    
    # Mapowanie starych osiągnięć na nowe
    achievement_mapping = {
        "perfection_Podstawy": "perfection_Agile_Podstawy",
        "perfection_Technologia": "perfection_Scrum",
        "perfection_Nauka": "perfection_Praktyki"
    }
    
    changed = False
    
    for username, user_data in users.items():
        # Migracja odblokowanych modułów
        if "unlocked" in user_data and isinstance(user_data["unlocked"], list):
            new_unlocked = []
            for module in user_data["unlocked"]:
                if module in module_mapping:
                    new_module = module_mapping[module]
                    # Dodaj tylko jeśli nowy moduł istnieje w quiz_data
                    if new_module in quiz_data and new_module not in new_unlocked:
                        new_unlocked.append(new_module)
                    changed = True
                elif module in quiz_data and module not in new_unlocked:
                    # Moduł już ma nową nazwę, zostaw go
                    new_unlocked.append(module)
            user_data["unlocked"] = new_unlocked
        
        # Migracja osiągnięć
        if "achievements" in user_data and isinstance(user_data["achievements"], list):
            new_achievements = []
            for achievement in user_data["achievements"]:
                if achievement in achievement_mapping:
                    new_achievement = achievement_mapping[achievement]
                    if new_achievement not in new_achievements:
                        new_achievements.append(new_achievement)
                    changed = True
                else:
                    # Osiągnięcie już ma nową nazwę lub nie wymaga migracji
                    if achievement not in new_achievements:
                        new_achievements.append(achievement)
            user_data["achievements"] = new_achievements
    
    return changed


ACHIEVEMENTS_DEF = {
    "add_q": {"name": "Scrum Master", "desc": "Dodano pierwsze własne pytanie"},
    "top5": {"name": "Elita Agile", "desc": "Zajęcie miejsca w rankingu TOP 5"},
    "perfection_Agile_Podstawy": {"name": "Mistrz Podstaw Agile", "desc": "100% poprawnych w Podstawach Agile"},
    "perfection_Scrum": {"name": "Scrum Expert", "desc": "100% poprawnych w Scrum"},
    "perfection_Praktyki": {"name": "Praktyk Agile", "desc": "100% poprawnych w Praktykach Agile"},
    "correct_25": {"name": "Agile Mędrzec", "desc": "25 łącznych poprawnych odpowiedzi"},
    "wrong_10": {"name": "Uczeń Iteracji", "desc": "Udzielenie 10 błędnych odpowiedzi"},
    "first_quiz": {"name": "Pierwszy Sprint", "desc": "Ukończenie pierwszego quizu"}
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


def get_scale_factor(screen_width, screen_height):
    """Oblicza współczynnik skalowania na podstawie rozmiaru ekranu"""
    scale_x = screen_width / INIT_WIDTH
    scale_y = screen_height / INIT_HEIGHT
    return min(scale_x, scale_y, 1.5)  # Maksymalne skalowanie 1.5x


def scale_value(value, scale):
    """Skaluje wartość zgodnie z współczynnikiem"""
    return int(value * scale)


def get_font_size(scale):
    """Oblicza rozmiar czcionki na podstawie skalowania"""
    return max(int(BASE_FONT_SIZE * scale), 16)  # Minimalny rozmiar 16


def center_x(screen_width, element_width):
    """Wyśrodkowuje element poziomo"""
    return (screen_width - element_width) // 2


def get_content_offset(screen_width, screen_height):
    """Oblicza offset do wyśrodkowania zawartości względem oryginalnego rozmiaru"""
    offset_x = (screen_width - INIT_WIDTH) // 2
    offset_y = (screen_height - INIT_HEIGHT) // 2
    return offset_x, offset_y


# ================== UI ELEMENTY ==================
class Button:
    def __init__(self, x, y, width, text, font, padding=12, data=None, locked=False, scale=1.0, screen_width=None, center_horizontal=False):
        self.scale = scale
        self.base_x, self.base_y, self.base_width = x, y, width
        self.base_padding = padding
        self.font = font
        self.text = text
        self.data = data
        self.locked = locked
        self.screen_width = screen_width
        self.center_horizontal = center_horizontal
        self.update_position_and_size()

    def update_position_and_size(self, screen_width=None):
        """Aktualizuje pozycję i rozmiar przycisku na podstawie skalowania"""
        if screen_width is not None:
            self.screen_width = screen_width
        
        self.width = scale_value(self.base_width, self.scale)
        self.padding = scale_value(self.base_padding, self.scale)
        self.text_lines = wrap_text(self.text, self.font, self.width - (self.padding * 2))
        self.line_height = self.font.get_linesize()
        self.height = (len(self.text_lines) * self.line_height) + (self.padding * 2)
        
        # Wyśrodkowanie poziome jeśli wymagane
        if self.center_horizontal and self.screen_width:
            self.x = center_x(self.screen_width, self.width)
        else:
            self.x = scale_value(self.base_x, self.scale)
        
        self.y = scale_value(self.base_y, self.scale)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def set_scale(self, scale, screen_width=None):
        """Ustawia nowy współczynnik skalowania"""
        self.scale = scale
        self.update_position_and_size(screen_width)

    def draw(self, screen, mouse_pos):
        color = BTN_LOCKED if self.locked else (BTN_HOVER if self.rect.collidepoint(mouse_pos) else BTN_COLOR)
        border_radius = scale_value(8, self.scale)
        pygame.draw.rect(screen, color, self.rect, border_radius=border_radius)
        for i, line in enumerate(self.text_lines):
            c = (140, 140, 140) if self.locked else TEXT_COLOR
            screen.blit(self.font.render(line, True, c),
                        (self.x + self.padding, self.y + self.padding + i * self.line_height))

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(
            event.pos) and not self.locked


class InputBox:
    def __init__(self, rect, placeholder="", password=False, scale=1.0, screen_width=None, center_horizontal=False):
        self.base_rect = rect
        self.scale = scale
        self.text = "";
        self.active = False
        self.placeholder = placeholder;
        self.password = password
        self.screen_width = screen_width
        self.center_horizontal = center_horizontal
        self.update_rect()

    def update_rect(self, screen_width=None):
        """Aktualizuje prostokąt na podstawie skalowania"""
        if screen_width is not None:
            self.screen_width = screen_width
        
        x, y, w, h = self.base_rect
        width = scale_value(w, self.scale)
        height = scale_value(h, self.scale)
        
        # Wyśrodkowanie poziome jeśli wymagane
        if self.center_horizontal and self.screen_width:
            x_pos = center_x(self.screen_width, width)
        else:
            x_pos = scale_value(x, self.scale)
        
        y_pos = scale_value(y, self.scale)
        self.rect = pygame.Rect(x_pos, y_pos, width, height)

    def set_scale(self, scale, screen_width=None):
        """Ustawia nowy współczynnik skalowania"""
        self.scale = scale
        self.update_rect(screen_width)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN: self.active = self.rect.collidepoint(event.pos)
        if self.active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE: self.text = self.text[:-1]
            elif event.type == pygame.TEXTINPUT:
                # Sanityzacja inputu
                sanitized = sanitize_input(event.text, 100)
                self.text += sanitized

    def draw(self, screen, font):
        color = (100, 100, 255) if self.active else (80, 80, 80)
        border_radius = scale_value(5, self.scale)
        border_width = scale_value(2, self.scale)
        pygame.draw.rect(screen, color, self.rect, border_radius=border_radius, width=border_width)
        display = "*" * len(self.text) if self.password else self.text
        txt = font.render(display if self.text else self.placeholder, True,
                          TEXT_COLOR if self.text else (130, 130, 130))
        padding = scale_value(10, self.scale)
        screen.blit(txt, (self.rect.x + padding, self.rect.y + padding))


class Checkbox:
    def __init__(self, x, y, label, scale=1.0, screen_width=None, center_horizontal=False):
        self.base_x, self.base_y = x, y
        self.scale = scale
        self.checked = False;
        self.label = label
        self.screen_width = screen_width
        self.center_horizontal = center_horizontal
        self.update_rect()

    def update_rect(self, screen_width=None):
        """Aktualizuje prostokąt na podstawie skalowania"""
        if screen_width is not None:
            self.screen_width = screen_width
        
        size = scale_value(25, self.scale)
        
        # Wyśrodkowanie poziome jeśli wymagane (uwzględniając checkbox + label)
        if self.center_horizontal and self.screen_width:
            # Szacowana szerokość całego elementu (checkbox + label)
            label_width = self.scale * 150  # szacunek
            total_width = size + scale_value(10, self.scale) + label_width
            x_pos = center_x(self.screen_width, total_width) - scale_value(10, self.scale) - label_width
        else:
            x_pos = scale_value(self.base_x, self.scale)
        
        y_pos = scale_value(self.base_y, self.scale)
        self.rect = pygame.Rect(x_pos, y_pos, size, size)

    def set_scale(self, scale, screen_width=None):
        """Ustawia nowy współczynnik skalowania"""
        self.scale = scale
        self.update_rect(screen_width)

    def draw(self, screen, font):
        border_width = scale_value(2, self.scale)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, border_width)
        if self.checked:
            inflate = scale_value(-8, self.scale)
            pygame.draw.rect(screen, (100, 255, 100), self.rect.inflate(inflate, inflate))
        label_padding = scale_value(10, self.scale)
        screen.blit(font.render(self.label, True, TEXT_COLOR), (self.rect.right + label_padding, self.rect.y))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.checked = not self.checked


# ================== WIDOKI TABELARYCZNE ==================

def show_achievements(screen, font, username, users, screen_width, screen_height, scale):
    back_btn = Button(375, 750, 200, "Powrót", font, scale=scale, screen_width=screen_width, center_horizontal=True)
    # Kolumny dla tabeli achievementów - wyśrodkowane
    table_width = scale_value(790, scale)  # przybliżona szerokość tabeli
    table_start_x = center_x(screen_width, table_width)
    COL_STATUS = table_start_x + scale_value(20, scale)
    COL_NAME = table_start_x + scale_value(120, scale)
    COL_DESC = table_start_x + scale_value(370, scale)

    while True:
        back_btn.update_position_and_size(screen_width)
        screen.fill(BG_COLOR);
        mouse = pygame.mouse.get_pos()
        title = font.render(f"OSIĄGNIĘCIA UŻYTKOWNIKA: {username}", True, (255, 215, 0))
        screen.blit(title, (screen_width // 2 - title.get_width() // 2, scale_value(40, scale)))

        # Nagłówki tabeli
        h1 = font.render("Status", True, (150, 150, 150))
        h2 = font.render("Nazwa", True, (150, 150, 150))
        h3 = font.render("Wymaganie", True, (150, 150, 150))
        header_y = scale_value(100, scale)
        screen.blit(h1, (COL_STATUS, header_y))
        screen.blit(h2, (COL_NAME, header_y))
        screen.blit(h3, (COL_DESC, header_y))
        line_y = scale_value(130, scale)
        line_start_x = table_start_x + scale_value(0, scale)
        line_end_x = table_start_x + table_width
        pygame.draw.line(screen, (100, 100, 100), (line_start_x, line_y), (line_end_x, line_y), scale_value(2, scale))

        y_off = scale_value(150, scale)
        row_spacing = scale_value(40, scale)
        desc_width = scale_value(400, scale)
        for ach_id, info in ACHIEVEMENTS_DEF.items():
            has_it = ach_id in users[username].get("achievements", [])
            color = (100, 255, 100) if has_it else (100, 100, 100)

            status_txt = "[ V ]" if has_it else "[   ]"
            s_surf = font.render(status_txt, True, color)
            n_surf = font.render(info["name"], True, color)
            d_surf = font.render(truncate_text(info["desc"], font, desc_width), True, (180, 180, 180))

            screen.blit(s_surf, (COL_STATUS, y_off))
            screen.blit(n_surf, (COL_NAME, y_off))
            screen.blit(d_surf, (COL_DESC, y_off))
            y_off += row_spacing

        back_btn.draw(screen, mouse);
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if event.type == pygame.VIDEORESIZE:
                screen_width, screen_height = event.w, event.h
                if screen_width < MIN_WIDTH:
                    screen_width = MIN_WIDTH
                if screen_height < MIN_HEIGHT:
                    screen_height = MIN_HEIGHT
                screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
                scale = get_scale_factor(screen_width, screen_height)
                font = pygame.font.SysFont("Arial", get_font_size(scale))
                break
            if back_btn.clicked(event): return


def show_leaderboard(screen, font, users, screen_width, screen_height, scale):
    back_btn = Button(375, 650, 200, "Powrót", font, scale=scale, screen_width=screen_width, center_horizontal=True)
    sorted_users = sorted(users.items(), key=lambda x: x[1].get('xp', 0), reverse=True)[:5]
    # Wyśrodkowanie tabeli
    table_width = scale_value(570, scale)
    table_start_x = center_x(screen_width, table_width)
    COL_RANK = table_start_x + scale_value(0, scale)
    COL_NICK = table_start_x + scale_value(100, scale)
    COL_XP = table_start_x + scale_value(400, scale)

    while True:
        back_btn.update_position_and_size(screen_width)
        screen.fill(BG_COLOR);
        mouse = pygame.mouse.get_pos()
        t = font.render("RANKING TOP 5", True, (255, 215, 0));
        screen.blit(t, (screen_width // 2 - t.get_width() // 2, scale_value(50, scale)))

        h1 = font.render("Poz.", True, (150, 150, 150))
        h2 = font.render("Użytkownik", True, (150, 150, 150))
        h3 = font.render("Punkty XP", True, (150, 150, 150))
        header_y = scale_value(120, scale)
        screen.blit(h1, (COL_RANK, header_y))
        screen.blit(h2, (COL_NICK, header_y))
        screen.blit(h3, (COL_XP, header_y))
        line_y = scale_value(150, scale)
        line_start_x = table_start_x
        line_end_x = table_start_x + table_width
        pygame.draw.line(screen, (180, 180, 180), (line_start_x, line_y), (line_end_x, line_y), scale_value(2, scale))

        start_y = scale_value(170, scale)
        row_spacing = scale_value(50, scale)
        name_width = scale_value(250, scale)
        for i, (name, stats) in enumerate(sorted_users):
            r_s = font.render(f"{i + 1}.", True, TEXT_COLOR)
            n_s = font.render(truncate_text(name, font, name_width), True, TEXT_COLOR)
            x_s = font.render(str(stats.get('xp', 0)), True, (100, 255, 100))
            y_pos = start_y + i * row_spacing
            screen.blit(r_s, (COL_RANK, y_pos))
            screen.blit(n_s, (COL_NICK, y_pos))
            screen.blit(x_s, (COL_XP, y_pos))

        back_btn.draw(screen, mouse);
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                break
            if back_btn.clicked(event): return


# ================== MODYFIKACJA PYTAŃ ==================

def add_question_screen(screen, font, data, module, username, users, screen_width, screen_height, scale):
    inputs = [
        InputBox((225, 80, 500, 45), "Treść pytania", scale=scale, screen_width=screen_width, center_horizontal=True),
        InputBox((225, 140, 500, 45), "Opcja A", scale=scale, screen_width=screen_width, center_horizontal=True),
        InputBox((225, 200, 500, 45), "Opcja B", scale=scale, screen_width=screen_width, center_horizontal=True),
        InputBox((225, 260, 500, 45), "Opcja C", scale=scale, screen_width=screen_width, center_horizontal=True),
        InputBox((225, 320, 500, 45), "Opcja D", scale=scale, screen_width=screen_width, center_horizontal=True),
        InputBox((225, 380, 200, 45), "Poprawna (A-D)", scale=scale, screen_width=screen_width, center_horizontal=True)
    ]
    save_btn = Button(225, 460, 240, "Zapisz pytanie", font, scale=scale, screen_width=screen_width, center_horizontal=False)
    back_btn = Button(485, 460, 240, "Powrót", font, scale=scale, screen_width=screen_width, center_horizontal=False)
    msg = ""

    while True:
        # Aktualizacja pozycji
        for inp in inputs:
            inp.update_rect(screen_width)
        save_btn.update_position_and_size(screen_width)
        back_btn.update_position_and_size(screen_width)
        # Wyśrodkowanie przycisków obok siebie (grupa przycisków wyśrodkowana)
        btn_spacing = scale_value(20, scale)
        total_btn_width = save_btn.width + btn_spacing + back_btn.width
        center_start = center_x(screen_width, total_btn_width)
        save_btn.x = center_start
        save_btn.rect.x = save_btn.x
        back_btn.x = center_start + save_btn.width + btn_spacing
        back_btn.rect.x = back_btn.x
        
        screen.fill(BG_COLOR);
        mouse = pygame.mouse.get_pos()
        for i in inputs: i.draw(screen, font)
        save_btn.draw(screen, mouse);
        back_btn.draw(screen, mouse)
        if msg:
            msg_surf = font.render(msg, True, (100, 255, 100))
            screen.blit(msg_surf, (screen_width // 2 - msg_surf.get_width() // 2, scale_value(550, scale)))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if event.type == pygame.VIDEORESIZE:
                screen_width, screen_height = event.w, event.h
                if screen_width < MIN_WIDTH:
                    screen_width = MIN_WIDTH
                if screen_height < MIN_HEIGHT:
                    screen_height = MIN_HEIGHT
                screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
                scale = get_scale_factor(screen_width, screen_height)
                font = pygame.font.SysFont("Arial", get_font_size(scale))
                break
            if back_btn.clicked(event): return
            for i in inputs: i.handle_event(event)
            if save_btn.clicked(event):
                # Walidacja i sanityzacja danych
                question = sanitize_input(inputs[0].text, MAX_QUESTION_LEN)
                options = [sanitize_input(inputs[i].text, MAX_OPTION_LEN) for i in range(1, 5)]
                ans = inputs[5].text.upper().strip()
                
                if not question:
                    msg = "Treść pytania jest wymagana!"
                elif not all(options):
                    msg = "Wszystkie opcje są wymagane!"
                elif ans not in "ABCD":
                    msg = "Poprawna odpowiedź musi być A, B, C lub D!"
                elif len(question) > MAX_QUESTION_LEN:
                    msg = f"Pytanie może mieć maksymalnie {MAX_QUESTION_LEN} znaków!"
                elif any(len(opt) > MAX_OPTION_LEN for opt in options):
                    msg = f"Opcje mogą mieć maksymalnie {MAX_OPTION_LEN} znaków!"
                else:
                    data[module].append({
                        "question": question,
                        "options": options,
                        "correct": "ABCD".index(ans)
                    })
                    save_json(DATA_FILE, data)
                    check_achievement(username, users, "add_q")
                    msg = "Dodano pomyślnie!"
                    for i in inputs: i.text = ""


# ================== QUIZ I LOGIKA ODBLOKOWANIA ==================

def quiz_loop(screen, font, module_name, quiz_data, username, users, screen_width, screen_height, scale):
    questions = list(quiz_data[module_name])
    if not questions:
        screen.fill(BG_COLOR)
        msg = font.render("Brak pytań w tym module!", True, (255, 100, 100))
        screen.blit(msg, (screen_width // 2 - msg.get_width() // 2, screen_height // 2))
        pygame.display.flip()
        pygame.time.wait(2000)
        return
    
    random.shuffle(questions)
    idx, score, total = 0, 0, len(questions)
    question_width = scale_value(800, scale)

    while idx < total:
        q = questions[idx]
        correct_content = q["options"][q["correct"]]
        shuffled_opts = list(q["options"]);
        random.shuffle(shuffled_opts)
        answered = False
        while not answered:
            screen.fill(BG_COLOR)
            stats = font.render(f"{username} | Pytanie: {idx + 1}/{total} | Wynik: {score}", True, (100, 255, 100))
            screen.blit(stats, (scale_value(20, scale), scale_value(20, scale)))
            curr_y = scale_value(120, scale)
            question_start_x = center_x(screen_width, question_width)
            for line in wrap_text(q["question"], font, question_width):
                line_surf = font.render(line, True, TEXT_COLOR)
                screen.blit(line_surf, (question_start_x, curr_y));
                curr_y += scale_value(35, scale)
            ans_btns = []
            btn_width = scale_value(400, scale)
            for opt in shuffled_opts:
                btn = Button(275, curr_y + scale_value(40, scale), btn_width, opt, font, data=opt, scale=scale, screen_width=screen_width, center_horizontal=True)
                btn.update_position_and_size(screen_width)
                ans_btns.append(btn);
                curr_y += btn.height + scale_value(15, scale)
            mouse = pygame.mouse.get_pos()
            for b in ans_btns: b.draw(screen, mouse)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); exit()
                if event.type == pygame.VIDEORESIZE:
                    screen_width, screen_height = event.w, event.h
                    if screen_width < MIN_WIDTH:
                        screen_width = MIN_WIDTH
                    if screen_height < MIN_HEIGHT:
                        screen_height = MIN_HEIGHT
                    screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
                    scale = get_scale_factor(screen_width, screen_height)
                    font = pygame.font.SysFont("Arial", get_font_size(scale))
                    question_width = scale_value(800, scale)
                    break
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
    screen.blit(res_t, (screen_width // 2 - res_t.get_width() // 2, screen_height // 2))
    if unlocked_msg:
        u_t = font.render(unlocked_msg, True, (100, 255, 100))
        screen.blit(u_t, (screen_width // 2 - u_t.get_width() // 2, screen_height // 2 + scale_value(50, scale)))
    pygame.display.flip();
    pygame.time.wait(3000)


# ================== LOGOWANIE I REJESTRACJA ==================

def auth_screen(screen, font, users, quiz_data, screen_width, screen_height, scale):
    mode = "login";
    u_box = InputBox((325, 250, 300, 45), "Username", scale=scale, screen_width=screen_width, center_horizontal=True)
    p_box = InputBox((325, 310, 300, 45), "Password", password=True, scale=scale, screen_width=screen_width, center_horizontal=True)
    mod_check = Checkbox(325, 370, "Moderator", scale=scale, screen_width=screen_width, center_horizontal=True)
    btn_action = Button(325, 420, 300, "Zaloguj", font, scale=scale, screen_width=screen_width, center_horizontal=True)
    btn_switch = Button(325, 480, 300, "Zmień na Rejestrację", font, scale=scale, screen_width=screen_width, center_horizontal=True)
    feedback = ""

    while True:
        # Aktualizacja pozycji przy zmianie rozmiaru
        u_box.update_rect(screen_width)
        p_box.update_rect(screen_width)
        mod_check.update_rect(screen_width)
        btn_action.update_position_and_size(screen_width)
        btn_switch.update_position_and_size(screen_width)
        
        screen.fill(BG_COLOR);
        mouse = pygame.mouse.get_pos()
        title_txt = "LOGOWANIE" if mode == "login" else "REJESTRACJA"
        title_surf = font.render(title_txt, True, (255, 200, 100))
        screen.blit(title_surf, (screen_width // 2 - title_surf.get_width() // 2, scale_value(150, scale)))
        u_box.draw(screen, font);
        p_box.draw(screen, font)
        if mode == "register": mod_check.draw(screen, font)
        btn_action.draw(screen, mouse);
        btn_switch.draw(screen, mouse)
        if feedback:
            f_s = font.render(feedback, True, (255, 100, 100))
            screen.blit(f_s, (screen_width // 2 - f_s.get_width() // 2, scale_value(550, scale)))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if event.type == pygame.VIDEORESIZE:
                screen_width, screen_height = event.w, event.h
                if screen_width < MIN_WIDTH:
                    screen_width = MIN_WIDTH
                if screen_height < MIN_HEIGHT:
                    screen_height = MIN_HEIGHT
                screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
                scale = get_scale_factor(screen_width, screen_height)
                font = pygame.font.SysFont("Arial", get_font_size(scale))
                break
            u_box.handle_event(event);
            p_box.handle_event(event)
            if mode == "register": mod_check.handle_event(event)
            if btn_switch.clicked(event):
                mode = "register" if mode == "login" else "login"
                btn_action = Button(325, 420, 300, "Zaloguj" if mode == "login" else "Zarejestruj", font, scale=scale, screen_width=screen_width, center_horizontal=True)
                btn_switch = Button(325, 480, 300, "Zmień na Rejestrację" if mode == "login" else "Zmień na Logowanie",
                                    font, scale=scale, screen_width=screen_width, center_horizontal=True)
                feedback = ""
            if btn_action.clicked(event):
                u = sanitize_input(u_box.text, MAX_USERNAME_LEN)
                p = p_box.text
                
                # Walidacja
                if mode == "register":
                    username_valid, username_msg = validate_username(u)
                    password_valid, password_msg = validate_password(p)
                    
                    if not username_valid:
                        feedback = username_msg
                    elif not password_valid:
                        feedback = password_msg
                    elif u in users:
                        feedback = "Użytkownik już istnieje!"
                    else:
                        first_mod = list(quiz_data.keys())[0] if quiz_data else ""
                        users[u] = {
                            "pw": hash_password(p),  # Hashowanie hasła
                            "is_mod": mod_check.checked,
                            "xp": 0,
                            "unlocked": [first_mod] if first_mod else [],
                            "achievements": [],
                            "stats_correct": 0,
                            "stats_wrong": 0
                        }
                        save_json(USERS_FILE, users);
                        mode = "login"
                        feedback = "Konto założone! Zaloguj się."
                        u_box.text = ""
                        p_box.text = ""
                else:
                    if not u:
                        feedback = "Wprowadź nazwę użytkownika"
                    elif not p:
                        feedback = "Wprowadź hasło"
                    elif u in users:
                        # Sprawdzanie hasła (może być w starym formacie lub nowym)
                        stored_pw = users[u].get("pw", "")
                        # Kompatybilność wsteczna - jeśli hasło jest w plain text, przekształć na hash
                        if len(stored_pw) < 64:  # SHA-256 hash ma 64 znaki hex
                            if stored_pw == p:  # Stary format - plain text
                                users[u]["pw"] = hash_password(p)
                                save_json(USERS_FILE, users)
                            else:
                                feedback = "Błędny login lub hasło!"
                                continue
                        elif not verify_password(p, stored_pw):
                            feedback = "Błędny login lub hasło!"
                            continue
                        
                        # Migracja danych użytkownika (na wypadek, gdyby migracja nie została wykonana przy starcie)
                        migrate_user_data({u: users[u]}, quiz_data)
                        
                        # Naprawa starych kont
                        changed = False
                        first_mod = list(quiz_data.keys())[0] if quiz_data else ""
                        for key, val in {
                            "achievements": [],
                            "unlocked": [first_mod] if first_mod else [],
                            "stats_correct": 0,
                            "stats_wrong": 0
                        }.items():
                            if key not in users[u]:
                                users[u][key] = val
                                changed = True
                        
                        # Jeśli unlocked jest puste lub zawiera tylko nieistniejące moduły, dodaj pierwszy moduł
                        if "unlocked" in users[u] and isinstance(users[u]["unlocked"], list):
                            existing_unlocked = [m for m in users[u]["unlocked"] if m in quiz_data]
                            if not existing_unlocked and first_mod:
                                users[u]["unlocked"] = [first_mod]
                                changed = True
                            elif existing_unlocked != users[u]["unlocked"]:
                                users[u]["unlocked"] = existing_unlocked
                                changed = True
                        
                        if changed:
                            save_json(USERS_FILE, users)
                        return u
                    else:
                        feedback = "Błędny login lub hasło!"


def select_module_screen(screen, font, data, user_unlocked, is_mod, screen_width, screen_height, scale):
    back_btn = Button(375, 750, 200, "Powrót", font, scale=scale, screen_width=screen_width, center_horizontal=True)
    while True:
        screen.fill(BG_COLOR);
        mouse = pygame.mouse.get_pos()
        m_btns = []
        btn_width = scale_value(400, scale)
        start_y = scale_value(120, scale)
        btn_spacing = scale_value(90, scale)
        for i, m_name in enumerate(data.keys()):
            locked = (m_name not in user_unlocked) and not is_mod
            btn_text = f"{m_name} {'[ZABLOKOWANE]' if locked else ''}"
            m_btns.append(
                Button(275, start_y + i * btn_spacing, btn_width, btn_text, font, data=m_name,
                       locked=locked, scale=scale, screen_width=screen_width, center_horizontal=True))
        # Aktualizacja pozycji
        back_btn.update_position_and_size(screen_width)
        for btn in m_btns:
            btn.update_position_and_size(screen_width)
        for b in m_btns: b.draw(screen, mouse)
        back_btn.draw(screen, mouse);
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if event.type == pygame.VIDEORESIZE:
                screen_width, screen_height = event.w, event.h
                if screen_width < MIN_WIDTH:
                    screen_width = MIN_WIDTH
                if screen_height < MIN_HEIGHT:
                    screen_height = MIN_HEIGHT
                screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
                scale = get_scale_factor(screen_width, screen_height)
                font = pygame.font.SysFont("Arial", get_font_size(scale))
                break
            if back_btn.clicked(event): return None
            for b in m_btns:
                if b.clicked(event): return b.data


def delete_manager_screen(screen, font, data, module, screen_width, screen_height, scale):
    while True:
        screen.fill(BG_COLOR);
        mouse = pygame.mouse.get_pos()
        if not data[module]: return
        btns = []
        btn_width = scale_value(750, scale)
        start_y = scale_value(70, scale)
        btn_spacing = scale_value(55, scale)
        question_width = scale_value(700, scale)
        for i, q in enumerate(data[module]):
            txt = truncate_text(q.get("question", ""), font, question_width)
            btns.append(Button(100, start_y + i * btn_spacing, btn_width, txt, font, padding=scale_value(8, scale), data=i, scale=scale, screen_width=screen_width, center_horizontal=True))
        back = Button(375, 750, 200, "Powrót", font, scale=scale, screen_width=screen_width, center_horizontal=True)
        # Aktualizacja pozycji
        back.update_position_and_size(screen_width)
        for btn in btns:
            btn.update_position_and_size(screen_width)
        for b in btns: b.draw(screen, mouse)
        back.draw(screen, mouse);
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if event.type == pygame.VIDEORESIZE:
                screen_width, screen_height = event.w, event.h
                if screen_width < MIN_WIDTH:
                    screen_width = MIN_WIDTH
                if screen_height < MIN_HEIGHT:
                    screen_height = MIN_HEIGHT
                screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
                scale = get_scale_factor(screen_width, screen_height)
                font = pygame.font.SysFont("Arial", get_font_size(scale))
                break
            if back.clicked(event): return
            for b in btns:
                if b.clicked(event):
                    if 0 <= b.data < len(data[module]):
                        data[module].pop(b.data);
                        save_json(DATA_FILE, data);
                    break


# ================== MAIN ==================

def main():
    pygame.init();
    screen = pygame.display.set_mode((INIT_WIDTH, INIT_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Quiz Agile/Scrum")
    clock = pygame.time.Clock()
    
    # Pobieranie aktualnych wymiarów ekranu
    screen_width, screen_height = screen.get_size()
    scale = get_scale_factor(screen_width, screen_height)
    font_size = get_font_size(scale)
    font = pygame.font.SysFont("Arial", font_size)
    
    # Domyślne moduły Agile/Scrum
    default_modules = {
        "Agile_Podstawy": [],
        "Scrum": [],
        "Praktyki": []
    }
    quiz_data = load_json(DATA_FILE, default_modules)
    users = load_json(USERS_FILE, {})
    
    # Migracja danych użytkowników do nowych nazw modułów
    if migrate_user_data(users, quiz_data):
        save_json(USERS_FILE, users)
        print("Dokonano migracji danych użytkowników do nowych nazw modułów.")

    while True:
        screen_width, screen_height = screen.get_size()
        # Wymuszanie minimalnego rozmiaru
        if screen_width < MIN_WIDTH:
            screen_width = MIN_WIDTH
        if screen_height < MIN_HEIGHT:
            screen_height = MIN_HEIGHT
        if screen.get_size() != (screen_width, screen_height):
            screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
        
        scale = get_scale_factor(screen_width, screen_height)
        font_size = get_font_size(scale)
        font = pygame.font.SysFont("Arial", font_size)
        
        curr_u = auth_screen(screen, font, users, quiz_data, screen_width, screen_height, scale)

        while True:
            screen_width, screen_height = screen.get_size()
            if screen_width < MIN_WIDTH:
                screen_width = MIN_WIDTH
            if screen_height < MIN_HEIGHT:
                screen_height = MIN_HEIGHT
            if screen.get_size() != (screen_width, screen_height):
                screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
            
            scale = get_scale_factor(screen_width, screen_height)
            font_size = get_font_size(scale)
            font = pygame.font.SysFont("Arial", font_size)
            
            is_mod = users[curr_u]["is_mod"]
            screen.fill(BG_COLOR);
            mouse = pygame.mouse.get_pos()
            lvl = get_level(users[curr_u]["xp"])
            stats_text = f"Gracz: {curr_u} | LVL: {lvl} | XP: {users[curr_u]['xp']}"
            stats_surf = font.render(stats_text, True, (200, 200, 100))
            screen.blit(stats_surf, (scale_value(20, scale), scale_value(20, scale)))

            main_btns = [
                Button(375, 150, 200, "Start Quiz", font, data="start", scale=scale, screen_width=screen_width, center_horizontal=True),
                Button(375, 230, 200, "Dodaj Pytanie", font, data="add", scale=scale, screen_width=screen_width, center_horizontal=True),
                Button(375, 310, 200, "Usuń Pytania", font, data="del", locked=not is_mod, scale=scale, screen_width=screen_width, center_horizontal=True),
                Button(375, 390, 200, "Achievements", font, data="ach", scale=scale, screen_width=screen_width, center_horizontal=True),
                Button(375, 470, 200, "Ranking", font, data="rank", scale=scale, screen_width=screen_width, center_horizontal=True),
                Button(375, 550, 200, "Wyloguj", font, data="logout", scale=scale, screen_width=screen_width, center_horizontal=True)
            ]
            # Aktualizacja pozycji przycisków
            for btn in main_btns:
                btn.update_position_and_size(screen_width)
            for b in main_btns: b.draw(screen, mouse)
            pygame.display.flip()

            act = None
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); exit()
                if event.type == pygame.VIDEORESIZE:
                    # Obsługa zmiany rozmiaru okna
                    screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    break
                for b in main_btns:
                    if b.clicked(event): act = b.data

            if act == "start":
                m = select_module_screen(screen, font, quiz_data, users[curr_u]["unlocked"], is_mod, screen_width, screen_height, scale)
                if m: quiz_loop(screen, font, m, quiz_data, curr_u, users, screen_width, screen_height, scale)
            elif act == "add":
                m = select_module_screen(screen, font, quiz_data, users[curr_u]["unlocked"], is_mod, screen_width, screen_height, scale)
                if m: add_question_screen(screen, font, quiz_data, m, curr_u, users, screen_width, screen_height, scale)
            elif act == "del":
                m = select_module_screen(screen, font, quiz_data, users[curr_u]["unlocked"], is_mod, screen_width, screen_height, scale)
                if m: delete_manager_screen(screen, font, quiz_data, m, screen_width, screen_height, scale)
            elif act == "ach":
                show_achievements(screen, font, curr_u, users, screen_width, screen_height, scale)
            elif act == "rank":
                show_leaderboard(screen, font, users, screen_width, screen_height, scale)
            elif act == "logout":
                break
            
            clock.tick(60)


if __name__ == "__main__":
    main()