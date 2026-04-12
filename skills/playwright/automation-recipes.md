---
title: Automation Recipes
impact: HIGH
impactDescription: Incorrect automation patterns lead to unreliable scraping, broken auth flows, and missed edge cases
tags: playwright, automation, screenshots, pdf, network, auth, upload, scraping
---

# Automation Recipes

## Screenshots

```python
# Full page screenshot
page.goto("https://example.com")
page.screenshot(path="full.png", full_page=True)

# Element screenshot
page.get_by_role("main").screenshot(path="content.png")

# Clip region
page.screenshot(path="header.png", clip={"x": 0, "y": 0, "width": 1280, "height": 200})
```

```typescript
// TypeScript equivalents
await page.screenshot({ path: 'full.png', fullPage: true });
await page.getByRole('main').screenshot({ path: 'content.png' });
```

### Visual comparison in tests

```typescript
// Snapshot testing -- compares against saved baseline
await expect(page).toHaveScreenshot('homepage.png');

// With threshold for minor rendering differences
await expect(page).toHaveScreenshot('chart.png', { maxDiffPixelRatio: 0.01 });

// Element-level snapshot
await expect(page.getByTestId('card')).toHaveScreenshot('card.png');
```

---

## PDF Generation

```python
# PDF works only with Chromium in headless mode
page.goto("https://example.com/report")
page.pdf(
    path="report.pdf",
    format="A4",
    margin={"top": "1cm", "bottom": "1cm", "left": "1cm", "right": "1cm"},
    print_background=True,
)
```

```typescript
await page.pdf({
  path: 'report.pdf',
  format: 'A4',
  margin: { top: '1cm', bottom: '1cm', left: '1cm', right: '1cm' },
  printBackground: true,
});
```

---

## Network Interception

### Mock an API response

```typescript
// Intercept and mock
await page.route('**/api/users', route =>
  route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify([{ id: 1, name: 'Test User' }]),
  })
);

await page.goto('/users');
await expect(page.getByText('Test User')).toBeVisible();
```

```python
def handle_route(route):
    route.fulfill(
        status=200,
        content_type="application/json",
        body='[{"id": 1, "name": "Test User"}]',
    )

page.route("**/api/users", handle_route)
page.goto("/users")
expect(page.get_by_text("Test User")).to_be_visible()
```

### Block resources (faster tests)

```typescript
// Block images, fonts, and CSS for faster page loads
await page.route('**/*.{png,jpg,jpeg,gif,svg,woff,woff2,css}', route =>
  route.abort()
);
```

### Modify requests

```typescript
// Add auth header to all API calls
await page.route('**/api/**', route =>
  route.continue_({
    headers: { ...route.request().headers(), 'Authorization': 'Bearer token123' },
  })
);
```

### Capture network traffic

```python
responses: list[dict] = []

def log_response(response):
    if "/api/" in response.url:
        responses.append({"url": response.url, "status": response.status})

page.on("response", log_response)
page.goto("/dashboard")

# Assert on captured traffic
assert any(r["url"].endswith("/api/data") for r in responses)
```

---

## Authentication

### Save and reuse auth state (recommended)

```typescript
// global-setup.ts -- runs once before all tests
import { chromium } from '@playwright/test';

async function globalSetup() {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  await page.goto('/login');
  await page.getByLabel('Email').fill('admin@example.com');
  await page.getByLabel('Password').fill('password');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL('/dashboard');

  // Save signed-in state
  await page.context().storageState({ path: 'auth.json' });
  await browser.close();
}

export default globalSetup;
```

```typescript
// playwright.config.ts
export default defineConfig({
  globalSetup: require.resolve('./global-setup'),
  use: {
    storageState: 'auth.json', // all tests start authenticated
  },
});
```

```typescript
// tests that need unauthenticated state
test.describe('public pages', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test('shows login page', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
  });
});
```

### Python auth setup

