import asyncio
from playwright.async_api import async_playwright

GROUPS = [
    "https://www.facebook.com/groups/224102010207139"
]

KEYWORDS = [
    "builder",
    "looking for a quote",
    "need a builder",
    "recommend a builder",
    "@everyone",
    "need a ticket sold"
]

def contains_keywords(text):
    text_lower = text.lower()
    return any(k.lower() in text_lower for k in KEYWORDS)

async def scan_groups():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="fb_state.json")
        page = await context.new_page()

        await page.goto(GROUPS[0])
        await page.wait_for_timeout(5000)

        # Scroll to load more posts
        for _ in range(5):
            await page.mouse.wheel(0, 3000)
            await page.wait_for_timeout(2000)

        # Expand "See more"
        see_more_buttons = await page.query_selector_all("div[role='button']:text('See more')")
        for btn in see_more_buttons:
            try:
                await btn.click()
            except:
                pass

        posts = await page.query_selector_all("div[role='article']")

        for post in posts:
            content = await post.inner_text()
            html = await post.inner_html()

            # --- USER NAME ---
            user_name = None

            # Pattern A: <a><span dir="auto">Name</span></a>
            name_el = await post.query_selector("a[role='link'] span[dir='auto']")
            if name_el:
                user_name = await name_el.inner_text()

            # Pattern B: <span dir="auto">Name</span> (no <a>)
            if not user_name:
                name_el = await post.query_selector("span[dir='auto']")
                if name_el:
                    user_name = await name_el.inner_text()


            # --- PROFILE LINK / USER ID ---
            profile_href = None
            user_id = None

            # Pattern A: /groups/.../user/ID/
            profile_el = await post.query_selector("a[href*='/user/']")
            if profile_el:
                profile_href = await profile_el.get_attribute("href")
                user_id = profile_href.split("/user/")[1].split("/")[0]

            # Pattern B: /profile.php?id=ID
            if not user_id:
                profile_el = await post.query_selector("a[href*='profile.php?id=']")
                if profile_el:
                    profile_href = await profile_el.get_attribute("href")
                    user_id = profile_href.split("id=")[1].split("&")[0]


            # --- BADGES ---
            badges = []

            # Pattern A: aria-label contains badge text
            badge_elements = await post.query_selector_all("div[aria-label*='view badge']")
            for b in badge_elements:
                try:
                    badges.append(await b.inner_text())
                except:
                    pass

            # Pattern B: <span>Author</span>, <span>Admin</span>, etc.
            badge_texts = ["Author", "Admin", "Top contributor", "Moderator"]
            for bt in badge_texts:
                el = await post.query_selector(f"span:has-text('{bt}')")
                if el:
                    badges.append(bt)


            # --- PRINT RESULTS ---
            print("USER:", user_name)
            print("USER ID:", user_id)
            print("PROFILE LINK:", profile_href)
            print("BADGES:", badges)



            if contains_keywords(content):
                print("\n🔥 MATCH FOUND 🔥")
                print(content)
                print("------------------------")

        await browser.close()

asyncio.run(scan_groups())
