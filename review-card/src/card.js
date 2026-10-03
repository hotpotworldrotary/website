// Review card layout, shared by the Worker and the local preview script.
// Satori renders this tree, so every element with more than one child needs
// display:flex, and only flexbox layout is available.

const COLORS = {
  void: '#0E0D0C',
  surface: '#171413',
  line: '#2E2825',
  bone: '#F2EDE7',
  boneDim: '#B3AAA3',
  red: '#C0262E',
  redDeep: '#96181F',
  cream: '#F6F2EC',
  ink: '#141210',
  inkDim: '#5C544E',
  plates: ['#3B8FD9', '#45B36B', '#E0443E', '#F2C230'],
};

export const VARIANTS = {
  dark: {
    bg: COLORS.void, text: COLORS.bone, dim: COLORS.boneDim, mark: COLORS.red,
    star: '#F2C230', starEmpty: '#3A322E', band: COLORS.red, bandText: '#FFFFFF', logo: 'red',
  },
  cream: {
    bg: COLORS.cream, text: COLORS.ink, dim: COLORS.inkDim, mark: COLORS.red,
    star: COLORS.red, starEmpty: '#DDD5CC', band: COLORS.red, bandText: '#FFFFFF', logo: 'red',
  },
  red: {
    bg: COLORS.red, text: '#FFFFFF', dim: '#F6D5D6', mark: '#FFFFFF',
    star: '#F2C230', starEmpty: COLORS.redDeep, band: COLORS.void, bandText: COLORS.bone, logo: 'white',
  },
};

const MAX_QUOTE = 280;

// Google reviews run up to 4,096 characters. The card shows the opening and
// the Facebook caption carries the whole review.
export function fitQuote(raw) {
  const text = String(raw || '').replace(/\s+/g, ' ').trim();
  if (text.length <= MAX_QUOTE) return text;
  const cut = text.slice(0, MAX_QUOTE);
  return cut.slice(0, cut.lastIndexOf(' ')).replace(/[,.;:!?-]+$/, '') + '…';
}

function quoteSize(len) {
  if (len <= 70) return 66;
  if (len <= 130) return 54;
  if (len <= 200) return 46;
  return 40;
}

const STAR_PATH = 'M12 2.2l2.9 6.6 7.1.6-5.4 4.7 1.6 7-6.2-3.7-6.2 3.7 1.6-7L2 9.4l7.1-.6z';

function star(fill, size) {
  return {
    type: 'svg',
    props: {
      width: size, height: size, viewBox: '0 0 24 24',
      children: { type: 'path', props: { d: STAR_PATH, fill } },
    },
  };
}

function el(type, style, children) {
  return { type, props: { style, children } };
}

export function card({ stars, name, quote, variant = 'cream', logos }) {
  const v = VARIANTS[variant] || VARIANTS.cream;
  const words = { ONE: 1, TWO: 2, THREE: 3, FOUR: 4, FIVE: 5 };
  const n = Math.max(1, Math.min(5, words[String(stars).toUpperCase()] || Number(stars) || 5));
  const text = fitQuote(quote);
  const size = quoteSize(text.length);
  const who = name ? `${name} · Google review` : 'Google review';

  return el('div', {
    width: 1080, height: 1080, display: 'flex', flexDirection: 'column',
    backgroundColor: v.bg, fontFamily: 'Be Vietnam Pro', color: v.text,
  }, [
    // Logo and stars
    el('div', { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '64px 80px 0' }, [
      { type: 'img', props: { src: logos[v.logo], width: 250, height: 186 } },
      el('div', { display: 'flex', gap: 10 },
        Array.from({ length: 5 }, (_, i) => star(i < n ? v.star : v.starEmpty, 64))),
    ]),
    // Quote
    el('div', { display: 'flex', flexDirection: 'column', flexGrow: 1, justifyContent: 'center', padding: '0 80px' }, [
      el('div', { display: 'flex', fontSize: 180, fontWeight: 800, color: v.mark, lineHeight: 1, height: 110 }, '“'),
      el('div', { display: 'flex', fontSize: size, fontWeight: 600, lineHeight: 1.28, letterSpacing: -0.5 }, text),
      el('div', { display: 'flex', fontSize: 30, fontWeight: 400, color: v.dim, marginTop: 36 }, who),
    ]),
    // Footer band
    el('div', {
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      backgroundColor: v.band, color: v.bandText, padding: '30px 80px',
    }, [
      el('div', { display: 'flex', flexDirection: 'column' }, [
        el('div', { display: 'flex', fontSize: 30, fontWeight: 800, letterSpacing: 0.5 }, 'Hot Pot World Rotary'),
        el('div', { display: 'flex', fontSize: 24, fontWeight: 400, marginTop: 4, opacity: 0.85 }, '2020 S 320th St, Suite G, Federal Way, WA 98003'),
      ]),
      el('div', { display: 'flex', gap: 12 },
        COLORS.plates.map((c) => el('div', {
          display: 'flex', width: 40, height: 40, borderRadius: 20, backgroundColor: c,
          border: '5px solid #FFFFFF',
        }, []))),
    ]),
  ]);
}
