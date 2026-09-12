# Offline demo anchors

`anchors.json`에는 데모에서 허용된 공고가 정확히 3개 있습니다. 모두 자체 작성한 합성 fixture이며 실제 회사나 지역 통계로 해석할 수 없습니다.

전체 흐름은 `tests/backend/test_offline_demo.py`가 네트워크와 API 키 없이 검증합니다. 프론트 요청과 예상 핵심값은 루트의 `FRONTEND_API_HANDOFF.md`를 따릅니다.
