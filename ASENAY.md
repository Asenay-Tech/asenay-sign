# Asenay Sign

Asenay Sign is the document and e-signature app of [Asenay](https://asenayy.com), live at
https://sign.asenayy.com. It is a fork of [Documenso](https://github.com/documenso/documenso) v2.20.0.

## Licence

- Everything outside `packages/ee` is licensed under the **GNU Affero General Public License v3**
  ([LICENSE](LICENSE)), like upstream Documenso. This repository is the complete corresponding source of
  the version Asenay runs, as section 13 of the AGPL requires; every page of the app links here.
- `packages/ee` is under the **Documenso Commercial License** ([packages/ee/LICENSE](packages/ee/LICENSE)) and
  is unchanged. Asenay Sign does not use those features in production (Stripe billing, organisation SSO portal,
  passkey/2FA document re-authentication, 21 CFR, email domains, embed authoring, CSC remote signing); they stay
  switched off.
- "Documenso" is a trademark of Documenso, Inc. Asenay Sign is not affiliated with or endorsed by Documenso, Inc.

## What Asenay changed

All changes are reproducible from two scripts, so they can be re-applied after merging an upstream release:

- `scripts/asenay/brand_assets.py` - Asenay Sign logos, favicons, social image, sign-up example, background pattern
- `scripts/asenay/rebrand.py` - visible name, links, Asenay blue theme, logo components, source-code link

Plus `docker/Dockerfile`: build heap capped at 4 GB.

## Build

    docker build -f docker/Dockerfile -t asenay-sign .

Configuration is the same as Documenso's (see `.env.example`).
