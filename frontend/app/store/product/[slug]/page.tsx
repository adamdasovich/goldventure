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
      cache: "no-store",
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

  return <ProductPageClient />;
}
