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
        <div class="search_q_item">
          <div class="search_q_tit">{{ currentQuery }}</div>

          <!-- 생성 중 화면 -->
          <div v-if="isSearching && !sources.length" class="loading_wrap">
            <div class="circle_wrap">
              <img src="/img/icon/ic_ing.gif" alt="" class="circle_img" />
            </div>
            <div class="loading_txt">답변 생성 중 입니다...</div>
          </div>

          <!-- 결과 화면 -->
          <div
            v-else-if="!isSearching && (answerText || sources.length)"
            class="list_answer_list"
          >
            <!-- [S] 질의 요약 -->
            <div class="list_answer_item">
              <div class="con_tit ty_02 mb_20i">
                <img src="/img/icon/ic_summary.svg" alt="" class="ic" />
                질의 요약
              </div>
              <div class="summary_txt" v-html="renderedAnswer"></div>
            </div>
            <!-- [E] 질의 요약 -->

            <!-- [S] 관련 키워드 -->
            <div class="list_answer_item" v-if="relatedKeywords.length">
              <div class="con_tit ty_02">
                <img src="/img/icon/ic_related_keyword.svg" alt="" class="ic" />
                관련 키워드
              </div>
              <ul class="related_keyword_list">
                <li
                  v-for="keyword in relatedKeywords"
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
            <div class="list_answer_item" v-if="relatedCollections.length">
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
                    v-for="collection in relatedCollections"
                    :key="collection.title"
                    :href="collection.link || '#'"
                    class="sc_menu_item"
                    target="_blank"
                    rel="noopener"
                  >
                    <span class="txt_underline">
                      <span class="inn_txt">{{ collection.title }}</span>
                    </span>
                  </a>
                </div>
              </div>
            </div>
            <!-- [E] 관련 컬렉션 -->

            <!-- [S] 관련 자원 -->
            <div class="list_answer_item" v-if="relatedResources.length">
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
                      v-for="resource in relatedResources"
                      :key="resource.key"
                      :href="resource.detail_url || '#'"
                      class="sc_menu_item"
                      target="_blank"
                      rel="noopener"
                    >
                      <div class="img_wrap">
                        <img
                          v-if="resource.thumbnail"
                          :src="resource.thumbnail"
                          :alt="resource.title_main"
                          @error="hideBrokenImage"
                        />
                      </div>

                      <div class="txt_wrap">
                        <span class="resource_type">
                          {{ resource.badge || "텍스트" }}
                        </span>
                        <div class="tit ellipsis line02">
                          {{ resource.title_sub || resource.title_main }}
                        </div>
                        <div class="resource_meta">
                          {{ resource.provider }}
                        </div>
                      </div>
                    </a>
                  </div>
                </div>
              </div>
            </div>
            <!-- [E] 관련 자원 -->
          </div>

          <div v-else-if="!isSearching && hasSearched" class="empty_result">
            관련 자료를 찾을 수 없습니다.
          </div>
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

// SourceItem → StorySource로 교체
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

marked.setOptions({
  breaks: true,
  gfm: true,
});

const renderedAnswer = computed(() => {
  const raw = answerText.value?.trim();
  if (!raw) return "";
  return marked.parse(raw) as string;
});

// 관련 키워드: 모든 스토리의 keywords 합산
const relatedKeywords = computed(() => {
  const flat = sources.value.flatMap((s) => s.keywords || []);
  return [...new Set(flat)].filter(Boolean).slice(0, 14);
});

// 관련 컬렉션: 스토리 단위 (title_main + detail_url)
const relatedCollections = computed(() => {
  return sources.value
    .filter((s) => s.title_main)
    .map((s) => ({ title: s.title_main, link: s.detail_url }))
    .slice(0, 12);
});

// 관련 자원: substory 카드 단위로 펼치기
const relatedResources = computed(() => {
  const out: Array<{
    key: string;
    title_main: string;
    title_sub: string;
    badge?: string;
    detail_url?: string;
    thumbnail?: string;
    provider?: string;
  }> = [];

  for (const story of sources.value) {
    const subs = story.substories || [];
    if (subs.length === 0) {
      // substory 없으면 스토리 자체를 1개 카드로
      out.push({
        key: story.item_id,
        title_main: story.title_main,
        title_sub: "",
        badge: story.badge,
        detail_url: story.detail_url,
        thumbnail: story.thumbnail,
        provider: story.provider,
      });
    } else {
      for (const sub of subs) {
        out.push({
          key: `${story.item_id}_${sub.title_sub}`,
          title_main: story.title_main,
          title_sub: sub.title_sub,
          badge: sub.badge || story.badge,
          detail_url: sub.detail_url || story.detail_url,
          thumbnail: sub.thumbnail || story.thumbnail,
          provider: sub.provider || story.provider,
        });
      }
    }
  }

  return out.slice(0, 12);
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
          console.log("[onSources payload]", payload);
          sources.value = Array.isArray(payload) ? payload : [];
          console.log("[sources.value]", sources.value);
          isSearching.value = false;
          isGenerating.value = true;
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
    if (error?.name !== "AbortError") {
      console.error(error);
    }
    isSearching.value = false;
    isGenerating.value = false;
  }
}
</script>

<style scoped>
.sc_menu.ty_03 {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.sc_menu.ty_03 .sc_menu_item {
  display: block;
}

.sc_menu.ty_03 .img_wrap {
  width: 100%;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  background: #f5f5f5;
  border-radius: 8px;
}

.sc_menu.ty_03 .img_wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.sc_menu.ty_03 .txt_wrap {
  margin-top: 8px;
}

.related_keyword_list,
.sc_menu.ty_02,
.sc_menu.ty_03 {
  opacity: 1 !important;
  visibility: visible !important;
}
.hd_logo_link {
  display: inline-flex;
  align-items: center;
}

.history_con_wrap_scroll {
  max-height: calc(100vh - 260px);
  overflow-y: auto;
  padding-right: 4px;
}

.history_empty {
  padding: 16px 4px;
  font-size: 14px;
  color: #767676;
}

.empty_result {
  padding: 40px 0;
  text-align: center;
  font-size: 15px;
  color: #666;
}

.resource_meta {
  margin-top: 6px;
  font-size: 12px;
  color: #7a7a7a;
}

.summary_txt :deep(p) {
  margin-bottom: 12px;
  line-height: 1.8;
}

.summary_txt :deep(ul),
.summary_txt :deep(ol) {
  padding-left: 20px;
  margin: 10px 0 14px;
}

.summary_txt :deep(li) {
  margin-bottom: 6px;
  line-height: 1.7;
}

.summary_txt :deep(strong) {
  font-weight: 700;
}

.summary_txt :deep(h1),
.summary_txt :deep(h2),
.summary_txt :deep(h3),
.summary_txt :deep(h4) {
  margin: 18px 0 10px;
  font-weight: 700;
  line-height: 1.5;
}

.sc_menu.ty_03 .img_wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.search_main_wrap .search_main {
  min-height: calc(100vh - 120px);
  display: flex;
  align-items: center;
}

.search_main_wrap .inner {
  width: 100%;
}

.search_main .inner {
  text-align: center;
}

.search_main .inner > img.tab_hidden {
  display: block;
  margin: 0 auto;
}

@media (max-width: 1024px) {
  .history_con_wrap_scroll {
    max-height: calc(100vh - 220px);
  }
}
</style>
