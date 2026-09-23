from __future__ import annotations

import ctypes
import gc
from ctypes import wintypes
import sys
import tkinter as tk

import webview
from PIL import Image, ImageDraw, ImageOps, ImageTk

from config import (
    APP_FULL_NAME,
    BRANDING_DIR,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    UI_INDEX_PATH,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
)


WINDOW_TITLE = APP_FULL_NAME

APP_ICON_SOURCE = BRANDING_DIR / "jam_icon.png"
APP_ICON_PATH = BRANDING_DIR / "jam_runtime.ico"
SPLASH_LOGO_PATH = BRANDING_DIR / "jam_bg.png"


# ============================================================
# WINDOWS / DPI
# ============================================================

def enable_dpi_awareness() -> None:
    if sys.platform != "win32":
        return

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass

    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def refresh_app_icon_from_brand() -> None:
    if not APP_ICON_SOURCE.exists():
        return

    try:
        if (
            APP_ICON_PATH.exists()
            and APP_ICON_PATH.stat().st_mtime_ns
            >= APP_ICON_SOURCE.stat().st_mtime_ns
        ):
            return
    except OSError:
        pass

    try:
        source = Image.open(
            APP_ICON_SOURCE
        ).convert("RGBA")

        side = max(
            source.width,
            source.height,
        )

        square = Image.new(
            "RGBA",
            (side, side),
            (0, 0, 0, 0),
        )

        square.alpha_composite(
            source,
            (
                (side - source.width) // 2,
                (side - source.height) // 2,
            ),
        )

        icon_image = ImageOps.contain(
            square,
            (256, 256),
            Image.Resampling.LANCZOS,
        )

        APP_ICON_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        icon_image.save(
            APP_ICON_PATH,
            format="ICO",
            sizes=[
                (16, 16),
                (24, 24),
                (32, 32),
                (48, 48),
                (64, 64),
                (128, 128),
                (256, 256),
            ],
        )

    except Exception:
        pass


def set_windows_app_identity() -> None:
    if sys.platform != "win32":
        return

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "Farouk.JAM.JobApplicationManager"
        )
    except Exception:
        pass


def apply_windows_window_icon(
    title: str,
) -> None:
    if (
        sys.platform != "win32"
        or not APP_ICON_PATH.exists()
    ):
        return

    try:
        user32 = ctypes.windll.user32

        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x0010
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1

        hwnd = user32.FindWindowW(
            None,
            title,
        )

        if not hwnd:
            current_pid = (
                ctypes
                .windll
                .kernel32
                .GetCurrentProcessId()
            )

            matches = []

            enum_proc_type = ctypes.WINFUNCTYPE(
                ctypes.c_bool,
                wintypes.HWND,
                wintypes.LPARAM,
            )

            def enum_proc(
                candidate,
                _lparam,
            ):
                process_id = wintypes.DWORD()

                user32.GetWindowThreadProcessId(
                    candidate,
                    ctypes.byref(
                        process_id
                    ),
                )

                if (
                    process_id.value
                    == current_pid
                    and user32.IsWindowVisible(
                        candidate
                    )
                ):
                    matches.append(
                        candidate
                    )

                return True

            user32.EnumWindows(
                enum_proc_type(
                    enum_proc
                ),
                0,
            )

            if matches:
                hwnd = matches[-1]

        if not hwnd:
            return

        big_icon = user32.LoadImageW(
            None,
            str(APP_ICON_PATH),
            IMAGE_ICON,
            64,
            64,
            LR_LOADFROMFILE,
        )

        small_icon = user32.LoadImageW(
            None,
            str(APP_ICON_PATH),
            IMAGE_ICON,
            32,
            32,
            LR_LOADFROMFILE,
        )

        if big_icon:
            user32.SendMessageW(
                hwnd,
                WM_SETICON,
                ICON_BIG,
                big_icon,
            )

        if small_icon:
            user32.SendMessageW(
                hwnd,
                WM_SETICON,
                ICON_SMALL,
                small_icon,
            )

    except Exception:
        pass


# ============================================================
# MONITOR DETECTION
# ============================================================

class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
    ]


def _fallback_monitor() -> dict:
    root = tk.Tk()
    root.withdraw()

    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()

    root.destroy()

    return {
        "left": 0,
        "top": 0,
        "right": width,
        "bottom": height,
        "width": width,
        "height": height,
        "primary": True,
    }


