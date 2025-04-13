import multiprocessing
from app.main_window import run_main_window_sync
from app.zoom_window import run_zoom_window_sync

if __name__ == "__main__":
    p1 = multiprocessing.Process(target=run_zoom_window_sync)
    p2 = multiprocessing.Process(target=run_main_window_sync)
    
    p1.start()
    p2.start()
    
    p1.join()
    p2.join()
