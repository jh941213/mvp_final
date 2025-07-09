#!/bin/bash

# 로고 함수들 로드
source "$(dirname "${BASH_SOURCE[0]}")/logo.sh"

echo ""
echo -e "${MS_BLUE}${BOLD}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${MS_BLUE}${BOLD}║                                                                  ║${NC}"
echo -e "${MS_BLUE}${BOLD}║${NC}              ${MS_YELLOW}${BOLD}🚀 FastAPI Multi-Agent Backend 🚀${NC}                ${MS_BLUE}${BOLD}║${NC}"
echo -e "${MS_BLUE}${BOLD}║                                                                  ║${NC}"
echo -e "${MS_BLUE}${BOLD}╚══════════════════════════════════════════════════════════════════╝${NC}"

show_windows_logo
show_autogen_logo
show_ktds_logo
show_multiagent_logo

echo -e "${MS_BLUE}${BOLD}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${MS_GREEN}${BOLD}║  🎯 AutoGen Multi-Agent System Starting...                      ║${NC}"
echo -e "${MS_YELLOW}${BOLD}║  📡 KT ds Enterprise Solution                                    ║${NC}"
echo -e "${MS_RED}${BOLD}║  🔥 Powered by Microsoft Technologies                           ║${NC}"
echo -e "${MS_PURPLE}${BOLD}║  ⚡ FastAPI + Azure + AI Agents                                ║${NC}"
echo -e "${MS_BLUE}${BOLD}╚══════════════════════════════════════════════════════════════════╝${NC}"

show_system_info
show_success_message

echo ""
echo -e "${MS_GREEN}${BOLD}🎉 KT ds AutoGen Multi-Agent 백엔드 로고 시스템 완료! 🎉${NC}"
echo "" 