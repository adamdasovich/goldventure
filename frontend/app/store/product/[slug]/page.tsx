import { Metadata } from "next";
import { notFound } from "next/navigation";
import ProductPageClient from "./ProductPageClient";

const API_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

async function getProduct(slug: string) {
  try {
    const response = await fetch(`${API_URL}/store/products/${slug}/`, {
      next: { revalidate: 1800 },
    });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

type Props = {
  params: Promise<{ slug: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const product = await getProduct(slug);

  if (!product) {
    return {
      title: "Product Not Found",
    };
  }

  const title = `${product.name} | Mining Specimens & Field Gear`;
  const description =
    product.short_description ||
    product.description?.slice(0, 155) ||
    `${product.name} - premium mining specimen available at Junior Mining Intelligence Store.`;

  const images = product.primary_image?.image_url
    ? [product.primary_image.image_url]
    : product.images?.[0]?.image_url
      ? [product.images[0].image_url]
      : ["/og-image.png"];

  return {
    title,
    description,
    openGraph: {
      title,
      description,
      type: "website",
      images,
      url: `https://juniorminingintelligence.com/store/product/${slug}`,
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images,
    },
    alternates: {
      canonical: `https://juniorminingintelligence.com/store/product/${slug}`,
    },
  };
}

export default async function ProductPage({ params }: Props) {
  const { slug } = await params;
  const product = await getProduct(slug);

  if (!product) {
    notFound();
  }

  const canonicalUrl = `https://juniorminingintelligence.com/store/product/${slug}`;
  const image =
    product.primary_image?.image_url || product.images?.[0]?.image_url;
  const inStock = (product.stock_quantity ?? product.inventory ?? 1) > 0;

  const productJsonLd = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: product.name,
    description:
      product.short_description ||
      product.description?.slice(0, 300) ||
      product.name,
    ...(image && { image: [image] }),
    sku: product.sku || product.slug,
    ...(product.category?.name && { category: product.category.name }),
    brand: {
      "@type": "Brand",
      name: "Junior Mining Intelligence Store",
    },
    ...(product.price && {
      offers: {
        "@type": "Offer",
        price: product.price,
        priceCurrency: product.currency || "USD",
        availability: inStock
          ? "https://schema.org/InStock"
          : "https://schema.org/OutOfStock",
        url: canonicalUrl,
        seller: {
          "@type": "Organization",
          name: "Junior Mining Intelligence",
        },
      },
    }),
  };

  const breadcrumbJsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      {
        "@type": "ListItem",
        position: 1,
        name: "Home",
        item: "https://juniorminingintelligence.com",
      },
      {
        "@type": "ListItem",
        position: 2,
        name: "Store",
        item: "https://juniorminingintelligence.com/store",
      },
      {
        "@type": "ListItem",
        position: 3,
        name: product.name,
        item: canonicalUrl,
      },
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(productJsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }}
      />
      <ProductPageClient />
    </>
  );
}
