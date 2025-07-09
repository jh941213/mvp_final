#!/usr/bin/env python3
"""
세션 관리 기능 테스트 스크립트
"""

import asyncio
import os
import sys
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import check_azure_sql_config, get_database_url
from session_manager import SessionManager
from multi_agent_system import get_magentic_system


def test_config():
    """환경 설정 테스트"""
    print("🔧 환경 설정 테스트")
    print("-" * 50)
    
    config_status = check_azure_sql_config()
    print(f"연결 문자열 제공: {config_status['connection_string_provided']}")
    print(f"서버 제공: {config_status['server_provided']}")
    print(f"데이터베이스 제공: {config_status['database_provided']}")
    print(f"사용자명 제공: {config_status['username_provided']}")
    print(f"비밀번호 제공: {config_status['password_provided']}")
    print(f"연결 가능: {config_status['can_connect']}")
    print(f"현재 DB URL: {config_status['current_db_url']}")
    print()
    
    return config_status


def test_session_manager():
    """세션 관리자 테스트"""
    print("💾 세션 관리자 테스트")
    print("-" * 50)
    
    try:
        # 세션 관리자 초기화
        session_manager = SessionManager()
        print(f"✅ 세션 관리자 초기화 성공: {session_manager.manager_type}")
        
        # 세션 생성
        user_id = "test_user_001"
        session_id = session_manager.create_session(user_id)
        print(f"✅ 세션 생성 성공: {session_id}")
        
        # 세션 정보 조회
        session_info = session_manager.get_session_info(session_id)
        print(f"✅ 세션 정보 조회: {session_info}")
        
        # 대화 저장
        conversation_success = session_manager.save_conversation_turn(
            session_id=session_id,
            user_message="안녕하세요, 테스트 메시지입니다.",
            assistant_response="안녕하세요! 테스트 응답입니다."
        )
        print(f"✅ 대화 저장 성공: {conversation_success}")
        
        # 대화 히스토리 조회
        history = session_manager.get_conversation_history(session_id)
        print(f"✅ 대화 히스토리 조회: {len(history)}개 메시지")
        
        # 사용자 세션 목록 조회
        user_sessions = session_manager.get_user_sessions(user_id)
        print(f"✅ 사용자 세션 목록: {len(user_sessions)}개 세션")
        
        # 세션 통계
        stats = session_manager.get_session_stats()
        print(f"✅ 세션 통계: {stats}")
        
        # 세션 종료
        end_success = session_manager.end_session(session_id)
        print(f"✅ 세션 종료 성공: {end_success}")
        
        return True
        
    except Exception as e:
        print(f"❌ 세션 관리자 테스트 실패: {str(e)}")
        return False


async def test_magentic_system_with_session():
    """MagenticOne 시스템과 세션 관리 통합 테스트"""
    print("🎯 MagenticOne 시스템 세션 관리 통합 테스트")
    print("-" * 50)
    
    try:
        # MagenticOne 시스템 초기화
        system = get_magentic_system(verbose=True)
        print("✅ MagenticOne 시스템 초기화 완료")
        
        # 세션 생성
        user_id = "test_user_002"
        session_id = system.create_session(user_id)
        print(f"✅ 세션 생성: {session_id}")
        
        # 첫 번째 질문 (세션 생성됨)
        query1 = "우리 회사의 급여 체계에 대해 알려주세요."
        print(f"🔍 질문 1: {query1}")
        response1 = await system.process_query(query1, user_id, session_id)
        print(f"💬 응답 1: {response1[:100]}...")
        
        # 두 번째 질문 (기존 세션 사용)
        query2 = "방금 전 답변에 대해 더 자세히 설명해주세요."
        print(f"🔍 질문 2: {query2}")
        response2 = await system.process_query(query2, user_id, session_id)
        print(f"💬 응답 2: {response2[:100]}...")
        
        # 세션 정보 조회
        session_info = system.get_session_info(session_id)
        print(f"✅ 세션 정보: {session_info}")
        
        # 대화 히스토리 조회
        history = system.get_conversation_history(session_id)
        print(f"✅ 대화 히스토리: {len(history)}개 메시지")
        
        # 사용자 세션 목록
        user_sessions = system.get_user_sessions(user_id)
        print(f"✅ 사용자 세션 목록: {len(user_sessions)}개 세션")
        
        # 세션 통계
        stats = system.get_session_stats()
        print(f"✅ 세션 통계: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ MagenticOne 시스템 세션 테스트 실패: {str(e)}")
        return False


def print_environment_setup():
    """환경 설정 방법 안내"""
    print("🛠️  Azure SQL 환경 설정 방법")
    print("=" * 50)
    print("1. 환경 변수 설정:")
    print("   export AZURE_SQL_SERVER='your-server.database.windows.net'")
    print("   export AZURE_SQL_DATABASE='your-database'")
    print("   export AZURE_SQL_USERNAME='your-username'")
    print("   export AZURE_SQL_PASSWORD='your-password'")
    print()
    print("2. 또는 연결 문자열 직접 설정:")
    print("   export AZURE_SQL_CONNECTION_STRING='DRIVER={ODBC Driver 17 for SQL Server};SERVER=...;'")
    print()
    print("3. 필요한 패키지 설치:")
    print("   pip install pyodbc sqlalchemy")
    print()
    print("4. 개발 모드 (SQLite 사용):")
    print("   환경 변수 없이 실행하면 자동으로 SQLite 사용")
    print()


async def main():
    """메인 테스트 함수"""
    print("🚀 KTDS 세션 관리 시스템 테스트")
    print("=" * 50)
    print(f"테스트 시작: {datetime.now()}")
    print()
    
    # 1. 환경 설정 테스트
    config_status = test_config()
    
    # 2. 세션 관리자 테스트
    session_test_success = test_session_manager()
    
    # 3. MagenticOne 시스템과 세션 관리 통합 테스트
    if session_test_success:
        integration_test_success = await test_magentic_system_with_session()
    else:
        integration_test_success = False
    
    # 테스트 결과 요약
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약")
    print(f"환경 설정: {'✅ 통과' if config_status['can_connect'] else '⚠️ Azure SQL 미설정 (SQLite 사용)'}")
    print(f"세션 관리자: {'✅ 통과' if session_test_success else '❌ 실패'}")
    print(f"통합 테스트: {'✅ 통과' if integration_test_success else '❌ 실패'}")
    
    if not config_status['can_connect']:
        print("\n")
        print_environment_setup()
    
    print(f"\n테스트 완료: {datetime.now()}")


if __name__ == "__main__":
    asyncio.run(main()) 