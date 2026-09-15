#!/usr/bin/env bash
# Установка связки «Claude + Avito» на этот компьютер.
#
# Ставит два скилла в ~/.claude/skills:
#   avito-api        — доступ к Avito Business API (чужой, MIT, полный OpenAPI-спек)
#   avito-strategist — стратегия, аналитика и тексты объявлений (наш)
#
# Запуск:  bash avito/setup.sh

set -euo pipefail

SKILLS_DIR="${HOME}/.claude/skills"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_SKILL="${SKILLS_DIR}/avito-api"
STRATEGIST_SKILL="${SKILLS_DIR}/avito-strategist"

say() { printf '\n\033[1m%s\033[0m\n' "$1"; }
ok()  { printf '  ✓ %s\n' "$1"; }
warn(){ printf '  ! %s\n' "$1"; }

say "1. Проверяю, что нужно для работы"

for cmd in git python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "  ✗ не найден $cmd — установи его и запусти снова"
    exit 1
  fi
  ok "$cmd на месте"
done

mkdir -p "$SKILLS_DIR"
ok "папка скиллов: $SKILLS_DIR"

say "2. Ставлю доступ к Avito API"

if [ -d "${API_SKILL}/.git" ]; then
  git -C "$API_SKILL" pull --quiet --ff-only && ok "avito-api обновлён"
else
  rm -rf "$API_SKILL"
  git clone --quiet --depth 1 https://github.com/MissiaL/avito-api.git "$API_SKILL"
  ok "avito-api установлен"
fi

if [ -f "${API_SKILL}/references/avito-api-openapi.json" ]; then
  ok "спек на месте ($(du -h "${API_SKILL}/references/avito-api-openapi.json" | cut -f1))"
else
  warn "спек не нашёлся — проверь ${API_SKILL}"
fi

say "3. Ставлю стратега"

rm -rf "$STRATEGIST_SKILL"
cp -r "${HERE}/skills/avito-strategist" "$STRATEGIST_SKILL"
ok "avito-strategist установлен"

say "4. Ключи доступа"

ENV_FILE="${HERE}/.env"
if [ -f "$ENV_FILE" ]; then
  ok "файл avito/.env уже есть"
else
  cat > "$ENV_FILE" <<'ENVEOF'
# Ключи из кабинета Avito: Настройки -> Avito API -> регистрация приложения.
# Этот файл не попадает в репозиторий.
AVITO_CLIENT_ID=
AVITO_CLIENT_SECRET=
ENVEOF
  ok "создал avito/.env — впиши в него client_id и client_secret"
fi

say "5. Проверяю связь с Avito"

set +e
# shellcheck disable=SC1090
set -a; . "$ENV_FILE" 2>/dev/null; set +a

if [ -z "${AVITO_CLIENT_ID:-}" ] || [ -z "${AVITO_CLIENT_SECRET:-}" ]; then
  warn "ключи ещё не вписаны — впиши их в avito/.env и запусти скрипт снова"
else
  TOKEN_JSON=$(curl -sS -m 30 -X POST https://api.avito.ru/token/ \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=client_credentials&client_id=${AVITO_CLIENT_ID}&client_secret=${AVITO_CLIENT_SECRET}" 2>&1)

  if printf '%s' "$TOKEN_JSON" | grep -q access_token; then
    ok "связь есть, токен получен"
    TOKEN=$(printf '%s' "$TOKEN_JSON" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
    WHO=$(curl -sS -m 30 https://api.avito.ru/core/v1/accounts/self -H "Authorization: Bearer ${TOKEN}")
    printf '  ✓ кабинет: %s\n' "$(printf '%s' "$WHO" | python3 -c "import sys,json;d=json.load(sys.stdin);print('{} (id {})'.format(d.get('name','?'),d.get('id','?')))" 2>/dev/null || echo '?')"
  else
    warn "токен не получен. Ответ Avito:"
    printf '    %s\n' "$TOKEN_JSON" | head -3
    warn "проверь ключи в avito/.env и что в кабинете подключён платный тариф"
  fi
fi
set -e

say "Готово"
cat <<'DONEEOF'
  Перезапусти Claude Code, чтобы он увидел новые скиллы.

  Дальше просто говори обычными словами:
    «разбери мой авито»
    «почему по объявлению про ChatGPT не пишут»
    «напиши новое объявление под запрос "нейросети для маркетологов"»
    «куда вложить 3000 рублей на продвижение»
    «что ответить в чате»
DONEEOF
