#!/usr/bin/env bash
# =============================================================================
# Agent Harness — One-Command Installer
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/r3moteBee/agent-harness/main/deploy.sh | bash
#   # Or with options:
#   curl -fsSL https://raw.githubusercontent.com/r3moteBee/agent-harness/main/deploy.sh | bash -s -- --dir ~/agent-harness --port 80
# =============================================================================

set -euo pipefail

# ── Defaults ─────────────────────────────────────────────────────────────────
REPO_URL="https://github.com/r3moteBee/agent-harness.git"
INSTALL_DIR="${AGENT_HARNESS_DIR:-$HOME/agent-harness}"
HTTP_PORT="${AGENT_HARNESS_PORT:-80}"
LLM_BASE_URL="${LLM_BASE_URL:-}"
LLM_API_KEY="${LLM_API_KEY:-}"
LLM_MODEL="${LLM_MODEL:-gpt-4o}"
BRANCH="main"
SKIP_CONFIRM=false

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[info]${RESET}  $*"; }
success() { echo -e "${GREEN}[ok]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[warn]${RESET}  $*"; }
error()   { echo -e "${RED}[error]${RESET} $*" >&2; }
die()     { error "$*"; exit 1; }
header()  { echo -e "\n${BOLD}${BLUE}$*${RESET}"; }

# ── Parse arguments ───────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir)        INSTALL_DIR="$2"; shift 2 ;;
    --port)       HTTP_PORT="$2";   shift 2 ;;
    --api-key)    LLM_API_KEY="$2"; shift 2 ;;
    --model)      LLM_MODEL="$2";   shift 2 ;;
    --base-url)   LLM_BASE_URL="$2";shift 2 ;;
    --branch)     BRANCH="$2";      shift 2 ;;
    --yes|-y)     SKIP_CONFIRM=true; shift ;;
    --help|-h)
      echo "Usage: deploy.sh [options]"
      echo ""
      echo "Options:"
      echo "  --dir PATH       Installation directory (default: ~/agent-harness)"
      echo "  --port PORT      HTTP port (default: 80)"
      echo "  --api-key KEY    LLM API key (can also set LLM_API_KEY env var)"
      echo "  --model MODEL    LLM model name (default: gpt-4o)"
      echo "  --base-url URL   LLM provider base URL (default: OpenAI)"
      echo "  --branch NAME    Git branch to deploy (default: main)"
      echo "  --yes, -y        Skip confirmation prompts"
      echo ""
      echo "Environment variables (alternative to flags):"
      echo "  LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, AGENT_HARNESS_DIR, AGENT_HARNESS_PORT"
      exit 0
      ;;
    *) warn "Unknown option: $1"; shift ;;
  esac
done

# ── Banner ────────────────────────────────────────────────────────────────────
echo -e "${BOLD}"
echo "  ╔═══════════════════════════════════════════╗"
echo "  ║        Agent Harness  Installer           ║"
echo "  ║   Self-hosted AI Agent Framework v1.0.0   ║"
echo "  ╚═══════════════════════════════════════════╝"
echo -e "${RESET}"

# ── OS detection ──────────────────────────────────────────────────────────────
OS="unknown"
case "$(uname -s)" in
  Linux*)  OS="linux"  ;;
  Darwin*) OS="macos"  ;;
  CYGWIN*|MINGW*|MSYS*) OS="windows" ;;
esac
info "Detected OS: ${OS}"

# ── Requirement checks ────────────────────────────────────────────────────────
header "Checking requirements..."

check_cmd() {
  if command -v "$1" &>/dev/null; then
    success "$1 found ($(command -v "$1"))"
  else
    die "$1 is required but not installed. $2"
  fi
}

check_cmd git    "Install from https://git-scm.com"
check_cmd docker "Install from https://docs.docker.com/get-docker/"

# Check Docker Compose (plugin v2 or standalone v1)
if docker compose version &>/dev/null 2>&1; then
  success "docker compose (plugin) found"
elif command -v docker-compose &>/dev/null; then
  success "docker-compose (standalone) found"
  # Alias for the rest of the script
  alias docker-compose='docker compose'
else
  die "Docker Compose is required. Install from https://docs.docker.com/compose/install/"
fi

# Check Docker is running
if ! docker info &>/dev/null; then
  die "Docker daemon is not running. Start Docker and try again."
fi
success "Docker daemon is running"

# ── Confirmation ──────────────────────────────────────────────────────────────
header "Installation plan"
echo -e "  Directory : ${BOLD}${INSTALL_DIR}${RESET}"
echo -e "  HTTP Port : ${BOLD}${HTTP_PORT}${RESET}"
echo -e "  LLM Model : ${BOLD}${LLM_MODEL}${RESET}"
echo ""

if [[ "$SKIP_CONFIRM" == false ]]; then
  read -rp "Proceed with installation? [Y/n] " confirm
  confirm="${confirm:-Y}"
  [[ "$confirm" =~ ^[Yy]$ ]] || { info "Aborted."; exit 0; }
fi

# ── Clone or update ───────────────────────────────────────────────────────────
header "Fetching code..."

if [[ -d "$INSTALL_DIR/.git" ]]; then
  info "Existing installation found at ${INSTALL_DIR}. Updating..."
  git -C "$INSTALL_DIR" fetch origin
  git -C "$INSTALL_DIR" checkout "$BRANCH"
  git -C "$INSTALL_DIR" pull origin "$BRANCH"
  success "Updated to latest ${BRANCH}"
