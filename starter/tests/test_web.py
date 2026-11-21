"""Public web pages + shared chrome + SEO plumbing."""

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
    assert 'class="topnav"' in r.text and 'href="/boats"' in r.text
    assert 'href="/faq"' in r.text
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


async def test_boats_page_lists_verified_boat(client, app):
    op = seed_operator(app)
    seed_boat(app, op, price_display="₹9,500/night", amenities=["life jackets", "shaded deck"])
    r = await client.get("/boats")
    assert r.status_code == 200
    assert "Lake Queen" in r.text and "Raj Boats" in r.text
    assert "₹9,500/night" in r.text
    assert "life jackets" in r.text and "shaded deck" in r.text
    assert ">available<" in r.text
    assert "Paayal never confirms bookings" in r.text
    assert "/inquire" not in r.text  # form removed — call CTA instead
    assert f'tel:+{"".join(c for c in PHONE if c.isdigit())}' in r.text


async def test_boats_hides_unverified_and_badges_demo(client, app):
    op = seed_operator(app)
    seed_boat(app, op, name="Ghost Boat", verified=False)
    seed_boat(app, op, name="Seed Cruiser", source="demo-seed")
    r = await client.get("/boats")
    assert "Ghost Boat" not in r.text
    assert "Seed Cruiser" in r.text
    assert ">DEMO<" in r.text


async def test_boats_hides_inactive_operator_boats(client, app):
    op = seed_operator(app)
    seed_boat(app, op, name="Mothballed", verified=True)
    with Session(app.state.engine) as s:
        s.get(Operator, op.id).active = False
        s.commit()
    r = await client.get("/boats")
    assert "Mothballed" not in r.text


async def test_paayal_page(client):
    r = await client.get("/paayal")
    assert r.status_code == 200
    assert "Meet Paayal" in r.text
    assert "Malayalam" in r.text
    assert "never" in r.text.lower()  # what Paayal never does
    assert "return call is simulated" in r.text  # honest callback disclosure
    assert PHONE in r.text  # call CTA


async def test_explore_page(client):
    r = await client.get("/explore")
    assert r.status_code == 200
    assert "Alappuzha" in r.text
    assert "Finishing Point" in r.text and "Punnamada" in r.text
    assert 'href="/boats"' in r.text


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


# --- new content pages ---

async def test_before_you_book_page(client):
    r = await client.get("/before-you-book")
    assert r.status_code == 200
    assert "What to ask before you book an Alappuzha houseboat" in r.text
    assert "registration" in r.text.lower()
    assert "Silver, Gold, or Diamond" in r.text
    assert "keralatourism.org/cls/houseboats" in r.text
    assert "onmanorama.com" in r.text
    assert PHONE in r.text


async def test_dtpc_page(client):
    r = await client.get("/dtpc-houseboat-counter")
    assert r.status_code == 200
    assert "DTPC" in r.text and "pre-paid houseboat counter" in r.text
    assert "₹2,500" in r.text
    assert "keralatourism.org/houseboat" in r.text
    assert "Confirm current details with DTPC" in r.text


async def test_faq_page(client):
    r = await client.get("/faq")
    assert r.status_code == 200
    assert "Can I book a houseboat through Kaayal?" in r.text
    assert "Nothing is booked until they say yes" in r.text
    assert "Malayalam and English" in r.text
    assert "recorded" not in r.text.lower()  # Q02 pending — no recording claim


async def test_nav_has_aria_current_and_all_pages(client):
    r = await client.get("/faq")
    assert 'href="/faq" aria-current="page"' in r.text
    for path in ("/explore", "/boats", "/paayal", "/before-you-book", "/faq"):
        assert f'href="{path}"' in r.text


async def test_boats_empty_state_is_honest(client):
    r = await client.get("/boats")
    assert "No boats on the list yet" in r.text
    assert "Call Paayal" in r.text


async def test_privacy_page(client):
    r = await client.get("/privacy")
    assert r.status_code == 200
    assert "anonymized after 90 days" in r.text
    assert "don’t call me" in r.text
    assert "09:00 and 18:00 IST" in r.text
    assert "no real outbound call" in r.text.lower() or "simulated" in r.text


async def test_footer_links_privacy_and_whatsapp(client):
    r = await client.get("/")
    assert 'href="/privacy"' in r.text
    assert "wa.me/" in r.text


# --- SEO plumbing ---

async def test_canonical_and_hreflang_present(client):
    r = await client.get("/faq")
    assert 'rel="canonical" href="http://test/faq"' in r.text
    assert 'hreflang="en"' in r.text
    assert 'hreflang="x-default"' in r.text


async def test_organization_jsonld_on_public_pages(client):
    r = await client.get("/")
    assert '"@type":"Organization"' in r.text
    assert '"name":"Kaayal"' in r.text
    # no fabricated rating/address
    assert "AggregateRating" not in r.text and "address" not in r.text


async def test_faqpage_jsonld_valid(client):
    r = await client.get("/faq")
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
    for p in ("/", "/boats", "/paayal", "/explore",
              "/before-you-book", "/dtpc-houseboat-counter", "/faq", "/privacy"):
        assert f"<loc>http://test{p}</loc>" in r.text
    assert "/admin" not in r.text and "/portal" not in r.text


async def test_public_pages_have_one_h1_and_titles(client):
    for path in ("/", "/boats", "/paayal", "/explore",
                 "/before-you-book", "/dtpc-houseboat-counter", "/faq", "/privacy"):
        r = await client.get(path)
        assert r.status_code == 200, path
        assert r.text.count("<h1") == 1, path
        title = re.search(r"<title>(.*?)</title>", r.text).group(1)
        assert len(title) <= 60, (path, title)
        if path != "/":
            assert title.endswith("| Kaayal"), (path, title)
        desc = re.search(r'name="description" content="(.*?)"', r.text)
        assert desc and len(desc.group(1)) <= 155, path
