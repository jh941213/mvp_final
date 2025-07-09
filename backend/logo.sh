#!/bin/bash

# Microsoft RGB 색상 정의
MS_BLUE='\033[38;2;0;120;212m'      # #0078D4
MS_GREEN='\033[38;2;16;124;16m'     # #107C10
MS_YELLOW='\033[38;2;255;185;0m'    # #FFB900
MS_RED='\033[38;2;209;52;56m'       # #D13438
MS_CYAN='\033[38;2;0;188;212m'      # #00BCD4
MS_PURPLE='\033[38;2;136;23;152m'   # #881798
NC='\033[0m'                        # No Color
BOLD='\033[1m'
RESET='\033[0m'

# Microsoft Windows 로고 (정확한 4색상)
show_windows_logo() {
    echo ""
    echo -e "        ${MS_RED}${BOLD}████████████████${NC}  ${MS_GREEN}${BOLD}████████████████${NC}"
    echo -e "        ${MS_RED}${BOLD}████████████████${NC}  ${MS_GREEN}${BOLD}████████████████${NC}"
    echo -e "        ${MS_RED}${BOLD}████████████████${NC}  ${MS_GREEN}${BOLD}████████████████${NC}"
    echo -e "        ${MS_RED}${BOLD}████████████████${NC}  ${MS_GREEN}${BOLD}████████████████${NC}"
    echo -e "        ${MS_RED}${BOLD}████████████████${NC}  ${MS_GREEN}${BOLD}████████████████${NC}"
    echo -e "        ${MS_RED}${BOLD}████████████████${NC}  ${MS_GREEN}${BOLD}████████████████${NC}"
    echo ""
    echo -e "        ${MS_BLUE}${BOLD}████████████████${NC}  ${MS_YELLOW}${BOLD}████████████████${NC}"
    echo -e "        ${MS_BLUE}${BOLD}████████████████${NC}  ${MS_YELLOW}${BOLD}████████████████${NC}"
    echo -e "        ${MS_BLUE}${BOLD}████████████████${NC}  ${MS_YELLOW}${BOLD}████████████████${NC}"
    echo -e "        ${MS_BLUE}${BOLD}████████████████${NC}  ${MS_YELLOW}${BOLD}████████████████${NC}"
    echo -e "        ${MS_BLUE}${BOLD}████████████████${NC}  ${MS_YELLOW}${BOLD}████████████████${NC}"
    echo -e "        ${MS_BLUE}${BOLD}████████████████${NC}  ${MS_YELLOW}${BOLD}████████████████${NC}"
    echo ""
    echo -e "               ${MS_BLUE}${BOLD}🪟 Microsoft Windows${NC}"
    echo ""
}

# AutoGen 로고
show_autogen_logo() {
    echo ""
    echo -e "${MS_PURPLE}${BOLD}  █████╗ ██╗   ██╗████████╗ ██████╗  ██████╗ ███████╗███╗   ██╗${NC}"
    echo -e "${MS_PURPLE}${BOLD} ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗██╔════╝ ██╔════╝████╗  ██║${NC}"
    echo -e "${MS_CYAN}${BOLD} ███████║██║   ██║   ██║   ██║   ██║██║  ███╗█████╗  ██╔██╗ ██║${NC}"
    echo -e "${MS_CYAN}${BOLD} ██╔══██║██║   ██║   ██║   ██║   ██║██║   ██║██╔══╝  ██║╚██╗██║${NC}"
    echo -e "${MS_BLUE}${BOLD} ██║  ██║╚██████╔╝   ██║   ╚██████╔╝╚██████╔╝███████╗██║ ╚████║${NC}"
    echo -e "${MS_BLUE}${BOLD} ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═══╝${NC}"
    echo ""
}

# KT ds 로고
show_ktds_logo() {
    echo ""
    echo -e "${MS_RED}${BOLD} ██╗  ██╗████████╗      ██████╗ ███████╗${NC}"
    echo -e "${MS_RED}${BOLD} ██║ ██╔╝╚══██╔══╝      ██╔══██╗██╔════╝${NC}"
    echo -e "${MS_YELLOW}${BOLD} █████╔╝    ██║         ██║  ██║███████╗${NC}"
    echo -e "${MS_YELLOW}${BOLD} ██╔═██╗    ██║         ██║  ██║╚════██║${NC}"
    echo -e "${MS_GREEN}${BOLD} ██║  ██╗   ██║         ██████╔╝███████║${NC}"
    echo -e "${MS_GREEN}${BOLD} ╚═╝  ╚═╝   ╚═╝         ╚═════╝ ╚══════╝${NC}"
    echo ""
    echo -e "${MS_BLUE}${BOLD}        📡 KT ds - KT IT Subsidiary${NC}"
    echo -e "${MS_PURPLE}${BOLD}          Digital Solutions Provider${NC}"
    echo ""
}

# 멀티에이전트 시스템 로고
show_multiagent_logo() {
    echo ""
    echo -e "${MS_CYAN}${BOLD}    🤖 ────── 🤖 ────── 🤖 ────── 🤖${NC}"
    echo -e "${MS_BLUE}${BOLD}     │         │         │         │${NC}"
    echo -e "${MS_PURPLE}${BOLD}     └─── 🧠 Central Hub 🧠 ────┘${NC}"
    echo -e "${MS_GREEN}${BOLD}            Multi-Agent System${NC}"
    echo -e "${MS_YELLOW}${BOLD}         Powered by Microsoft AI${NC}"
    echo ""
}

# 전체 시작 배너
show_startup_banner() {
    clear
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
    echo ""
}

# 시스템 정보 표시
show_system_info() {
    echo -e "${MS_CYAN}${BOLD}📋 System Information:${NC}"
    echo -e "${MS_BLUE}   OS: ${NC}$(uname -s) $(uname -r)"
    echo -e "${MS_GREEN}   Python: ${NC}$(python3 --version 2>/dev/null || echo 'Not found')"
    echo -e "${MS_YELLOW}   FastAPI: ${NC}Starting..."
    echo -e "${MS_RED}   Agents: ${NC}Initializing..."
    echo ""
}

# 성공 메시지
show_success_message() {
    echo ""
    echo -e "${MS_GREEN}${BOLD}✅ ═══════════════════════════════════════════════════════════════ ✅${NC}"
    echo -e "${MS_GREEN}${BOLD}   🎉 KT ds Multi-Agent System Successfully Started! 🎉${NC}"
    echo -e "${MS_GREEN}${BOLD}✅ ═══════════════════════════════════════════════════════════════ ✅${NC}"
    echo ""
    echo -e "${MS_BLUE}${BOLD}🌐 Server URLs:${NC}"
    echo -e "${MS_CYAN}   • Main API: ${NC}http://localhost:8000"
    echo -e "${MS_YELLOW}   • API Docs: ${NC}http://localhost:8000/docs"
    echo -e "${MS_PURPLE}   • ReDoc: ${NC}http://localhost:8000/redoc"
    echo ""
    echo -e "${MS_RED}${BOLD}🔧 Available Endpoints:${NC}"
    echo -e "${MS_BLUE}   • ${NC}/chat - Multi-Agent Chat Interface"
    echo -e "${MS_GREEN}   • ${NC}/agents - Agent Management"
    echo -e "${MS_YELLOW}   • ${NC}/sessions - Session Management"
    echo -e "${MS_PURPLE}   • ${NC}/health - System Health Check"
    echo ""
} 