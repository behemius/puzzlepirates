import os
import cv2
import numpy as np
from mss import mss

# Współrzędne planszy
monitor_area = {
    "left": 190,
    "top": 198,
    "width": 544,
    "height": 1086
}

COLS = 6
ROWS = 12

def load_templates():
    """Wczytuje szablony normalne oraz podwodne"""
    templates_normal = {}
    templates_underwater = {}
    
    # Przykładowe wczytywanie (zakładamy, że masz foldery templates/normal i templates/underwater)
    # Możesz dostosować nazwy plików do swoich szablonów
    normal_dir = "templates/normal"
    underwater_dir = "templates/underwater"
    
    if os.path.exists(normal_dir):
        for fname in os.listdir(normal_dir):
            if fname.endswith(".png"):
                path = os.path.join(normal_dir, fname)
                img = cv2.imread(path, cv2.IMREAD_COLOR)
                # Bierzemy tylko środek szablonu do porównań
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

def recognize_board():
    templates_normal, templates_underwater = load_templates()
    
    if not templates_normal:
        print("Brak szablonów w folderzie templates/normal! Najpierw zapisz szablony.")
        return

    with mss() as sct:
        print("Uruchomiono silnik bota. Naciśnij 'q', aby wyjść.")
        
        while True:
            # 1. Zrzut ekranu planszy
            sct_img = sct.grab(monitor_area)
            frame = np.array(sct_img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
            h, w, _ = frame.shape
            cell_w = w / COLS
            cell_h = h / ROWS
            
            board_matrix = [[None for _ in range(COLS)] for _ in range(ROWS)]
            
            # 2. Skanowanie siatki
            for r in range(ROWS):
                # Przykład: wiersze od 8 w dół są pod wodą (możemy to precyzyjnie dostosować)
                is_underwater = r >= 8 
                current_templates = templates_underwater if is_underwater else templates_normal
                
                for c in range(COLS):
                    x1 = int(c * cell_w)
                    y1 = int(r * cell_h)
                    x2 = int((c + 1) * cell_w)
                    y2 = int((r + 1) * cell_h)
                    
                    cell_img = frame[y1:y2, x1:x2]
                    
                    # Wycinamy WYŁĄCZNIE ŚRODEK kafelka (np. środkowe 50%)
                    ch, cw, _ = cell_img.shape
                    cell_center = cell_img[int(ch*0.25):int(ch*0.75), int(cw*0.25):int(cw*0.75)]
                    
                    best_match_name = "UNKNOWN"
                    highest_val = -1
                    
                    # Dopasowanie szablonu (Template Matching)
                    for name, templ in current_templates.items():
                        # Upewniamy się, że rozmiary pozwalają na dopasowanie
                        if cell_center.shape[0] >= templ.shape[0] and cell_center.shape[1] >= templ.shape[1]:
                            res = cv2.matchTemplate(cell_center, templ, cv2.TM_CCOEFF_NORMED)
                            _, max_val, _, _ = cv2.minMaxLoc(res)
                            if max_val > highest_val:
                                highest_val = max_val
                                best_match_name = name if max_val > 0.75 else "UNKNOWN"
                                
                    board_matrix[r][c] = best_match_name
                    
                    # Rysujemy wynik na podglądzie
                    cv2.putText(frame, best_match_name[:3], (x1 + 10, y1 + int(cell_h/2)), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

            cv2.imshow("Bot - Stan Planszy", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    recognize_board()