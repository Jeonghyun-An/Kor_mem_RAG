# Kor_mem_RAG – 코리안메모리 AI 지식검색 RAG

## 포트 분리 (Library_AI_land와 충돌 없음)

| 서비스    | Library_AI_land | Kor_mem_RAG |
| --------- | --------------- | ----------- |
| Nginx(UI) | :90             | **:91**     |
| FastAPI   | :8000           | **:8001**   |
| vLLM      | :18080          | **:18082**  |
| Milvus    | :19530          | **:19531**  |
| Attu      | –               | **:8086**   |

## 빠른 시작

```bash
cd docker && bash setup-volumes.sh
cp .env.example .env          # HF_TOKEN 설정
docker compose up -d
curl -X POST http://localhost:8001/api/index/run   # 인덱싱
open http://localhost:91/koreanmemory              # UI
```

# JSON 데이터 구조

```
collected_data.json
├── meta
│   ├── source_url      # 크롤링 출처
│   ├── total_items     # 전체 109건
│   └── collected_at    # 수집 시각
└── items[]
    ├── editor_id / data_idx / editor_gbn_cd
    ├── badge           # "포스트", "시리즈" 등 콘텐츠 유형
    ├── thumbnail / thumbnail_alt
    ├── title / title_main
    └── sub_pages[]     # ★ 핵심: 1개 아이템에 여러 하위 페이지
        ├── title_sub
        ├── detail_url
        └── detail
            ├── provider         # 제공 기관
            ├── date_registered / date_modified
            ├── body_text        # ★ RAG 핵심 텍스트 (수천 자)
            ├── body_images[]    # 이미지 src/alt
            ├── license          # "1 유형"
            ├── keywords[]       # 한자 병기 키워드
            ├── related_stories[]
            └── related_resources[]  # 연관 자료 링크
```

# 개발자 가이드

## 코드 수정 후 재빌드 및 푸쉬 자동화 스크립트 실행

.\scripts\build_fastapi.ps1
.\scripts\build_nuxt.ps1
