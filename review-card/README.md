# Review card

Cloudflare Worker that turns a Google review into a branded 1080x1080 card for
the Hot Pot World Rotary Facebook Page. Make.com calls it from the
"Google review → Facebook" scenario and posts the image.

- Live: https://hotpotworld-review-card.anh-add.workers.dev/card.png (Phan Ventures LLC Cloudflare account)
- Query: `stars` (FIVE/FOUR or 1-5), `name` (Google display name; the card shows the first name only), `quote`, `sig`
- `sig` = hex HMAC-SHA256 of `stars|name|quote` with the `CARD_SECRET` Worker secret. Without it the Worker returns 403, so nobody else can make a "Hot Pot World review" card.
- The key lives on Anh's Mac at `~/.config/hotpotworld/card-secret` and inside the Make scenario's `sha256(...)` formula. To rotate: write a new value there, `npx wrangler secret put CARD_SECRET < ~/.config/hotpotworld/card-secret`, and update the Make formula.
- Layout is `src/card.js` (Satori, flexbox only). `npm run preview` renders samples to `preview/` with the same layout. Deploy: `npx wrangler deploy`.
- Fonts: Be Vietnam Pro (OFL, `fonts/OFL.txt`).
