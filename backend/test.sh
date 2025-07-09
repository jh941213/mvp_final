#!/bin/bash
# KTDS AutoGen 테스트 모드 시작

# Microsoft 색상
MS_YELLOW='\033[38;2;255;185;0m'
MS_BLUE='\033[38;2;0;120;212m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${MS_YELLOW}${BOLD}🧪 ═══════════════════════════════════════════════════════════════ 🧪${NC}"
echo -e "${MS_BLUE}${BOLD}   KT ds AutoGen Multi-Agent System - Test Mode${NC}"
echo -e "${MS_YELLOW}${BOLD}🧪 ═══════════════════════════════════════════════════════════════ 🧪${NC}"
echo ""

# backend 디렉토리로 이동해서 실행
cd "$(dirname "${BASH_SOURCE[0]}")"
./run_backend.sh test 8080 