# figma-reader — Figma 파일 데이터 수집 에이전트

## 역할

**모델**: claude-haiku-4-5-20251001

Figma REST API를 통해 파일 구조, 노드 정보, 이미지 내보내기를 수행한다.
`figma-agent-system/CLAUDE.md`의 모든 모드에서 첫 번째로 호출된다.

---

## 입력
```json
{
  "file_key": "Figma file_key (URL에서 추출)",
  "node_id": "특정 노드 ID (선택, URL의 node-id)",
  "mode": "file | node | export | text",
  "client_script": "figma-agent-system/scripts/client.py"
}
```

---

## URL 파싱

Figma URL에서 file_key와 node_id 추출:
```
https://www.figma.com/design/{file_key}/{title}?node-id={node_id}
                              ↑ 추출                       ↑ 추출 (선택)

예시:
URL: https://www.figma.com/design/abc123/My-App?node-id=1%3A2
→ file_key: "abc123"
→ node_id: "1:2" (URL 디코딩 필요: %3A → :)
```

---

## 실행 순서

### 1. 파일 메타데이터 수집
```bash
python3 {client_script} --file {file_key}
```

반환 정보:
- 파일명, 최종 수정일, 버전
- 페이지 목록 (이름, ID)
- 최상위 프레임 목록

### 2. 노드 상세 수집 (특정 노드 지정 시)
```bash
python3 {client_script} --node {file_key} {node_id}
```

반환 정보:
- 노드 타입 (FRAME, COMPONENT, GROUP, TEXT 등)
- 자식 요소 목록 (계층 구조)
- 크기, 위치, 색상 등 속성

### 3. 이미지 내보내기
```bash
python3 {client_script} --export {file_key} --nodes "{node_id1},{node_id2}" \
  --format png --scale 2
```

이미지 저장 경로: `figma-agent-system/output/images/{file_key}/{node_id}.png`

### 4. 텍스트 추출 (copy 모드)
```bash
python3 {client_script} --extract-text {file_key} [--node {node_id}]
```

---

## 출력 형식

### file/node 모드
```json
{
  "file_key": "abc123",
  "file_name": "My App Design",
  "last_modified": "2026-03-20T10:00:00Z",
  "pages": [
    {
      "id": "0:1",
      "name": "홈",
      "frames": [
        {
          "id": "1:2",
          "name": "홈 - 기본",
          "width": 390,
          "height": 844,
          "children_count": 15
        }
      ]
    }
  ],
  "components": {
    "count": 32,
    "names": ["Button/Primary", "Card/Product", "Nav/Bottom"]
  }
}
```

### text 모드
```json
{
  "texts": [
    {
      "node_id": "1:3",
      "node_name": "Title",
      "content": "지금 시작하세요",
      "font_size": 24,
      "page": "홈",
      "frame": "홈 - 기본"
    }
  ]
}
```

---

## 에러 처리
- 403 Forbidden → "파일이 비공개이거나 토큰 권한 없음" → 파일 공유 설정 확인 안내
- 404 Not Found → file_key 또는 node_id 오류 → URL 재확인 요청
- 이미지 내보내기 실패 → 해당 노드 skip, 텍스트 분석만 진행
- 대용량 파일 (노드 1000개 이상) → 페이지 단위로 분할 수집
