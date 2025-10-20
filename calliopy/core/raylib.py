import ctypes

raylib = ctypes.CDLL("./clibs/libraylib.so")

# TODO: Windows
# raylib = ctypes.CDLL("raylib.dll")

raylib.InitWindow.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
raylib.InitWindow.restype = None

raylib.WindowShouldClose.argtypes = []
raylib.WindowShouldClose.restype = ctypes.c_bool

raylib.CloseWindow.argtypes = []
raylib.CloseWindow.restype = None

raylib.BeginDrawing.argtypes = []
raylib.BeginDrawing.restype = None

raylib.EndDrawing.argtypes = []
raylib.EndDrawing.restype = None

raylib.ClearBackground.argtypes = [ctypes.c_int]
raylib.ClearBackground.restype = None

raylib.SetTargetFPS.argtypes = [ctypes.c_int]
raylib.SetTargetFPS.restype = None

raylib.IsKeyPressed.argtypes = [ctypes.c_int]
raylib.IsKeyPressed.restype = ctypes.c_bool

raylib.DrawRectangle.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
raylib.DrawRectangle.restype = None

raylib.DrawRectangleLines.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
raylib.DrawRectangleLines.restype = None

raylib.DrawText.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
raylib.DrawText.restype = None

class Texture2D(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint),
        ("width", ctypes.c_int),
        ("height", ctypes.c_int),
        ("mipmaps", ctypes.c_int),
        ("format", ctypes.c_int)
    ]

raylib.LoadTexture.argtypes = [ctypes.c_char_p]
raylib.LoadTexture.restype = Texture2D

raylib.DrawTexture.argtypes = [Texture2D, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
raylib.DrawTexture.restype = None

raylib.UnloadTexture.argtypes = [Texture2D]
raylib.UnloadTexture.restype = None


class Vector2(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float)
    ]


class Rectangle(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("width", ctypes.c_float),
        ("height", ctypes.c_float)
    ]


raylib.DrawTextureEx.argtypes = [Texture2D, Vector2, ctypes.c_float, ctypes.c_float, ctypes.c_uint]
raylib.DrawTextureEx.restype = None

raylib.DrawTexturePro.argtypes = [Texture2D, Rectangle, Rectangle, Vector2, ctypes.c_float, ctypes.c_uint]
raylib.DrawTexturePro.restype = None

TRACELOGCALLBACK = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p)
raylib.SetTraceLogCallback.argtypes = [TRACELOGCALLBACK]
raylib.SetTraceLogCallback.restype = None

# Constants
RAYWHITE = 0xFFFFFFFF
BLACK = 0xFF000000
WHITE = 0xFFFFFFFF

KEY_ENTER = 257
KEY_ESCAPE = 256
KEY_1 = 49
KEY_2 = 50
KEY_3 = 51
KEY_4 = 52
KEY_5 = 53
KEY_6 = 54
KEY_7 = 55
KEY_8 = 56
KEY_9 = 57


class Raylib:
    def __init__(self) -> None:
        self._trace_callback = None

    def init_window(self, width: int, height: int, name: str) -> None:
        raylib.InitWindow(width, height, bytes(name, "utf-8"))

    def window_should_close(self) -> bool:
        return raylib.WindowShouldClose()

    def close_window(self) -> None:
        raylib.CloseWindow()

    def begin_drawing(self) -> None:
        raylib.BeginDrawing()

    def end_drawing(self) -> None:
        raylib.EndDrawing()

    def clear_background(self, color: int) -> None:
        raylib.ClearBackground(color)

    def set_target_fps(self, fps: int) -> None:
        raylib.SetTargetFPS(fps)

    def is_key_pressed(self, code: int) -> bool:
        return raylib.IsKeyPressed(code)

    def draw_rectangle(self, x: int, y: int, width: int, height: int, color: int) -> None:
        raylib.DrawRectangle(x, y, width, height, color)

    def draw_rectangle_lines(self, x: int, y: int, width: int, height: int, color: int) -> None:
        raylib.DrawRectangleLines(x, y, width, height, color)

    def draw_text(self, text: str, x: int, y: int, font_size: int, color: int) -> None:
        raylib.DrawText(bytes(text, "utf-8"), x, y, font_size, color)

    def load_texture(self, path: str) -> Texture2D:
        return raylib.LoadTexture(bytes(path, "utf-8"))

    def draw_texture(self, texture: Texture2D, x: int, y: int, color: int) -> None:
        raylib.DrawTexture(texture, x, y, color)

    def unload_texture(self, texture: Texture2D) -> None:
        raylib.UnloadTexture(texture)

    def draw_texture_ex(self, texture: Texture2D, pos: Vector2, rotation: float, scale: float, color: int) -> None:
        raylib.DrawTextureEx(texture, pos, rotation, scale, color)

    def draw_texture_pro(
        self,
        texture: Texture2D,
        src: Rectangle,
        dest: Rectangle,
        origin: Vector2,
        rotation: float,
        color: int
    ) -> None:
        raylib.DrawTexturePro(texture, src, dest, origin, rotation, color)

    def set_trace_log_callback(self, func):
        self._trace_callback = TRACELOGCALLBACK(func)
        raylib.SetTraceLogCallback(self._trace_callback)
