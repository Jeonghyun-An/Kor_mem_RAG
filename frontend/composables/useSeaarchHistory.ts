/**
 * useSearchHistory – 검색 히스토리 관리 (localStorage)
 * Library_AI_land의 history 패턴 그대로
 */

export interface HistoryItem {
  id: string;
  query: string;
  timestamp: number;
}

const STORAGE_KEY = "kormem_search_history";
const MAX_ITEMS = 30;

export const useSearchHistory = () => {
  const history = ref<HistoryItem[]>([]);

  const _load = () => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      history.value = raw ? JSON.parse(raw) : [];
    } catch {
      history.value = [];
    }
  };

  const _save = () => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history.value));
    } catch {}
  };

  const addHistory = (query: string) => {
    const id = `${Date.now()}_${Math.random().toString(36).slice(2)}`;
    const item: HistoryItem = { id, query, timestamp: Date.now() };
    // 중복 제거
    history.value = history.value.filter((h) => h.query !== query);
    history.value.unshift(item);
    if (history.value.length > MAX_ITEMS)
      history.value = history.value.slice(0, MAX_ITEMS);
    _save();
  };

  const deleteHistory = (id: string) => {
    history.value = history.value.filter((h) => h.id !== id);
    _save();
  };

  const clearHistory = () => {
    history.value = [];
    _save();
  };

  /** Library_AI_land와 동일: "오늘" / "어제" / 날짜 문자열로 그룹핑 */
  const groupedHistory = computed(() => {
    const groups: Record<string, HistoryItem[]> = {};
    const now = new Date();
    const today = new Date(
      now.getFullYear(),
      now.getMonth(),
      now.getDate(),
    ).getTime();
    const yesterday = today - 86400000;

    for (const item of history.value) {
      const d = new Date(item.timestamp);
      const dStart = new Date(
        d.getFullYear(),
        d.getMonth(),
        d.getDate(),
      ).getTime();
      let label: string;
      if (dStart === today) label = "오늘";
      else if (dStart === yesterday) label = "어제";
      else
        label = `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getDate()).padStart(2, "0")}`;

      if (!groups[label]) groups[label] = [];
      groups[label].push(item);
    }
    return groups;
  });

  const formatDate = (timestamp: number): string => {
    const d = new Date(timestamp);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const yest = new Date(today);
    yest.setDate(today.getDate() - 1);
    const dDate = new Date(d);
    dDate.setHours(0, 0, 0, 0);
    if (+dDate === +today) return "오늘";
    if (+dDate === +yest) return "어제";
    return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getDate()).padStart(2, "0")}`;
  };

  onMounted(_load);

  return {
    history,
    groupedHistory,
    addHistory,
    deleteHistory,
    clearHistory,
    formatDate,
  };
};
