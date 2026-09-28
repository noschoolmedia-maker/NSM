#!/usr/bin/env python3
"""No School Media — static site builder.

  python3 build.py            build index.html from data.json
  python3 build.py --serve    build, then serve at http://localhost:8000
                              (YouTube embeds need http(s); file:// gives error 153)
  python3 build.py --check    ask YouTube which videos allow embedding (needs internet)

Edit data.json (videos, copy, links), run again, upload the folder to any static host.
"""
import argparse, html, json, sys, urllib.parse, urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
esc = html.escape


def load():
    return json.loads((ROOT / "data.json").read_text(encoding="utf-8"))


def thumb(vid):
    return f"https://img.youtube.com/vi/{urllib.parse.quote(vid)}/hqdefault.jpg"


def card(i, v):
    cls = "card" + (" vertical" if v.get("vertical") else "") + (" featured" if v.get("featured") else "")
    return (
        f'<article class="{cls}" data-type="{esc(v["type"])}" data-i="{i}" tabindex="0" role="button" '
        f'aria-label="Play {esc(v["title"])}"><div class="thumb">'
        f'<img src="{thumb(v["id"])}" alt="{esc(v["title"])} thumbnail" loading="lazy">'
        f'<span class="play">▶</span></div><div class="info"><h3>{esc(v["title"])}</h3>'
        f'<div class="mono dim">{esc(v["client"])} • {esc(v["type"])} • {esc(v["year"])}</div></div></article>'
    )


def render(d):
    s, h, w, sv, ab, ct = d["site"], d["hero"], d["work"], d["services"], d["about"], d["contact"]
    vids = d["videos"]
    types = ["All"] + list(dict.fromkeys(v["type"] for v in vids))
    marquee = "".join(f"<span>{esc(c)}</span>" for c in d["clients"] * 4)
    pieces = {
        "TITLE": esc(s["title"]),
        "DESC": esc(s["description"]),
        "SHORT": esc(s["short"]),
        "NAME": esc(s["name"]),
        "YEAR": esc(s["year"]),
        "BASE": esc(s["base"]),
        "EMAIL": esc(s["email"]),
        "AVAIL": esc(s["availability"]),
        "EYEBROW": esc(h["eyebrow"]),
        "H1": esc(h["title"]),
        "TAGLINE": esc(h["tagline"]),
        "CTA1": esc(h["cta_primary"]),
        "CTA2": esc(h["cta_secondary"]),
        "REEL_ID": esc(h["reel_id"]),
        "REEL_THUMB": thumb(h["reel_id"]),
        "REEL_LABEL": esc(h["reel_label"]),
        "SPEC": esc(h["spec"]),
        "MARQUEE": marquee,
        "WORK_H": esc(w["heading"]),
        "WORK_INTRO": esc(w["intro"]),
        "COUNT": str(len(vids)),
        "FILTERS": "".join(
            f'<button class="chip mono{" on" if t == "All" else ""}" data-f="{esc(t)}">{esc(t)}</button>' for t in types
        ),
        "CARDS": "\n".join(card(i, v) for i, v in enumerate(vids)),
        "SV_H": esc(sv["heading"]),
        "SV_INTRO": esc(sv["intro"]),
        "SERVICES": "".join(
            f'<li class="glass"><span>{esc(x)}</span><span class="mono lime">{n:02d}</span></li>' for n, x in enumerate(sv["items"], 1)
        ),
        "AB_H": esc(ab["heading"]),
        "AB_ROLE": esc(ab["role"]),
        "AB_META": "".join(f'<div class="mono dim">{esc(m)}</div>' for m in ab["meta"]),
        "AB_P": "".join(f"<p>{esc(p)}</p>" for p in ab["paragraphs"]),
        "STATS": "".join(f'<div class="glass"><b>{esc(y)}</b><span class="mono dim">{esc(t)}</span></div>' for y, t in ab["timeline"]),
        "MANIFESTO": "".join(f"<li>{esc(m)}</li>" for m in ab["manifesto"]),
        "CT_H": esc(ct["heading"]),
        "CT_INTRO": esc(ct["intro"]),
        "CT_LOC": esc(ct["location"]),
        "SOCIALS": "".join(
            f'<a class="glass" href="{esc(x["href"])}" target="_blank" rel="noopener"><span><b>{esc(x["handle"])}</b> '
            f'<span class="mono dim">{esc(x["name"])}</span></span><span class="mono lime">{esc(x["label"])} →</span></a>'
            for x in d["socials"]
        ),
        # JSON embedded for the modal; "<" escaped so it can't close the script tag
        "VIDEOS_JSON": json.dumps(vids, ensure_ascii=False).replace("<", "\\u003c"),
        "MAIL_JSON": json.dumps(s["email"]),
    }
    out = TEMPLATE
    for k, v in pieces.items():
        out = out.replace("{{" + k + "}}", v)
    return out


