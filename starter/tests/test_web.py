"""Public single-page site + shared chrome + SEO plumbing."""

import json
import re

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session

from app.config import Settings
from app.db import Boat, Operator, utcnow
from app.main import create_app
from app.portal import hash_token

SECRET = "test-tool-secret"
PHONE = "+91 94000 00000"


def make_settings() -> Settings:
    return Settings(
        sarvam_tool_shared_secret=SECRET,
        database_url="sqlite://",
        kaayal_public_base_url="",
        kaayal_phone_number=PHONE,
        kaayal_whatsapp_number="+91 94000 00001",
        _env_file=None,
    )


async def noop_responder(u, lang):
    return "ok"


@pytest.fixture
def app():
    return create_app(settings=make_settings(), responder=noop_responder)


@pytest.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def seed_operator(app, name="Raj Boats", phone="+910000000001", reachable=True):
    with Session(app.state.engine) as s:
        op = Operator(
            name=name, phone=phone, token_hash=hash_token("tok-" + phone),
            reachable=reachable, approved_at=utcnow(),
        )
        s.add(op)
        s.commit()
        s.refresh(op)
        return op


def seed_boat(app, op, name="Lake Queen", verified=True, available=True,
              source="operator-submitted", **kw):
    with Session(app.state.engine) as s:
        b = Boat(
            operator_id=op.id, name=name, embarkation_point="Finishing Point",
            verified_at=utcnow() if verified else None, available=available,
            source=source, **kw,
        )
        s.add(b)
        s.commit()
        s.refresh(b)
        return b


# --- shared chrome + page markers ---

