import type { ImgHTMLAttributes } from 'react';

export type LogoProps = ImgHTMLAttributes<HTMLImageElement>;

// Asenay Sign artwork (public/static/logo.png, made by scripts/asenay/brand_assets.py)
export const BrandingLogo = ({ ...props }: LogoProps) => {
  return <img src="/static/logo.png" alt="Asenay Sign" {...props} />;
};
