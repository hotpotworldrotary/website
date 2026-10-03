// Hot Pot World review card: GET /card.png?stars=5&name=...&quote=...&sig=...
// sig = hex HMAC-SHA256 of "stars|name|quote" with CARD_SECRET, computed in Make,
// so only the restaurant's own scenario can produce a card.
import { ImageResponse } from 'workers-og';
import { card } from './card.js';
import { LOGOS } from './logos.js';
import regular from '../fonts/BeVietnamPro-Regular.ttf';
import semibold from '../fonts/BeVietnamPro-SemiBold.ttf';
import extrabold from '../fonts/BeVietnamPro-ExtraBold.ttf';

const fonts = [
  { name: 'Be Vietnam Pro', data: regular, weight: 400, style: 'normal' },
  { name: 'Be Vietnam Pro', data: semibold, weight: 600, style: 'normal' },
  { name: 'Be Vietnam Pro', data: extrabold, weight: 800, style: 'normal' },
];

// Google shows "A Google User" for anonymous reviewers; the card then drops the name.
export function firstName(raw) {
  const name = String(raw || '').trim();
  if (!name || /^a google user$/i.test(name)) return '';
  return name.split(/\s+/)[0].slice(0, 24);
}

async function hmacHex(secret, message) {
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const mac = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(message));
  return [...new Uint8Array(mac)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

function safeEqual(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname !== '/card.png') return new Response('Not found', { status: 404 });
    if (!env.CARD_SECRET) return new Response('Not configured', { status: 500 });

    const p = url.searchParams;
    const stars = p.get('stars') || '';
    const name = p.get('name') || '';
    const quote = p.get('quote') || '';
    const sig = (p.get('sig') || '').toLowerCase();

    const expected = await hmacHex(env.CARD_SECRET, `${stars}|${name}|${quote}`);
    if (!safeEqual(sig, expected)) return new Response('Bad signature', { status: 403 });
    if (!quote.trim()) return new Response('Missing quote', { status: 400 });

    const res = new ImageResponse(
      card({ stars, name: firstName(name), quote, variant: p.get('variant') || 'cream', logos: LOGOS }),
      { width: 1080, height: 1080, fonts },
    );
    const headers = new Headers(res.headers);
    headers.set('Cache-Control', 'public, max-age=31536000, immutable');
    return new Response(res.body, { status: res.status, headers });
  },
};
