#!/usr/bin/env bash
# ============================================================
#  RAG 智能客服 · 服务器一键部署脚本
#  适用：Ubuntu 22.04 / 24.04（腾讯云轻量、阿里云 ECS 等）
#  用法：sudo bash setup.sh <域名或留空> <ADMIN_PASSWORD>
#    例：sudo bash setup.sh                          # 用 IP:8501 直接访问
#        sudo bash setup.sh rag.example.com 我的密码  # 配域名 + 自动 HTTPS
#  说明：脚本可重复执行，会先备份旧代码再拉取最新版本
# ============================================================
set -euo pipefail

# ---------------- 配置区（按需修改） ----------------
APP_DIR="${APP_DIR:-/opt/rag/app}"
REPO="${REPO:-https://github.com/Baoaolong/RAG-.git}"
PORT="${PORT:-8501}"

DOMAIN="${1:-}"
ADMIN_PASSWORD="${2:-${ADMIN_PASSWORD:-}}"

RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; BOLD=$'\033[1m'; NC=$'\033[0m'
info() { printf '%s==>%s %s\n' "$BOLD" "$NC" "$*"; }
ok()   { printf '%s[OK]%s %s\n' "$GREEN" "$NC" "$*"; }
warn() { printf '%s[!]%s %s\n' "$YELLOW" "$NC" "$*"; }
die()  { printf '%s[X]%s %s\n' "$RED" "$NC" "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "请用 root 运行：sudo bash setup.sh ..."
[ -n "$ADMIN_PASSWORD" ] || die "缺少管理员密码。用法：sudo bash setup.sh <域名或留空> <ADMIN_PASSWORD>"

if [ "$(uname -m)" != "x86_64" ]; then
  warn "当前架构是 $(uname -m)。本项目的向量库 chroma_db 建议在 x86_64 上使用，"
  warn "ARM 机器上如果检索报错，改用 git 拉代码后按知识库页重新导入 data/ 里的 txt。"
fi

# ---------------- 1. 系统依赖与 Python ----------------
info "安装系统依赖 python3-venv / git / curl"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3-venv python3-pip git curl ca-certificates
python3 --version
ok "系统依赖就绪"

# ---------------- 2. 拉取代码 ----------------
info "部署代码到 $APP_DIR"
mkdir -p "$(dirname "$APP_DIR")"
if [ -e "$APP_DIR/.git" ]; then
  warn "检测到已有代码，先备份再更新"
  cp -a "$APP_DIR/.env" "/tmp/rag_env_backup" 2>/dev/null || true
  rm -rf "${APP_DIR}.bak"
  mv "$APP_DIR" "${APP_DIR}.bak"
  ok "旧版本已备份到 ${APP_DIR}.bak"
fi
git clone --depth 1 "$REPO" "$APP_DIR" >/dev/null
ok "代码已拉取：$(git -C "$APP_DIR" log --oneline -1)"

# ---------------- 3. 虚拟环境与依赖 ----------------
info "创建虚拟环境并安装依赖（首次约 5~15 分钟，会下载约 2GB 的 chromadb 相关包）"
python3 -m venv "$APP_DIR/.venv"
# 国内 pip 源加速（如果服务器在海外可注释掉这两行）
"$APP_DIR/.venv/bin/pip" config set global.index-url https://mirrors.tencent.com/pypi/simple/ >/dev/null
"$APP_DIR/.venv/bin/pip" config set global.trusted-host mirrors.tencent.com >/dev/null
"$APP_DIR/.venv/bin/pip" install -q -U pip
"$APP_DIR/.venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"
ok "依赖安装完成"

# ---------------- 4. 密钥与配置 ----------------
info "写入 .env"
# 优先从旧备份里继承原来的 DASHSCOPE_API_KEY
if [ ! -f "$APP_DIR/.env" ] && [ -f "/tmp/rag_env_backup" ]; then
  cp "/tmp/rag_env_backup" "$APP_DIR/.env"
  ok "已从旧版本继承 .env"
fi
if ! grep -q '^DASHSCOPE_API_KEY=' "$APP_DIR/.env" 2>/dev/null; then
  read -r -s -p "请输入阿里云百炼的 DASHSCOPE_API_KEY（sk- 开头，输入时不显示）: " DS_KEY
  echo
  [ -n "$DS_KEY" ] || die "API Key 不能为空"
  printf 'DASHSCOPE_API_KEY=%s\n' "$DS_KEY" >> "$APP_DIR/.env"
fi
if grep -q '^ADMIN_PASSWORD=' "$APP_DIR/.env" 2>/dev/null; then
  sed -i "s|^ADMIN_PASSWORD=.*|ADMIN_PASSWORD=${ADMIN_PASSWORD}|" "$APP_DIR/.env"
else
  printf 'ADMIN_PASSWORD=%s\n' "$ADMIN_PASSWORD" >> "$APP_DIR/.env"
fi
chmod 600 "$APP_DIR/.env"
ok ".env 已写入（权限 600，密钥不会出现在命令行历史里）"

# ---------------- 5. systemd 常驻服务 ----------------
info "注册 systemd 服务 rag.service"
cat > /etc/systemd/system/rag.service <<EOF
[Unit]
Description=RAG Knowledge QA (Streamlit)
After=network.target

[Service]
Type=simple
WorkingDirectory=${APP_DIR}
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONUTF8=1
ExecStart=${APP_DIR}/.venv/bin/streamlit run ${APP_DIR}/app_qa.py \\
  --server.port=${PORT} \\
  --server.address=127.0.0.1 \\
  --server.headless=true \\
  --browser.gatherUsageStats=false \\
  --server.maxUploadSize=200
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable -q rag
systemctl restart rag
ok "服务已启动并设置开机自启"

# ---------------- 6. 域名 + 自动 HTTPS（可选） ----------------
if [ -n "$DOMAIN" ]; then
  info "安装 Caddy 并为 $DOMAIN 申请自动 HTTPS 证书"
  apt-get install -y -qq debian-keyring debian-archive-keyring apt-transport-https
  curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/gpg.key \
    | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt \
    > /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -qq
  apt-get install -y -qq caddy
  cat > /etc/caddy/Caddyfile <<EOF
${DOMAIN} {
    encode gzip
    reverse_proxy 127.0.0.1:${PORT} {
        header_up Host {host}
        header_up X-Real-IP {remote_host}
    }
}
EOF
  systemctl reload caddy || systemctl restart caddy
  ok "Caddy 已配置，证书会在几分钟内自动签发"
fi

# ---------------- 7. 自检 ----------------
info "等待应用启动并自检"
HEALTH=""
for _ in $(seq 1 30); do
  HEALTH="$(curl -fsS "http://127.0.0.1:${PORT}/_stcore/health" 2>/dev/null || true)"
  [ "$HEALTH" = "ok" ] && break
  sleep 2
done
if [ "$HEALTH" = "ok" ]; then
  ok "应用健康检查通过：ok"
else
  warn "健康检查还没通过，请看日志：journalctl -u rag -n 50 --no-pager"
fi

echo
echo "=================================================================="
echo " 部署完成"
if [ -n "$DOMAIN" ]; then
  echo "   访问地址：https://${DOMAIN}"
  echo "   （前提：域名已解析到本机 IP，且安全组放行 80/443）"
else
  IP="$(curl -4 -fsS --max-time 5 ifconfig.me 2>/dev/null || echo '<你的公网IP>')"
  echo "   访问地址：http://${IP}:${PORT}"
  echo "   （必须先在云控制台的【防火墙/安全组】放行 ${PORT} 端口）"
fi
echo "   服务管理：systemctl restart rag | systemctl status rag"
echo "   查看日志：journalctl -u rag -f"
echo "=================================================================="