def _get_windows_monitors() -> list[dict]:
    if sys.platform != "win32":
        return []

    user32 = ctypes.windll.user32
    monitors: list[dict] = []

    callback_type = ctypes.WINFUNCTYPE(
        ctypes.c_int,
        wintypes.HMONITOR,
        wintypes.HDC,
        ctypes.POINTER(RECT),
        wintypes.LPARAM,
    )

    def callback(
        hmonitor,
        _hdc,
        _rect,
        _lparam,
    ):
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(
            MONITORINFO
        )

        user32.GetMonitorInfoW(
            hmonitor,
            ctypes.byref(info),
        )

        width = (
            info.rcWork.right
            - info.rcWork.left
        )

        height = (
            info.rcWork.bottom
            - info.rcWork.top
        )

        monitors.append(
            {
                "left": info.rcWork.left,
                "top": info.rcWork.top,
                "right": info.rcWork.right,
                "bottom": info.rcWork.bottom,
                "width": width,
                "height": height,
                "primary": bool(
                    info.dwFlags & 1
                ),
            }
        )

        return 1

    user32.EnumDisplayMonitors(
        0,
        0,
        callback_type(
            callback
        ),
        0,
    )

    return monitors


def choose_target_monitor() -> dict:
    try:
        monitors = (
            _get_windows_monitors()
        )

        if not monitors:
            return _fallback_monitor()

        secondary = [
            monitor
            for monitor in monitors
            if not monitor["primary"]
        ]

        if secondary:
            return max(
                secondary,
                key=lambda monitor: (
                    monitor["width"]
                    * monitor["height"]
                ),
            )

        return monitors[0]

    except Exception:
        return _fallback_monitor()


# ============================================================
# SPLASH SCREEN
# ============================================================

def _splash_geometry(
    monitor: dict,
    width: int,
    height: int,
) -> str:
    x = (
        monitor["left"]
        + (
            monitor["width"]
            - width
        )
        // 2
    )

    y = (
        monitor["top"]
        + (
            monitor["height"]
            - height
        )
        // 2
    )

    return (
        f"{width}x{height}"
        f"+{x}+{y}"
    )


def _build_rounded_splash_image(
    width: int,
    height: int,
    radius: int,
    transparent_key: str,
) -> Image.Image:
    key_rgb = tuple(
        int(
            transparent_key[
                i:i + 2
            ],
            16,
        )
        for i in (
            1,
            3,
            5,
        )
    )

    canvas = Image.new(
        "RGB",
        (
            width,
            height,
        ),
        key_rgb,
    )

    rounded_mask = Image.new(
        "L",
        (
            width,
            height,
        ),
        0,
    )

    mask_draw = ImageDraw.Draw(
        rounded_mask
    )

    mask_draw.rounded_rectangle(
        (
            0,
            0,
            width - 1,
            height - 1,
        ),
        radius=radius,
        fill=255,
    )

    splash_surface = Image.new(
        "RGB",
        (
            width,
            height,
        ),
        "#121720",
    )

    if SPLASH_LOGO_PATH.exists():
        try:
            wallpaper = Image.open(
                SPLASH_LOGO_PATH
            ).convert("RGB")

            splash_surface = ImageOps.fit(
                wallpaper,
                (
                    width,
                    height,
                ),
                method=Image.Resampling.LANCZOS,
                centering=(
                    0.5,
                    0.5,
                ),
            )
        except Exception:
            pass

    canvas.paste(
        splash_surface,
        (
            0,
            0,
        ),
        rounded_mask,
    )

    return canvas


