# Hot Pot World Rotary · Website

Static rebuild of hotpotworld.com. Plain HTML, CSS and one small JS file. No build
step, no framework, no CMS. Open `index.html` in a browser and it works.

## One page

The whole site is `index.html`. The nav scrolls to sections rather than loading
new documents.

| Nav item | Anchor | What is there |
|---|---|---|
| Home | `#top` | Hero |
| How It Works | `#how-it-works` | Three steps, then things worth knowing |
| Menu | `#menu` | $39.99, the notice, broths, the gallery, meat, drinks |
| Our Story | `#story` | What hot pot is, why the belt, recognition, guest quotes |
| Visit Us | `#visit` | Address, hours, contact form, directions |

Anchor sections are marked `section--anchor` and carry a `[id]`. Three things
depend on that and will break quietly if you rename an id:

- The nav and the footer's Explore list both link to these anchors.
- `[id] { scroll-margin-top: 84px }` in the stylesheet keeps a jump from landing
  underneath the sticky header. The header is 68px; if you change its height,
  change that number.
- `main.js` highlights the current nav item by observing these same sections.
  `#top` has no section of its own, so the script maps it to `.hero`.

It was five separate pages until 2026-08-19. Those files are kept, unchanged, in
`source/pages-archive/` for reference. They are not deployed and their internal
links point at pages that no longer exist, so do not put them back without
rewriting the nav.

## Layout

```
Website/
├── index.html              the entire site
├── assets/
│   ├── css/style.css        all styling, one file
│   ├── js/main.js           mobile nav, click-to-load video, scroll reveal
│   ├── fonts/               Be Vietnam Pro, self-hosted, 104 KB
│   └── img/web/             the only images the site serves
├── DESIGN.md                the visual system and the rules that hold it
├── PRODUCT.md               who this is for and what a win looks like
├── source/                  NOT deployed
│   ├── originals/           full resolution photos
│   ├── build_assets.py      regenerates assets/img/web from originals
│   ├── pages-archive/       the five pages this replaced, not deployed
│   ├── style.old.css        the pre-redesign stylesheet, kept for reference
│   └── harness/             the throwaway pages used to test and screenshot
└── README.md
```

Deploy the root **excluding `source/`**. Deployed weight is about 9 MB.

### Regenerating images

```bash
cd Website
python3 source/build_assets.py     # needs Pillow + numpy
```

Rewrites everything under `assets/img/web/`: crops each photo to its aspect ratio,
emits a 1x and 2x JPG, rebuilds the transparent logo and the favicon set.
Drop new photos into `source/originals/` and add a row to the `PHOTOS` list.

A row is `(name, source file, aspect ratio, 1x width)`, with an optional fifth
field: a fractional `(left, top, right, bottom)` window applied **before** the
aspect crop. Use it when a centred crop lands in the wrong place, which is what
the phone hero needs: cropping the room shot to portrait keeps every pixel of
height, so without trimming the ceiling first the belt falls out of frame.

Pick the 1x width so that `2x` still fits inside the source, otherwise the 2x is
silently skipped and any `srcset` pointing at it will 404.

## Brand

The site **alternates dark and light bands** (hero, header and footer dark), with brand red as the only accent.
Full palette, type rules, layout rules and the accessibility floor are in
[DESIGN.md](DESIGN.md). Read that before changing anything visual.

The short version: `--void #0E0D0C` page, `--bone #F2EDE7` text, `--red #C0262E`
for fills and large type, `--red-ink #F0565C` for anything small and red. The two
reds are not interchangeable and DESIGN.md explains why.

Type is Be Vietnam Pro, self-hosted under `assets/fonts/` (SIL OFL, licence
included). It was chosen for its Vietnamese diacritics, which the menu names
need. Headings keep the printed menu's device: bold English with the Vietnamese
name underneath in red italics (the `.vn` class).

Logos: `logo.png` is red art on transparency for light backgrounds, `logo-white.png`
is the knockout for dark ones. The header and footer both use the white one.

`award-guru-{gold,disc,laurel,plaque}.png` (+`@2x`) are the four Restaurant
Guru "Recommended 2023" badges the old WordPress site embedded as widgets,
rendered to PNG from those widgets (`source/badge-source/`, CSS and fonts from
`awards.infcdn.net`, which the new site never calls at runtime). Each links to
the restaurant's listing on restaurantguru.com.

## Deliberate choices worth knowing

- **No external requests on page load.** No CDN, no web fonts, no analytics, no map
  iframe. The YouTube player is a click-to-load facade: nothing is requested from
  youtube.com until a visitor presses play, and then it uses `youtube-nocookie.com`.
  The map is a link, not an embed. This keeps the site fast and avoids dropping
  third party cookies on visitors before they have done anything.
