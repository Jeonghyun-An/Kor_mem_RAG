<template>
  <!-- [S] skip menu -->
  <ul class="skip_menu">
    <li><a href="#contents_wrap">검색 바로가기</a></li>
  </ul>
  <!-- [E] skip menu -->

  <!-- [S] contents_wrap -->
  <div class="contents_wrap" id="contents_wrap">
    <!-- [S] left_menu_wrap -->
    <div class="left_menu_wrap" :class="{ open: sidebarOpen || hasSearched }">
      <div class="left_menu_hd">
        <a href="#;" class="hd_logo_link" @click.prevent="resetHome">
          <img
            src="/img/layout/hd_logo.svg"
            alt="기억의 도서관 코리안메모리 AI에이전트"
            class="hd_logo view_ctr"
          />
        </a>
        <a
          href="#;"
          class="left_menu_trigger"
          :aria-label="sidebarOpen ? '메뉴 닫기' : '메뉴 열기'"
          @click.prevent="toggleSidebar"
        ></a>
      </div>

      <div class="left_menu_con_wrap view_ctr">
        <div class="left_menu_con">
          <div class="tab_con_wrap">
            <div class="tab_history tab_con on">
              <div class="con_tit ty_01 mt_20i">히스토리</div>

              <div class="history_con_wrap history_con_wrap_scroll">
                <template v-if="history.length">
                  <div
                    v-for="(items, date) in groupedHistory"
                    :key="date"
                    class="history_con"
                  >
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
                  <div class="history_empty">검색 기록이 없습니다.</div>
                </template>
              </div>
            </div>
          </div>

          <div class="left_menu_btm_info">
            <div class="left_menu_btm_txt">
              AI가 생성한 콘텐츠입니다.
              <br class="tab_show" />
              품질이 달라질 수 있으니 정확성을 확인해 주세요.
            </div>

            <div class="info_wrap ty_01">
              <span class="info">
                <a
                  href="https://nl.go.kr/koreanmemory/"
                  target="_blank"
                  rel="noopener"
                  class="info_item ty_01"
                >
                  <img src="/img/icon/ic_q.svg" alt="" />
                  코리안메모리 바로가기
                </a>
              </span>
              <span class="info">
                <a href="#;" class="info_item ty_01" @click.prevent>
                  <img src="/img/icon/ic_privacy.svg" alt="" />
                  개인정보 보호 방침 및 면책 조항
                </a>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- [E] left_menu_wrap -->

    <!-- [S] search_wrap : 메인 -->
    <div v-if="!hasSearched" class="search_wrap search_main_wrap">
      <div class="search_wrap_hd">
        <div class="area">
          <img
            src="/img/layout/hd_logo.svg"
            alt="기억의 도서관 코리안메모리 AI에이전트"
            class="hd_logo tab_hidden"
          />
        </div>

        <div
          class="member_util_wrap trigger_wrap"
          :class="{ on: memberMenuOpen }"
          id="member_util_trigger_wrap"
        >
          <a
            href="#;"
            class="trigger member_util_trigger"
            id="member_util_trigger"
            @click.prevent="memberMenuOpen = !memberMenuOpen"
          >
            <img src="/img/icon/ic_member.svg" alt="" />
            {{ memberName }}
          </a>

          <div
            v-show="memberMenuOpen"
            class="trigger_toggle member_util_trigger_toggle"
            id="member_util_trigger_toggle"
          >
            <div class="member_wrap">
              <div class="member_info">
                <div class="member_name">{{ memberName }}</div>
                <div class="member_email">{{ memberEmail }}</div>
              </div>
              <a href="#;" class="logout btn sz_md" @click.prevent>
                <img src="/img/icon/ic_logout.svg" alt="" />
                로그아웃
              </a>
            </div>

            <ul class="member_util_list">
              <li class="member_util_item">
                <a href="#;" class="util_item_inn" @click.prevent>
                  <span class="ic ic_bookmark"></span>
                  <span class="txt">내 즐겨찾기</span>
                </a>
              </li>
              <li class="member_util_item">
                <a href="#;" class="util_item_inn" @click.prevent>
                  <span class="ic ic_history"></span>
                  <span class="txt">내 검색기록</span>
                </a>
              </li>
              <li
                class="member_util_item lang_trigger_wrap trigger_wrap"
                :class="{ on: langMenuOpen }"
              >
                <a
                  href="#;"
                  class="util_item_inn trigger"
                  id="lang_trigger"
                  @click.prevent="langMenuOpen = !langMenuOpen"
                >
                  <span class="ic ic_lang"></span>
                  <span class="txt">
                    표시언어:
                    <span class="fw_b lang">{{ displayLanguage }}</span>
                  </span>
                </a>

                <div
                  v-show="langMenuOpen"
                  class="trigger_toggle lang_trigger_toggle"
                  id="lang_trigger_toggle"
                >
                  <div class="lang_trigger_toggle_hd">
                    <img src="/img/icon/ic_lang_b.svg" alt="" />
                    표시언어
                  </div>
                  <ul class="lang_list">
                    <li
                      class="lang_item"
                      :class="{ on: displayLanguage === 'English' }"
                    >
                      <a
                        href="#;"
                        class="inn"
                        @click.prevent="setLanguage('English')"
                      >
                        English
                      </a>
                    </li>
                    <li
                      class="lang_item"
                      :class="{ on: displayLanguage === '한국어' }"
                    >
                      <a
                        href="#;"
                        class="inn"
                        @click.prevent="setLanguage('한국어')"
                      >
                        한국어
                      </a>
                    </li>
                  </ul>
                  <a
                    href="#;"
                    class="btn bg_black sz_md trigger_close"
                    @click.prevent="langMenuOpen = false"
                  >
                    취소
                  </a>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div class="search_main">
        <div class="inner">
          <img
            src="/img/main/txt_search_main.svg"
            alt="기억의 도서관 코리안메모리 AI 에이전트"
            class="tab_hidden"
          />
          <img
            src="/img/main/txt_search_main_mo.svg"
            alt="기억의 도서관 코리안메모리 AI 에이전트"
            class="tab_show_ib"
          />

          <div class="main_txt">
            자원을 디지털화하고 큐레이션을 분석해주는 코리안메모리의 생성형
            인공지능 서비스입니다.
          </div>

          <div class="search_box">
            <div
              class="trigger_wrap search_condition_trigger_wrap"
              :class="{ on: conditionOpen }"
              id="search_condition_trigger_wrap"
            >
              <a
                href="#;"
                aria-label="검색 조건 설정"
                class="trigger search_condition_trigger"
                id="search_condition_trigger"
                @click.prevent="conditionOpen = !conditionOpen"
              ></a>

              <div
                v-show="conditionOpen"
                class="trigger_toggle search_condition_trigger_toggle"
                id="search_condition_trigger_toggle"
              >
                <div class="search_condition_wrap">
                  <div class="select_box">
                    <select v-model="selectedBadge">
                      <option :value="null">모든 양식</option>
                      <option
                        v-for="badge in BADGES"
                        :key="badge"
                        :value="badge"
                      >
                        {{ badge }}
                      </option>
                    </select>
                  </div>

                  <div class="select_box">
                    <select v-model="dateFilter">
                      <option value="">모든 날짜</option>
                      <option value="latest">최신순</option>
                    </select>
                  </div>

                  <div class="form_check ty_01">
                    <input id="online" v-model="onlineOnly" type="checkbox" />
                    <label for="online">온라인 이용가능</label>
                  </div>
                </div>
              </div>
            </div>

            <input
              v-model="searchQuery"
              type="text"
              title="검색어 입력"
              placeholder="질문을 입력해주세요."
              class="search_box_input"
              @keyup.enter="handleSearch"
            />
            <button
              class="search_box_btn"
              aria-label="검색"
              :disabled="isSearching || isGenerating"
              @click="handleSearch"
            ></button>
          </div>

          <div class="question_example">
            <div class="question_example_hd">
              <div class="con_tit ty_01">질문 예시</div>
              <a href="#;" class="info_item ty_01" @click.prevent>
                <img src="/img/icon/ic_q.svg" alt="" />
                Ai 어시스턴트 소개
              </a>
            </div>

            <ul class="question_example_list">
              <li
                v-for="example in EXAMPLES"
                :key="example"
                class="question_example_item"
              >
                <a
                  href="#;"
                  class="inn"
                  @click.prevent="searchFromExample(example)"
                >
                  <div class="item ellipsis line02">
                    {{ example }}
                  </div>
                  <div class="arr"></div>
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
    <!-- [E] search_wrap : 메인 -->

    <!-- [S] search_wrap : 결과/생성중 -->
    <div v-else class="search_wrap search_result_wrap open">
      <div class="search_wrap_hd">
        <div class="area"></div>

        <div
          class="member_util_wrap trigger_wrap"
          :class="{ on: memberMenuOpen }"
          id="member_util_trigger_wrap_result"
        >
          <a
            href="#;"
            class="trigger member_util_trigger"
            id="member_util_trigger_result"
            @click.prevent="memberMenuOpen = !memberMenuOpen"
          >
            <img src="/img/icon/ic_member.svg" alt="" />
            {{ memberName }}
          </a>

          <div
            v-show="memberMenuOpen"
            class="trigger_toggle member_util_trigger_toggle"
          >
            <div class="member_wrap">
              <div class="member_info">
                <div class="member_name">{{ memberName }}</div>
                <div class="member_email">{{ memberEmail }}</div>
              </div>
              <a href="#;" class="logout btn sz_md" @click.prevent>
                <img src="/img/icon/ic_logout.svg" alt="" />
                로그아웃
              </a>
            </div>

            <ul class="member_util_list">
              <li class="member_util_item">
                <a href="#;" class="util_item_inn" @click.prevent>
                  <span class="ic ic_bookmark"></span>
                  <span class="txt">내 즐겨찾기</span>
                </a>
              </li>
              <li class="member_util_item">
                <a href="#;" class="util_item_inn" @click.prevent>
                  <span class="ic ic_history"></span>
                  <span class="txt">내 검색기록</span>
                </a>
              </li>
              <li
                class="member_util_item lang_trigger_wrap trigger_wrap"
                :class="{ on: langMenuOpen }"
              >
                <a
                  href="#;"
                  class="util_item_inn trigger"
                  @click.prevent="langMenuOpen = !langMenuOpen"
                >
                  <span class="ic ic_lang"></span>
                  <span class="txt">
                    표시언어:
                    <span class="fw_b lang">{{ displayLanguage }}</span>
                  </span>
                </a>

                <div
                  v-show="langMenuOpen"
                  class="trigger_toggle lang_trigger_toggle"
                >
                  <div class="lang_trigger_toggle_hd">
                    <img src="/img/icon/ic_lang_b.svg" alt="" />
                    표시언어
                  </div>
                  <ul class="lang_list">
                    <li
                      class="lang_item"
                      :class="{ on: displayLanguage === 'English' }"
                    >
                      <a
                        href="#;"
                        class="inn"
                        @click.prevent="setLanguage('English')"
                      >
                        English
                      </a>
                    </li>
                    <li
                      class="lang_item"
                      :class="{ on: displayLanguage === '한국어' }"
                    >
                      <a
                        href="#;"
                        class="inn"
                        @click.prevent="setLanguage('한국어')"
                      >
                        한국어
                      </a>
                    </li>
                  </ul>
                  <a
                    href="#;"
                    class="btn bg_black sz_md trigger_close"
                    @click.prevent="langMenuOpen = false"
                  >
                    취소
                  </a>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div class="search_list_wrap">
        <!-- 생성 중 화면 -->
        <div v-if="isSearching && !sources.length" class="search_q_item">
          <div class="search_q_tit">{{ currentQuery }}</div>
          <div class="loading_wrap">
            <div class="circle_wrap">
              <img src="/img/icon/ic_ing.gif" alt="" class="circle_img" />
            </div>
            <div class="loading_txt">답변 생성 중 입니다...</div>
          </div>
        </div>

        <!-- 결과 화면: 스토리별 반복 -->
        <template v-else-if="!isSearching && (answerText || sources.length)">
          <div
            v-for="(story, idx) in sources"
            :key="story.item_id"
            class="search_q_item"
            :class="{ story_divider: idx > 0 }"
          >
            <!-- 첫 번째는 검색어, 이후는 스토리 제목 -->
            <div class="search_q_tit">
              {{ idx === 0 ? currentQuery : story.title_main }}
            </div>

            <div class="list_answer_list">
              <!-- [S] 질의 요약 -->
              <div class="list_answer_item">
                <div class="con_tit ty_02 mb_20i">
                  <img src="/img/icon/ic_summary.svg" alt="" class="ic" />
                  질의 요약
                </div>
                <div
                  class="summary_txt"
                  v-html="markedParse(storyAnswers[idx] || '')"
                ></div>
              </div>
              <!-- [E] 질의 요약 -->

              <!-- [S] 관련 키워드 -->
              <div class="list_answer_item" v-if="story.keywords?.length">
                <div class="con_tit ty_02">
                  <img
                    src="/img/icon/ic_related_keyword.svg"
                    alt=""
                    class="ic"
                  />
                  관련 키워드
                </div>
                <ul class="related_keyword_list">
                  <li
                    v-for="keyword in story.keywords"
                    :key="keyword"
                    class="related_keyword_item"
                  >
                    <a
                      href="#;"
                      class="inn"
                      @click.prevent="searchByKeyword(keyword)"
                    >
                      {{ keyword }}
                    </a>
                  </li>
                </ul>
              </div>
              <!-- [E] 관련 키워드 -->

              <!-- [S] 관련 컬렉션 -->
              <div class="list_answer_item" v-if="story.title_main">
                <div class="con_tit ty_02">
                  <img
                    src="/img/icon/ic_related_collection.svg"
                    alt=""
                    class="ic"
                  />
                  관련 컬렉션
                </div>
                <div class="sc_menu_wrap bar_no">
                  <div class="sc_menu ty_02">
                    <a
                      :href="story.detail_url || '#'"
                      class="sc_menu_item"
                      target="_blank"
                      rel="noopener"
                    >
                      <span class="txt_underline">
                        <span class="inn_txt">{{ story.title_main }}</span>
                      </span>
                    </a>
                  </div>
                </div>
              </div>
              <!-- [E] 관련 컬렉션 -->

              <!-- [S] 관련 자원 -->
              <div class="list_answer_item" v-if="story.substories?.length">
                <div class="con_tit ty_02 mb_20i">
                  <img
                    src="/img/icon/ic_related_resource.svg"
                    alt=""
                    class="ic"
                  />
                  관련 자원
                </div>

                <div class="sc_tab_con_wrap">
                  <div class="sc_menu_wrap">
                    <div class="sc_menu ty_03">
                      <a
                        v-for="sub in story.substories.slice(0, 12)"
                        :key="`${story.item_id}_${sub.title_sub}`"
                        :href="sub.detail_url || story.detail_url || '#'"
                        class="sc_menu_item"
                        target="_blank"
                        rel="noopener"
                      >
                        <div class="img_wrap">
                          <img
                            v-if="sub.thumbnail || story.thumbnail"
                            :src="sub.thumbnail || story.thumbnail"
                            :alt="sub.title_sub"
                            @error="hideBrokenImage"
                          />
                        </div>
                        <div class="txt_wrap">
                          <span class="resource_type">
                            {{ sub.badge || story.badge || "텍스트" }}
                          </span>
                          <div class="tit ellipsis line02">
                            {{ sub.title_sub || story.title_main }}
                          </div>
                          <div class="resource_meta">
                            {{ sub.provider || story.provider }}
                          </div>
                        </div>
                      </a>
                    </div>
                  </div>
                </div>
              </div>
              <!-- [E] 관련 자원 -->
            </div>
          </div>
        </template>

        <!-- 빈 결과 -->
        <div v-else-if="!isSearching && hasSearched" class="search_q_item">
          <div class="search_q_tit">{{ currentQuery }}</div>
          <div class="empty_result">관련 자료를 찾을 수 없습니다.</div>
        </div>
      </div>

      <div class="search_box_wrap">
        <div class="search_box">
          <div
            class="trigger_wrap search_condition_trigger_wrap"
            :class="{ on: conditionOpen }"
          >
            <a
              href="#;"
              aria-label="검색 조건 설정"
              class="trigger search_condition_trigger"
              @click.prevent="conditionOpen = !conditionOpen"
            ></a>

            <div
              v-show="conditionOpen"
              class="trigger_toggle search_condition_trigger_toggle"
            >
              <div class="search_condition_wrap">
                <div class="select_box">
                  <select v-model="selectedBadge">
                    <option :value="null">모든 양식</option>
                    <option v-for="badge in BADGES" :key="badge" :value="badge">
                      {{ badge }}
                    </option>
                  </select>
                </div>

                <div class="select_box">
                  <select v-model="dateFilter">
                    <option value="">모든 날짜</option>
                    <option value="latest">최신순</option>
                  </select>
                </div>

                <div class="form_check ty_01">
                  <input
                    id="online_result"
                    v-model="onlineOnly"
                    type="checkbox"
                  />
                  <label for="online_result">온라인 이용가능</label>
                </div>
              </div>
            </div>
          </div>

          <input
            v-model="searchQuery"
            type="text"
            title="검색어 입력"
            placeholder="질문을 입력해주세요."
            class="search_box_input"
            @keyup.enter="handleSearch"
          />
          <button
            class="search_box_btn"
            aria-label="검색"
            :disabled="isSearching || isGenerating"
            @click="handleSearch"
          ></button>
        </div>
      </div>
    </div>
    <!-- [E] search_wrap : 결과/생성중 -->
  </div>
  <!-- [E] contents_wrap -->
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { marked } from "marked";
import { useKorMemAPI } from "@/composables/useKorMemAPI";
import { useSearchHistory } from "@/composables/useSearchHistory";

