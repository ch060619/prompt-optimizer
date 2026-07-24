export type Locale = "zh-CN" | "en-US";

const messages = {
  "en-US": {
    "settings.configure": "CONFIGURE",
    "settings.savedLocally": "SAVED LOCALLY",
    "settings.scope": "WORKSPACE SCOPE / {workspace}",
    "settings.section.appearance": "Appearance",
    "settings.section.providers": "Providers & models",
    "settings.section.language": "Language",
    "settings.section.terminal": "Terminal",
    "settings.section.permissions": "Permissions",
    "settings.section.sandbox": "Sandbox",
    "settings.section.data": "Data",
    "settings.section.privacy": "Privacy",
    "settings.section.updates": "Updates",
    "settings.section.shortcuts": "Shortcuts",
    "settings.section.mcp": "MCP",
    "settings.section.plugins": "Plugins",
    "settings.section.advanced": "Advanced",
    "settings.title.appearance": "Set the visual rhythm.",
    "settings.title.providers": "Route the work safely.",
    "settings.title.language": "Choose the language.",
    "settings.title.terminal": "Shape the terminal session.",
    "settings.title.permissions": "Decide what needs approval.",
    "settings.title.sandbox": "Constrain tool access.",
    "settings.title.data": "Keep local data under control.",
    "settings.title.privacy": "Choose what leaves the machine.",
    "settings.title.updates": "Keep the app current.",
    "settings.title.shortcuts": "Tune the keyboard layer.",
    "settings.title.mcp": "Connect Model Context Protocol.",
    "settings.title.plugins": "Manage local extensions.",
    "settings.title.advanced": "Expose the sharp edges carefully.",
  },
  "zh-CN": {
    "settings.configure": "配置",
    "settings.savedLocally": "已保存到本地",
    "settings.scope": "工作区范围 / {workspace}",
    "settings.section.appearance": "外观",
    "settings.section.providers": "Provider 与模型",
    "settings.section.language": "语言",
    "settings.section.terminal": "终端",
    "settings.section.permissions": "权限",
    "settings.section.sandbox": "沙箱",
    "settings.section.data": "数据",
    "settings.section.privacy": "隐私",
    "settings.section.updates": "更新",
    "settings.section.shortcuts": "快捷键",
    "settings.section.mcp": "MCP",
    "settings.section.plugins": "插件",
    "settings.section.advanced": "高级",
    "settings.title.appearance": "调整视觉节奏。",
    "settings.title.providers": "安全地选择执行路线。",
    "settings.title.language": "选择界面语言。",
    "settings.title.terminal": "设置终端会话。",
    "settings.title.permissions": "决定哪些操作需要批准。",
    "settings.title.sandbox": "限制工具访问范围。",
    "settings.title.data": "控制本地数据。",
    "settings.title.privacy": "选择哪些数据可以离开设备。",
    "settings.title.updates": "保持应用为最新版本。",
    "settings.title.shortcuts": "调整键盘操作层。",
    "settings.title.mcp": "连接 Model Context Protocol。",
    "settings.title.plugins": "管理本地扩展。",
    "settings.title.advanced": "谨慎暴露高级选项。",
  },
} as const;

export type MessageKey = keyof typeof messages["en-US"];

export function localeFromSetting(value: unknown): Locale {
  return value === "简体中文" || value === "zh-CN" ? "zh-CN" : "en-US";
}

export function t(locale: Locale, key: MessageKey, values: Record<string, string> = {}) {
  const template = messages[locale][key] || messages["en-US"][key];
  return template.replace(/\{(\w+)\}/g, (_, name: string) => values[name] ?? `{${name}}`);
}

export function formatNumber(value: number, locale: Locale) {
  return new Intl.NumberFormat(locale).format(value);
}

export function formatDate(value: Date | number | string, locale: Locale) {
  return new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

export function formatCount(value: number, locale: Locale, singular: string, plural: string) {
  const label = locale === "zh-CN" ? singular : value === 1 ? singular : plural;
  return `${formatNumber(value, locale)} ${label}`;
}

export function resourceKeys() {
  return Object.keys(messages["en-US"]).sort();
}

export function resourceCatalog() {
  return messages;
}
