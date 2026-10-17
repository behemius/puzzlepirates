import cv2
import numpy as np
from mss import mss

points = []

def mouse_click(event, x, y, flags, param):
    global points
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(points) < 4:
            points.append((x, y))
            print(f"Zarejestrowano punkt: x={x}, y={y} (łącznie: {len(points)}/4)")

def order_points(pts):
    """Sortuje 4 punkty w kolejności: lewy-górny, prawy-górny, prawy-dolny, lewy-dolny"""
    rect = np.zeros((4, 2), dtype="float32")
    s = np.sum(pts, axis=1)
    rect[0] = pts[np.argmin(s)]  # Lewy-górny ma najmniejszą sumę x+y
    rect[2] = pts[np.argmax(s)]  # Prawy-dolny ma największą sumę x+y

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)] # Prawy-górny ma najmniejszą różnicę x-y
    rect[3] = pts[np.argmax(diff)] # Lewy-dolny ma największą różnicę x-y
    
    return rect.astype("int").tolist()

def calibrate_board():
    global points
    
    with mss() as sct:
        print("Robię zrzut ekranu do kalibracji...")
        sct_img = sct.grab(sct.monitors[1])
        frame = np.array(sct_img)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        
    window_name = "Kalibracja - Kliknij 4 rogi w dowolnej kolejności"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window_name, mouse_click)
    
    print("\n--- INSTRUKCJA ---")
    print("Kliknij 4 rogi złotej ramki planszy w DOWOLNEJ kolejności.")
    print("Po kliknięciu 4 punktów okno zamknie się automatycznie.\n")
    
    while True:
        display_frame = frame.copy()
        
        for i, pt in enumerate(points):
            cv2.circle(display_frame, pt, 6, (0, 0, 255), -1)
            cv2.putText(display_frame, str(i+1), (pt[0]+10, pt[1]-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
        if len(points) == 4:
            # Porządkujemy punkty, żeby narysować prostokąt bez względu na kolejność kliknięcia
            ordered_pts = order_points(np.array(points))
            pts = np.array(ordered_pts, np.int32)
            cv2.polylines(display_frame, [pts], True, (0, 255, 0), 2)
            
        cv2.imshow(window_name, display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or len(points) == 4:
            if len(points) == 4:
                cv2.waitKey(1000)
            break
            
    cv2.destroyAllWindows()
    
    if len(points) == 4:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        
        left = min(xs)
        top = min(ys)
        width = max(xs) - left
        height = max(ys) - top
        
        print("\nSukces! Wyliczone współrzędne dla Twojego monitora:")
        print("monitor_area = {")
        print(f'    "left": {left},')
        print(f'    "top": {top},')
        print(f'    "width": {width},')
        print(f'    "height": {height}')
        print("}")
    else:
        print("Anulowano kalibrację.")

if __name__ == "__main__":
    calibrate_board()