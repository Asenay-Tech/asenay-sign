"""Rebrands the Documenso source as Asenay Sign. Idempotent; re-run after merging an upstream release.

  * visible name "Documenso" -> "Asenay Sign" (whole word only: code names such as isDocumensoCloud,
    @documenso/* packages and DOCUMENSO_* settings are untouched), in the app, emails and translations
  * "Documenso, Inc." -> "Asenay"; links to documenso.com's home page -> asenayy.com
  * colours: Documenso green -> Asenay blue (#005be0) in the shared theme
  * the logo components render the Asenay Sign artwork (scripts/asenay/brand_assets.py)
The Commercial-License folder packages/ee is not edited, and its features stay switched off.
Run from the repo root:  python scripts/asenay/rebrand.py
"""
import io
import pathlib
import re

ROOTS = ["apps/remix", "packages"]
SKIP = re.compile(r"(node_modules|/packages/ee/|/migrations/|\.test\.|/e2e/|/apps/docs/|/scripts/asenay/)")
EXT = {".ts", ".tsx", ".po", ".html", ".json", ".md"}


def text_files():
    for root in ROOTS:
        for p in pathlib.Path(root).rglob("*"):
            s = p.as_posix()
            if p.is_file() and p.suffix in EXT and not SKIP.search("/" + s) and not s.endswith("package.json"):
                yield p


def rewrite(p, fn):
    s = io.open(p, encoding="utf-8", newline="").read()
    t = fn(s)
    if t != s:
        io.open(p, "w", encoding="utf-8", newline="").write(t)
        return 1
    return 0


def rename(s):
    s = s.replace("Documenso, Inc.", "Asenay")
    s = re.sub(r"https://(www\.)?documenso\.com/?(?=[\"'`)\s])", "https://asenayy.com", s)
    # no Latin letter/digit around it (Korean and Japanese text attach particles directly to the name)
    return re.sub(r"(?<![A-Za-z0-9_@/.-])Documenso(?![A-Za-z0-9_])", "Asenay Sign", s)


changed = sum(rewrite(p, rename) for p in text_files())

# Asenay blue instead of Documenso green (light and dark mode, plus the 50..950 scale)
THEME = pathlib.Path("packages/ui/styles/theme.css")
SCALE = {50: 97, 100: 93, 200: 86, 300: 77, 400: 67, 500: 57, 600: 50, 700: 44, 800: 34, 900: 24, 950: 14}


def recolour(s):
    s = s.replace("--primary: 95.08 71.08% 67.45%;\n    --primary-foreground: 95.08 71.08% 10%;",
                  "--primary: 215.6 100% 43.9%;\n    --primary-foreground: 0 0% 100%;", 1)
    s = s.replace("--primary: 95.08 71.08% 67.45%;\n    --primary-foreground: 95.08 71.08% 10%;",
                  "--primary: 217 100% 62%;\n    --primary-foreground: 0 0% 100%;", 1)
    s = s.replace("--secondary-foreground: 95.08 71.08% 67.45%;", "--secondary-foreground: 217 100% 70%;")
    for k, l in SCALE.items():
        s = re.sub(rf"--new-primary-{k}: [^;]+;", f"--new-primary-{k}: 216, 100%, {l}%;", s)
    return s


changed += rewrite(THEME, lambda s: recolour(s.replace("\r\n", "\n")))

LOGO = """import type { ImgHTMLAttributes } from 'react';

export type LogoProps = ImgHTMLAttributes<HTMLImageElement>;

// Asenay Sign artwork (public/static/logo.png, made by scripts/asenay/brand_assets.py)
export const BrandingLogo = ({ ...props }: LogoProps) => {
  return <img src="/static/logo.png" alt="Asenay Sign" {...props} />;
};
"""
ICON = """import type { ImgHTMLAttributes } from 'react';

export type LogoProps = ImgHTMLAttributes<HTMLImageElement>;

// The Asenay mark (public/android-chrome-192x192.png, made by scripts/asenay/brand_assets.py)
export const BrandingLogoIcon = ({ ...props }: LogoProps) => {
  return <img src="/android-chrome-192x192.png" alt="Asenay Sign" {...props} />;
};
"""
for path, body in (("apps/remix/app/components/general/branding-logo.tsx", LOGO),
                   ("apps/remix/app/components/general/branding-logo-icon.tsx", ICON)):
    changed += rewrite(pathlib.Path(path), lambda s, b=body: b)

# a colour logo must not be inverted in dark mode
changed += rewrite(pathlib.Path("apps/remix/app/components/general/app-nav-mobile.tsx"),
                   lambda s: s.replace('className="dark:invert" width={170}', 'width={170}'))

# Documenso's green Tailwind palette ("documenso-*" classes) -> the Asenay blue scale
BLUE = {"DEFAULT": "#005BE0", "50": "#FFFFFF", "100": "#F2F7FF", "200": "#D6E6FF", "300": "#A8C9FF", "400": "#6FA4FF",
        "500": "#3D86FF", "600": "#1A6CF0", "700": "#005BE0", "800": "#0048B3", "900": "#003685", "950": "#002456"}


def palette(s):
    i = s.index("documenso: {")
    j = s.index("},", i)
    block = s[i:j]
    for k, v in BLUE.items():
        block = re.sub(rf"(\b{k}: )'#[0-9A-Fa-f]{{6}}'", rf"\g<1>'{v}'", block)
    return s[:i] + block + s[j:]


changed += rewrite(pathlib.Path("packages/tailwind-config/index.cjs"), palette)

# the sign-up example profile is Asenay, not Documenso's founder
changed += rewrite(pathlib.Path("apps/remix/app/components/general/user-profile-timur.tsx"), lambda s: s
                   .replace("{baseUrl.host}/u/timur", "{baseUrl.host}/u/asenay")
                   .replace('alt="image of timur ercan founder of documenso"', 'alt="Asenay"')
                   .replace(">Timur Ercan<", ">Asenay<")
                   .replace("<Trans>Hey I’m Timur</Trans>", "<Trans>Send, sign and keep your agreements in one place.</Trans>"))

# AGPL section 13: everyone using Asenay Sign over the network is offered its source code
SOURCE = "https://github.com/Asenay-Tech/asenay-sign"
changed += rewrite(pathlib.Path("apps/remix/app/components/general/public-legal-links.tsx"), lambda s: s if SOURCE in s else s
                   .replace("    imprintUrl ? { label: msg`Imprint`, href: imprintUrl } : null,\n  ];",
                            "    imprintUrl ? { label: msg`Imprint`, href: imprintUrl } : null,\n"
                            "    // Asenay Sign is AGPL-licensed: its source code is offered to every user\n"
                            "    { label: msg`Source code`, href: '" + SOURCE + "' },\n  ];"))
print("files changed:", changed)
