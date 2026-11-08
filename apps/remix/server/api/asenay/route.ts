/**
 * Asenay: open Sign from an Asenay workspace (single sign-on + the company's own organisation).
 *
 * The Asenay launcher (launch.asenayy.com) sends the browser to GET /api/asenay/sso?t=<ticket>, a
 * short HS256 ticket signed with ASENAY_SSO_SECRET (audience "sign", used once). On the first open the
 * workspace's company gets its own organisation and team with this person as owner; colleagues who open
 * Sign later join it as members (admins if they administer the workspace). Nobody needs a password:
 * the session is the normal one (onAuthorize), so everything else in Sign works unchanged.
 *
 * POST /api/asenay/forget closes the organisation of a removed free-trial workspace: its people are
 * signed out and the organisation is unlinked from the workspace. Nothing is deleted.
 */
import { createHash, createHmac, timingSafeEqual } from 'node:crypto';

import { onAuthorize } from '@documenso/auth/server/lib/utils/authorizer';
import { addUserToOrganisation } from '@documenso/lib/server-only/organisation/accept-organisation-invitation';
import { createOrganisation } from '@documenso/lib/server-only/organisation/create-organisation';
import { getSubscriptionClaim } from '@documenso/lib/server-only/subscription/get-subscription-claim';
import { createTeam } from '@documenso/lib/server-only/team/create-team';
import { createAdminUser } from '@documenso/lib/server-only/user/create-admin-user';
import { INTERNAL_CLAIM_ID } from '@documenso/lib/types/subscription';
import { extractRequestMetadata } from '@documenso/lib/universal/extract-request-metadata';
import { prisma } from '@documenso/prisma';
import { OrganisationMemberRole, OrganisationType } from '@prisma/client';
import { Hono } from 'hono';

const SECRET = process.env.ASENAY_SSO_SECRET || '';
const used = new Map<string, number>();

type Ticket = {
  aud: string;
  iss: string;
  exp: number;
  jti: string;
  ext: string;
  email: string;
  name?: string;
  admin?: boolean;
  action?: string;
  company?: { name?: string };
};

const verify = (token: string | undefined): Ticket | null => {
  const parts = String(token || '').split('.');
  if (parts.length !== 3 || !SECRET) return null;
  const want = createHmac('sha256', SECRET).update(`${parts[0]}.${parts[1]}`).digest();
  const got = Buffer.from(parts[2], 'base64url');
  if (got.length !== want.length || !timingSafeEqual(got, want)) return null;
  try {
    const head = JSON.parse(Buffer.from(parts[0], 'base64url').toString());
    const c = JSON.parse(Buffer.from(parts[1], 'base64url').toString()) as Ticket;
    const now = Date.now() / 1000;
    if (head.alg !== 'HS256' || c.aud !== 'sign' || c.iss !== 'asenay-launcher') return null;
    if (!c.exp || c.exp < now || !c.jti || !c.ext || !c.email) return null;
    for (const [k, exp] of used) if (exp < now) used.delete(k);
    if (used.has(c.jti)) return null;
    used.set(c.jti, c.exp);
    return c;
  } catch {
    return null;
  }
};

/** The organisation url of a workspace: fixed, so no extra table is needed to find it again. */
const orgUrl = (ext: string) => `ws-${createHash('sha256').update(ext).digest('hex').slice(0, 20)}`;

const page = (title: string, text: string) =>
  `<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Asenay Sign</title>` +
  `<body style="margin:0;font:15px/1.5 Inter,Segoe UI,system-ui,sans-serif;background:#f4f6fa;color:#111827">` +
  `<div style="max-width:440px;margin:12vh auto;padding:28px;background:#fff;border:1px solid #e5e7eb;border-radius:14px">` +
  `<h1 style="font-size:19px;margin:0 0 8px">${title}</h1><p style="margin:0;color:#374151">${text}</p></div>`;

