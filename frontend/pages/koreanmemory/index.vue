<template>
  <!-- skip nav -->
  <ul class="skip_menu">
    <li><a href="#contents_wrap">검색 바로가기</a></li>
  </ul>

  <div class="contents_wrap" id="contents_wrap">
    <!-- ======================================================
         [S] left_menu_wrap  –  Library_AI_land와 동일한 구조
         ====================================================== -->
    <div class="left_menu_wrap" :class="{ open: hasSearched }">
      <!-- 헤더: 로고 + 토글 -->
      <div class="left_menu_hd">
        <a href="#;" class="hd_logo view_ctr" @click.prevent="resetHome">
          <img src="/img/layout/km_logo.png" alt="코리안메모리 AI 검색" />
        </a>
        <button
          class="left_menu_trigger"
          aria-label="메뉴 열기/닫기"
          @click="toggleSidebar"
        ></button>
      </div>

      <!-- 히스토리 (사이드바 열림 시) -->
      <div class="left_menu_con_wrap view_ctr">
        <div class="left_menu_con">
          <div class="tab_con_wrap">
            <div class="tab_con on">
              <div class="con_tit ty_01 mt_20">검색 히스토리</div>
              <div class="history_con_wrap history_con_wrap--scrollable mt_10">
                <template v-if="history.length > 0">
                  <div v-for="(items, date) in groupedHistory" :key="date">
                    <div class="history_con_date">{{ date }}</div>
                    <ul class="history_con_list">
                      <li
                        v-for="item in items"
                        :key="item.id"
                        class="history_con_item"
                      >
                        <a
                          href="#;"
                          class="history_con_inn"
                          @click.prevent="loadHistory(item)"
                        >
                          <div class="txt ellipsis line02">
                            {{ item.query }}
                          </div>
                          <button
                            class="ic_del"
                            aria-label="삭제"
                            @click.stop="deleteHistory(item.id)"
                          ></button>
                        </a>
                      </li>
                    </ul>
                  </div>
                </template>
                <template v-else>
                  <p
                    class="txt_gray"
                    style="font-size: 0.65rem; margin-top: 0.5rem"
                  >
                    검색 기록이 없습니다.
                  </p>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 사이드바 하단 -->
      <div class="left_menu_btm_info view_ctr">
        <div class="left_menu_btm_txt">
          AI가 생성한 콘텐츠입니다. 정확성을 확인해 주세요.
        </div>
        <div class="info_wrap ty_01">
          <a
            href="https://nl.go.kr/koreanmemory/"
            target="_blank"
            class="info_item ty_01"
          >
            코리안메모리 바로가기
          </a>
        </div>
      </div>
    </div>
    <!-- [E] left_menu_wrap -->

    <!-- ======================================================
         상태 1: 검색 전 (search_main_wrap)
         Library_AI_land의 search_main_wrap 구조와 동일
         ====================================================== -->
    <div v-if="!hasSearched" class="search_wrap search_main_wrap">
      <!-- 헤더 -->
      <div class="search_wrap_hd">
        <div class="area">
          <img
            src="/img/layout/km_logo.png"
            alt="코리안메모리 AI 검색"
            class="hd_logo"
          />
        </div>
      </div>

      <!-- 메인 검색 -->
      <div class="search_main">
        <div class="inner">
          <img
            src="/img/main/km_title.svg"
            alt="코리안메모리 AI 도서정보 검색"
            style="max-width: 24rem; margin: 0 auto 1rem"
          />
          <div class="main_txt">
            국립중앙도서관 코리안메모리 컬렉션을 AI로 탐색하세요.
          </div>

          <!-- 배지 필터 -->
          <div class="badge_filter_wrap" style="justify-content: center">
            <button
              class="badge_filter_btn"
              :class="{ on: !selectedBadge }"
              @click="selectedBadge = null"
            >
              전체
            </button>
            <button
              v-for="b in BADGES"
              :key="b"
              class="badge_filter_btn"
              :class="{ on: selectedBadge === b }"
              @click="selectedBadge = b"
            >
              {{ b }}
            </button>
          </div>

          <!-- 검색 박스 -->
          <div class="search_box mt_20">
            <input
              v-model="searchQuery"
              @keyup.enter="handleSearch"
              type="text"
              class="search_box_input"
              placeholder="찾고 싶은 주제나 질문을 입력하세요."
            />
            <button
              class="search_box_btn"
              aria-label="검색"
              @click="handleSearch"
              :disabled="isSearching"
            ></button>
          </div>

          <!-- 질문 예시 -->
          <div class="question_example">
            <div class="question_example_hd">
              <div class="con_tit ty_01">질문 예시</div>
            </div>
            <ul class="question_example_list">
              <li
                v-for="ex in EXAMPLES"
                :key="ex"
                class="question_example_item"
              >
                <a
                  href="#;"
                  class="inn"
                  @click.prevent="
                    searchQuery = ex;
                    handleSearch();
                  "
                >
                  <div class="item ellipsis line02">{{ ex }}</div>
                  <div class="arr"></div>
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
    <!-- [E] search_main_wrap -->

    <!-- ======================================================
         상태 2/3: 검색 중 + 결과 (search_result_wrap)
         Library_AI_land의 search_result_wrap 구조와 동일
         ====================================================== -->
    <div v-else class="search_wrap search_result_wrap open">
      <!-- 헤더 -->
      <div class="search_wrap_hd">
        <div class="area"></div>
      </div>

      <!-- 스크롤 영역 -->
      <div class="search_list_wrap">
        <div class="search_q_item fade_in">
          <!-- 현재 검색어 -->
          <div class="search_q_tit">{{ currentQuery }}</div>

          <!-- 배지 필터 탭 -->
          <div class="badge_filter_wrap">
            <button
              class="badge_filter_btn"
              :class="{ on: !selectedBadge }"
              @click="selectedBadge = null"
            >
              전체
            </button>
            <button
              v-for="b in BADGES"
              :key="b"
              class="badge_filter_btn"
              :class="{ on: selectedBadge === b }"
              @click="selectedBadge = b"
            >
              {{ b }}
            </button>
          </div>

          <!-- 로딩 -->
          <div v-if="isSearching" class="loading_wrap">
            <div class="spinner"></div>
            <div class="loading_txt">관련 자료를 검색하는 중입니다...</div>
          </div>

          <!-- 소스 카드 -->
          <template v-if="sources.length > 0">
            <div class="source_cards_wrap">
              <a
                v-for="card in sources"
                :key="card.chunk_id"
                :href="card.detail_url || '#'"
                target="_blank"
                rel="noopener"
                class="source_card"
              >
                <div class="card_thumb">
                  <img
                    v-if="card.thumbnail"
                    :src="card.thumbnail"
                    :alt="card.title_main"
                    @error="
                      ($event.target as HTMLImageElement).style.display = 'none'
                    "
                  />
                </div>
                <div class="card_body">
                  <div class="card_badge">
                    <span :class="`badge ty_${badgeClass(card.badge)}`">{{
                      card.badge
                    }}</span>
                  </div>
                  <div class="card_title">{{ card.title_main }}</div>
                  <div v-if="card.title_sub" class="card_sub">
                    {{ card.title_sub }}
                  </div>
                  <div v-if="card.keywords.length" class="card_keywords">
                    <span
                      v-for="kw in card.keywords.slice(0, 4)"
                      :key="kw"
                      class="card_keyword"
                      >#{{ kw }}</span
                    >
                  </div>
                  <div class="card_meta">
                    <span>{{ card.provider }}</span>
                    <span class="card_score"
                      >{{ (card.score * 100).toFixed(0) }}% 관련</span
                    >
                  </div>
                </div>
              </a>
            </div>
          </template>

          <!-- 소스 없음 -->
          <div
            v-if="!isSearching && hasSearched && sources.length === 0"
            style="
              padding: 2rem;
              text-align: center;
              color: var(--gray60);
              font-size: 0.75rem;
            "
          >
            관련 자료를 찾을 수 없습니다. 다른 검색어를 시도해 보세요.
          </div>

          <!-- AI 답변 -->
          <div v-if="answerText || isGenerating" class="answer_wrap fade_in">
            <div class="answer_hd">
              <div class="ai_icon">
                <svg
                  viewBox="0 0 24 24"
                  fill="white"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"
                  />
                </svg>
              </div>
              <div class="ai_label">AI 답변</div>
            </div>
            <div class="answer_body" v-html="renderedAnswer"></div>
            <span v-if="isGenerating" class="answer_cursor"></span>
          </div>
        </div>
      </div>

      <!-- 하단 고정 검색 박스 -->
      <div class="search_box_wrap">
        <div class="search_box">
          <input
            v-model="searchQuery"
            @keyup.enter="handleSearch"
            type="text"
            class="search_box_input"
            placeholder="다른 질문을 입력하세요."
          />
          <button
            class="search_box_btn"
            aria-label="검색"
            @click="handleSearch"
            :disabled="isSearching || isGenerating"
          ></button>
        </div>
      </div>
    </div>
    <!-- [E] search_result_wrap -->
  </div>