async def test_landing_uses_shared_nav_and_footer(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert 'class="topnav"' in r.text
    for frag in ("#paayal", "#boats", "#explore", "#before-you-book", "#faq"):
        assert f'href="{frag}"' in r.text
    assert "Nothing on this site is a confirmed booking" in r.text
    assert "return calls are simulated" in r.text  # honesty line
    assert f'tel:+{"".join(c for c in PHONE if c.isdigit())}' in r.text


async def test_landing_has_no_data_storing_form_links(client):
    r = await client.get("/")
    assert "/inquire" not in r.text
    assert "/join" not in r.text


async def test_landing_shows_availability_and_demo_badges(client, app):
    op = seed_operator(app)
    seed_boat(app, op, name="Seed Cruiser", available=False, source="demo-seed")
    r = await client.get("/")
    assert "Seed Cruiser" in r.text
    assert ">DEMO<" in r.text
    assert "unavailable" in r.text


async def test_landing_callback_wording_is_honest_about_simulation(client):
    r = await client.get("/")
    assert "Paayal can call <i>you</i> back" in r.text  # the offer exists
    assert "return calls are simulated" in r.text      # footer disclosure


async def test_boats_section_lists_verified_boat(client, app):
    op = seed_operator(app)
    seed_boat(app, op, price_display="₹9,500/night", amenities=["life jackets", "shaded deck"])
    r = await client.get("/")
    assert r.status_code == 200
    assert "Lake Queen" in r.text and "Raj Boats" in r.text
    assert "₹9,500/night" in r.text
    assert "life jackets" in r.text and "shaded deck" in r.text
    assert ">available<" in r.text
    assert "Paayal never confirms bookings" in r.text


async def test_boats_hides_unverified_and_badges_demo(client, app):
    op = seed_operator(app)
    seed_boat(app, op, name="Ghost Boat", verified=False)
    seed_boat(app, op, name="Seed Cruiser", source="demo-seed")
    r = await client.get("/")
    assert "Ghost Boat" not in r.text
    assert "Seed Cruiser" in r.text
    assert ">DEMO<" in r.text


async def test_boats_hides_inactive_operator_boats(client, app):
    op = seed_operator(app)
    seed_boat(app, op, name="Mothballed", verified=True)
    with Session(app.state.engine) as s:
        s.get(Operator, op.id).active = False
        s.commit()
    r = await client.get("/")
    assert "Mothballed" not in r.text


async def test_boats_empty_state_is_honest(client):
    r = await client.get("/")
    assert "No boats on the list yet" in r.text
    assert "Call Paayal" in r.text


async def test_all_sections_present_on_one_page(client):
    r = await client.get("/")
    for sec in ('id="paayal"', 'id="boats"', 'id="explore"',
                'id="before-you-book"', 'id="dtpc"', 'id="faq"', 'id="privacy"'):
        assert sec in r.text, sec
    # spot-check content carried over from the retired pages
    for text in ("Finishing Point", "Punnamada",
                 "Silver, Gold, or Diamond", "₹2,500",
                 "Nothing is booked until they say yes",
                 "anonymized after 90 days", "09:00 and 18:00 IST",
                 "Malayalam and English"):
        assert text in r.text, text
    assert "keralatourism.org/cls/houseboats" in r.text
    assert "onmanorama.com" in r.text
    assert "/static/paayal.png" in r.text
    assert 'class="scene"' in r.text


async def test_footer_links_privacy_and_whatsapp(client):
    r = await client.get("/")
    assert 'href="#privacy"' in r.text
    assert "wa.me/" in r.text


# --- old page URLs redirect to anchors ---

async def test_old_page_routes_redirect(client):
    for path, frag in {
        "/paayal": "#paayal", "/boats": "#boats", "/explore": "#explore",
        "/before-you-book": "#before-you-book",
        "/dtpc-houseboat-counter": "#dtpc", "/faq": "#faq",
        "/privacy": "#privacy",
    }.items():
        r = await client.get(path)
        assert r.status_code == 301, path
        assert r.headers["location"].endswith("/" + frag), path


# --- removed form routes ---

async def test_inquire_route_is_gone(client):
    r = await client.get("/inquire")
    assert r.status_code == 404
    r = await client.post("/inquire", data={"name": "Anu", "phone": "+91 90000 00000"})
    assert r.status_code == 404


async def test_join_route_is_gone(client):
    r = await client.get("/join")
    assert r.status_code == 404
    r = await client.post("/join", data={"name": "X", "phone": "+91 90000 00000"})
    assert r.status_code == 404


# --- SEO plumbing ---

async def test_canonical_and_hreflang_present(client):
    r = await client.get("/")
    assert 'rel="canonical" href="http://test/"' in r.text
    assert 'hreflang="en"' in r.text
    assert 'hreflang="x-default"' in r.text


async def test_organization_jsonld_on_public_pages(client):
    r = await client.get("/")
    assert '"@type":"Organization"' in r.text
    assert '"name":"Kaayal"' in r.text
    # no fabricated rating/address
    assert "AggregateRating" not in r.text and "address" not in r.text


async def test_faqpage_jsonld_valid(client):
    r = await client.get("/")
    blocks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', r.text, re.DOTALL
    )
    data = next(
        (json.loads(b) for b in blocks if '"FAQPage"' in b), None
    )
    assert data, "FAQPage JSON-LD missing"
    assert data["@type"] == "FAQPage"
    assert len(data["mainEntity"]) == 10
    assert all(e["@type"] == "Question" for e in data["mainEntity"])


async def test_robots_txt(client):
    r = await client.get("/robots.txt")
    assert r.status_code == 200
    assert "Disallow: /admin" in r.text
    assert "Disallow: /api" in r.text
    assert "Sitemap: http://test/sitemap.xml" in r.text


async def test_sitemap_xml_lists_public_pages(client):
    r = await client.get("/sitemap.xml")
    assert r.status_code == 200
    assert "<loc>http://test/</loc>" in r.text
    assert "<loc>http://test/boats</loc>" not in r.text  # single-page now
    assert "/admin" not in r.text and "/portal" not in r.text


async def test_landing_has_one_h1_and_valid_metadata(client):
    r = await client.get("/")
    assert r.text.count("<h1") == 1
    title = re.search(r"<title>(.*?)</title>", r.text).group(1)
    assert len(title) <= 60, title
    desc = re.search(r'name="description" content="(.*?)"', r.text)
    assert desc and len(desc.group(1)) <= 155
