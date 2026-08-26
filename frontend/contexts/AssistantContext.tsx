"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";
import dynamic from "next/dynamic";
import { Modal } from "@/components/ui/Modal";

/* Lazy so the assistant does not sit in the shared bundle on every route.
   It is a large client component and most page loads never open it. */
const ChatInterface = dynamic(() => import("@/components/ChatInterface"), {
  ssr: false,
});

interface AssistantContextValue {
  /** Open the assistant. Pass a question to send it immediately. */
  open: (prompt?: string) => void;
  close: () => void;
  isOpen: boolean;
}

const AssistantContext = createContext<AssistantContextValue | null>(null);

/**
 * One assistant for the whole site.
 *
 * It lived only on the homepage, which is the wrong place for the thing people
 * come here for — a visitor reading a company page had no way to ask about the
 * company they were looking at. The provider sits in ClientLayout so any
 * header, page or component can call `useAssistant().open()`.
 */
export function AssistantProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [prompt, setPrompt] = useState<string | undefined>();

  const open = useCallback((next?: string) => {
    setPrompt(next);
    setIsOpen(true);
  }, []);

  const close = useCallback(() => setIsOpen(false), []);

  const value = useMemo(() => ({ open, close, isOpen }), [open, close, isOpen]);

  return (
    <AssistantContext.Provider value={value}>
      {children}
      {isOpen && (
        <Modal onClose={close} size="2xl" labelledBy="assistant-title">
          <ChatInterface initialPrompt={prompt} onClose={close} />
        </Modal>
      )}
    </AssistantContext.Provider>
  );
}

export function useAssistant() {
  const ctx = useContext(AssistantContext);
  if (!ctx) {
    throw new Error("useAssistant must be used inside AssistantProvider");
  }
  return ctx;
}