</template>

<script setup lang="ts">
import { marked } from "marked";
import { useKorMemAPI } from "@/composables/useKorMemAPI";
import { useSearchHistory } from "@/composables/useSearchHistory";
import { computed, ref } from "vue";

definePageMeta({ layout: false });
useHead({ title: "코리안메모리 AI 검색" });

const { chatStream, getBadges } = useKorMemAPI();
const { history, groupedHistory, addHistory, deleteHistory } =
  useSearchHistory();

// ─── 상수 ───────────────────────────────────────────
const BADGES = ["포스트", "시리즈", "특집", "큐레이션", "전시", "아카이브"];
const EXAMPLES = [
  "한국 근현대 문학 작가와 그 대표 작품은?",
  "6.25 전쟁 당시의 피란민 생활을 담은 자료를 찾아줘.",
  "한국 전통 공예 – 도자기와 자수의 역사를 알려줘.",
  "독립운동 관련 희귀 기록물이나 사진 자료가 있나요?",
];

// ─── 상태 ───────────────────────────────────────────
const searchQuery = ref("");
const currentQuery = ref("");
const selectedBadge = ref<string | null>(null);
const hasSearched = ref(false);
const isSearching = ref(false);
const isGenerating = ref(false);
const sources = ref<any[]>([]);
const answerText = ref("");

