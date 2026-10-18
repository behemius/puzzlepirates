import os
import time
import cv2
import numpy as np
from mss import mss
import pyautogui
import random

pyautogui.FAILSAFE = True

monitor_area = {
    "left": 190,
    "top": 198,
    "width": 544,
    "height": 1086
}

COLS = 6
ROWS = 12

def load_templates():
    templates_normal = {}
    templates_underwater = {}
    
    normal_dir = "templates/normal"
    underwater_dir = "templates/underwater"
    
    if os.path.exists(normal_dir):
        for fname in os.listdir(normal_dir):
            if fname.endswith(".png"):
                path = os.path.join(normal_dir, fname)
                img = cv2.imread(path, cv2.IMREAD_COLOR)
                h, w, _ = img.shape
                center_crop = img[int(h*0.25):int(h*0.75), int(w*0.25):int(w*0.75)]
                templates_normal[fname.split('.')[0]] = center_crop
                
    if os.path.exists(underwater_dir):
        for fname in os.listdir(underwater_dir):
            if fname.endswith(".png"):
                path = os.path.join(underwater_dir, fname)
                img = cv2.imread(path, cv2.IMREAD_COLOR)
                h, w, _ = img.shape
                center_crop = img[int(h*0.25):int(h*0.75), int(w*0.25):int(w*0.75)]
                templates_underwater[fname.split('.')[0]] = center_crop
                
    return templates_normal, templates_underwater

def simulate_click_cell(board, r, c):
    """
    Symuluje kliknięcie w konkretną komórkę (r, c):
    Zamienia miejscami kafelek w kolumnie c z kolumną c+1 (lub c-1, jeśli to prawy brzeg).
    """
    new_board = [row[:] for row in board]
    row = new_board[r]
    
    target_c = c + 1 if c < COLS - 1 else c - 1
    row[c], row[target_c] = row[target_c], row[c]
    new_board[r] = row
    
    return new_board

def evaluate_board(board):
    """
    Ocenia planszę pod kątem gotowych dopasowań (3+ w linii w poziomie lub pionie).
    """
    score = 0
    
    # Poziomo
    for r in range(ROWS):
        c = 0
        while c < COLS:
            val = board[r][c]
            if val == "UNKNOWN":
                c += 1
                continue
            length = 1
            while c + length < COLS and board[r][c + length] == val:
                length += 1
            
            if length >= 3:
                score += length * 10000
            elif length == 2:
                score += 100
            c += length

    # Pionowo
    for c in range(COLS):
        r = 0
        while r < ROWS:
            val = board[r][c]
            if val == "UNKNOWN":
                r += 1
                continue
            length = 1
            while r + length < ROWS and board[r + length][c] == val:
                length += 1
            
            if length >= 3:
                score += length * 10000
            elif length == 2:
                score += 100
            r += length

    return score

def find_best_moves_ranked(board):
    """
    Zwraca ranking ruchów oparty na realnym przyroście punktów (delta).
    Promuje tylko te kliknięcia, które tworzą nowe trójki!
    """
    base_score = evaluate_board(board)
    all_scored_moves = []
    
    for r in range(ROWS):
        for c in range(COLS):
            sim_board = simulate_click_cell(board, r, c)
            score_after = evaluate_board(sim_board)
            
            # Liczymy realny zysk z ruchu (delta)
            score_gain = score_after - base_score
            
            # Bierzemy pod uwagę tylko te ruchy, które faktycznie coś dają lub poprawiają układ
            all_scored_moves.append(("click", r, c, score_gain))
            
    # Sortujemy malejąco po największym zysku punktowym
    all_scored_moves.sort(key=lambda x: x[3], reverse=True)
    return all_scored_moves

recent_moves = []

def execute_move(move):
    global recent_moves
    _, r, c, _ = move
    cell_w = monitor_area["width"] / COLS
    cell_h = monitor_area["height"] / ROWS
    
    # Klikamy w środek wybranej komórki
    x = monitor_area["left"] + int((c + 0.5) * cell_w)
    y = monitor_area["top"] + int((r + 0.5) * cell_h)
    
    pyautogui.click(x, y)
    
    # Krótka pauza na animację gry i opadanie kafelków
    time.sleep(0.8)

