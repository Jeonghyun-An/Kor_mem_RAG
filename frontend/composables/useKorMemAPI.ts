/**
 * useKorMemAPI – 코리안메모리 RAG API composable
 *
 * 헌법 시스템의 useConstitutionAPI 구조를 참고:
 *   - 환경변수로 apiBase 관리
 *   - SSE 스트리밍 (sources → token → done)
 *   - 순수 검색 (벡터만)
 */

export interface SourceCard {
  chunk_id: string;
  title_main: string;
  title_sub: string;
  badge: string;
  keywords: string[];
  provider: string;
  detail_url: string;
  thumbnail: string;
  score: number;
  text_preview: string;
}

export interface ChatStreamCallbacks {
  onSources: (sources: SourceCard[]) => void;
  onToken: (token: string) => void;
  onDone: () => void;
  onError: (err: string) => void;
}

export const useKorMemAPI = () => {
  const config = useRuntimeConfig();
  const apiBase = computed(
    () => (config.public.apiBase as string) || "http://localhost:8001/api",
  );

  /**
   * SSE 채팅 스트리밍
   * POST /api/chat  →  sources → token → done
   */
  const chatStream = async (
    query: string,
    badgeFilter: string | null,
    callbacks: ChatStreamCallbacks,
    signal?: AbortSignal,
  ) => {
    const res = await fetch(`${apiBase.value}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        badge_filter: badgeFilter || null,
        top_k: 8,
        stream: true,
      }),
      signal,
    });

    if (!res.ok || !res.body) {
      callbacks.onError(`HTTP ${res.status}`);
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE 이벤트 파싱 (event: xxx\ndata: xxx\n\n)
      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";

      for (const raw of events) {
        if (!raw.trim()) continue;

        const lines = raw.split("\n");
        let eventType = "message";
        let dataStr = "";

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            dataStr = line.slice(6).trim();
          }
        }

        if (!dataStr) continue;
        try {
          const payload = JSON.parse(dataStr);
          if (eventType === "sources") callbacks.onSources(payload);
          else if (eventType === "token")
            callbacks.onToken(payload.token ?? "");
          else if (eventType === "done") callbacks.onDone();
          else if (eventType === "error")
            callbacks.onError(payload.error ?? "Unknown error");
        } catch {
          /* ignore bad JSON */
        }
      }
    }
  };

  /**
   * 순수 벡터 검색 (LLM 없이)
   * GET /api/search?q=...&top_k=8&badge=포스트
   */
  const search = async (params: {
    q: string;
    top_k?: number;
    badge?: string | null;
  }) => {
    const url = new URL(`${apiBase.value}/search`);
    url.searchParams.set("q", params.q);
    url.searchParams.set("top_k", String(params.top_k ?? 8));
    if (params.badge) url.searchParams.set("badge", params.badge);

    const res = await $fetch<{
      query: string;
      total: number;
      results: SourceCard[];
    }>(url.toString());
    return res;
  };

  /** 배지 목록 */
  const getBadges = async (): Promise<string[]> => {
    const res = await $fetch<{ badges: string[] }>(`${apiBase.value}/badges`);
    return res.badges;
  };

  return { chatStream, search, getBadges };
};
