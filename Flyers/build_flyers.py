#!/usr/bin/env python3
"""Hot Pot World Rotary street flyers, English + Vietnamese.

One layout, two copy blocks. Shared facts live in FACTS (from the live site
and project memory, 2026-10-27). Output: flyer-en.html / flyer-vi.html, then
render.sh turns them into letter PDFs + PNG previews.
"""
import base64, io, pathlib, subprocess
import qrcode, qrcode.image.svg
from PIL import Image

HERE = pathlib.Path(__file__).parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
NAMES = {"en": "English", "vi": "Vietnamese", "bi": "Bilingual"}
SITE = HERE.parent / "Website" / "assets"

FACTS = {
    "phone": "(206) 429-3770",
    "addr1": "2020 S 320th St, Suite G",
    "addr2": "Federal Way, WA 98003",
    "url": "hotpotworld.com",
    "qr": "https://www.hotpotworld.com",
    "p_combo": "$39.99", "p_hotpot": "$30.00", "p_broth": "$8.50", "p_kids": "$20",
    "plates": [("#2F7FD0", "$2.50"), ("#3FA34D", "$3.50"), ("#C0262E", "$4.50"), ("#E9B21C", "$5.50")],
}

COPY = {
    "en": {
        "lang": "en",
        "kicker": "Conveyor-belt hot pot &amp; BBQ",
        "h1": "Cook it yourself.<br>Eat until you are happy.",
        "sub": "All you can eat, right off the belt. Federal Way.",
        "combo": "All You Can Eat<br><b>Hot Pot &amp; BBQ</b>",
        "hotpot": "All You Can Eat<br><b>Hot Pot</b>",
        "payg": "Pay What You Eat",
        "payg_note": "Broth {p_broth}, then by plate color",
        "plate_names": ["Blue", "Green", "Red", "Yellow"],
        "decal_big": "$2 off",
        "decal_small": "Seniors &amp;<br>Military",
        "kids": "Kids 5–10: <b>{p_kids}</b>",
        "how_h": "How it works",
        "how": [
            "Vegetables, noodles and dumplings ride the belt.",
            "Order meat from your server.",
            "Seafood, mushrooms and sauces are self-serve.",
            "Broths from across Asia, mild to very spicy.",
        ],
        "open_k": "Open daily", "open_v": "11 AM – 10 PM",
        "call_k": "Call",
        "find_k": "Find us",
        "scan": "Scan for the menu",
    },
    "vi": {
        "lang": "vi",
        "kicker": "Lẩu băng chuyền &amp; Nướng BBQ",
        "h1": "Tự nấu.<br>Ăn thỏa thích.",
        "sub": "Ăn thả ga ngay trên băng chuyền. Tại Federal Way.",
        "combo": "Buffet<br><b>Lẩu &amp; Nướng</b>",
        "hotpot": "Buffet<br><b>Lẩu</b>",
        "payg": "Ăn bao nhiêu, trả bấy nhiêu",
        "payg_note": "Nước lẩu {p_broth}, rồi tính theo màu dĩa",
        "plate_names": ["Xanh dương", "Xanh lá", "Đỏ", "Vàng"],
        "decal_big": "Giảm $2",
        "decal_small": "Người cao niên<br>&amp; quân nhân",
        "kids": "Trẻ em 5–10 tuổi: <b>{p_kids}</b>",
        "how_h": "Cách ăn",
        "how": [
            "Rau, mì và há cảo chạy trên băng chuyền.",
            "Thịt thì gọi nhân viên phục vụ.",
            "Hải sản, nấm và nước chấm tự lấy.",
            "Nước lẩu khắp châu Á, từ không cay đến rất cay.",
        ],
        "open_k": "Mở cửa mỗi ngày", "open_v": "11 giờ sáng – 10 giờ tối",
        "call_k": "Gọi",
        "find_k": "Địa chỉ",
        "scan": "Quét mã xem thực đơn",
    },
    "bi": {
        "lang": "en",
        "kicker": "Hot pot &amp; BBQ · Lẩu &amp; Nướng",
        "h1": "Cook it yourself.<br>Eat until you are happy.<span class=\"vn\">Tự nấu. Ăn thỏa thích.</span>",
        "sub": "",
        "combo": "All You Can Eat<br><b>Hot Pot &amp; BBQ</b><span class=\"vn\">Buffet Lẩu &amp; Nướng</span>",
        "hotpot": "All You Can Eat<br><b>Hot Pot</b><span class=\"vn\">Buffet Lẩu</span>",
        "payg": "Pay What You Eat<span class=\"vn\">Ăn bao nhiêu, trả bấy nhiêu</span>",
        "payg_note": "Broth {p_broth}, then by plate color<br>Nước lẩu {p_broth}, tính theo màu dĩa",
        "plate_names": ["Blue<br>Xanh dương", "Green<br>Xanh lá", "Red<br>Đỏ", "Yellow<br>Vàng"],
        "decal_big": "$2 off",
        "decal_small": "Seniors &amp; Military<i>Cao niên &amp;<br>quân nhân</i>",
        "kids": "Kids 5–10 · Trẻ em 5–10 tuổi: <b>{p_kids}</b>",
        "how_h": "How it works · Cách ăn",
        "how": [
            "Vegetables, noodles and dumplings ride the belt.<span class=\"vn\">Rau, mì và há cảo chạy trên băng chuyền.</span>",
            "Order meat from your server.<span class=\"vn\">Thịt thì gọi nhân viên phục vụ.</span>",
            "Seafood, mushrooms and sauces are self-serve.<span class=\"vn\">Hải sản, nấm và nước chấm tự lấy.</span>",
            "Broths from across Asia, mild to very spicy.<span class=\"vn\">Nước lẩu khắp châu Á, từ không cay đến rất cay.</span>",
        ],
        "open_k": "Open daily<span class=\"vn\">Mở cửa mỗi ngày</span>",
        "open_v": "11 AM – 10 PM<span class=\"vn\">11 giờ sáng – 10 giờ tối</span>",
        "call_k": "Call<span class=\"vn\">Gọi</span>",
        "find_k": "Find us<span class=\"vn\">Địa chỉ</span>",
        "scan": "Scan for the menu<br>Quét mã xem thực đơn",
    },
}