- **Works without JavaScript.** JS only adds the mobile menu and the video. Every
  page reads fine with it disabled.
- **`Restaurant` JSON-LD on the home page** carries the address, phone and hours so
  Google can pick them up directly.
- **Old per-plate prices are not republished.** The January 2024 menu priced colour
  coded plates at $2.50 to $5.50. The $39.99 all you can eat price supersedes that.

## Open items before launch

1. **Contact form.** Removed 2026-09-28 at the restaurant's request (phone is the
   channel). It had posted to a placeholder Formspree ID and delivered nothing.
   To restore: take the `<form>` from commit 519ce64 and give it a real Formspree
   ID pointed at hotpotworld@gmail.com.
2. **Menu.** Done 2026-08-20. The `#menu` section shows the printed 11x14 menu
   as two page images (`assets/menu/menu-page-{1,2}.jpg` + `@2x`) with the PDFs
   alongside for download. Source PDFs: `source/originals/menu-2026/`. To update:
   `pdftoppm -r 200 -jpeg -singlefile page.pdf out`, crop to the gold frame
   (page 1 of the 2026 menu needed `(110,95,2890,2305)` at 200 dpi; page 2 none),
   export 1100 and 2200 wide at JPEG q84, copy the PDFs into `assets/menu/`.
3. **Photography.** Two professional wide shots of the belt were sitting unused
   in `source/originals/` and are now the home hero and the belt section
   (`room-wide`, `room-wide-tall`, `belt-tall`). That closes the gap this item
   used to describe. Six more photos were supplied in August 2026: five plated
   raw cuts (`belt-*`) and the drinks tower (`drinks-fountain`). Four of the five
   plated shots look generated rather than photographed, so treat them as
   placeholders for real product photography.

4. **Guest quotes are unattributed.** Four quotes run on the home and story
   pages with no name against them, which is the weakest form of social proof.
   Three real Google reviews with first names would be worth more than all four.
   Names were deliberately not invented.
5. **Hero video.** Currently the YouTube embed. If the original mp4 turns up, a
   muted autoplay loop behind the hero would be a real upgrade.
6. **Facts to confirm with the restaurant:** the drive-time and "between the
   freeway and Pacific Highway" copy in the directions band is ours, not theirs.
7. **Awards.** Done 2026-08-20: the Seattle Times card links to the article and the
   Restaurant Guru badge is the real one, linked to the listing.

## Share image

`assets/img/web/og-share.jpg` (1200×630) is what Messages, Facebook and Slack show
when the link is shared. It is rendered from `source/harness/og.html` with headless
Chrome; edit that file and re-screenshot to change it. The `og:*` and `twitter:*`
tags point at the GitHub Pages URL until the domain moves.

## Hosting

The old site is WordPress. This replaces it with static files, which can go on
Netlify or Vercel free tier, or any static host.

Whatever the host, **`assets/` must stay lowercase.** The folder was created as
`Assets` at one point, which works on macOS (case-insensitive) and 404s every
stylesheet and image on Linux. It has been corrected; do not let it drift back.

DNS for hotpotworld.com needs pointing at the new host once it is up.

**Redirect the old WordPress paths to anchors** when you cut over, or anything
already indexed will 404. On Netlify, `_redirects`:

```
/instructions   /#how-it-works   301
/menu           /#menu           301
/about          /#story          301
/contact        /#visit          301
```

On Vercel the same thing goes in `vercel.json` under `redirects`. Confirm the
real old paths in Search Console first; the list above is the likely shape, not
a verified inventory.

## Google reviews

The quotes at the bottom of Our Story are the restaurant's latest 4 and 5 star
Google reviews. `.github/workflows/reviews.yml` runs every night, calls
`scripts/reviews/fetch_reviews.py`, and rewrites only the block between the
`reviews:start` and `reviews:end` markers in `index.html`. It commits only when
the reviews changed, then starts the Pages deploy.

- Data comes from the Google Business Profile API with the owner's sign-in, not
  the public Places API (that one returns 5 reviews, not newest first, and may
  not be stored).
- Secrets `GBP_CLIENT_ID`, `GBP_CLIENT_SECRET`, `GBP_REFRESH_TOKEN` and the
  variable `GBP_LOCATION` live on the GitHub repo. `scripts/reviews/connect_google.py`
  sets them. Run it again to reconnect if the job starts failing on a token error.
- Until those secrets exist the job skips, and the four original quotes stay.
- Names are shown as first name and last initial. Long reviews are cut at 180
  characters. Both are constants at the top of the script.
- Scheduled workflows in a public repo pause after 60 days with no commits. If
  no new reviews land for two months, re-enable it under Actions.
