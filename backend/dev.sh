#!/bin/bash
# KTDS AutoGen 개발 모드 빠른 시작

# Microsoft 색상
MS_CYAN='\033[38;2;0;188;212m'
MS_BLUE='\033[38;2;0;120;212m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${MS_CYAN}${BOLD}🔧 ═══════════════════════════════════════════════════════════════ 🔧${NC}"
echo -e "${MS_BLUE}${BOLD}   KT ds AutoGen Multi-Agent System - Development Mode${NC}"
echo -e "${MS_CYAN}${BOLD}🔧 ═══════════════════════════════════════════════════════════════ 🔧${NC}"
echo ""

# backend 디렉토리로 이동해서 실행
cd "$(dirname "${BASH_SOURCE[0]}")"
./run_backend.sh development 8000 