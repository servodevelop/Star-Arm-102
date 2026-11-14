"use client";

import { useEffect, useSyncExternalStore } from "react";
import { Toaster } from "sonner";
import { getLocale, restoreLocale, subscribeLocale } from "@/lib/i18n";

export function useLocale() {
  return useSyncExternalStore(subscribeLocale, getLocale, () => "en" as const);
}
export function LocaleProvider({ children }: { children: React.ReactNode }) {
  const locale = useLocale();
  useEffect(() => {
    restoreLocale();
  }, []);
  useEffect(() => {
    document.documentElement.lang = locale === "zh" ? "zh-CN" : "en";
  }, [locale]);
  return (
    <>
      <title>
        {locale === "zh"
          ? "vla-arms-agent · AI 机械臂"
          : "vla-arms-agent · AI robot arm"}
      </title>
      <meta
        name="description"
        content={
          locale === "zh"
            ? "用自然语言控制机械臂，完成观察、抓取与放置。"
            : "Control a robot arm with natural language for observation, grasping, and placement."
        }
      />
      {children}
      <Toaster
        position="bottom-center"
        theme="dark"
        duration={5000}
        richColors
        closeButton
        toastOptions={{
          closeButtonAriaLabel:
            locale === "zh" ? "关闭提示" : "Dismiss notification",
          classNames: { title: "toast-message" },
        }}
      />
    </>
  );
}