let abortController: AbortController | null = null;

// ─── 사이드바 ────────────────────────────────────────
const toggleSidebar = () => {
  hasSearched.value = !hasSearched.value;
};

// ─── 마크다운 렌더링 ─────────────────────────────────
const renderedAnswer = computed(() => marked.parse(answerText.value) as string);

// ─── 배지 CSS 클래스 매핑 ────────────────────────────
const BADGE_CLASS_MAP: Record<string, string> = {
  포스트: "post",
  시리즈: "series",
  특집: "special",
  큐레이션: "curation",
  전시: "exhibit",
  아카이브: "archive",
};
const badgeClass = (badge: string) => BADGE_CLASS_MAP[badge] ?? "post";

// ─── 홈으로 리셋 ─────────────────────────────────────
const resetHome = () => {
  hasSearched.value = false;
  searchQuery.value = "";
  currentQuery.value = "";
  sources.value = [];
  answerText.value = "";
  isSearching.value = false;
  isGenerating.value = false;
  abortController?.abort();
};

// ─── 히스토리 로드 ───────────────────────────────────
const loadHistory = (item: { query: string }) => {
  searchQuery.value = item.query;
  handleSearch();
};

// ─── 검색 실행 (핵심) ────────────────────────────────
const handleSearch = async () => {
  const q = searchQuery.value.trim();
  if (!q || isSearching.value) return;

  // 이전 요청 취소
  abortController?.abort();
  abortController = new AbortController();

  // 상태 초기화
  hasSearched.value = true;
  isSearching.value = true;
  isGenerating.value = false;
  sources.value = [];
  answerText.value = "";
  currentQuery.value = q;

  addHistory(q);

  try {
    await chatStream(
      q,
      selectedBadge.value,
      {
        onSources: (s) => {
          sources.value = s;
          isSearching.value = false;
          isGenerating.value = true;
        },
        onToken: (token) => {
          answerText.value += token;
        },
        onDone: () => {
          isGenerating.value = false;
        },
        onError: (err) => {
          console.error("[CHAT ERROR]", err);
          isSearching.value = false;
          isGenerating.value = false;
        },
      },
      abortController.signal,
    );
  } catch (e: any) {
    if (e?.name !== "AbortError") {
      console.error(e);
    }
    isSearching.value = false;
    isGenerating.value = false;
  }
};
</script>

<style scoped>
/* 히스토리 스크롤 */
.history_con_wrap--scrollable {
  max-height: calc(100vh - 220px);
  overflow-y: auto;
  padding-right: 0.25rem;
}
</style>
