// Hot Pot World review card.
//
// GET /card.png?stars=5&name=...&quote=...&sig=...
//   sig = hex HMAC-SHA256 of "stars|name|quote" with CARD_SECRET, computed in Make,
//   so only the restaurant's own scenario can produce a card. Every signed 4 or 5
//   star card is also remembered in KV, because Make only asks for a card when it
//   posts a good review to Facebook.
//
// GET /reviews.json
//   The newest remembered reviews, in the Google Business Profile API shape, so
//   scripts/reviews/fetch_reviews.py can render them into the website.
//
// POST /reviews/seed   (header X-Signature = hex HMAC-SHA256 of the body)
//   Backfill: a JSON array of { stars, name, quote, createTime }.
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

const KEEP = 20;
const WORDS = { 1: 'ONE', 2: 'TWO', 3: 'THREE', 4: 'FOUR', 5: 'FIVE' };
const NUMBERS = { ONE: 1, TWO: 2, THREE: 3, FOUR: 4, FIVE: 5 };

function isAnonymous(name) {
  return !name || /^a google user$/i.test(name);
}

// Google shows "A Google User" for anonymous reviewers; the card then drops the name.
export function firstName(raw) {
  const name = String(raw || '').trim();
  if (isAnonymous(name)) return '';
  return name.split(/\s+/)[0].slice(0, 24);
}

// What the website may publish: first name and last initial, like the page credits people.
export function shortName(raw) {
  const parts = String(raw || '').trim().split(/\s+/).filter(Boolean);
  if (isAnonymous(parts.join(' '))) return '';
  return parts.length === 1 ? parts[0] : `${parts[0]} ${parts[parts.length - 1][0]}.`;
}

function starCount(raw) {
  return NUMBERS[String(raw).toUpperCase()] || Number(raw) || 0;
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

async function remember(env, items) {
  const list = JSON.parse((await env.REVIEWS.get('latest')) || '[]');
  for (const { stars, name, quote, createTime } of items) {
    const n = starCount(stars);
    const text = String(quote || '').trim();
    if (n < 4 || !text) continue;
    const id = (await hmacHex('id', `${shortName(name)}|${text}`)).slice(0, 16);
    if (list.some((r) => r.id === id)) continue;   // Facebook fetches a card more than once
    list.push({ id, stars: n, name: shortName(name), quote: text.slice(0, 2000),
      createTime: createTime || new Date().toISOString() });
  }
  list.sort((a, b) => b.createTime.localeCompare(a.createTime));
  await env.REVIEWS.put('latest', JSON.stringify(list.slice(0, KEEP)));
}

async function cardPng(request, env, ctx) {
  const p = new URL(request.url).searchParams;
  const stars = p.get('stars') || '';
  const name = p.get('name') || '';
  const quote = p.get('quote') || '';
  const sig = (p.get('sig') || '').toLowerCase();

  const expected = await hmacHex(env.CARD_SECRET, `${stars}|${name}|${quote}`);
  if (!safeEqual(sig, expected)) return new Response('Bad signature', { status: 403 });
  if (!quote.trim()) return new Response('Missing quote', { status: 400 });

  ctx.waitUntil(remember(env, [{ stars, name, quote }]));

  const res = new ImageResponse(
    card({ stars, name: firstName(name), quote, variant: p.get('variant') || 'cream', logos: LOGOS }),
    { width: 1080, height: 1080, fonts },
  );
  const headers = new Headers(res.headers);
  headers.set('Cache-Control', 'public, max-age=31536000, immutable');
  return new Response(res.body, { status: res.status, headers });
}

async function reviewsJson(env) {
  const list = JSON.parse((await env.REVIEWS.get('latest')) || '[]');
  const reviews = list.map((r) => ({
    starRating: WORDS[r.stars],
    comment: r.quote,
    createTime: r.createTime,
    reviewer: { displayName: r.name },
  }));
  return Response.json({ reviews }, {
    headers: { 'Cache-Control': 'public, max-age=300', 'Access-Control-Allow-Origin': '*' },
  });
}

async function seed(request, env) {
  const body = await request.text();
  const sig = (request.headers.get('X-Signature') || '').toLowerCase();
  if (!safeEqual(sig, await hmacHex(env.CARD_SECRET, body))) {
    return new Response('Bad signature', { status: 403 });
  }
  await remember(env, JSON.parse(body));
  return reviewsJson(env);
}

export default {
  async fetch(request, env, ctx) {
    if (!env.CARD_SECRET) return new Response('Not configured', { status: 500 });
    const { pathname } = new URL(request.url);
    if (pathname === '/card.png' && request.method === 'GET') return cardPng(request, env, ctx);
    if (pathname === '/reviews.json' && request.method === 'GET') return reviewsJson(env);
    if (pathname === '/reviews/seed' && request.method === 'POST') return seed(request, env);
    return new Response('Not found', { status: 404 });
  },
};
