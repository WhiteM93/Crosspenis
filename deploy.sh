#!/usr/bin/env bash
# Деплой Crosspenis на Ubuntu: git pull, venv, зависимости, systemd, проверки.
# Запуск из корня репозитория: ./deploy.sh
# Первый раз: cp .env.example .env && nano .env

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$SCRIPT_DIR"
SERVICE_NAME="${SERVICE_NAME:-crosspenis}"
GIT_BRANCH="${GIT_BRANCH:-main}"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SERVICE_TEMPLATE="$APP_DIR/deploy/crosspenis.service"

# Пользователь, под которым крутится бот (владелец каталога или тот, кто вызвал sudo)
if [[ -n "${RUN_USER:-}" ]]; then
    :
elif [[ -n "${SUDO_USER:-}" && "$SUDO_USER" != "root" ]]; then
    RUN_USER="$SUDO_USER"
else
    RUN_USER="$(stat -c '%U' "$APP_DIR" 2>/dev/null || echo "$USER")"
fi

log()  { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m[OK]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[WARN]\033[0m %s\n' "$*"; }
fail() { printf '\033[1;31m[FAIL]\033[0m %s\n' "$*" >&2; exit 1; }

need_cmd() {
    command -v "$1" >/dev/null 2>&1 || fail "Не найдена команда: $1"
}

run_as_user() {
    if [[ "$(id -un)" == "$RUN_USER" ]]; then
        "$@"
    else
        sudo -u "$RUN_USER" -- "$@"
    fi
}

run_root() {
    if [[ "$(id -u)" -eq 0 ]]; then
        "$@"
    elif command -v sudo >/dev/null 2>&1; then
        sudo "$@"
    else
        fail "Нужны права root для systemd (запустите через sudo)"
    fi
}

git_update() {
    log "Обновление из git (ветка: $GIT_BRANCH)"
    need_cmd git

    if [[ ! -d "$APP_DIR/.git" ]]; then
        fail "Каталог $APP_DIR не является git-репозиторием"
    fi

    run_as_user git -C "$APP_DIR" fetch origin "$GIT_BRANCH"
    run_as_user git -C "$APP_DIR" checkout "$GIT_BRANCH"
    run_as_user git -C "$APP_DIR" pull --ff-only origin "$GIT_BRANCH"
    ok "Код обновлён: $(git -C "$APP_DIR" rev-parse --short HEAD) ($(git -C "$APP_DIR" log -1 --format='%s'))"
}

check_env() {
    log "Проверка .env"
    local env_file="$APP_DIR/.env"

    if [[ ! -f "$env_file" ]]; then
        if [[ -f "$APP_DIR/.env.example" ]]; then
            fail "Нет $env_file — создайте: cp .env.example .env && nano .env"
        fi
        fail "Нет $env_file — задайте TOKEN"
    fi

    # shellcheck disable=SC1090
    set -a
    source "$env_file"
    set +a

    local token="${TOKEN:-${BOT_TOKEN:-}}"
    if [[ -z "${token// }" ]]; then
        fail "В .env не задан TOKEN (или BOT_TOKEN)"
    fi

    # Windows CRLF в .env ломает токен в systemd/python
    if grep -q $'\r' "$env_file" 2>/dev/null; then
        warn "Убираю Windows-переносы строк в .env"
        sed -i 's/\r$//' "$env_file"
    fi
    ok ".env в порядке"
}

setup_venv() {
    log "Виртуальное окружение и зависимости"
    need_cmd python3

    local venv_dir="$APP_DIR/venv"
    local venv_python="$venv_dir/bin/python"
    local venv_pip="$venv_dir/bin/pip"

    if [[ -d "$venv_dir" ]] && [[ ! -x "$venv_python" || ! -x "$venv_pip" ]]; then
        warn "Битый venv — пересоздаю"
        rm -rf "$venv_dir"
    fi

    if [[ ! -x "$venv_python" ]]; then
        log "Создаю venv"
        if ! run_as_user python3 -m venv "$venv_dir"; then
            fail "Не удалось создать venv. Установите: sudo apt install -y python3-venv"
        fi
    fi

    if [[ ! -x "$venv_pip" ]]; then
        fail "В venv нет pip. Выполните: sudo apt install -y python3-venv && rm -rf $venv_dir && ./deploy.sh"
    fi

    run_as_user "$venv_python" -m pip install -q --upgrade pip
    run_as_user "$venv_python" -m pip install -q -r "$APP_DIR/requirements.txt"
    ok "Зависимости установлены"
}

smoke_test_app() {
    log "Проверка приложения (токен, импорты)"
    local venv_python="$APP_DIR/venv/bin/python"

    if ! run_as_user "$venv_python" -c "
from pathlib import Path
import os, sys
from dotenv import load_dotenv
load_dotenv(Path('${APP_DIR}') / '.env')
token = (os.environ.get('TOKEN') or os.environ.get('BOT_TOKEN') or '').strip()
if not token:
    print('TOKEN не загружен из .env', file=sys.stderr)
    sys.exit(1)
import aiogram  # noqa: F401
print('ok')
"; then
        fail "Бот не стартует даже вручную — проверьте .env и venv"
    fi
    ok "Приложение готово к запуску"
}

show_service_logs() {
    run_root systemctl status "$SERVICE_NAME" --no-pager -l || true
    echo ""
    log "Логи (journalctl -u $SERVICE_NAME -n 40):"
    run_root journalctl -u "$SERVICE_NAME" -n 40 --no-pager || true
}

install_systemd_unit() {
    log "Установка systemd unit ($SERVICE_NAME)"

    if [[ ! -f "$SERVICE_TEMPLATE" ]]; then
        fail "Не найден шаблон: $SERVICE_TEMPLATE"
    fi

    local tmp_unit
    tmp_unit="$(mktemp)"
    sed \
        -e "s|YOUR_USER|$RUN_USER|g" \
        -e "s|/home/YOUR_USER/crosspenis|$APP_DIR|g" \
        "$SERVICE_TEMPLATE" > "$tmp_unit"

    if [[ ! -f "$SERVICE_FILE" ]] || ! run_root cmp -s "$tmp_unit" "$SERVICE_FILE" 2>/dev/null; then
        run_root install -m 644 "$tmp_unit" "$SERVICE_FILE"
        run_root systemctl daemon-reload
        run_root systemctl enable "$SERVICE_NAME"
        ok "Unit обновлён и включён в автозагрузку"
    else
        ok "Unit без изменений"
    fi
    rm -f "$tmp_unit"
}

restart_service() {
    log "Перезапуск $SERVICE_NAME"
    if ! run_root systemctl restart "$SERVICE_NAME"; then
        warn "Не удалось запустить сервис — логи:"
        run_root journalctl -u "$SERVICE_NAME" -n 30 --no-pager || true
        fail "systemctl restart $SERVICE_NAME завершился с ошибкой"
    fi
    sleep 2
}

verify_deployment() {
    log "Проверка деплоя"

    local errors=0

    if run_root systemctl is-active --quiet "$SERVICE_NAME"; then
        ok "Сервис активен"
    else
        warn "Сервис не запущен — диагностика:"
        show_service_logs
        fail "Сервис не запущен — см. логи выше"
    fi

    if run_root systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
        ok "Автозапуск включён"
    else
        warn "Автозапуск не включён"
        errors=$((errors + 1))
    fi

    if [[ -x "$APP_DIR/venv/bin/python" ]]; then
        if run_as_user "$APP_DIR/venv/bin/python" -c "import aiogram; import dotenv" 2>/dev/null; then
            ok "Python-зависимости импортируются"
        else
            warn "Проблема с импортом зависимостей"
            errors=$((errors + 1))
        fi
    fi

    echo ""
    run_root systemctl status "$SERVICE_NAME" --no-pager -l || true
    echo ""
    log "Последние логи (journalctl -u $SERVICE_NAME -n 20):"
    run_root journalctl -u "$SERVICE_NAME" -n 20 --no-pager || true

    if [[ "$errors" -gt 0 ]]; then
        fail "Деплой завершён с предупреждениями ($errors)"
    fi
    ok "Деплой успешен"
}

main() {
    log "Crosspenis deploy"
    log "Каталог: $APP_DIR | Пользователь: $RUN_USER | Сервис: $SERVICE_NAME"

    git_update
    check_env
    setup_venv
    smoke_test_app
    install_systemd_unit
    restart_service
    verify_deployment
}

main "$@"
