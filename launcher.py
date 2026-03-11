"""
Графический лаунчер TgBot: запуск/остановка бота и статус Ollama.
Запуск: python launcher.py  (или двойной клик по launcher.py)
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

        self.title("TgBot — Паша Техник")
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

        self._refresh()

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
            subprocess.Popen(
                [sys.executable, str(BOT_SCRIPT)],
                cwd=str(PROJECT_ROOT),
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
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
