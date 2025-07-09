#!/bin/bash

# Azure SQL 빠른 설정 스크립트
# 매일 삭제되는 Azure SQL 리소스를 자동으로 재생성

echo "🚀 Azure SQL 자동 설정 스크립트 실행"
echo "====================================="
echo ""

# Azure 로그인 상태 확인
if ! az account show &>/dev/null; then
    echo "❌ Azure에 로그인되어 있지 않습니다."
    echo "az login 명령어를 실행해주세요."
    exit 1
fi

echo "✅ Azure 로그인 상태 확인 완료"
echo ""

# 기존 리소스 정리 여부 확인
read -p "기존 kdb-chatsession 서버를 자동 삭제하시겠습니까? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 기존 리소스 정리 모드로 실행합니다."
    ./setup_azure_sql_auto.sh
else
    echo "📋 기존 리소스 유지 모드로 실행합니다."
    echo "   (기존 서버 삭제 시 'n'을 선택하세요)"
    ./setup_azure_sql_auto.sh
fi

echo ""
echo "🎉 Azure SQL 설정 완료!"
echo ""
echo "📝 다음 단계:"
echo "1. 환경 변수 설정: source ./set_azure_env.sh"
echo "2. 세션 관리자 테스트: python3 test_session_manager.py"
echo "3. MagenticOne 시스템 테스트: python3 multi_agent_system.py"
echo ""
echo "💡 팁: 매일 리소스가 삭제되면 이 스크립트를 다시 실행하세요!" 