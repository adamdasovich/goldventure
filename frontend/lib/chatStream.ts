/**
 * Shared orchestration for the two chat surfaces (ChatInterface and
 * CompanyChatbot): stream-first with recovery, in one place so the policy
 * cannot drift between components.
 *
 * Policy:
 * - Stream when signed in; anonymous callers go straight to the blocking
 *   JSON endpoint (the stream endpoints require auth).
 * - A 401 refreshes the token once and retries the stream; a second 401
 *   (or a failed refresh) is a session-expired outcome.
 * - A server-decided rejection or mid-stream error event (ApiError) is
 *   surfaced, never re-posted — the server may already have charged the
 *   message, and re-posting would double-charge and double-run it.
 * - Only a transport-level failure before any text arrived (network drop,
 *   proxy trouble — a non-ApiError) falls back to the blocking endpoint.
 * - Text callbacks are throttled (~12/s) so a long answer doesn't force a
 *   re-render per SSE chunk.
 */

import { claudeAPI, ApiError } from "@/lib/api";
import type {
  ChatMessage,
  ChatStreamResult,
} from "@/lib/api";

export type UsageRemaining = NonNullable<ChatStreamResult["usage_remaining"]>;

export type ChatOutcome =
  | { kind: "answer"; text: string; usageRemaining?: UsageRemaining }
  | { kind: "session-expired" }
  | {
      kind: "error";
      message: string;
      /** Whatever streamed before the failure — show it with an interruption marker. */
      partialText: string;
      /** True only for the backend's own daily-quota rejection. */
      limitReached: boolean;
    };

export interface SendChatOptions {
  message: string;
  history: ChatMessage[];
  accessToken: string | null;
  /** From useAuth(); enables the 401 refresh-and-retry. */
  refreshAccessToken?: () => Promise<string | null>;
  /** Set to target /api/companies/{id}/chat/ instead of the main assistant. */
  companyId?: number;
  /** Live tool activity ("Searching technical reports"), null when it clears. */
  onStatus: (status: string | null) => void;
  /** The full accumulated answer text so far (not a delta), throttled. */
  onText: (fullText: string) => void;
}

const TEXT_FLUSH_MS = 80;

export async function sendChatMessage(
  opts: SendChatOptions,
): Promise<ChatOutcome> {
  const request = {
    message: opts.message,
    conversation_history: opts.history,
  };

  let text = "";
  let flushTimer: ReturnType<typeof setTimeout> | null = null;

  const flush = () => {
    flushTimer = null;
    opts.onText(text);
  };
  const finalFlush = () => {
    if (flushTimer) {
      clearTimeout(flushTimer);
      flush();
    }
  };

  const callbacks = {
    onStatus: (status: string) => opts.onStatus(status),
    onText: (delta: string) => {
      const first = text === "";
      text += delta;
      if (first) {
        // Paint the first words immediately; batch the rest.
        opts.onStatus(null);
        flush();
      } else if (!flushTimer) {
        flushTimer = setTimeout(flush, TEXT_FLUSH_MS);
      }
    },
  };

  const streamOnce = async (token: string): Promise<ChatStreamResult> => {
    text = "";
    try {
      return opts.companyId != null
        ? await claudeAPI.companyChatStream(
            opts.companyId,
            request,
            token,
            callbacks,
          )
        : await claudeAPI.chatStream(request, token, callbacks);
    } finally {
      finalFlush();
    }
  };

  const blockingOnce = async (token: string | null): Promise<ChatOutcome> => {
    const response =
      opts.companyId != null
        ? await claudeAPI.companyChat(opts.companyId, request, token || undefined)
        : await claudeAPI.chat(request, token || undefined);
    text = response.message;
    opts.onStatus(null);
    opts.onText(text);
    return {
      kind: "answer",
      text,
      usageRemaining: (response as any).usage_remaining,
    };
  };

  const answer = (result: ChatStreamResult): ChatOutcome => ({
    kind: "answer",
    text,
    usageRemaining: result.usage_remaining,
  });

  const failure = (error: unknown): ChatOutcome => ({
    kind: "error",
    message:
      error instanceof Error ? error.message : "Failed to get response",
    partialText: text,
    limitReached: error instanceof ApiError && error.limitReached,
  });

  const emptyAnswer = (): ChatOutcome => ({
    kind: "error",
    message: "The assistant returned an empty response — please try again.",
    partialText: "",
    limitReached: false,
  });

  try {
    if (!opts.accessToken) {
      return await blockingOnce(null);
    }

    try {
      const result = await streamOnce(opts.accessToken);
      // A completed stream with no text is a server-side oddity; the message
      // was already charged there, so surfacing beats a re-post that would
      // charge it twice.
      return text ? answer(result) : emptyAnswer();
    } catch (error) {
      if (
        error instanceof ApiError &&
        error.status === 401 &&
        opts.refreshAccessToken
      ) {
        const newToken = await opts.refreshAccessToken();
        if (!newToken) return { kind: "session-expired" };
        try {
          const result = await streamOnce(newToken);
          return text ? answer(result) : emptyAnswer();
        } catch (retryError) {
          if (retryError instanceof ApiError && retryError.status === 401) {
            return { kind: "session-expired" };
          }
          return failure(retryError);
        }
      }

      if (error instanceof ApiError) {
        // Definitive server answer (429 quota, 400, relayed provider error):
        // never re-post.
        return failure(error);
      }

      if (!text) {
        // Transport-level failure before anything arrived — the blocking
        // endpoint may still be reachable.
        return await blockingOnce(opts.accessToken);
      }

      // Died mid-answer: keep the partial text, mark the interruption.
      return failure(error);
    }
  } catch (error) {
    if (
      error instanceof ApiError &&
      error.status === 401 &&
      opts.accessToken
    ) {
      return { kind: "session-expired" };
    }
    return failure(error);
  }
}
