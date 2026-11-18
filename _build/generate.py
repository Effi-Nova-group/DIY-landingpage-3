#!/usr/bin/env python3
"""
Build the DIY Blinds satellite sites.

Each site in _build/content/*.json becomes a folder of plain static HTML:

    <domain>/
      index.html                      landing page (video hero -> main site)
      blog/index.html                 blog index
      blog/<slug>/index.html          5 articles
      assets/                         css, video, logos, blog images
      robots.txt, sitemap.xml

No build step, no dependencies, no server-side anything. Drop the folder on
any host (Netlify, Vercel, cPanel, S3) and it works.

Usage:  python3 _build/generate.py [site-key ...]
"""

import html
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "_build"
CONTENT = BUILD / "content"
SHARED = BUILD / "shared"
ASSETS = ROOT / "_assets"

# --------------------------------------------------------------------------
# The main site. Every satellite points here. When the Shopify store goes
# live, change these five values and re-run the script — all 9 sites update.
# --------------------------------------------------------------------------
MAIN = {
    "home": "https://diy-blinds.com.au/",
    "shop": "https://diy-blinds.com.au/shop/",
    "contact": "https://diy-blinds.com.au/contact-us/",
    "gallery": "https://diy-blinds.com.au/gallery/",
    "faq": "https://diy-blinds.com.au/faq/",
}

BRAND = {
    "legal": "DIY Blinds",
    "phone": "1300 040 577",
    "phone_href": "tel:1300040577",
}

BUILD_DATE = date.today().isoformat()


# ==========================================================================
# helpers
# ==========================================================================

def e(text):
    """Escape for HTML text/attribute context."""
    return html.escape(str(text), quote=True)


def jsonld(data):
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def strip_tags(markup):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", markup)).strip()


# ==========================================================================
# partials
# ==========================================================================

def head(site, *, title, desc, canonical, image=None, depth=0, extra=""):
    """depth = how many folders deep the page is, for relative asset paths."""
    up = "../" * depth
    base = f"https://{site['domain']}"
    og_image = f"{base}/{image}" if image else f"{base}/assets/img/logo.png"
    return f"""<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(canonical)}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">

<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(site['siteName'])}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:image" content="{e(og_image)}">
<meta property="og:locale" content="en_AU">
<meta name="twitter:card" content="summary_large_image">

<link rel="icon" href="{up}assets/img/favicon.png" type="image/png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap">
<link rel="stylesheet" href="{up}assets/css/site.css">
{extra}</head>
<body>
"""


def nav(site, *, depth=0, current=None):
    up = "../" * depth
    def mark(name):
        return ' aria-current="page"' if current == name else ""
    return f"""<header class="nav">
  <a class="nav__logo" href="{up}index.html" aria-label="{e(site['siteName'])} home">
    <img src="{up}assets/img/logo.png" alt="{e(site['siteName'])}" width="240" height="107">
  </a>
  <nav aria-label="Main">
    <ul class="nav__links">
      <li><a href="{up}blog/index.html"{mark('blog')}>Blogs</a></li>
      <li><a href="{e(MAIN['contact'])}">Contact</a></li>
    </ul>
  </nav>
</header>
"""


def footer(site, *, depth=0):
    up = "../" * depth
    return f"""<footer class="footer">
  <div class="wrap">
    <div class="footer__grid">
      <div>
        <img src="{up}assets/img/logo-white.png" alt="{e(site['siteName'])}" width="300" height="134">
        <p>{e(site['footerBlurb'])}</p>
      </div>
      <div>
        <h4>Shop</h4>
        <ul>
          <li><a href="{e(MAIN['shop'])}">All products</a></li>
          <li><a href="{e(MAIN['gallery'])}">Gallery</a></li>
          <li><a href="{e(MAIN['faq'])}">FAQs</a></li>
        </ul>
      </div>
      <div>
        <h4>Get in touch</h4>
        <ul>
          <li><a href="{e(MAIN['contact'])}">Contact us</a></li>
          <li><a href="{BRAND['phone_href']}">{e(BRAND['phone'])}</a></li>
          <li><a href="{up}blog/index.html">Blogs</a></li>
        </ul>
      </div>
    </div>
    <div class="footer__base">
      <span>&copy; {date.today().year} {e(BRAND['legal'])}. All rights reserved.</span>
      <span>{e(site['domain'])} is an official {e(BRAND['legal'])} site.</span>
    </div>
  </div>
</footer>
</body>
</html>
"""


def cta_strip(site):
    return f"""<section class="strip">
  <div class="wrap">
    <h2>{e(site['ctaHeading'])}</h2>
    <p>{e(site['ctaBody'])}</p>
    <a class="btn btn--primary" href="{e(MAIN['shop'])}">View all products</a>
  </div>
</section>
"""


