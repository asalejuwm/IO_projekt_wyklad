# Instrukcja konfiguracji MySQL dla Quiz Agile/Scrum

## Wymagania

- Python 3.7+
- MySQL Server 5.7+ lub MariaDB 10.3+
- Biblioteki Python: pygame, mysql-connector-python

## Instalacja zależności

```bash
pip install -r requirements.txt
```

## Konfiguracja bazy danych

1. **Zainstaluj i uruchom MySQL Server**

2. **Utwórz użytkownika i bazę danych** (opcjonalnie, skrypt może to zrobić automatycznie):

```sql
CREATE DATABASE quiz_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'quiz_user'@'localhost' IDENTIFIED BY 'quiz_password';
GRANT ALL PRIVILEGES ON quiz_db.* TO 'quiz_user'@'localhost';
FLUSH PRIVILEGES;
```

3. **Skonfiguruj połączenie** w pliku `quiz.py`:

Edytuj sekcję `DB_CONFIG` w pliku `quiz.py`:

```python
DB_CONFIG = {
    'host': 'localhost',        # Adres serwera MySQL
    'database': 'quiz_db',      # Nazwa bazy danych
    'user': 'quiz_user',        # Nazwa użytkownika
    'password': 'quiz_password', # Hasło użytkownika
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': False
}
```

## Migracja danych z JSON do MySQL

Jeśli masz istniejące dane w plikach JSON, uruchom skrypt migracji:

```bash
python3 migrate_json_to_mysql.py
```

Skrypt:
- Utworzy strukturę bazy danych (tabele)
- Przeniesie wszystkie pytania z `quiz_data.json`
- Przeniesie wszystkich użytkowników z `users.json`
- Zaktualizuje stare nazwy modułów i osiągnięć

## Uruchomienie aplikacji

```bash
python3 quiz.py
```

Aplikacja automatycznie:
- Połączy się z bazą danych
- Utworzy strukturę tabel jeśli nie istnieją
- Utworzy domyślne moduły jeśli nie istnieją

## Struktura bazy danych

### Tabela `users`
- `username` (VARCHAR(20), PRIMARY KEY) - nazwa użytkownika
- `password_hash` (VARCHAR(64)) - zahashowane hasło
- `is_mod` (BOOLEAN) - czy użytkownik jest moderatorem
- `xp` (INT) - punkty doświadczenia
- `stats_correct` (INT) - liczba poprawnych odpowiedzi
- `stats_wrong` (INT) - liczba błędnych odpowiedzi
- `created_at` (TIMESTAMP) - data utworzenia konta

### Tabela `modules`
- `module_name` (VARCHAR(50), PRIMARY KEY) - nazwa modułu

### Tabela `questions`
- `question_id` (INT, AUTO_INCREMENT, PRIMARY KEY) - ID pytania
- `module_name` (VARCHAR(50), FOREIGN KEY) - moduł do którego należy pytanie
- `question_text` (TEXT) - treść pytania
- `option_a`, `option_b`, `option_c`, `option_d` (VARCHAR(200)) - opcje odpowiedzi
- `correct_answer` (INT, 0-3) - indeks poprawnej odpowiedzi
- `created_at` (TIMESTAMP) - data utworzenia pytania

### Tabela `user_achievements`
- `username` (VARCHAR(20), FOREIGN KEY) - użytkownik
- `achievement_id` (VARCHAR(50)) - ID osiągnięcia
- `unlocked_at` (TIMESTAMP) - data odblokowania

### Tabela `user_unlocked_modules`
- `username` (VARCHAR(20), FOREIGN KEY) - użytkownik
- `module_name` (VARCHAR(50), FOREIGN KEY) - odblokowany moduł
- `unlocked_at` (TIMESTAMP) - data odblokowania

## Bezpieczeństwo

- Wszystkie zapytania SQL używają parametrów (prepared statements) - ochrona przed SQL injection
- Hasła są hashowane przed zapisem do bazy
- Transakcje zapewniają spójność danych
- Foreign keys zapewniają integralność referencyjną

## Rozwiązywanie problemów

### Błąd połączenia z bazą danych
- Sprawdź czy MySQL jest uruchomiony: `sudo systemctl status mysql`
- Sprawdź dane w `DB_CONFIG`
- Sprawdź uprawnienia użytkownika

### Błąd przy inicjalizacji
- Upewnij się że użytkownik ma uprawnienia CREATE DATABASE
- Sprawdź logi MySQL

### Błąd przy migracji
- Sprawdź czy pliki JSON istnieją
- Sprawdź czy dane w JSON są poprawne
- Sprawdź logi błędu w konsoli