def b64(path, max_w=None, quality=86):
    im = Image.open(path)
    if im.mode == "RGBA":
        bbox = im.getchannel("A").getbbox()  # crop logo to ink bounds
        im = im.crop(bbox)
        buf = io.BytesIO(); im.save(buf, "PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    im = im.convert("RGB")
    if max_w and im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=quality)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def font_faces():
    css = []
    for w in (400, 600, 800):
        for sub in ("latin", "latin-ext", "vietnamese"):
            f = SITE / "fonts" / f"bevietnampro-{w}-{sub}.woff2"
            data = base64.b64encode(f.read_bytes()).decode()
            css.append(f"@font-face{{font-family:'BVP';font-weight:{w};"
                       f"src:url(data:font/woff2;base64,{data}) format('woff2');}}")
    return "\n".join(css)


def qr_svg(url):
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, border=0,
                      error_correction=qrcode.constants.ERROR_CORRECT_M)
    return img.to_string(encoding="unicode")


CSS = """
@page { size: letter; margin: 0.3in; }
html, body { margin: 0; }
* { box-sizing: border-box; }
:root { --void:#0E0D0C; --dim:#5C544E; --ink:#141210; --red:#C0262E; --red-deep:#96181F;
  --yellow:#FFC72C; --blue:#2F7FD0; --green:#3FA34D; --cream:#FFF3E0; --line:#F0DFC4; }
body { font-family:'BVP', sans-serif; color:var(--ink); background:#fff;
  -webkit-print-color-adjust:exact; print-color-adjust:exact; }
.page { width:7.9in; height:10.4in; display:flex; flex-direction:column; overflow:hidden; }
.vn { display:block; font-style:italic; font-weight:400; }

.hero { height:3.5in; flex:0 0 auto; border-radius:14px; overflow:hidden; background:var(--red); color:#fff;
  display:grid; grid-template-columns:2.85in 1fr; grid-template-rows:3.5in; }
.hero > * { min-height:0; height:3.5in; }
.hero img.photo { width:100%; height:100%; object-fit:cover; object-position:50% 40%; display:block; }
.hero .panel { padding:.24in .3in .24in; display:flex; flex-direction:column; }
.hero .logo { width:1.25in; }
.hero .copy { margin-top:auto; }
.kicker { font-weight:800; font-size:12pt; color:var(--yellow); margin:0 0 6pt; }
h1 { font-weight:800; font-size:26pt; line-height:1.06; letter-spacing:-.022em; margin:0; }
html[lang=vi] h1 { font-size:36pt; }
h1 .vn { font-size:17pt; letter-spacing:0; margin-top:4pt; color:#FFE6A6; }
.hero .sub { font-size:11pt; color:#FFE9E3; margin:9pt 0 0; line-height:1.35; }

.stripe { display:flex; gap:.06in; margin-top:.1in; flex:0 0 auto; }
.stripe i { flex:1; height:.1in; border-radius:99px; }

.prices { display:grid; grid-template-columns:1fr 1fr 1.25in; gap:.14in; margin-top:.1in; flex:0 0 auto; }
.price { border-radius:14px; padding:.14in .18in .12in; }
.price--y { background:var(--yellow); }
.price--b { background:var(--blue); color:#fff; }
.price .what { font-size:11.5pt; line-height:1.25; }
.price .what b { display:block; font-weight:800; font-size:15pt; }
.price .what .vn { font-size:10.5pt; margin-top:1pt; }
.price .amt { font-weight:800; font-size:31pt; letter-spacing:-.02em; line-height:1.05; margin-top:3pt; }
.price--y .amt { color:var(--red-deep); }
.decal { background:var(--green); color:#fff; border-radius:50%; width:1.25in; height:1.25in; align-self:center;
  border:.05in solid var(--yellow); display:flex; flex-direction:column; align-items:center; justify-content:center;
  text-align:center; transform:rotate(-6deg); }
.decal .big { font-weight:800; font-size:21pt; line-height:1; }
html[lang=vi] .decal .big { font-size:18pt; }
.decal .small { font-weight:600; font-size:8.5pt; line-height:1.2; margin-top:4pt; }
.decal .small i { font-weight:400; display:block; }

.payg { margin-top:.12in; background:var(--cream); border-radius:14px; padding:.12in .18in;
  display:flex; align-items:center; gap:.2in; flex:0 0 auto; }
.payg .t { flex:1 1 auto; }
.payg .t b { display:block; font-weight:800; font-size:15pt; color:var(--red-deep); }
.payg .t b .vn { font-size:11pt; color:var(--ink); }
.payg .t span { font-size:10.5pt; color:var(--dim); }
.plates { display:flex; gap:.08in; flex:0 0 auto; }
.plate { text-align:center; font-size:8.5pt; line-height:1.2; color:var(--dim); width:.8in; }
.plate i { display:flex; align-items:center; justify-content:center; width:.74in; height:.74in; margin:0 auto 3pt; border-radius:50%;
  border:.1in solid var(--c); background:#fff; font-style:normal; font-weight:800; font-size:10pt; color:var(--ink); }
.kids { font-size:11pt; margin:.09in 0 0; flex:0 0 auto; }
.kids span { display:inline-block; background:var(--yellow); border-radius:99px; padding:2pt 10pt; }

.how { display:grid; grid-template-columns:2.5in 1fr; gap:.2in; margin-top:.1in; flex:1 1 0; min-height:0; }
.how img { width:100%; height:100%; object-fit:cover; border-radius:10px; }
.how h2 { font-weight:800; font-size:15pt; margin:0 0 5pt; color:var(--red); }
.how ul { margin:0; padding:0; list-style:none; }
.how li { font-size:11.5pt; line-height:1.3; padding:4pt 0 4pt 20pt; position:relative; border-top:1px solid var(--line); }
.how li .vn { font-size:10pt; color:var(--dim); }
.how li::before { content:""; position:absolute; left:2pt; top:8pt; width:10pt; height:10pt; border-radius:50%; background:var(--blue); }
.how li:nth-child(2)::before { background:var(--green); }
.how li:nth-child(3)::before { background:var(--red); }
.how li:nth-child(4)::before { background:var(--yellow); }

.foot { flex:0 0 auto; margin-top:.14in; background:var(--red); color:#fff; border-radius:14px; padding:.16in .22in;
  display:grid; grid-template-columns:1fr 1.3in; gap:.2in; align-items:center; }
.facts { display:grid; grid-template-columns:auto 1fr; gap:4pt 14pt; font-size:12pt; }
.facts dt { color:var(--yellow); font-weight:600; font-size:10pt; padding-top:2pt; }
.facts dt .vn { font-weight:400; color:#FFE6A6; }
.facts dd { margin:0; font-weight:600; }
.facts dd .vn { font-weight:400; font-size:10.5pt; }
.facts dd.phone { font-weight:800; font-size:20pt; line-height:1.1; }
.qr { text-align:center; font-size:8.5pt; color:#FFE9E3; line-height:1.3; }
.qr .box { background:#fff; padding:6pt; border-radius:8px; width:1.1in; margin:0 auto; }
.qr svg { width:100%; height:auto; display:block; }
.qr .url { color:#fff; font-weight:800; font-size:9.5pt; margin-top:3pt; }

/* bilingual: two languages in the same space */
.bi .hero { height:2.95in; grid-template-rows:2.95in; }
.bi .hero > * { height:2.95in; }
.bi .hero .logo { width:1.05in; }
.bi .price { padding:.11in .18in .09in; }
.bi .price .amt { font-size:28pt; }
.bi .payg { padding:.09in .18in; }
.bi .plate i { width:.64in; height:.64in; border-width:.085in; font-size:9.5pt; }
.bi .foot { padding:.12in .22in; }
.bi .how li { font-size:10.5pt; padding:3pt 0 3pt 20pt; line-height:1.25; }
.bi .how li .vn { font-size:9.5pt; }
.bi .facts { gap:3pt 14pt; }
"""


