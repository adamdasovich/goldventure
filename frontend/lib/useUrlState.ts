"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

/**
 * Keep a tool's controls in the query string.
 *
 * Every investor tool held its entire configuration in component state, so a
 * comparison someone spent five minutes assembling could not be bookmarked,
 * shared or reloaded. This mirrors a small record of control values into the
 * URL and reads it back on mount.
 *
 * Values equal to their default are omitted, so an untouched tool keeps a clean
 * URL rather than accumulating `?window=90&metal=XAU&sort=grade` for settings
 * nobody changed.
 *
 * History is replaced rather than pushed: typing in a search box should not
 * bury the previous page under a dozen back-button entries.
 */
export function useUrlState<T extends Record<string, string>>(
  defaults: T,
): [T, (patch: Partial<T>) => void] {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Defaults are captured once. A caller that rebuilds the object inline each
  // render would otherwise reset state on every render.
  const defaultsRef = useRef(defaults);

  const readFromUrl = useCallback((): T => {
    const next = { ...defaultsRef.current };
    for (const key of Object.keys(defaultsRef.current) as (keyof T)[]) {
      const fromUrl = searchParams.get(String(key));
      if (fromUrl !== null) {
        next[key] = fromUrl as T[keyof T];
      }
    }
    return next;
  }, [searchParams]);

  const [state, setState] = useState<T>(readFromUrl);

  // Adopt browser navigation (back/forward, or a pasted link).
  useEffect(() => {
    setState(readFromUrl());
  }, [readFromUrl]);

  const update = useCallback(
    (patch: Partial<T>) => {
      setState((prev) => {
        const next = { ...prev, ...patch };

        const params = new URLSearchParams();
        for (const [key, value] of Object.entries(next)) {
          if (value !== "" && value !== defaultsRef.current[key]) {
            params.set(key, value as string);
          }
        }
        const qs = params.toString();
        router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });

        return next;
      });
    },
    [pathname, router],
  );

  return [state, update];
}
