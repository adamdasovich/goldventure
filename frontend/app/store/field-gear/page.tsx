import FieldGearClient from "./FieldGearClient";
import StoreCategoryContent from "@/components/StoreCategoryContent";

// Metadata + canonical live in layout.tsx.
export const revalidate = 3600;

/**
 * Server shell. The listing itself is a client component whose product grid
 * loads after hydration, so the page rendered under 100 words to a crawler and
 * Google reported it under Soft 404 on 2026-08-23. The category copy below is
 * server-rendered, which makes the page indexable without disturbing the
 * commerce UI above it.
 */
export default function FieldGearPage() {
  return (
    <>
      <FieldGearClient />
      <StoreCategoryContent category="field-gear" />
    </>
  );
}