def get_random_move():
    r = random.randint(0, ROWS - 1)
    c = random.randint(0, COLS - 1)
    return ("click", r, c, 0)

def run_smart_bot():
    global recent_moves
    
    templates_normal, templates_underwater = load_templates()
    if not templates_normal and not templates_underwater:
        print("Brak szablonów w folderach!")
        return

    with mss() as sct:
        print("Bot Bilging (Cell Clicker) aktywny! Naciśnij 'q' w oknie podglądu, aby wyjść.")
        
        while True:
            time.sleep(0.1)
            sct_img = sct.grab(monitor_area)
            frame = np.array(sct_img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
            h, w, _ = frame.shape
            cell_w = w / COLS
            cell_h = h / ROWS
            
            board_matrix = [[None for _ in range(COLS)] for _ in range(ROWS)]
            
            for r in range(ROWS):
                for c in range(COLS):
                    x1 = int(c * cell_w)
                    y1 = int(r * cell_h)
                    x2 = int((c + 1) * cell_w)
                    y2 = int((r + 1) * cell_h)
                    
                    cell_img = frame[y1:y2, x1:x2]
                    ch, cw, _ = cell_img.shape
                    cell_center = cell_img[int(ch*0.25):int(ch*0.75), int(cw*0.25):int(cw*0.75)]
                    
                    best_match_name = "UNKNOWN"
                    highest_val = -1
                    
                    # Sprawdzamy szablony normalne (próg 0.72)
                    for name, templ in templates_normal.items():
                        if cell_center.shape[0] >= templ.shape[0] and cell_center.shape[1] >= templ.shape[1]:
                            res = cv2.matchTemplate(cell_center, templ, cv2.TM_CCOEFF_NORMED)
                            _, max_val, _, _ = cv2.minMaxLoc(res)
                            if max_val > highest_val:
                                highest_val = max_val
                                best_match_name = name if max_val > 0.72 else "UNKNOWN"
                                
                    # Sprawdzamy szablony podwodne (próg 0.72)
                    for name, templ in templates_underwater.items():
                        if cell_center.shape[0] >= templ.shape[0] and cell_center.shape[1] >= templ.shape[1]:
                            res = cv2.matchTemplate(cell_center, templ, cv2.TM_CCOEFF_NORMED)
                            _, max_val, _, _ = cv2.minMaxLoc(res)
                            if max_val > highest_val:
                                highest_val = max_val
                                best_match_name = name if max_val > 0.72 else "UNKNOWN"
                                
                    board_matrix[r][c] = best_match_name
            
            # Diagnostyka widoku w konsoli
            print("\n--- Aktualny widok bota ---")
            for row in board_matrix:
                print([str(cell)[:3] if cell != "UNKNOWN" else "---" for cell in row])
            
            # Pobieramy ranking ruchów (kliknięć)
            ranked_moves = find_best_moves_ranked(board_matrix)
            
            # Wybieramy najlepszy ruch, który nie jest w świeżej historii zapętleń
            chosen_move = None
            for move in ranked_moves:
                move_signature = (move[1], move[2]) # (wiersz, kolumna)
                if move_signature not in recent_moves:
                    chosen_move = move
                    break
            
            if chosen_move:
                move_signature = (chosen_move[1], chosen_move[2])
                print(f"Wykonuję kliknięcie w komórkę: wiersz {chosen_move[1]}, kolumna {chosen_move[2]} (wynik: {chosen_move[3]})")
                execute_move(chosen_move)
                
                recent_moves.append(move_signature)
                if len(recent_moves) > 6:
                    recent_moves.pop(0)
            else:
                print("Brak unikalnych ruchów. Czyszczę historię i wykonuję losowe kliknięcie...")
                recent_moves.clear()
                emergency_move = get_random_move()
                execute_move(emergency_move)
            
            cv2.imshow("Bilging Bot - Clicker", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_smart_bot()