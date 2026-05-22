"""
record_and_run.py
Ghi man hinh trong khi chay CF4 test
"""
import mss
import cv2
import numpy as np
import subprocess
import threading
import time
import os

OUTPUT_FILE = "cf4_test_recording.avi"
FPS = 10
STOP_FLAG = threading.Event()


def record_screen():
    """Ghi man hinh vao file AVI."""
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Man hinh chinh
        width  = monitor["width"]
        height = monitor["height"]

        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter(OUTPUT_FILE, fourcc, FPS, (width, height))

        print(f"[RECORDER] Bat dau ghi: {width}x{height} @ {FPS}fps -> {OUTPUT_FILE}")
        frame_interval = 1.0 / FPS

        while not STOP_FLAG.is_set():
            t0 = time.time()
            img = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            out.write(frame)
            elapsed = time.time() - t0
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        out.release()
        print(f"[RECORDER] Da luu video: {OUTPUT_FILE}")


def run_tests():
    """Chay pytest CF4."""
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    result = subprocess.run(
        ["python", "-m", "pytest",
         "ShopeeFood_Automation_Test.py::TC_CF4_FoodyRedirect",
         "-v", "-s"],
        capture_output=False,
        env=env
    )
    return result.returncode


# ── Main ──────────────────────────────────────────────────────────────
recorder = threading.Thread(target=record_screen, daemon=True)
recorder.start()
time.sleep(1)  # Cho recorder khoi dong

print("[MAIN] Bat dau chay CF4 tests...")
exit_code = run_tests()

print("[MAIN] Tests xong! Dung ghi man hinh...")
STOP_FLAG.set()
recorder.join(timeout=5)

print(f"[MAIN] Ket qua test: {'PASS' if exit_code == 0 else 'FAIL'}")
print(f"[MAIN] Video da luu: {os.path.abspath(OUTPUT_FILE)}")
