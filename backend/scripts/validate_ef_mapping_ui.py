"""
Visual validation script for EF mapping.

TASK-FE-P8-011: Validates that emission factors auto-select in the UI.

Usage:
    python backend/scripts/validate_ef_mapping_ui.py
"""
import asyncio
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Error: Playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)


async def validate():
    """Validate EF mapping in the PCF Calculator UI."""
    screenshots_dir = Path(__file__).parent.parent.parent / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Navigating to PCF Calculator...")
        await page.goto("http://localhost:5173")
        await page.wait_for_load_state("networkidle")

        # Check if page loaded
        title = await page.title()
        print(f"Page title: {title}")

        # Take initial screenshot
        await page.screenshot(path=str(screenshots_dir / "pcf_initial.png"))
        print(f"Saved initial screenshot to {screenshots_dir / 'pcf_initial.png'}")

        # Look for product selector (could be ComboBox or Select)
        product_trigger = page.locator('[data-testid="product-combobox-trigger"], [data-testid="product-selector"]').first
        if await product_trigger.count() > 0:
            print("Found product selector trigger")
            await product_trigger.click()
            await page.wait_for_timeout(500)

            # Take screenshot of dropdown
            await page.screenshot(path=str(screenshots_dir / "pcf_dropdown.png"))

            # Try to find product options
            options = page.locator('[role="option"], [cmdk-item]')
            count = await options.count()
            print(f"Found {count} product options")

            if count > 1:
                # Click on a product
                await options.nth(1).click()
                await page.wait_for_timeout(1000)
                await page.screenshot(path=str(screenshots_dir / "pcf_product_selected.png"))
                print(f"Saved product selected screenshot")

        # Check the page content for BOM
        page_text = await page.text_content("body")

        if "Bill of Materials" in page_text or "BOM" in page_text:
            print("Found BOM section")

        # Look for emission factor dropdowns with selected values
        ef_triggers = page.locator('[aria-label="Emission factor"]')
        ef_count = await ef_triggers.count()
        print(f"Found {ef_count} emission factor dropdowns")

        selected_count = 0
        for i in range(min(ef_count, 10)):
            trigger = ef_triggers.nth(i)
            text = await trigger.text_content()
            if text and "Select factor" not in text:
                selected_count += 1
                print(f"  EF {i+1}: {text[:60]}...")

        print(f"\nEFs with auto-selection: {selected_count}/{ef_count}")

        await browser.close()
        print("\nValidation complete!")

        return selected_count > 0


if __name__ == "__main__":
    success = asyncio.run(validate())
    sys.exit(0 if success else 1)
