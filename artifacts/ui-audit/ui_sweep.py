"""UI audit sweep: screenshots + measurements across 3 viewports.

Read-only against the app; mutation-flavored states (auth, status change) are
fully route-mocked so no backend write ever happens.
"""
import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

BASE = "http://localhost:3000"
OUT = r"F:\Projects\house-hunter\artifacts\ui-audit"
MEAS = r"C:\Users\Maverick\AppData\Local\Temp\claude\F--Projects-house-hunter\7ff09736-2cbf-441f-8379-66941617609c\scratchpad\ui_measurements.json"

VIEWPORTS = {
    "mobile": {"width": 390, "height": 844},
    "tablet": {"width": 768, "height": 1024},
    "desktop": {"width": 1440, "height": 900},
}

console_log = []   # (viewport, state, type, text)
page_errors = []   # (viewport, state, text)
measurements = {}

os.makedirs(OUT, exist_ok=True)


def attach_console(page, vp, state_ref):
    page.on("console", lambda m: console_log.append((vp, state_ref[0], m.type, m.text[:400])))
    page.on("pageerror", lambda e: page_errors.append((vp, state_ref[0], str(e)[:400])))


def wait_board(page):
    # loading text gone and either grid, empty-state or error-state present
    page.wait_for_function(
        """() => !document.body.innerText.includes('Retrieving normalized') &&
                 (document.querySelector('.grid.grid-cols-1') ||
                  document.body.innerText.includes('No properties fit') ||
                  document.body.innerText.includes('Database Connection Failed'))""",
        timeout=20000,
    )
    page.evaluate("document.fonts && document.fonts.ready")
    page.wait_for_timeout(600)


def shot(page, vp, state, full=True, locator=None):
    path = os.path.join(OUT, f"{vp}_{state}.png")
    if locator is not None:
        locator.screenshot(path=path)
    else:
        page.screenshot(path=path, full_page=full)
    print(f"  shot {vp}_{state}.png")


def measure(page, vp):
    m = {}
    m["horizontal_overflow_px"] = page.evaluate(
        "document.documentElement.scrollWidth - document.documentElement.clientWidth")
    # tap targets: visible interactive elements smaller than 44px in either dimension
    m["small_tap_targets"] = page.evaluate("""() => {
        const out = [];
        for (const el of document.querySelectorAll('button, a, select, input')) {
            const r = el.getBoundingClientRect();
            if (r.width === 0 || r.height === 0) continue;
            const s = getComputedStyle(el);
            if (s.visibility === 'hidden' || s.display === 'none') continue;
            if (r.height < 44 || r.width < 44) {
                out.push({tag: el.tagName.toLowerCase(),
                          text: (el.innerText || el.value || el.type || '').slice(0, 32),
                          w: Math.round(r.width), h: Math.round(r.height)});
            }
        }
        return out;
    }""")
    # font sizes of the custom (possibly undefined) utility classes
    m["fontsize_text-3xs"] = page.evaluate(
        "(() => { const e = document.querySelector('.text-3xs'); return e ? getComputedStyle(e).fontSize : null })()")
    m["fontsize_text-2xs"] = page.evaluate(
        "(() => { const e = document.querySelector('.text-2xs'); return e ? getComputedStyle(e).fontSize : null })()")
    m["fontsize_text-xs"] = page.evaluate(
        "(() => { const e = document.querySelector('.text-xs'); return e ? getComputedStyle(e).fontSize : null })()")
    # does animate-fade-in resolve to an animation?
    m["animate-fade-in_resolved"] = page.evaluate(
        "(() => { const e = document.querySelector('.animate-fade-in'); return e ? getComputedStyle(e).animationName : 'no-element' })()")
    # color samples for contrast computation (walk-up composited background)
    m["color_samples"] = page.evaluate("""() => {
        function bgStack(el) {
            const stack = [];
            let n = el;
            while (n && n !== document.documentElement) {
                const bg = getComputedStyle(n).backgroundColor;
                if (bg && bg !== 'rgba(0, 0, 0, 0)') stack.push(bg);
                n = n.parentElement;
            }
            return stack;
        }
        const picks = [
            ['stat_label', 'p.text-xs.font-semibold.uppercase'],
            ['card_metric_label', '.text-3xs'],
            ['slider_legend', '.text-2xs'],
            ['fit_badge', 'span.text-indigo-300'],
            ['card_sub_label_slate500', 'p.text-3xs.text-slate-500'],
            ['header_sub', 'p.text-slate-400'],
        ];
        const out = {};
        for (const [name, sel] of picks) {
            const e = document.querySelector(sel);
            if (!e) { out[name] = null; continue; }
            out[name] = {color: getComputedStyle(e).color, bgs: bgStack(e),
                         text: (e.innerText || '').slice(0, 30)};
        }
        return out;
    }""")
    measurements[vp] = m


