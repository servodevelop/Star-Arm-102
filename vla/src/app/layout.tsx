import type { Metadata } from "next";
import { Toaster } from "sonner";
import "./globals.css";
export const metadata: Metadata = {
  title: "vla-arms-agent · AI 机械臂",
  description: "用自然语言控制机械臂，完成观察、抓取与放置。",
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        {children}
        <Toaster
          position="bottom-center"
          theme="dark"
          duration={5000}
          richColors
          closeButton
          toastOptions={{
            closeButtonAriaLabel: "关闭提示",
            classNames: { title: "toast-message" },
          }}
        />
      </body>
    </html>
  );
}
