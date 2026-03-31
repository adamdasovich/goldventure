import { Metadata } from "next";
import AccountLayoutClient from "./AccountLayoutClient";

export const metadata: Metadata = {
  robots: {
    index: false,
    follow: false,
  },
  title: "My Account",
};

export default function AccountLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AccountLayoutClient>{children}</AccountLayoutClient>;
}
