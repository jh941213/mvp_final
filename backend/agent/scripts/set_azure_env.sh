#!/bin/bash
# Azure SQL 환경 변수 설정 스크립트

export AZURE_SQL_CONNECTION_STRING="DRIVER={ODBC Driver 17 for SQL Server};Server=kdb-chatsession-1751955774.database.windows.net;Database=chatsession-db;UID=kdbadmin;PWD=ChatSession123!;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
export AZURE_SQL_SERVER="kdb-chatsession-1751955774.database.windows.net"
export AZURE_SQL_DATABASE="chatsession-db"
export AZURE_SQL_USERNAME="kdbadmin"
export AZURE_SQL_PASSWORD="ChatSession123!"
export ODBCINI="/opt/homebrew/etc/odbc.ini"
export ODBCSYSINI="/opt/homebrew/etc"

# Gemini API 키 설정
export GEMINI_API_KEY="AIzaSyDgYXrzEKHHcmQNAnSN4PfOKd2FEYEC8Iw"

echo "✅ Azure SQL 환경 변수 설정 완료"
echo "서버: kdb-chatsession-1751955774.database.windows.net"
echo "데이터베이스: chatsession-db"
echo "사용자명: kdbadmin"
echo "✅ Gemini API 키 설정 완료"
echo "모델: gemini-2.0-flash-preview-image-generation"
