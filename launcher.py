"""
Графический лаунчер TgBot: запуск/остановка бота и статус Ollama.
Запуск без консоли: pythonw launcher.py  (или двойной клик по «Запуск бота.bat»).
"""
from __future__ import annotations

import os
import sys
import subprocess
import threading
from pathlib import Path

try:
    import customtkinter as ctk
except ImportError as e:
    err = str(e)
    if "tkinter" in err.lower():
        print("Не найден модуль tkinter. Установите его или переустановите Python с компонентом tcl/tk.")
        print("Либо используйте скрипт: run_bot.ps1 start | stop | status | restart")
    else:
        print("Установите: pip install customtkinter")
    sys.exit(1)

try:
    import psutil
except ImportError:
    print("Установите: pip install psutil")
    sys.exit(1)

try:
    import httpx
except ImportError:
    httpx = None

try:
    import pystray
    from PIL import Image
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

# Корень проекта — папка, где лежит launcher.py
PROJECT_ROOT = Path(__file__).resolve().parent
BOT_SCRIPT = PROJECT_ROOT / "bot.py"
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "gemma2:9b"


def get_bot_pids() -> list[int]:
    """Найти PID процессов python, запустивших bot.py."""
    pids = []
    for p in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmdline = p.info.get("cmdline") or []
            if isinstance(cmdline, (list, tuple)):
                cmd = " ".join(str(x) for x in cmdline)
            else:
                cmd = str(cmdline)
            if "bot.py" in cmd and "python" in cmd.lower():
                pids.append(p.info["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return pids


def get_ollama_status() -> tuple[bool, bool]:
    """(Ollama доступна?, модель gemma2:9b найдена?)"""
    if not httpx:
        return False, False
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        r.raise_for_status()
        data = r.json()
        models = [m.get("name", "") for m in data.get("models", [])]
        found = any(OLLAMA_MODEL in m or m == OLLAMA_MODEL for m in models)
        return True, found
    except Exception:
        return False, False


class LauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.title("TgBot — Митрич Суровый")
        self.geometry("420x380")
        self.minsize(380, 340)
        self._after_id = None

        # Заголовок
        title = ctk.CTkLabel(
            self,
            text="TgBot Launcher",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.pack(pady=(20, 8))

        subtitle = ctk.CTkLabel(
            self,
            text="Запуск бота и проверка Ollama",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        subtitle.pack(pady=(0, 20))

        # Статус
        self.frame_status = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_status.pack(fill="x", padx=24, pady=(0, 16))

        self.label_bot = ctk.CTkLabel(
            self.frame_status,
            text="Бот: —",
            font=ctk.CTkFont(size=14),
        )
        self.label_bot.pack(anchor="w")

        self.label_ollama = ctk.CTkLabel(
            self.frame_status,
            text="Ollama: —",
            font=ctk.CTkFont(size=14),
        )
        self.label_ollama.pack(anchor="w")

        self.label_model = ctk.CTkLabel(
            self.frame_status,
            text="Модель: —",
            font=ctk.CTkFont(size=14),
        )
        self.label_model.pack(anchor="w")

        # Кнопки
        self.frame_buttons = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_buttons.pack(fill="x", padx=24, pady=12)

        self.btn_start = ctk.CTkButton(
            self.frame_buttons,
            text="Запустить бота",
            command=self._on_start,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color="#2e7d32",
            hover_color="#1b5e20",
        )
        self.btn_start.pack(fill="x", pady=4)

        self.btn_stop = ctk.CTkButton(
            self.frame_buttons,
            text="Остановить бота",
            command=self._on_stop,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color="#c62828",
            hover_color="#b71c1c",
        )
        self.btn_stop.pack(fill="x", pady=4)

        self.btn_restart = ctk.CTkButton(
            self.frame_buttons,
            text="Перезапустить бота",
            command=self._on_restart,
            height=36,
            font=ctk.CTkFont(size=13),
        )
        self.btn_restart.pack(fill="x", pady=4)

        self.btn_refresh = ctk.CTkButton(
            self.frame_buttons,
            text="Обновить статус",
            command=self._refresh,
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
        )
        self.btn_refresh.pack(fill="x", pady=(8, 4))

        # Сообщение внизу
        self.label_msg = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=360,
        )
        self.label_msg.pack(side="bottom", pady=(8, 16))

        self._tray_icon = None
        if TRAY_AVAILABLE:
            self._setup_tray()
            self.protocol("WM_DELETE_WINDOW", self._hide_to_tray)
            self.bind("<Unmap>", self._on_unmap)

        self._refresh()

    def _setup_tray(self) -> None:
        """Иконка в трее: Открыть / Выход."""
        try:
            size = 64
            img = Image.new("RGB", (size, size), color=(55, 95, 140))
            for y in range(size):
                for x in range(size):
                    if (x - size // 2) ** 2 + (y - size // 2) ** 2 < (size // 3) ** 2:
                        img.putpixel((x, y), (80, 140, 200))
            menu = pystray.Menu(
                pystray.MenuItem("Открыть", self._show_from_tray, default=True),
                pystray.MenuItem("Выход", self._quit_from_tray),
            )
            self._tray_icon = pystray.Icon("tgbot", img, "TgBot — Митрич Суровый", menu=menu)
            threading.Thread(target=self._tray_icon.run_detached, daemon=True).start()
        except Exception:
            pass

    def _hide_to_tray(self) -> None:
        """Свернуть в трей (крестик или минимизация)."""
        self.withdraw()

    def _on_unmap(self, event) -> None:
        """При минимизации — убрать в трей вместо панели задач."""
        if self.state() == "iconic":
            self.after(10, self.withdraw)

    def _show_from_tray(self, *args) -> None:
        """Показать окно из трея (вызов из потока иконки)."""
        self.after(0, self._do_show_from_tray)

    def _do_show_from_tray(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()

    def _quit_from_tray(self, *args) -> None:
        """Выход из трея."""
        self.after(0, self._do_quit)

    def _do_quit(self) -> None:
        if self._tray_icon:
            try:
                self._tray_icon.stop()
            except Exception:
                pass
        self.destroy()
        sys.exit(0)

    def _set_msg(self, text: str) -> None:
        self.label_msg.configure(text=text)

    def _refresh(self) -> None:
        def do():
            pids = get_bot_pids()
            ollama_ok, model_ok = get_ollama_status()
            self.after(0, lambda: self._update_ui(pids, ollama_ok, model_ok))

        threading.Thread(target=do, daemon=True).start()

    def _update_ui(
        self,
        pids: list[int],
        ollama_ok: bool,
        model_ok: bool,
    ) -> None:
        if pids:
            self.label_bot.configure(
                text=f"Бот: запущен (PID: {', '.join(map(str, pids))})",
                text_color="#81c784",
            )
        else:
            self.label_bot.configure(
                text="Бот: не запущен",
                text_color="#e57373",
            )

        if ollama_ok:
            self.label_ollama.configure(text="Ollama: работает", text_color="#81c784")
        else:
            self.label_ollama.configure(
                text="Ollama: недоступна (запусти Ollama)",
                text_color="#e57373",
            )

        if model_ok:
            self.label_model.configure(
                text=f"Модель: {OLLAMA_MODEL} ✓",
                text_color="#81c784",
            )
        else:
            if ollama_ok:
                self.label_model.configure(
                    text=f"Модель: {OLLAMA_MODEL} не найдена",
                    text_color="#ffb74d",
                )
            else:
                self.label_model.configure(
                    text=f"Модель: —",
                    text_color="gray",
                )

    def _on_start(self) -> None:
        if get_bot_pids():
            self._set_msg("Бот уже запущен.")
            self._refresh()
            return
        if not BOT_SCRIPT.exists():
            self._set_msg(f"Файл не найден: {BOT_SCRIPT}")
            return
        try:
            flags = 0
            if os.name == "nt":
                flags = subprocess.CREATE_NO_WINDOW  # без отдельного окна консоли
            subprocess.Popen(
                [sys.executable, str(BOT_SCRIPT)],
                cwd=str(PROJECT_ROOT),
                creationflags=flags,
            )
            self._set_msg("Бот запускается…")
            self.after(2000, self._refresh)
        except Exception as e:
            self._set_msg(f"Ошибка: {e}")

    def _on_stop(self) -> None:
        pids = get_bot_pids()
        if not pids:
            self._set_msg("Бот не запущен.")
            self._refresh()
            return
        for pid in pids:
            try:
                p = psutil.Process(pid)
                p.terminate()
                p.wait(timeout=5)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        self._set_msg("Бот остановлен.")
        self._refresh()

    def _on_restart(self) -> None:
        self._on_stop()
        self.after(1500, self._on_start)
        self.after(3500, self._refresh)

    def _tick(self) -> None:
        self._refresh()
        self._after_id = self.after(10000, self._tick)

    def run(self) -> None:
        self._tick()
        self.mainloop()
        if self._after_id:
            self.after_cancel(self._after_id)


if __name__ == "__main__":
    app = LauncherApp()
    app.run()
