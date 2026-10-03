// Renders sample cards to preview/ with the same layout the Worker uses.
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import satori from 'satori';
import { Resvg } from '@resvg/resvg-js';
import { card, VARIANTS } from '../src/card.js';
import { LOGOS } from '../src/logos.js';

const font = (w, f) => ({ name: 'Be Vietnam Pro', weight: w, style: 'normal', data: readFileSync(`fonts/${f}`) });
const fonts = [font(400, 'BeVietnamPro-Regular.ttf'), font(600, 'BeVietnamPro-SemiBold.ttf'), font(800, 'BeVietnamPro-ExtraBold.ttf')];

const samples = [
  { id: 'short', stars: 5, name: 'Sam', quote: 'We thoroughly enjoyed the delightful hot pot and are now completely full.' },
  { id: 'long', stars: 4, name: 'Sam', quote: 'SAMPLE TEXT for a long review. The conveyor belt is a blast and everyone at the table gets their own pot, so my kids got the mild broth while I went spicy. The BBQ meats came out quickly, the sauce bar has everything, and the staff kept checking on us the whole night. Parking was a little tight on a Saturday but we will absolutely be back with the whole family.' },
];

mkdirSync('preview', { recursive: true });
for (const variant of Object.keys(VARIANTS)) {
  for (const s of samples) {
    const svg = await satori(card({ ...s, variant, logos: LOGOS }), { width: 1080, height: 1080, fonts });
    const png = new Resvg(svg, { fitTo: { mode: 'width', value: 1080 } }).render().asPng();
    writeFileSync(`preview/${variant}-${s.id}.png`, png);
    console.log(`preview/${variant}-${s.id}.png`, png.length);
  }
}