def build():
    d = load()
    (ROOT / "index.html").write_text(render(d), encoding="utf-8")
    print(f"built index.html — {len(d['videos'])} videos")


def serve(port=8000):
    handler = partial(SimpleHTTPRequestHandler, directory=str(ROOT))
    print(f"serving http://localhost:{port}  (Ctrl+C to stop)")
    try:
        ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()
    except KeyboardInterrupt:
        pass


def check():
    """oEmbed returns 401/403 for videos whose owner disabled embedding, 404 for missing/private ones."""
    bad = 0
    for v in load()["videos"]:
        url = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(f"https://www.youtube.com/watch?v={v['id']}")
        try:
            urllib.request.urlopen(url, timeout=10).read()
            print(f"  ok      {v['id']}  {v['title']}")
        except Exception as e:
            bad += 1
            print(f"  PROBLEM {v['id']}  {v['title']}  ({getattr(e, 'code', e)})")
    print("all good" if not bad else f"{bad} video(s) need attention (embedding disabled, private, or removed)")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>{{TITLE}}</title>
<meta name="description" content="{{DESC}}">
<meta property="og:title" content="{{TITLE}}">
<meta property="og:description" content="{{DESC}}">
<meta property="og:image" content="{{REEL_THUMB}}">
<meta name="theme-color" content="#08080A">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
</head>
<body>
<div id="progress"></div>

<nav class="top">
  <a class="logo" href="#home">{{SHORT}}</a>
  <ul class="mono">
    <li><a href="#home">Home</a></li><li><a href="#work">Work</a></li><li><a href="#services">Services</a></li>
    <li><a href="#about">About</a></li><li><a href="#contact">Contact</a></li>
  </ul>
  <a class="btn solid mono" href="#contact">Start Project →</a>
</nav>

<header class="hero grid-bg" id="home">
  <div class="wrap">
    <div class="mono lime">{{EYEBROW}}</div>
    <h1 class="syne">{{H1}}</h1>
    <p class="lead">{{TAGLINE}}</p>
    <div class="cta">
      <a class="btn solid" href="#work">{{CTA1}}</a>
      <a class="btn" href="#contact">{{CTA2}}</a>
    </div>
    <div class="player" id="reel" data-id="{{REEL_ID}}" role="button" tabindex="0" aria-label="Play showreel">
      <img src="{{REEL_THUMB}}" alt="Showreel poster">
      <div class="shade"></div>
      <span class="play">▶</span>
      <div class="meta mono"><span>Click to play • {{REEL_LABEL}}</span><span class="dim">{{SPEC}}</span></div>
    </div>
    <div class="mono dim" style="margin-top:14px">{{AVAIL}}</div>
  </div>
</header>

<div class="marquee" aria-hidden="true"><div class="marquee-track">{{MARQUEE}}</div></div>

<section id="work">
  <div class="wrap">
    <div class="sec-head">
      <div><div class="mono lime">Work — {{COUNT}} pieces</div><h2 class="syne">{{WORK_H}}</h2></div>
      <p class="dim" style="max-width:36ch">{{WORK_INTRO}}</p>
    </div>
    <div class="filters">{{FILTERS}}</div>
    <div class="grid" id="grid">
{{CARDS}}
    </div>
  </div>
</section>

<section id="services">
  <div class="wrap">
    <div class="mono lime">Service</div>
    <h2 class="syne" style="font-size:clamp(34px,5vw,64px);margin:8px 0 14px">{{SV_H}}</h2>
    <p class="dim" style="max-width:60ch">{{SV_INTRO}}</p>
    <ul class="services-list">{{SERVICES}}</ul>
  </div>
</section>

<section id="about" class="about">
  <div class="wrap two">
    <div>
      <div class="mono lime">{{AB_ROLE}}</div>
      <h2 class="syne" style="font-size:clamp(34px,5vw,64px);margin:8px 0 14px">{{AB_H}}</h2>
      <div style="margin-bottom:22px">{{AB_META}}</div>
      {{AB_P}}
      <div class="stats">{{STATS}}</div>
    </div>
    <div>
      <div class="mono lime">Manifesto</div>
      <ul class="manifesto">{{MANIFESTO}}</ul>
    </div>
  </div>
</section>

