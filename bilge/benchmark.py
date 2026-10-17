import time
import cv2
import numpy as np
from mss import mss

# Pełna lewa połówka ekranu 2K
monitor_area = {
    "left": 135,    # Zostaje bez zmian
    "top": 80,      # Zostaje bez zmian
    "width": 640,   # Szerokość na pełne 6 kolumn
    "height": 1200   # Zwiększona wysokość, żeby domknąć dół planszy
}

def run_benchmark():
    with mss() as sct:
        print("Rozpoczynam podgląd. Wejdź w grze w planszę bilgingu.")
        print("Naciśnij klawisz 's', aby zapisać zrzut planszy do pliku.")
        print("Naciśnij 'q', aby zamknąć.")
        
        frame_count = 0
        start_time = time.time()
        
        while True:
            loop_start = time.time()
            
            # Zrzut ekranu
            sct_img = sct.grab(monitor_area)
            frame = np.array(sct_img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
            cv2.imshow("Pelny podglad Puzzle Pirates", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                # Zapisujemy klatkę do pliku po naciśnięciu 's'
                cv2.imwrite("bilging_board_capture.png", frame)
                print("Zapisano zrzut ekranu do pliku 'bilging_board_capture.png'!")
            
            frame_count += 1
            elapsed = time.time() - start_time
            
            if elapsed >= 1.0:
                fps = frame_count / elapsed
                frame_time_ms = (time.time() - loop_start) * 1000
                print(f"Wydajność: {fps:.1f} FPS | Czas klatki: {frame_time_ms:.1f} ms")
                frame_count = 0
                start_time = time.time()

    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_benchmark()