def card(site, art, *, depth):
    up = "../" * depth
    return f"""      <article class="card">
        <a class="card__media" href="{up}blog/{art['slug']}/index.html" tabindex="-1" aria-hidden="true">
          <img src="{up}assets/img/{art['image']}" alt="" width="800" height="500" loading="lazy" decoding="async">
        </a>
        <div class="card__body">
          <p class="card__kicker">{e(art['kicker'])}</p>
          <h3><a href="{up}blog/{art['slug']}/index.html">{e(art['title'])}</a></h3>
          <p>{e(art['desc'])}</p>
          <p class="card__foot">{e(art['read'])} read</p>
        </div>
      </article>
"""


# ==========================================================================
# pages
# ==========================================================================

def page_home(site):
    base = f"https://{site['domain']}"
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": f"{base}/#website",
                "url": f"{base}/",
                "name": site["siteName"],
                "description": site["metaDesc"],
                "inLanguage": "en-AU",
                "publisher": {"@id": f"{base}/#org"},
            },
            {
                "@type": "Organization",
                "@id": f"{base}/#org",
                "name": BRAND["legal"],
                "url": MAIN["home"],
                "logo": f"{base}/assets/img/logo.png",
                "telephone": BRAND["phone"],
                "areaServed": "AU",
                "sameAs": [MAIN["home"]],
            },
        ],
    }

    cards = "".join(card(site, a, depth=0) for a in site["articles"])

    body = f"""{nav(site, depth=0)}
<main id="main">

  <section class="hero">
    <video class="hero__video" autoplay muted loop playsinline preload="auto"
           poster="assets/img/hero-poster.jpg" aria-hidden="true" tabindex="-1">
      <source src="assets/video/hero.mp4" type="video/mp4">
    </video>
    <div class="hero__scrim"></div>
    <div class="hero__inner">
      <h1>{e(site['heroH1'])}</h1>
      <p class="hero__sub">{e(site['heroSub'])}</p>
      <div class="hero__actions">
        <a class="btn btn--primary" href="{e(MAIN['shop'])}">View all products</a>
        <a class="btn btn--ghost" href="#guides">Read the guides</a>
      </div>
    </div>
  </section>

  <section class="section" id="intro">
    <div class="wrap">
      <div class="section__head">
        <h2>{e(site['introHeading'])}</h2>
        <p>{e(site['introBody'])}</p>
      </div>
    </div>
  </section>

  <section class="section section--paper" id="guides">
    <div class="wrap">
      <div class="section__head">
        <h2>{e(site['blogHeading'])}</h2>
        <p>{e(site['blogIntro'])}</p>
      </div>
      <div class="cards">
{cards}      </div>
    </div>
  </section>

{cta_strip(site)}
</main>
"""

    extra = f'<script type="application/ld+json">{jsonld(graph)}</script>\n'
    return (
        head(site, title=site["metaTitle"], desc=site["metaDesc"],
             canonical=f"{base}/", depth=0, extra=extra)
        + body
        + footer(site, depth=0)
    )


def page_blog_index(site):
    base = f"https://{site['domain']}"
    cards = "".join(card(site, a, depth=1) for a in site["articles"])

    items = [
        {
            "@type": "ListItem",
            "position": i + 1,
            "url": f"{base}/blog/{a['slug']}/",
            "name": a["title"],
        }
        for i, a in enumerate(site["articles"])
    ]
    graph = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"Blog — {site['siteName']}",
        "url": f"{base}/blog/",
        "description": site["blogMetaDesc"],
        "mainEntity": {"@type": "ItemList", "itemListElement": items},
    }

    body = f"""{nav(site, depth=1, current='blog')}
<main id="main" class="page">
  <section class="section section--tight">
    <div class="wrap">
      <div class="section__head">
        <h1 style="font-size:clamp(2rem,4.4vw,3rem);text-transform:uppercase">{e(site['blogHeading'])}</h1>
        <p>{e(site['blogIntro'])}</p>
      </div>
      <div class="cards">
{cards}      </div>
    </div>
  </section>

{cta_strip(site)}
</main>
"""

    extra = f'<script type="application/ld+json">{jsonld(graph)}</script>\n'
    return (
        head(site, title=site["blogMetaTitle"], desc=site["blogMetaDesc"],
             canonical=f"{base}/blog/", depth=1, extra=extra)
        + body
        + footer(site, depth=1)
    )


