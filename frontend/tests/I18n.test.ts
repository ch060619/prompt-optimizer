import { describe, expect, it } from "vitest";

import { formatCount, formatDate, formatNumber, localeFromSetting, resourceCatalog, resourceKeys, t } from "../src/i18n";

// RC ID: RC-252. Verify typed locale resources, Chinese/English parity, and locale formatting.

describe("i18n resources", () => {
  it("keeps complete Chinese and English catalogs with stable keys", () => {
    const catalog = resourceCatalog();
    expect(Object.keys(catalog["zh-CN"]).sort()).toEqual(resourceKeys());
    expect(Object.keys(catalog["en-US"]).sort()).toEqual(resourceKeys());
    expect(t("zh-CN", "settings.scope", { workspace: "demo" })).toBe("工作区范围 / demo");
    expect(t("en-US", "settings.scope", { workspace: "demo" })).toBe("WORKSPACE SCOPE / demo");
  });

  it("formats dates, numbers, and plural labels by locale", () => {
    expect(localeFromSetting("简体中文")).toBe("zh-CN");
    expect(localeFromSetting("English")).toBe("en-US");
    expect(formatNumber(12345.6, "zh-CN")).toContain("12,345.6");
    expect(formatCount(1, "en-US", "item", "items")).toBe("1 item");
    expect(formatCount(2, "en-US", "item", "items")).toBe("2 items");
    expect(formatCount(2, "zh-CN", "项", "项")).toBe("2 项");
    expect(formatDate("2026-07-19T12:00:00Z", "zh-CN")).toContain("2026");
  });
});