<section id="contact">
  <div class="wrap two">
    <div>
      <div class="mono lime">Contact</div>
      <h2 class="syne" style="font-size:clamp(34px,5vw,64px);margin:8px 0 14px">{{CT_H}}</h2>
      <p class="dim">{{CT_INTRO}}</p>
      <div class="mono dim" style="margin-top:14px">Base — {{BASE}}</div>
      <div class="mono dim">{{CT_LOC}}</div>
      <div class="socials">{{SOCIALS}}</div>
    </div>
    <form class="inquiry glass" id="inquiry">
      <div class="mono lime">Project inquiry</div>
      <label><span class="mono dim">Name / brand</span><input name="name" required></label>
      <label><span class="mono dim">Email</span><input name="email" type="email" required></label>
      <label><span class="mono dim">Shoot date</span><input name="date"></label>
      <label><span class="mono dim">Brief</span><textarea name="brief" rows="4" required></textarea></label>
      <div style="display:flex;gap:10px;flex-wrap:wrap">
        <button class="btn solid" type="submit">Email us →</button>
        <button class="btn" type="button" id="copyMail">Copy email</button>
      </div>
      <div class="mono dim">Opens your mail app (mailto) — no backend needed.</div>
    </form>
  </div>
</section>

<footer>
  <div class="wrap" style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap">
    <span class="mono dim">© {{YEAR}} {{NAME}} • {{BASE}}</span>
    <span class="mono dim">Founder: David Mendoza</span>
  </div>
</footer>

<div id="modal" role="dialog" aria-modal="true" aria-label="Video player">
  <div class="modal-box" id="box">
    <div class="stage" id="stage"></div>
    <div class="modal-bar">
      <span class="mono dim" id="mtitle"></span>
      <span style="display:flex;gap:8px;flex-wrap:wrap">
        <button class="btn mono" id="prev">← Prev</button>
        <button class="btn mono" id="next">Next →</button>
        <button class="btn mono" id="copy">Copy link</button>
        <a class="btn solid mono" id="yt" target="_blank" rel="noopener">Watch on YouTube →</a>
        <button class="btn mono" id="close">✕ Close</button>
      </span>
    </div>
  </div>
</div>