else
  info "Cloning to ${INSTALL_DIR}..."
  git clone --branch "$BRANCH" --depth 1 "$REPO_URL" "$INSTALL_DIR"
  success "Cloned successfully"
fi

cd "$INSTALL_DIR"

# ── Environment setup ─────────────────────────────────────────────────────────
header "Configuring environment..."

if [[ ! -f .env ]]; then
  cp .env.example .env
  success "Created .env from template"
else
  info ".env already exists — skipping (won't overwrite)"
fi

# Generate secure keys if not already set
generate_key() {
  python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null \
    || openssl rand -hex 32 2>/dev/null \
    || cat /dev/urandom | tr -dc 'a-f0-9' | head -c 64
}

# Update .env with provided values
update_env() {
  local key="$1" value="$2"
  if grep -q "^${key}=" .env; then
    # Replace existing line (portable sed for both macOS and Linux)
    if [[ "$OS" == "macos" ]]; then
      sed -i '' "s|^${key}=.*|${key}=${value}|" .env
    else
      sed -i "s|^${key}=.*|${key}=${value}|" .env
    fi
  else
    echo "${key}=${value}" >> .env
  fi
}

# Inject LLM settings if provided
[[ -n "$LLM_BASE_URL" ]] && update_env "LLM_BASE_URL" "$LLM_BASE_URL" && info "Set LLM_BASE_URL"
[[ -n "$LLM_API_KEY"  ]] && update_env "LLM_API_KEY"  "$LLM_API_KEY"  && info "Set LLM_API_KEY"
[[ -n "$LLM_MODEL"    ]] && update_env "LLM_MODEL"     "$LLM_MODEL"    && info "Set LLM_MODEL"

# Auto-generate secure keys if still at defaults
if grep -q "change-this-to-a-random" .env; then
  VAULT_KEY="$(generate_key)"
  SECRET_KEY="$(generate_key)"
  update_env "VAULT_MASTER_KEY" "$VAULT_KEY"
  update_env "SECRET_KEY"       "$SECRET_KEY"
  success "Generated secure VAULT_MASTER_KEY and SECRET_KEY"
fi

# Update port in docker-compose if non-default
if [[ "$HTTP_PORT" != "80" ]]; then
  if [[ "$OS" == "macos" ]]; then
    sed -i '' "s|\"80:80\"|\"${HTTP_PORT}:80\"|g" docker-compose.yml
  else
    sed -i "s|\"80:80\"|\"${HTTP_PORT}:80\"|g" docker-compose.yml
  fi
  info "Configured nginx to serve on port ${HTTP_PORT}"
fi

# ── Create data directories ───────────────────────────────────────────────────
header "Preparing data directories..."
mkdir -p data/db data/chroma data/personality data/projects data/workspace
success "Data directories ready"

# ── Pull & build images ───────────────────────────────────────────────────────
header "Building Docker images (this may take a few minutes on first run)..."
docker compose pull chromadb 2>/dev/null || true
docker compose build --parallel
success "Images built"

# ── Start services ────────────────────────────────────────────────────────────
header "Starting services..."
docker compose up -d
success "All services started"

# ── Health check ──────────────────────────────────────────────────────────────
header "Waiting for backend to be healthy..."
MAX_TRIES=30
WAIT=2
for i in $(seq 1 $MAX_TRIES); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${HTTP_PORT}/health" 2>/dev/null || echo "000")
  if [[ "$STATUS" == "200" ]]; then
    success "Backend is healthy (HTTP 200)"
    break
  fi
  if [[ $i -eq $MAX_TRIES ]]; then
    warn "Health check timed out after $((MAX_TRIES * WAIT))s."
    warn "Services may still be starting. Run: docker compose logs -f"
    break
  fi
  echo -ne "\r  Attempt ${i}/${MAX_TRIES} (HTTP ${STATUS})... "
  sleep $WAIT
done

# ── Check for missing LLM config ──────────────────────────────────────────────
if grep -q "^LLM_API_KEY=$\|^LLM_API_KEY=sk-your" .env 2>/dev/null; then
  echo ""
  warn "┌─────────────────────────────────────────────────────┐"
  warn "│  ACTION REQUIRED: Set your LLM API key              │"
  warn "│                                                     │"
  warn "│  Edit ${INSTALL_DIR}/.env                           │"
  warn "│  Set LLM_API_KEY=<your key>                         │"
  warn "│  Then run: docker compose restart backend           │"
  warn "└─────────────────────────────────────────────────────┘"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}╔═══════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${GREEN}║   Agent Harness is running!                       ║${RESET}"
echo -e "${BOLD}${GREEN}╚═══════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  ${BOLD}Web UI${RESET}       →  http://localhost:${HTTP_PORT}"
echo -e "  ${BOLD}API Docs${RESET}     →  http://localhost:${HTTP_PORT}/docs"
echo -e "  ${BOLD}Backend logs${RESET} →  docker compose -C ${INSTALL_DIR} logs -f backend"
echo -e "  ${BOLD}Stop${RESET}         →  docker compose -C ${INSTALL_DIR} down"
echo ""
echo -e "  ${YELLOW}Next step:${RESET} Open Settings in the UI and configure your LLM provider."
echo ""