def build(key, assets):
    c = COPY[key]; f = FACTS
    plates = "".join(f'<div class="plate"><i style="--c:{col}">{price}</i>{name}</div>'
                     for (col, price), name in zip(f["plates"], c["plate_names"]))
    how = "".join(f"<li>{x}</li>" for x in c["how"])
    return f"""<!doctype html>
<html lang="{c['lang']}" class="{key}"><head><meta charset="utf-8">
<title>Hot Pot World Rotary flyer ({key.upper()})</title>
<style>{assets['fonts']}{CSS}</style></head>
<body><div class="page">
  <section class="hero">
    <img class="photo" src="{assets['room']}" alt="">
    <div class="panel">
      <img class="logo" src="{assets['logo']}" alt="Hot Pot World Rotary">
      <div class="copy"><p class="kicker">{c['kicker']}</p><h1>{c['h1']}</h1>{c['sub'] and '<p class="sub">' + c['sub'] + '</p>'}</div>
    </div>
  </section>
  <div class="stripe"><i style="background:var(--blue)"></i><i style="background:var(--green)"></i><i style="background:var(--red)"></i><i style="background:var(--yellow)"></i></div>
  <section class="prices">
    <div class="price price--y"><div class="what">{c['combo']}</div><div class="amt">{f['p_combo']}</div></div>
    <div class="price price--b"><div class="what">{c['hotpot']}</div><div class="amt">{f['p_hotpot']}</div></div>
    <div class="decal"><span class="big">{c['decal_big']}</span><span class="small">{c['decal_small']}</span></div>
  </section>
  <section class="payg">
    <div class="t"><b>{c['payg']}</b><span>{c['payg_note'].format(**f)}</span></div>
    <div class="plates">{plates}</div>
  </section>
  <p class="kids"><span>{c['kids'].format(**f)}</span></p>
  <section class="how">
    <img src="{assets['plates']}" alt="">
    <div><h2>{c['how_h']}</h2><ul>{how}</ul></div>
  </section>
  <section class="foot">
    <dl class="facts">
      <dt>{c['open_k']}</dt><dd>{c['open_v']}</dd>
      <dt>{c['find_k']}</dt><dd>{f['addr1']}<br>{f['addr2']}</dd>
      <dt>{c['call_k']}</dt><dd class="phone">{f['phone']}</dd>
    </dl>
    <div class="qr"><div class="box">{assets['qr']}</div><div class="url">{f['url']}</div>{c['scan']}</div>
  </section>
</div></body></html>"""


if __name__ == "__main__":
    web = SITE / "img" / "web"
    assets = {
        "fonts": font_faces(),
        "room": b64(web / "belt-tall@2x.jpg", 1400),
        "plates": b64(web / "plates-meat@2x.jpg", 1400),
        "logo": b64(web / "logo-white.png"),
        "qr": qr_svg(FACTS["qr"]),
    }
    for key in COPY:
        html = HERE / f"flyer-{key}.html"
        html.write_text(build(key, assets), encoding="utf-8")
        pdf = HERE / f"Hot Pot World Flyer - {NAMES[key]}.pdf"
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf}", html.as_uri()], check=True, capture_output=True)
        subprocess.run(["pdftoppm", "-r", "300", "-png", "-singlefile", str(pdf), str(pdf.with_suffix(""))], check=True)
        print("wrote", pdf)