definePageMeta({ layout: false });

type HistoryItem = {
  id: string | number;
  query: string;
};

type SubStory = {
  title_sub: string;
  detail_url?: string;
  thumbnail?: string;
  provider?: string;
  badge?: string;
};

type StorySource = {
  item_id: string;
  title_main: string;
  badge?: string;
  keywords?: string[];
  provider?: string;
  detail_url?: string;
  thumbnail?: string;
  substory_count?: number;
  substories?: SubStory[];
};

const sources = ref<StorySource[]>([]);
const BADGES = ["포스트", "시리즈", "특집", "큐레이션", "전시", "아카이브"];
const EXAMPLES = [
  "조선 후기, 민화만이 가진 독특한 구도 및 예술적 특징을 요약해 줘.",
  "'올해의 인물' 컬렉션 중, 이현세 거장의 작품세계 특징을 알려줘.",
  "전통의 숨결 위에 미래를 짓는 문화 도시, 서울의 스토리 콘텐츠 구성을 알려줘.",
  "한국 창작 뮤지컬의 여정의 관련 스토리와 컬렉션을 찾아줘.",
];

const memberName = "최승환 님";
const memberEmail = "test0505@ajou.ac.kr";

const searchQuery = ref("");
const currentQuery = ref("");
const selectedBadge = ref<string | null>(null);
const dateFilter = ref("");
const onlineOnly = ref(false);

