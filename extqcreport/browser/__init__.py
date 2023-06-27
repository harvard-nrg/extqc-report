import base64
import logging
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

async def snapshot(auth, url, saveto, landscape=False, scale=1):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        # create base64 encoded basic auth credentials
        credentials = f'{auth.username}:{auth.password}'
        credentials = base64.b64encode(
            f'{credentials}'.encode()).decode()
        await page.set_extra_http_headers({
            'Authorization': f'Basic {credentials}'
        })
        # get page
        await page.goto(url, timeout=0)
        await page.add_style_tag(
            content='html { -webkit-print-color-adjust: exact }'
        )
        # render to pdf
        await page.pdf(
            scale=scale,
            path=saveto,
            landscape=landscape,
            margin={
                'top': '30px',
                'right': '30px',
                'bottom': '30px',
                'left': '30px'
            }
        )
        await browser.close()