```python
# conftest.py
import pytest
from playwright.sync_api import Browser


@pytest.fixture(scope="session")
def auth_state(browser: Browser) -> dict:
    context = browser.new_context()
    page = context.new_page()
    page.goto("/login")
    page.get_by_label("Email").fill("admin@example.com")
    page.get_by_label("Password").fill("password")
    page.get_by_role("button", name="Sign in").click()
    page.wait_for_url("/dashboard")
    state = context.storage_state()
    context.close()
    return state


@pytest.fixture()
def authenticated_page(browser: Browser, auth_state: dict) -> Page:
    context = browser.new_context(storage_state=auth_state)
    page = context.new_page()
    yield page
    context.close()
```

---

## File Uploads

```typescript
// Single file
await page.getByLabel('Upload').setInputFiles('path/to/file.pdf');

// Multiple files
await page.getByLabel('Upload').setInputFiles(['file1.pdf', 'file2.pdf']);

// Clear file input
await page.getByLabel('Upload').setInputFiles([]);

// Non-input file uploads (drag-and-drop style)
const [fileChooser] = await Promise.all([
  page.waitForEvent('filechooser'),
  page.getByText('Drop files here').click(),
]);
await fileChooser.setFiles('path/to/file.pdf');
```

```python
# Python
page.get_by_label("Upload").set_input_files("path/to/file.pdf")

# Multiple
page.get_by_label("Upload").set_input_files(["file1.pdf", "file2.pdf"])

# File chooser
with page.expect_file_chooser() as fc_info:
    page.get_by_text("Drop files here").click()
file_chooser = fc_info.value
file_chooser.set_files("path/to/file.pdf")
```

---

## Downloads

```typescript
const downloadPromise = page.waitForEvent('download');
await page.getByRole('link', { name: 'Export CSV' }).click();
const download = await downloadPromise;

// Save to specific path
await download.saveAs('downloads/export.csv');

// Get download stream
const stream = await download.createReadStream();
```

```python
with page.expect_download() as download_info:
    page.get_by_role("link", name="Export CSV").click()
download = download_info.value
download.save_as("downloads/export.csv")
```

---

## Mobile Viewports

```typescript
import { devices } from '@playwright/test';

// In test file
test.use({ ...devices['iPhone 13'] });

test('mobile nav works', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Menu' }).click();
  await expect(page.getByRole('navigation')).toBeVisible();
});
```

```python
# conftest.py -- set viewport for mobile tests
@pytest.fixture()
def mobile_page(browser: Browser) -> Page:
    context = browser.new_context(
        viewport={"width": 390, "height": 844},
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)...",
        is_mobile=True,
        has_touch=True,
    )
    page = context.new_page()
    yield page
    context.close()
```

---

## Geolocation, Permissions, Locale

```typescript
test.use({
  geolocation: { latitude: 40.7128, longitude: -74.0060 },
  permissions: ['geolocation'],
  locale: 'en-US',
  timezoneId: 'America/New_York',
});

test('shows NYC weather', async ({ page }) => {
  await page.goto('/weather');
  await expect(page.getByText('New York')).toBeVisible();
});
```

---

## Web Scraping Pattern

```python
from playwright.sync_api import sync_playwright


def scrape_products(url: str) -> list[dict]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        # Wait for dynamic content
        page.wait_for_selector("[data-testid='product-list']")

        products = []
        for item in page.get_by_role("listitem").all():
            products.append({
                "name": item.get_by_role("heading").text_content(),
                "price": item.locator(".price").text_content(),
            })

        browser.close()
        return products
```

### WRONG -- scraping without waiting

```python
# WRONG: content might not have loaded yet
page.goto(url)
items = page.query_selector_all(".product")  # empty -- SPA hasn't rendered
```

### CORRECT -- wait for content

```python
# CORRECT: wait for the content you need
page.goto(url)
page.get_by_role("listitem").first.wait_for()  # at least one item present
items = page.get_by_role("listitem").all()
```