const hasSearched = ref(false);
const isSearching = ref(false);
const isGenerating = ref(false);

const sidebarOpen = ref(false);
const memberMenuOpen = ref(false);
const langMenuOpen = ref(false);
const conditionOpen = ref(false);
const displayLanguage = ref<"한국어" | "English">("한국어");

const answerText = ref("");

let abortController: AbortController | null = null;

const { chatStream } = useKorMemAPI();
const { history, groupedHistory, addHistory, deleteHistory } =
  useSearchHistory();

marked.setOptions({ breaks: true, gfm: true });

// template에서 직접 호출 가능하도록 노출
function markedParse(text: string): string {
  if (!text?.trim()) return "";
  return marked.parse(text) as string;
}

// LLM 출력을 ## 헤더(스토리 제목) 기준으로 분리해서 각 스토리에 매핑
const storyAnswers = computed((): string[] => {
  const raw = answerText.value?.trim();
  if (!raw || !sources.value.length) return sources.value.map(() => "");

  // "## " 기준으로 블록 분리
  const blocks = raw.split(/(?=^## )/m).filter((b) => b.trim());

  return sources.value.map((story, i) => {
    // title_main이 포함된 블록 우선 매핑
    const matched = blocks.find((b) =>
      b.toLowerCase().includes(story.title_main.toLowerCase()),
    );
    if (matched) return matched.trim();
    // 못 찾으면 순서대로
    return (blocks[i] || "").trim();
  });
});

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value;
}

function setLanguage(lang: "한국어" | "English") {
  displayLanguage.value = lang;
  langMenuOpen.value = false;
}

function resetHome() {
  abortController?.abort();
  searchQuery.value = "";
  currentQuery.value = "";
  answerText.value = "";
  sources.value = [];
  hasSearched.value = false;
  isSearching.value = false;
  isGenerating.value = false;
  memberMenuOpen.value = false;
  langMenuOpen.value = false;
  conditionOpen.value = false;
}

function loadHistory(item: HistoryItem) {
  searchQuery.value = item.query;
  handleSearch();
}

function searchFromExample(example: string) {
  searchQuery.value = example;
  handleSearch();
}

function searchByKeyword(keyword: string) {
  searchQuery.value = keyword;
  handleSearch();
}

function hideBrokenImage(event: Event) {
  const target = event.target as HTMLImageElement | null;
  if (target) target.style.display = "none";
}

async function handleSearch() {
  const q = searchQuery.value.trim();
  if (!q || isSearching.value || isGenerating.value) return;

  abortController?.abort();
  abortController = new AbortController();

  hasSearched.value = true;
  currentQuery.value = q;
  answerText.value = "";
  sources.value = [];
  isSearching.value = true;
  isGenerating.value = false;
  memberMenuOpen.value = false;
  langMenuOpen.value = false;
  conditionOpen.value = false;

  addHistory(q);

  try {
    await chatStream(
      q,
      selectedBadge.value,
      {
        onSources: (payload: any[]) => {
          sources.value = Array.isArray(payload) ? payload : [];
          isSearching.value = false;
          isGenerating.value = sources.value.length > 0;
        },
        onToken: (token: string) => {
          answerText.value += token;
        },
        onDone: () => {
          isSearching.value = false;
          isGenerating.value = false;
        },
        onError: (error: unknown) => {
          console.error("[koreanmemory chat error]", error);
          isSearching.value = false;
          isGenerating.value = false;
        },
      },
      abortController.signal,
    );
  } catch (error: any) {
    if (error?.name !== "AbortError") console.error(error);
    isSearching.value = false;
    isGenerating.value = false;
  }
}
</script>

<style scoped>
.search_main .inner > img.tab_hidden {
  display: block;
  margin: 0 auto;
}
</style>
