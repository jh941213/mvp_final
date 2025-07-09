#!/bin/bash
# KTDS AutoGen 프로덕션 모드 시작

# Microsoft 색상
MS_GREEN='\033[38;2;16;124;16m'
MS_BLUE='\033[38;2;0;120;212m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${MS_GREEN}${BOLD}🚀 ═══════════════════════════════════════════════════════════════ 🚀${NC}"
echo -e "${MS_BLUE}${BOLD}   KT ds AutoGen Multi-Agent System - Production Mode${NC}"
echo -e "${MS_GREEN}${BOLD}🚀 ═══════════════════════════════════════════════════════════════ 🚀${NC}"
echo ""

# backend 디렉토리로 이동해서 실행
cd "$(dirname "${BASH_SOURCE[0]}")"
./run_backend.sh production 8000 