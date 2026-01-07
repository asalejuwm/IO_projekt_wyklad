#!/usr/bin/env python3
"""
Skrypt migracji danych z plików JSON do bazy danych MySQL.
Uruchom ten skrypt raz, aby przenieść istniejące dane z JSON do MySQL.
"""

import json
import os
import sys
from quiz import (
    init_database, get_db_connection, add_module, add_question,
    save_user, unlock_module_for_user, DB_CONFIG
)

DATA_FILE = "quiz_data.json"
USERS_FILE = "users.json"


def migrate_quiz_data():
    """Migruje pytania quizu z JSON do MySQL"""
    if not os.path.exists(DATA_FILE):
        print(f"Plik {DATA_FILE} nie istnieje. Pomijam migrację pytań.")
        return
    
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            quiz_data = json.load(f)
        
        print("Migracja pytań quizu...")
        for module_name, questions in quiz_data.items():
            # Dodaj moduł jeśli nie istnieje
            add_module(module_name)
            print(f"  Moduł: {module_name}")
            
            # Dodaj pytania
            for q in questions:
                question_data = {
                    "question": q.get("question", ""),
                    "options": q.get("options", []),
                    "correct": q.get("correct", 0)
                }
                if add_question(module_name, question_data):
                    print(f"    ✓ Dodano pytanie: {question_data['question'][:50]}...")
                else:
                    print(f"    ✗ Błąd przy dodawaniu pytania")
        
        print("Migracja pytań zakończona pomyślnie.")
    except Exception as e:
        print(f"Błąd przy migracji pytań: {e}")


def migrate_users():
    """Migruje użytkowników z JSON do MySQL"""
    if not os.path.exists(USERS_FILE):
        print(f"Plik {USERS_FILE} nie istnieje. Pomijam migrację użytkowników.")
        return
    
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
        
        print("Migracja użytkowników...")
        for username, user_data in users.items():
            # Konwersja starego formatu hasła jeśli potrzeba
            pw = user_data.get("pw", "")
            if len(pw) < 64:  # Plain text password
                from quiz import hash_password
                pw = hash_password(pw)
                user_data["pw"] = pw
            
            # Migracja modułów
            module_mapping = {
                "Podstawy": "Agile_Podstawy",
                "Technologia": "Scrum",
                "Nauka": "Praktyki"
            }
            
            unlocked = user_data.get("unlocked", [])
            new_unlocked = []
            for module in unlocked:
                if module in module_mapping:
                    new_unlocked.append(module_mapping[module])
                else:
                    new_unlocked.append(module)
            
            user_data["unlocked"] = new_unlocked
            
            # Migracja osiągnięć
            achievement_mapping = {
                "perfection_Podstawy": "perfection_Agile_Podstawy",
                "perfection_Technologia": "perfection_Scrum",
                "perfection_Nauka": "perfection_Praktyki"
            }
            
            achievements = user_data.get("achievements", [])
            new_achievements = []
            for ach in achievements:
                if ach in achievement_mapping:
                    new_achievements.append(achievement_mapping[ach])
                else:
                    new_achievements.append(ach)
            
            user_data["achievements"] = new_achievements
            
            # Zapisz użytkownika
            if save_user(username, user_data):
                # Odblokuj moduły
                for module in new_unlocked:
                    unlock_module_for_user(username, module)
                print(f"  ✓ Zmigrowano użytkownika: {username}")
            else:
                print(f"  ✗ Błąd przy migracji użytkownika: {username}")
        
        print("Migracja użytkowników zakończona pomyślnie.")
    except Exception as e:
        print(f"Błąd przy migracji użytkowników: {e}")


def main():
    print("=" * 60)
    print("MIGRACJA DANYCH Z JSON DO MYSQL")
    print("=" * 60)
    print()
    print(f"Konfiguracja bazy danych:")
    print(f"  Host: {DB_CONFIG['host']}")
    print(f"  Database: {DB_CONFIG['database']}")
    print(f"  User: {DB_CONFIG['user']}")
    print()
    
    # Sprawdź połączenie
    connection = get_db_connection()
    if not connection:
        print("BŁĄD: Nie można połączyć się z bazą danych!")
        print("Upewnij się, że:")
        print("  1. MySQL jest uruchomiony")
        print("  2. Baza danych istnieje lub może być utworzona")
        print("  3. Użytkownik ma odpowiednie uprawnienia")
        print("  4. Dane w DB_CONFIG są poprawne")
        sys.exit(1)
    connection.close()
    
    # Inicjalizuj bazę danych
    print("Inicjalizacja bazy danych...")
    if not init_database():
        print("BŁĄD: Nie można zainicjalizować bazy danych!")
        sys.exit(1)
    
    print()
    
    # Migruj dane
    migrate_quiz_data()
    print()
    migrate_users()
    print()
    
    print("=" * 60)
    print("MIGRACJA ZAKOŃCZONA")
    print("=" * 60)
    print()
    print("Możesz teraz uruchomić aplikację quiz.py")
    print("Stare pliki JSON można zachować jako backup.")


if __name__ == "__main__":
    main()

