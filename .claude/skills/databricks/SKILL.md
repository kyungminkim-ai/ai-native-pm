---
description: Databricks에서 테이블 스키마 탐색, SQL 쿼리 실행, 결과 분석을 수행하는 데이터 탐색 에이전트
---

# /databricks — Databricks 데이터 탐색 에이전트

## 모델

`claude-haiku-4-5-20251001`

## 사용법
```
/databricks                                          ← Unity Catalog 전체 탐색
/databricks --explore [schema.table]                 ← 특정 스키마/테이블 구조 탐색
/databricks --query "[자연어 또는 SQL]"               ← 쿼리 실행 후 결과 요약
/databricks --analyze [table] "[분석 주제]"           ← 데이터 분석 + 인사이트 리포트
/databricks --initiative TM-XXXX "[분석 주제]"        ← 이니셔티브 컨텍스트 연결
```

## 실행 규칙
1. `databricks-agent-system/CLAUDE.md` 읽어 역할 파악
2. args 파싱:
   - `--explore [target]` → explore 모드
   - `--query "[질문]"` → query 모드
   - `--analyze [table] "[주제]"` → analyze 모드
   - args 없음 → explore 모드 (전체 카탈로그 탐색)
3. `DATABRICKS_HOST`, `DATABRICKS_TOKEN` 환경변수 확인
   - 없으면 연결 설정 가이드 출력 후 중단
4. `databricks-agent-system/CLAUDE.md` 워크플로우 실행
5. 산출물: `databricks-agent-system/output/` 저장

## 환경변수 (`.env`에 추가 필요)
```bash
# Databricks 연결 — https://your-workspace.databricks.com에서 발급
DATABRICKS_HOST=https://your-workspace.databricks.com
DATABRICKS_TOKEN=dapi-xxxxxxxxxxxxxxxxxxxx
DATABRICKS_WAREHOUSE_ID=your-sql-warehouse-id
```

## 연결 방식 (택 1)
- **방식 A (기본)**: Python 스크립트 `databricks-agent-system/scripts/client.py` 직접 실행
- **방식 B (권장, MCP)**: `.claude/mcp.json`에 Databricks MCP 서버 추가 시 자연어 직접 조회 가능
  - 설정 방법: `databricks-agent-system/CLAUDE.md` §연결 설정 참조
