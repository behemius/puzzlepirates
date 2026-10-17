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

def simulate_shift_col(board, c, direction):
    new_board = [row[:] for row in board]
    col_vals = [new_board[r][c] for r in range(ROWS)]
    if direction == "up":
        col_vals = col_vals[1:] + col_vals[:1]
    elif direction == "down":
        col_vals = col_vals[-1:] + col_vals[:-1]
    for r in range(ROWS):
        new_board[r][c] = col_vals[r]
    return new_board

def count_matches(board):
    matches = 0
    # Poziomo
    for r in range(ROWS):
        for c in range(COLS - 2):
            val = board[r][c]
            if val != "UNKNOWN" and val == board[r][c+1] and val == board[r][c+2]:
                matches += 1
    # Pionowo
    for r in range(ROWS - 2):
        for c in range(COLS):
            val = board[r][c]
            if val != "UNKNOWN" and val == board[r+1][c] and val == board[r+2][c]:
                matches += 1
    return matches

def simulate_shift_row(board, r, direction):
    """Symuluje przesunięcie wiersza w lewo ('left') lub w prawo ('right')"""
    new_board = [row[:] for row in board]
    row = new_board[r]
    if direction == "left":
        new_board[r] = row[1:] + row[:1]
    elif direction == "right":
        new_board[r] = row[-1:] + row[:-1]
    return new_board

def find_best_move(board):
    """Przeszukuje wyłącznie dozwolone ruchy poziome wierszy i wybiera najlepszy układ"""
    best_score = count_matches(board)
    best_move = None
    
    # Testujemy tylko przesunięcia wierszy w lewo i w prawo
    for r in range(ROWS):
        for direction in ["left", "right"]:
            sim_board = simulate_shift_row(board, r, direction)
            score = count_matches(sim_board)
            if score > best_score:
                best_score = score
                best_move = ("row", r, direction, best_score)
                
    return best_move

last_move = None
last_move_time = 0


def execute_move(move):
    global last_move, last_move_time
    move_type, index, direction, _ = move
    cell_w = monitor_area["width"] / COLS
    cell_h = monitor_area["height"] / ROWS
    
    y = monitor_area["top"] + int((index + 0.5) * cell_h)
    
    if direction == "left":
        click_x = monitor_area["left"] + int(0.2 * cell_w)
    else:
        click_x = monitor_area["left"] + monitor_area["width"] - int(0.2 * cell_w)
        
    pyautogui.click(click_x, y)
        
    last_move = (move[0], move[1], move[2])
    last_move_time = time.time()
    
    # Wydłużamy czas oczekiwania na fizyczną reakcję silnika gry i opadanie kafelków
    time.sleep(1.2)

def get_random_move():
    """Zwraca losowy ruch wierszem, gdy bot utknie w martwym punkcie"""
    r = random.randint(0, ROWS - 1)
    direction = random.choice(["left", "right"])
    return ("row", r, direction, 0)

def run_smart_bot():
    templates_normal, templates_underwater = load_templates()
    if not templates_normal and not templates_underwater:
        print("Brak szablonów w folderach!")
        return

    with mss() as sct:
        print("Inteligentny bot aktywny! Naciśnij 'q' w oknie podglądu, aby wyjść.")
        
        while True:
            time.sleep(0.1) # Dajmy chwilę procesorowi i buforowi ekranu
            sct_img = sct.grab(monitor_area)
            frame = np.array(sct_img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
            h, w, _ = frame.shape
            cell_w = w / COLS
            cell_h = h / ROWS
            
            board_matrix = [[None for _ in range(COLS)] for _ in range(ROWS)]
            
            # Dynamiczne sprawdzanie każdego kafelka w obu zestawach (normal i underwater)
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
                    
                   # Sprawdzamy szablony normalne
                    for name, templ in templates_normal.items():
                        if cell_center.shape[0] >= templ.shape[0] and cell_center.shape[1] >= templ.shape[1]:
                            res = cv2.matchTemplate(cell_center, templ, cv2.TM_CCOEFF_NORMED)
                            _, max_val, _, _ = cv2.minMaxLoc(res)
                            if max_val > highest_val:
                                highest_val = max_val
                                # Podnosimy próg z 0.7 na 0.82, żeby unikać pomyłek
                                best_match_name = name if max_val > 0.82 else "UNKNOWN"
                                
                    # Sprawdzamy szablony podwodne
                    for name, templ in templates_underwater.items():
                        if cell_center.shape[0] >= templ.shape[0] and cell_center.shape[1] >= templ.shape[1]:
                            res = cv2.matchTemplate(cell_center, templ, cv2.TM_CCOEFF_NORMED)
                            _, max_val, _, _ = cv2.minMaxLoc(res)
                            if max_val > highest_val:
                                highest_val = max_val
                                best_match_name = name if max_val > 0.82 else "UNKNOWN"
                                
                    board_matrix[r][c] = best_match_name
                    
            # Szukanie najlepszego ruchu
            best_move = find_best_move(board_matrix)
            
            if best_move:
                move_sig = (best_move[0], best_move[1], best_move[2])
                
                # Jeśli to ten sam ruch i minęło za mało czasu, albo utknęliśmy
                if move_sig == last_move and (time.time() - last_move_time) < 1.5:
                    print("Plansza zablokowana. Wykonuję losowy ruch ratunkowy...")
                    emergency_move = get_random_move()
                    execute_move(emergency_move)
                else:
                    print(f"Wykonuję ruch: {best_move}")
                    execute_move(best_move)
            else:
                # Jeśli solver w ogóle nie widzi żadnych punktowanych ruchów na planszy
                print("Brak ruchów dających punkty. Losuję ruch przmieszczenia...")
                emergency_move = get_random_move()
                execute_move(emergency_move)
            
            cv2.imshow("Bilging Bot - Dynamiczny", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_smart_bot()