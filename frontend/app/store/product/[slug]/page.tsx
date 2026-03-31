import { Metadata } from "next";
import ProductPageClient from "./ProductPageClient";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getProduct(slug: string) {
  const fetchUrl = `${API_URL}/store/products/${slug}/`;

  try {
    const response = await fetch(fetchUrl, {
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error("Failed to fetch product for metadata:", error);
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
      description: "The requested product could not be found.",
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

export default function ProductPage() {
  return <ProductPageClient />;
}
