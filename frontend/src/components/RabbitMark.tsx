import type { ImgHTMLAttributes } from "react";

// RC ID: RC-125. Route-facing brand slot with a closed internal asset boundary.
// RC ID: RC-128. Keep small marks independent from the full raster artwork.

export type RabbitVariant = "full" | "avatar" | "mark" | "empty" | "mono";

const dimensions: Record<RabbitVariant, { width: number; height: number }> = {
  full: { width: 643, height: 684 },
  avatar: { width: 256, height: 256 },
  mark: { width: 64, height: 64 },
  empty: { width: 480, height: 320 },
  mono: { width: 64, height: 64 },
};

type RabbitMarkProps = {
  variant: RabbitVariant;
  alt?: string;
  decorative?: boolean;
  className?: string;
  loading?: ImgHTMLAttributes<HTMLImageElement>["loading"];
  size?: number;
};

function RabbitGlyph({ variant, alt, decorative, className, size }: RabbitMarkProps) {
  const label = alt || "Rabbit Code 品牌标记";
  const classes = ["rabbit-glyph", `rabbit-glyph-${variant}`, className].filter(Boolean).join(" ");
  return (
    <svg
      className={classes}
      viewBox="0 0 64 64"
      width={size ?? dimensions[variant].width}
      height={size ?? dimensions[variant].height}
      role={decorative ? "presentation" : "img"}
      aria-hidden={decorative ? "true" : undefined}
      aria-label={decorative ? undefined : label}
      focusable="false"
    >
      <g fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="3.2">
        <path d="M22 29C16 27 11 21 12 13c1-6 4-9 8-6 4 3 5 11 4 18" />
        <path d="M42 29c6-2 11-8 10-16-1-6-4-9-8-6-4 3-5 11-4 18" />
        <path d="M14 37c0-10 8-16 18-16s18 6 18 16-8 19-18 19-18-9-18-19Z" />
        <path d="M16 23h32" />
        <path d="M22 17c3-4 7-6 10-6s7 2 10 6" />
        <circle cx="25" cy="37" r="1.8" fill="currentColor" stroke="none" />
        <circle cx="39" cy="37" r="1.8" fill="currentColor" stroke="none" />
        <path d="M29 43c1.5 1.5 4.5 1.5 6 0M32 42v3" />
      </g>
      {variant === "mark" ? <path className="rabbit-glyph-accent" d="M18 23h28c-4-4-9-6-14-6s-10 2-14 6Z" /> : null}
    </svg>
  );
}

export function RabbitMark({ variant, alt, decorative = false, className, loading = "lazy", size: requestedSize }: RabbitMarkProps) {
  if (variant === "mark" || variant === "mono") {
    return <RabbitGlyph variant={variant} alt={alt} decorative={decorative} className={className} size={requestedSize} />;
  }

  const rasterSize = dimensions[variant];
  const classes = ["rabbit-mark", `rabbit-mark-${variant}`, className].filter(Boolean).join(" ");
  return (
    <img
      className={classes}
      src="/rabbit-artwork.png"
      alt={decorative ? "" : alt || (variant === "full" ? "Rabbit Code 兔兔品牌插画" : "Rabbit Code 品牌标记")}
      aria-hidden={decorative ? "true" : undefined}
      width={rasterSize.width}
      height={rasterSize.height}
      loading={loading}
      decoding="async"
    />
  );
}