def show_splash(
    monitor: dict,
    duration_ms: int = 1250,
) -> None:
    splash_width = 680
    splash_height = 390
    corner_radius = 28
    transparent_key = "#FF00FF"

    root = tk.Tk()

    root.overrideredirect(
        True
    )
    root.resizable(
        False,
        False,
    )
    root.configure(
        bg=transparent_key,
    )
    root.attributes(
        "-topmost",
        True,
    )

    root.geometry(
        _splash_geometry(
            monitor,
            splash_width,
            splash_height,
        )
    )

    if sys.platform == "win32":
        try:
            root.wm_attributes(
                "-transparentcolor",
                transparent_key,
            )
        except Exception:
            pass

    canvas = tk.Canvas(
        root,
        width=splash_width,
        height=splash_height,
        bg=transparent_key,
        highlightthickness=0,
        borderwidth=0,
    )

    canvas.pack(
        fill="both",
        expand=True,
    )

    splash_image = (
        _build_rounded_splash_image(
            splash_width,
            splash_height,
            corner_radius,
            transparent_key,
        )
    )

    photo_reference = (
        ImageTk.PhotoImage(
            splash_image
        )
    )

    canvas.create_image(
        0,
        0,
        anchor="nw",
        image=photo_reference,
    )

    canvas._jam_splash_photo = (
        photo_reference
    )

    track_margin = 26
    track_left = track_margin
    track_right = (
        splash_width
        - track_margin
    )
    track_top = (
        splash_height
        - 12
    )
    track_bottom = (
        splash_height
        - 7
    )
    track_radius = 3

    _canvas_rounded_rectangle(
        canvas,
        track_left,
        track_top,
        track_right,
        track_bottom,
        track_radius,
        fill="#2B303A",
        outline="",
    )

    loading_bar = (
        _canvas_rounded_rectangle(
            canvas,
            track_left,
            track_top,
            track_left + 4,
            track_bottom,
            track_radius,
            fill="#D0AA70",
            outline="",
        )
    )

    steps = 90

    interval = max(
        10,
        duration_ms // steps,
    )

    usable_width = (
        track_right
        - track_left
    )

    def animate(
        step: int = 0,
    ) -> None:
        progress = (
            step
            / steps
        )

        current_right = (
            track_left
            + max(
                4,
                int(
                    usable_width
                    * progress
                ),
            )
        )

        canvas.coords(
            loading_bar,
            *_rounded_rectangle_points(
                track_left,
                track_top,
                current_right,
                track_bottom,
                track_radius,
            ),
        )

        if step < steps:
            root.after(
                interval,
                animate,
                step + 1,
            )

    animate()

    root.after(
        duration_ms,
        root.destroy,
    )

    root.mainloop()

    # IMPORTANT:
    # Tk/Tcl objects must die on the thread that created them.
    # The splash used to leave Python/Tk objects alive until a later garbage
    # collection. pywebview API calls run on worker threads, so those stale
    # splash objects could be finalized there and terminate JAM with:
    #
    #   Tcl_AsyncDelete: async handler deleted by the wrong thread
    #
    # Explicitly release every splash reference and collect it here, while we
    # are still on the main startup thread and before pywebview is created.
    try:
        canvas._jam_splash_photo = None
    except Exception:
        pass

    photo_reference = None
    splash_image = None
    canvas = None
    root = None

    gc.collect()


def _rounded_rectangle_points(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    radius: float,
) -> list[float]:
    radius = max(
        0,
        min(
            radius,
            (
                x2
                - x1
            )
            / 2,
            (
                y2
                - y1
            )
            / 2,
        ),
    )

    return [
        x1 + radius,
        y1,
        x2 - radius,
        y1,
        x2,
        y1,
        x2,
        y1 + radius,
        x2,
        y2 - radius,
        x2,
        y2,
        x2 - radius,
        y2,
        x1 + radius,
        y2,
        x1,
        y2,
        x1,
        y2 - radius,
        x1,
        y1 + radius,
        x1,
        y1,
        x1 + radius,
        y1,
    ]


def _canvas_rounded_rectangle(
    canvas: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    radius: float,
    **kwargs,
):
    points = (
        _rounded_rectangle_points(
            x1,
            y1,
            x2,
            y2,
            radius,
        )
    )

    return canvas.create_polygon(
        points,
        smooth=True,
        splinesteps=36,
        **kwargs,
    )


# ============================================================
# APPLICATION STARTUP
# ============================================================

def launch_application(
    bridge,
) -> None:
    enable_dpi_awareness()
    refresh_app_icon_from_brand()
    set_windows_app_identity()

    monitor = choose_target_monitor()

    # Exactly like the stable CVM startup:
    # finish the native splash before pywebview exists.
    show_splash(
        monitor
    )

    window = webview.create_window(
        WINDOW_TITLE,
        url=UI_INDEX_PATH.resolve().as_uri(),
        js_api=bridge,
        hidden=True,
        x=monitor["left"],
        y=monitor["top"],
        width=DEFAULT_WINDOW_WIDTH,
        height=DEFAULT_WINDOW_HEIGHT,
        min_size=(
            WINDOW_MIN_WIDTH,
            WINDOW_MIN_HEIGHT,
        ),
        background_color="#111827",
        text_select=True,
    )

    bridge._set_main_window(
        window
    )

    def on_closing():
        # If JAM itself closes, destroy an open Capture Mode window
        # without trying to restore the main window.
        try:
            bridge._close_capture_for_shutdown()
        except Exception:
            pass

        return True

    try:
        window.events.closing += (
            on_closing
        )
    except Exception:
        pass

    def after_start():
        try:
            window.show()
        except Exception:
            pass

        try:
            window.maximize()
        except Exception:
            pass

        try:
            apply_windows_window_icon(
                WINDOW_TITLE
            )
        except Exception:
            pass

    webview.start(
        after_start,
        debug=False,
    )
