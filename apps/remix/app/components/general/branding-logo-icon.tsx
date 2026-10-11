import type { ImgHTMLAttributes } from 'react';

export type LogoProps = ImgHTMLAttributes<HTMLImageElement>;

// The Asenay mark (public/android-chrome-192x192.png, made by scripts/asenay/brand_assets.py)
export const BrandingLogoIcon = ({ ...props }: LogoProps) => {
  return <img src="/android-chrome-192x192.png" alt="Asenay Sign" {...props} />;
};