def run_viewport(pw, vp, size):
    print(f"== {vp} {size['width']}x{size['height']} ==")
    browser = pw.chromium.launch(headless=True)

    # --- context A: real data states ---
    ctx = browser.new_context(viewport=size, device_scale_factor=2)
    page = ctx.new_page()
    state_ref = ["default"]
    attach_console(page, vp, state_ref)

    # loading state (delay the API response)
    state_ref[0] = "loading"
    def delay_route(route):
        time.sleep(3.5)
        route.continue_()
    page.route("**/api/listings*", delay_route)
    page.goto(BASE)
    page.wait_for_timeout(900)
    shot(page, vp, "loading", full=False)
    page.unroute("**/api/listings*")

    # default board
    state_ref[0] = "default"
    page.goto(BASE)
    wait_board(page)
    shot(page, vp, "default")
    measure_filters_closed = True

    # sorts
    for value, name in [("commute_asc", "sort_commute"), ("price_asc", "sort_price_asc"),
                        ("price_desc", "sort_price_desc"), ("created_desc", "sort_newest")]:
        state_ref[0] = name
        page.select_option("select#sort", value)
        page.wait_for_timeout(400)
        shot(page, vp, name)
    page.select_option("select#sort", "fit_desc")

    # filters open
    state_ref[0] = "filters_open"
    page.get_by_role("button", name="Filters", exact=True).click()
    page.wait_for_timeout(500)
    shot(page, vp, "filters_open")

    # measurements (filters open so slider legends are in DOM)
    measure(page, vp)

    # include_rejected on (filters still open)
    state_ref[0] = "include_rejected"
    page.locator("button.relative.inline-flex.h-6.w-11").click()
    page.wait_for_timeout(300)
    wait_board(page)
    page.wait_for_timeout(600)
    shot(page, vp, "include_rejected")

    # long-title card (longest title on default board)
    state_ref[0] = "long_title"
    page.locator("button.relative.inline-flex.h-6.w-11").click()  # toggle rejected back off
    page.wait_for_timeout(300)
    wait_board(page)
    titles = page.locator("h3").all_inner_texts()
    if titles:
        longest = max(titles, key=len)
        card = page.locator("h3", has_text=longest[:60]).first.locator(
            "xpath=ancestor::div[contains(@class,'rounded-3xl')][1]")
        card.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        shot(page, vp, "long_title", locator=card)

    # password modal (close the filters panel first; scope click to card grid
    # so we don't hit the FilterBar "Interested" status pill)
    state_ref[0] = "password_modal"
    page.get_by_role("button", name="Filters", exact=True).click()
    page.wait_for_timeout(400)
    page.locator("[class*=\"lg:grid-cols-3\"] button", has_text="Interested").first.click()
    page.wait_for_timeout(600)
    shot(page, vp, "password_modal", full=False)

    # status change interaction — fully mocked, no backend write
    state_ref[0] = "status_change"
    page.route("**/api/auth/verify", lambda r: r.fulfill(
        status=200, content_type="application/json", body='{"valid": true}'))
    page.route("**/api/listings/*/status*", lambda r: r.fulfill(
        status=200, content_type="application/json", body='{"status": "success"}'))
    page.fill("input#password", "audit-mock")
    page.get_by_role("button", name="Authorize").click()
    page.wait_for_timeout(1200)
    shot(page, vp, "status_change")
    ctx.close()

    # --- context B: mocked data states ---
    for state, handler in [
        ("empty_board", lambda r: r.fulfill(status=200, content_type="application/json", body="[]")),
        ("api_down", lambda r: r.abort()),
    ]:
        ctx2 = browser.new_context(viewport=size, device_scale_factor=2)
        p2 = ctx2.new_page()
        sr = [state]
        attach_console(p2, vp, sr)
        p2.route("**/api/listings*", handler)
        p2.goto(BASE)
        p2.wait_for_timeout(2500)
        shot(p2, vp, state)
        ctx2.close()

    # null deposit + null sqft (mutate first row of the real payload)
    ctx3 = browser.new_context(viewport=size, device_scale_factor=2)
    p3 = ctx3.new_page()
    sr = ["null_fields"]
    attach_console(p3, vp, sr)
    def nullify(route):
        resp = route.fetch()
        data = resp.json()
        if data:
            data[0]["deposit"] = None
            data[0]["area_sqft"] = None
        route.fulfill(status=200, content_type="application/json", body=json.dumps(data))
    p3.route("**/api/listings*", nullify)
    p3.goto(BASE)
    try:
        p3.wait_for_selector("[class*=\"lg:grid-cols-3\"] > div", timeout=15000)
        p3.wait_for_timeout(600)
        card = p3.locator("[class*=\"lg:grid-cols-3\"] > div").first
        shot(p3, vp, "null_fields", locator=card)
    except Exception as e:
        print("  null_fields failed:", e)
    ctx3.close()

    browser.close()


with sync_playwright() as pw:
    for vp, size in VIEWPORTS.items():
        run_viewport(pw, vp, size)

with open(MEAS, "w", encoding="utf-8") as f:
    json.dump({"measurements": measurements,
               "console": console_log,
               "page_errors": page_errors}, f, indent=1)
print("wrote measurements JSON")
print(f"console messages: {len(console_log)} | page errors: {len(page_errors)}")
