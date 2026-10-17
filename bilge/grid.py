import time
import cv2
import numpy as np
from mss import mss

# Twoje dopasowane współrzędne planszy bilgingu
monitor_area = {
    "left": 190,
    "top": 200,
    "width": 547,
    "height": 1083
}

# Parametry siatki bilgingu
COLS = 6
ROWS = 12

def run_grid_test():
    with mss() as sct:
        print("Uruchomiono test siatki bilgingu. Naciśnij 'q', aby wyjść.")
        
        while True:
            # 1. Zrzut ekranu precyzyjnego obszaru planszy
            sct_img = sct.grab(monitor_area)
            frame = np.array(sct_img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
            h, w, _ = frame.shape
            
            # 2. Obliczanie szerokości i wysokości pojedynczego kafelka
            cell_w = w / COLS
            cell_h = h / ROWS
            
            # 3. Rysowanie siatki na obrazie dla wizualnej weryfikacji
            for r in range(ROWS + 1):
                y = int(r * cell_h)
                cv2.line(frame, (0, y), (w, y), (0, 255, 0), 1) # Zielone poziome linie
                
            for c in range(COLS + 1):
                x = int(c * cell_w)
                cv2.line(frame, (x, 0), (x, h), (0, 255, 0), 1) # Zielone pionowe linie
                
            # Opcjonalnie: możemy zaznaczyć środki komórek
            for r in range(ROWS):
                for c in range(COLS):
                    cx = int((c + 0.5) * cell_w)
                    cy = int((r + 0.5) * cell_h)
                    cv2.circle(frame, (cx, cy), 3, (0, 0, 255), -1) # Czerwone kropki na środkach
            
            cv2.imshow("Siatka Bilgingu", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_grid_test()