export const asenayRoute = new Hono()
  .get('/sso', async (c) => {
    const t = verify(c.req.query('t'));
    if (!t) return c.html(page('This link is not valid', 'Go back to your workspace and open Sign again.'), 400);

    const email = t.email.trim().toLowerCase();
    const name = (t.name || email).slice(0, 120);
    const company = (t.company?.name || 'My company').slice(0, 120);
    const url = orgUrl(t.ext);

    let user = await prisma.user.findFirst({ where: { email } });
    if (!user) user = await createAdminUser({ name, email });
    if (user.disabled) return c.html(page('Your access was switched off', 'Ask the owner of your company’s Sign account.'), 403);

    let org = await prisma.organisation.findFirst({ where: { url }, include: { groups: true, members: true, teams: true } });
    if (!org) {
      const claim = await getSubscriptionClaim(INTERNAL_CLAIM_ID.FREE);
      const created = await createOrganisation({ userId: user.id, name: company, type: OrganisationType.ORGANISATION, url, claim });
      org = await prisma.organisation.findFirstOrThrow({ where: { id: created.id }, include: { groups: true, members: true, teams: true } });
    } else if (!org.members.some((m) => m.userId === user.id)) {
      await addUserToOrganisation({
        userId: user.id,
        organisationId: org.id,
        organisationGroups: org.groups,
        organisationMemberRole: t.admin ? OrganisationMemberRole.ADMIN : OrganisationMemberRole.MEMBER,
        bypassEmail: true,
      });
    }

    if (!org.teams.length) {
      // a closed workspace's team may still hold the address: then the new team gets its own
      const taken = await prisma.team.findFirst({ where: { url } });
      const teamUrl = taken ? `${url}-${Date.now().toString(36)}` : url;
      await createTeam({ userId: org.ownerUserId, teamName: company, teamUrl, organisationId: org.id, inheritMembers: true });
      org = await prisma.organisation.findFirstOrThrow({ where: { id: org.id }, include: { groups: true, members: true, teams: true } });
    }

    // onAuthorize reads the request metadata the auth sub-app normally sets
    c.set('requestMetadata' as never, extractRequestMetadata(c.req.raw) as never);
    await onAuthorize({ userId: user.id }, c as never);
    const team = org.teams[0];
    return c.redirect(team ? `/t/${team.url}/documents` : '/');
  })
  .post('/purge', async (c) => {
    // Organisations of free-trial workspaces closed more than `days` days ago (default 30) are deleted with
    // their teams and documents; so are their people who have no password and belong to no other organisation.
    const body = await c.req.json().catch(() => ({}));
    const t = verify((body as { t?: string }).t);
    if (!t || t.action !== 'purge') return c.json({ error: 'invalid' }, 400);
    const days = Math.max(1, Number((t as { days?: number }).days) || 30);
    const cutoff = Date.now() - days * 86400 * 1000;
    const closed = await prisma.organisation.findMany({ where: { url: { startsWith: 'closed-ws-' } }, include: { members: true } });
    let deleted = 0;
    let people = 0;
    for (const org of closed) {
      const stamp = parseInt(org.url.slice(org.url.lastIndexOf('-') + 1), 36);
      if (!Number.isFinite(stamp) || stamp > cutoff) continue;
      const userIds = org.members.map((m) => m.userId);
      await prisma.organisation.delete({ where: { id: org.id } });
      deleted++;
      for (const userId of userIds) {
        const elsewhere = await prisma.organisationMember.count({ where: { userId } });
        const u = await prisma.user.findUnique({ where: { id: userId } });
        if (u && !elsewhere && !u.password) {
          await prisma.user.delete({ where: { id: userId } });
          people++;
        }
      }
    }
    return c.json({ deleted, people });
  })
  .post('/forget', async (c) => {
    const body = await c.req.json().catch(() => ({}));
    const t = verify((body as { t?: string }).t);
    if (!t || t.action !== 'forget') return c.json({ error: 'invalid' }, 400);
    const url = orgUrl(t.ext);
    const org = await prisma.organisation.findFirst({ where: { url }, include: { members: true } });
    if (!org) return c.json({ closed: 0 });
    const userIds = org.members.map((m) => m.userId);
    await prisma.session.deleteMany({ where: { userId: { in: userIds } } });
    const stamp = Date.now().toString(36);
    await prisma.organisation.update({ where: { id: org.id }, data: { url: `closed-${url}-${stamp}` } });
    await prisma.team.updateMany({ where: { organisationId: org.id, url }, data: { url: `closed-${url}-${stamp}` } });
    return c.json({ closed: 1, signedOut: userIds.length });
  });
