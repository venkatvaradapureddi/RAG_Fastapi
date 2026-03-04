import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from fastapi import HTTPException

async def scrape_book_details(url: str) -> dict:
    """
    Scrapes books.toscrape.com.
    Returns a dict containing title, raw_html_table, description, and image_url.
    """
    # FIX: verify=False ignores SSL errors caused by corporate proxies
    async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            html_content = resp.text
        except httpx.HTTPError as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")

    soup = BeautifulSoup(html_content, "html.parser")

    try:
        # 1. Extract Title
        title_tag = soup.find("div", class_="product_main")
        title = title_tag.h1.text.strip() if title_tag else "Unknown Title"

        # 2. Extract Description
        desc_div = soup.find("div", id="product_description")
        description = desc_div.find_next_sibling("p").text.strip() if desc_div else "No description"

        # 3. Extract Raw HTML Table
        table_tag = soup.find("table", class_="table")
        raw_table_html = str(table_tag) if table_tag else ""

        # 4. Extract Image URL
        img_container = soup.find("div", class_="item active")
        img_rel = img_container.img['src'] if img_container else None
        full_img_url = urljoin(url, img_rel) if img_rel else None

    except Exception:
        raise HTTPException(status_code=400, detail="Invalid HTML structure. Is this books.toscrape.com?")

    # 5. Build the unified context chunk
    unified_text = f"""
    Title: {title}
    Description: {description}
    Product Data:
    {raw_table_html}
    """

    return {
        "title": title,
        "image_url": full_img_url,
        "content_chunk": unified_text
    }