def page_article(site, art):
    base = f"https://{site['domain']}"
    url = f"{base}/blog/{art['slug']}/"
    img = f"{base}/assets/img/{art['image']}"

    faq_html = ""
    if art.get("faq"):
        blocks = "".join(
            f"""    <div class="faq__item">
      <h3>{e(f['q'])}</h3>
      <p>{f['a']}</p>
    </div>
"""
            for f in art["faq"]
        )
        faq_html = f"""  <section class="faq">
    <h2>Common questions</h2>
{blocks}  </section>
"""

    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "BlogPosting",
                "@id": f"{url}#article",
                "headline": art["title"],
                "description": art["desc"],
                "image": [img],
                "datePublished": art["date"],
                "dateModified": art["date"],
                "inLanguage": "en-AU",
                "mainEntityOfPage": {"@type": "WebPage", "@id": url},
                "author": {"@type": "Organization", "name": BRAND["legal"], "url": MAIN["home"]},
                "publisher": {
                    "@type": "Organization",
                    "name": BRAND["legal"],
                    "url": MAIN["home"],
                    "logo": {"@type": "ImageObject", "url": f"{base}/assets/img/logo.png"},
                },
                "wordCount": len(strip_tags(art["body"]).split()),
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{base}/"},
                    {"@type": "ListItem", "position": 2, "name": "Blogs", "item": f"{base}/blog/"},
                    {"@type": "ListItem", "position": 3, "name": art["title"], "item": url},
                ],
            },
        ],
    }

    if art.get("faq"):
        graph["@graph"].append({
            "@type": "FAQPage",
            "@id": f"{url}#faq",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": f["q"],
                    "acceptedAnswer": {"@type": "Answer", "text": strip_tags(f["a"])},
                }
                for f in art["faq"]
            ],
        })

    # related = the other four articles on this site
    others = [a for a in site["articles"] if a["slug"] != art["slug"]][:3]
    related = "".join(card(site, a, depth=2) for a in others)

    body = f"""{nav(site, depth=2)}
<main id="main" class="page article">

  <header class="article__head">
    <nav class="crumbs" aria-label="Breadcrumb">
      <a href="../../index.html">Home</a> / <a href="../index.html">Blogs</a>
    </nav>
    <h1>{e(art['h1'])}</h1>
    <p class="article__standfirst">{e(art['standfirst'])}</p>
    <p class="article__meta">{e(art['kicker'])} &middot; {e(art['read'])} read &middot; Updated {e(art['dateLabel'])}</p>
  </header>

  <div class="wrap">
    <figure class="article__hero">
      <img src="../../assets/img/{art['image']}" alt="{e(art['imageAlt'])}"
           width="1600" height="686" fetchpriority="high" decoding="async">
    </figure>
  </div>

  <div class="wrap">
    <div class="prose">
{art['body']}
{faq_html}    </div>
  </div>

  <section class="section section--paper" style="margin-top:80px">
    <div class="wrap">
      <div class="section__head"><h2>Keep reading</h2></div>
      <div class="cards">
{related}      </div>
    </div>
  </section>

{cta_strip(site)}
</main>
"""

    extra = f'<script type="application/ld+json">{jsonld(graph)}</script>\n'
    return (
        head(site, title=art["metaTitle"], desc=art["desc"], canonical=url,
             image=f"assets/img/{art['image']}", depth=2, extra=extra)
        + body
        + footer(site, depth=2)
    )


# ==========================================================================
# build
# ==========================================================================

def build(site):
    out = ROOT / site["domain"]
    if out.exists():
        shutil.rmtree(out)

    (out / "assets" / "css").mkdir(parents=True)
    (out / "assets" / "img").mkdir(parents=True)
    (out / "assets" / "video").mkdir(parents=True)
    (out / "blog").mkdir(parents=True)

    # assets
    shutil.copy2(SHARED / "site.css", out / "assets" / "css" / "site.css")
    shutil.copy2(ASSETS / "hero.mp4", out / "assets" / "video" / "hero.mp4")
    for name in ("logo.png", "logo-white.png", "favicon.png", "hero-poster.jpg"):
        src = ASSETS / name
        if src.exists():
            shutil.copy2(src, out / "assets" / "img" / name)

    wanted = {a["image"] for a in site["articles"]}
    for name in wanted:
        src = ASSETS / "blog" / name
        if src.exists():
            shutil.copy2(src, out / "assets" / "img" / name)
        else:
            print(f"  ! missing image: {name}")

    # pages
    (out / "index.html").write_text(page_home(site), encoding="utf-8")
    (out / "blog" / "index.html").write_text(page_blog_index(site), encoding="utf-8")
    for art in site["articles"]:
        d = out / "blog" / art["slug"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(page_article(site, art), encoding="utf-8")

    # robots + sitemap
    base = f"https://{site['domain']}"
    (out / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n", encoding="utf-8"
    )

    urls = [(f"{base}/", "1.0"), (f"{base}/blog/", "0.8")]
    urls += [(f"{base}/blog/{a['slug']}/", "0.7") for a in site["articles"]]
    entries = "".join(
        f"  <url><loc>{u}</loc><lastmod>{BUILD_DATE}</lastmod><priority>{p}</priority></url>\n"
        for u, p in urls
    )
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}</urlset>\n",
        encoding="utf-8",
    )

    pages = 2 + len(site["articles"])
    print(f"  built {site['domain']} — {pages} pages")
    return out


def load_sites():
    """Each _build/content/*.py defines a module-level dict called SITE."""
    import importlib.util

    sites = []
    for f in sorted(CONTENT.glob("*.py")):
        if f.name.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location(f.stem, f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        sites.append(mod.SITE)
    return sites


def main():
    wanted = set(sys.argv[1:])
    sites = load_sites()
    if not sites:
        sys.exit("No content files in _build/content/")

    for site in sites:
        if wanted and site["key"] not in wanted and site["domain"] not in wanted:
            continue
        build(site)


if __name__ == "__main__":
    main()
