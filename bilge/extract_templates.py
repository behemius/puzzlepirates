import os
import cv2
import numpy as np
from mss import mss

# Twoje ostateczne, dopasowane współrzędne planszy
monitor_area = {
    "left": 190,
    "top": 200,
    "width": 547,
    "height": 1083
}

COLS = 6
ROWS = 12

def extract_tiles():
    # Tworzymy folder na szablony, jeśli nie istnieje
    os.makedirs("templates", exist_ok=True)
    
    with mss() as sct:
        print("Uruchomiono ekstraktor szablonów.")
        print("Wejdź w grze na planszę bilgingu, ustaw się i naciśnij klawisz 'c', aby zapisać kafelki.")
        print("Naciśnij 'q', aby wyjść.")
        
        while True:
            # 1. Zrzut ekranu planszy
            sct_img = sct.grab(monitor_area)
            frame = np.array(sct_img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
            display_frame = frame.copy()
            h, w, _ = frame.shape
            cell_w = w / COLS
            cell_h = h / ROWS
            
            # Rysujemy delikatną siatki dla orientacji
            for r in range(ROWS + 1):
                y = int(r * cell_h)
                cv2.line(display_frame, (0, y), (w, y), (0, 255, 0), 1)
            for c in range(COLS + 1):
                x = int(c * cell_w)
                cv2.line(display_frame, (x, 0), (x, h), (0, 255, 0), 1)
                
            cv2.imshow("Ekstraktor Szablonów - wciśnij 'c'", display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                # 2. Piekielnie precyzyjne cięcie każdego kafelka
                counter = 0
                for r in range(ROWS):
                    for c in range(COLS):
                        x1 = int(c * cell_w)
                        y1 = int(r * cell_h)
                        x2 = int((c + 1) * cell_w)
                        y2 = int((r + 1) * cell_h)
                        
                        # Wycinamy kafelek z macierzy obrazu
                        tile = frame[y1:y2, x1:x2]
                        
                        # Opcjonalnie: możemy lekko przyciąć krawędzie kafelka (padding), 
                        # żeby algorytm dopasowywania nie brał pod uwagę czarnych linii z siatki
                        pad = 4
                        if tile.shape[0] > 2*pad and tile.shape[1] > 2*pad:
                            tile = tile[pad:-pad, pad:-pad]
                            
                        filename = f"templates/tile_r{r}_c{c}.png"
                        cv2.imwrite(filename, tile)
                        counter += 1
                        
                print(f"Sukces! Zapisano {counter} kafelków do folderu 'templates/'.")
                
    cv2.destroyAllWindows()

if __name__ == "__main__":
    extract_tiles()