<script id="videos" type="application/json">{{VIDEOS_JSON}}</script>
<script>
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var VIDEOS = JSON.parse($("#videos").textContent);
  var MAIL = {{MAIL_JSON}};
  var BAD = { 101: 1, 150: 1, 152: 1, 153: 1 };
  var current = -1, lastFocus = null;

  /* ---- YouTube embed (error 153 fix: referrer + origin + error listener) ---- */
  function embedUrl(id) {
    var u = "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(id) +
      "?autoplay=1&rel=0&modestbranding=1&playsinline=1&enablejsapi=1";
    if (/^https?:$/.test(location.protocol)) u += "&origin=" + encodeURIComponent(location.origin);
    return u;
  }
  function mountPlayer(stage, id) {
    stage.innerHTML = "";
    var spin = document.createElement("div"); spin.className = "spinner"; stage.appendChild(spin);
    var f = document.createElement("iframe");
    f.src = embedUrl(id);
    f.title = "YouTube video " + id;
    f.allow = "autoplay; encrypted-media; fullscreen; picture-in-picture";
    f.allowFullscreen = true;
    f.referrerPolicy = "strict-origin-when-cross-origin";
    f.style.cssText = "position:absolute;inset:0;width:100%;height:100%;border:0";
    f.addEventListener("load", function () {
      spin.remove();
      var ping = function () { try { f.contentWindow.postMessage(JSON.stringify({ event: "listening", id: 1, channel: "widget" }), "*"); } catch (e) {} };
      ping(); setTimeout(ping, 500); setTimeout(ping, 1500);
    });
    stage.appendChild(f);
    // If the file was opened straight from disk YouTube will always refuse; say so up front.
    if (location.protocol === "file:") setTimeout(function () { fallback(stage, id, "file://"); }, 1800);
  }
  function fallback(stage, id, code) {
    if ($(".fallback", stage)) return;
    var d = document.createElement("div");
    d.className = "fallback";
    d.style.backgroundImage = "url(https://img.youtube.com/vi/" + id + "/hqdefault.jpg)";
    d.innerHTML = '<div class="mono">Player can\u2019t load here (' + code + ')</div>' +
      '<a class="btn solid mono" target="_blank" rel="noopener" href="https://youtu.be/' + id + '">Watch on YouTube →</a>';
    stage.appendChild(d);
  }
  window.addEventListener("message", function (e) {
    var host; try { host = new URL(e.origin).hostname; } catch (_) { return; }
    if (!/(^|\.)youtube(-nocookie)?\.com$/.test(host)) return;
    var d; try { d = typeof e.data === "string" ? JSON.parse(e.data) : e.data; } catch (_) { return; }
    if (d && d.event === "onError" && BAD[d.info]) {
      $$("iframe").forEach(function (f) {
        if (f.contentWindow === e.source) fallback(f.parentNode, (/embed\/([^?]+)/.exec(f.src) || [])[1] || "", "error " + d.info);
      });
    }
  });

  /* ---- hero reel: click poster to load the player in place ---- */
  var reel = $("#reel");
  function playReel() { if ($("iframe", reel)) return; mountPlayer(reel, reel.dataset.id); reel.style.cursor = "default"; }
  reel.addEventListener("click", playReel);
  reel.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); playReel(); } });

  /* ---- modal ---- */
  var modal = $("#modal"), box = $("#box"), stage = $("#stage");
  function visible() { return $$(".card:not(.hide)").map(function (c) { return +c.dataset.i; }); }
  function open(i) {
    var v = VIDEOS[i]; if (!v) return;
    current = i; lastFocus = document.activeElement;
    box.classList.toggle("vertical", !!v.vertical);
    $("#mtitle").textContent = v.title + " • " + v.client + " • " + v.year;
    $("#yt").href = "https://youtu.be/" + v.id;
    mountPlayer(stage, v.id);
    modal.classList.add("open"); document.body.style.overflow = "hidden";
  }
  function close() {
    modal.classList.remove("open"); stage.innerHTML = ""; document.body.style.overflow = ""; current = -1;
    if (lastFocus) lastFocus.focus();
  }
  function step(dir) {
    var list = visible(), pos = list.indexOf(current);
    if (pos < 0 || !list.length) return;
    open(list[(pos + dir + list.length) % list.length]);
  }
  $("#grid").addEventListener("click", function (e) { var c = e.target.closest(".card"); if (c) open(+c.dataset.i); });
  $("#grid").addEventListener("keydown", function (e) {
    var c = e.target.closest(".card"); if (c && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); open(+c.dataset.i); }
  });
  $("#close").onclick = close;
  $("#prev").onclick = function () { step(-1); };
  $("#next").onclick = function () { step(1); };
  modal.addEventListener("click", function (e) { if (e.target === modal) close(); });
  document.addEventListener("keydown", function (e) {
    if (!modal.classList.contains("open")) return;
    if (e.key === "Escape") close();
    if (e.key === "ArrowLeft") step(-1);
    if (e.key === "ArrowRight") step(1);
  });
  function toast(t) {
    var el = document.createElement("div"); el.className = "toast"; el.textContent = t; document.body.appendChild(el);
    setTimeout(function () { el.remove(); }, 1800);
  }
  function copy(text, msg) {
    (navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject()).then(function () { toast(msg); }, function () { toast("Copy failed"); });
  }
  $("#copy").onclick = function () { copy("https://youtu.be/" + VIDEOS[current].id, "Link copied!"); };
  $("#copyMail").onclick = function () { copy(MAIL, "Email copied!"); };

  /* ---- filters ---- */
  $$(".chip").forEach(function (b) {
    b.addEventListener("click", function () {
      $$(".chip").forEach(function (x) { x.classList.toggle("on", x === b); });
      $$(".card").forEach(function (c) { c.classList.toggle("hide", b.dataset.f !== "All" && c.dataset.type !== b.dataset.f); });
    });
  });

  /* ---- contact form (mailto) ---- */
  $("#inquiry").addEventListener("submit", function (e) {
    e.preventDefault();
    var f = e.target, body = "Name/Brand: " + f.name.value + "\nEmail: " + f.email.value + "\nShoot date: " + f.date.value + "\n\n" + f.brief.value;
    location.href = "mailto:" + MAIL + "?subject=" + encodeURIComponent("Project inquiry — " + f.name.value) + "&body=" + encodeURIComponent(body);
  });

  /* ---- scroll progress + active nav link ---- */
  var bar = $("#progress"), links = $$("nav.top ul a");
  function onScroll() {
    var h = document.documentElement, max = h.scrollHeight - h.clientHeight;
    bar.style.transform = "scaleX(" + (max > 0 ? h.scrollTop / max : 0) + ")";
  }
  addEventListener("scroll", onScroll, { passive: true }); onScroll();
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (en) {
        if (en.isIntersecting) links.forEach(function (a) { a.classList.toggle("active", a.getAttribute("href") === "#" + en.target.id); });
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    $$("header[id], section[id]").forEach(function (s) { io.observe(s); });
  }

  /* ---- local-file warning ---- */
  if (location.protocol === "file:") {
    var b = document.createElement("div"); b.className = "local-banner";
    b.textContent = "Opened from a local file — YouTube embeds need http(s). Run: python3 build.py --serve";
    document.body.appendChild(b);
  }
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Build the No School Media site from data.json")
    ap.add_argument("--serve", action="store_true", help="serve on http://localhost:8000 after building")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--check", action="store_true", help="check every video allows embedding (needs internet)")
    a = ap.parse_args()
    if a.check:
        check()
        sys.exit()
    build()
    if a.serve:
        serve(a.port)
