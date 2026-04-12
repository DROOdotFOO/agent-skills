---
title: Testing Patterns
impact: CRITICAL
impactDescription: Wrong test structure causes flaky tests, slow suites, and false confidence in coverage
tags: playwright, testing, fixtures, assertions, parallel, isolation
---

# Testing Patterns

## Test Structure

### TypeScript (@playwright/test)

```typescript
import { test, expect } from '@playwright/test';

test.describe('checkout flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/shop');
  });

  test('adds item to cart', async ({ page }) => {
    await page.getByRole('button', { name: 'Add to Cart' }).click();
    await expect(page.getByTestId('cart-count')).toHaveText('1');
  });

  test('completes purchase', async ({ page }) => {
    await page.getByRole('button', { name: 'Add to Cart' }).click();
    await page.getByRole('link', { name: 'Checkout' }).click();
    await expect(page).toHaveURL(/\/checkout/);
  });
});
```

### Python (pytest-playwright)

```python
import pytest
from playwright.sync_api import Page, expect


def test_adds_item_to_cart(page: Page) -> None:
    page.goto("/shop")
    page.get_by_role("button", name="Add to Cart").click()
    expect(page.get_by_test_id("cart-count")).to_have_text("1")


def test_completes_purchase(page: Page) -> None:
    page.goto("/shop")
    page.get_by_role("button", name="Add to Cart").click()
    page.get_by_role("link", name="Checkout").click()
    expect(page).to_have_url(re.compile(r"/checkout"))
```

---

## Fixtures and Context Isolation

Each test gets a fresh `BrowserContext` and `Page` by default. Do not reuse pages across tests.

### WRONG -- sharing state between tests

```typescript
// WRONG: test order dependency, shared state leaks
let sharedPage: Page;

test.beforeAll(async ({ browser }) => {
  sharedPage = await browser.newPage();
  await sharedPage.goto('/login');
  await sharedPage.fill('#user', 'admin');
  await sharedPage.fill('#pass', 'secret');
  await sharedPage.click('#submit');
});

test('sees dashboard', async () => {
  // uses sharedPage -- if beforeAll fails, all tests fail with confusing errors
  await expect(sharedPage.getByText('Dashboard')).toBeVisible();
});
```

### CORRECT -- isolated fixtures

```typescript
// CORRECT: each test is independent
test.describe('authenticated user', () => {
  test.use({ storageState: 'auth.json' }); // pre-saved auth state

  test('sees dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.getByText('Dashboard')).toBeVisible();
  });

  test('can update profile', async ({ page }) => {
    await page.goto('/profile');
    await page.getByLabel('Name').fill('New Name');
    await page.getByRole('button', { name: 'Save' }).click();
    await expect(page.getByText('Saved')).toBeVisible();
  });
});
```

### Python custom fixture

```python
import pytest
from playwright.sync_api import Browser, Page


@pytest.fixture()
def authenticated_page(browser: Browser) -> Page:
    context = browser.new_context(storage_state="auth.json")
    page = context.new_page()
    yield page
    context.close()


def test_dashboard(authenticated_page: Page) -> None:
    authenticated_page.goto("/dashboard")
    expect(authenticated_page.get_by_text("Dashboard")).to_be_visible()
```

---

## Assertions (Web-First)

Playwright assertions auto-retry until the condition is met or the timeout expires. Always use these over raw asserts.

### WRONG -- non-retrying assertion

```python
# WRONG: reads text once, fails immediately if element not ready
text = page.text_content(".status")
assert text == "Complete"
```

### CORRECT -- auto-retrying assertion

```python
# CORRECT: retries until text matches or timeout
expect(page.locator(".status")).to_have_text("Complete")
```

### Common assertions

```typescript
// Visibility
await expect(locator).toBeVisible();
await expect(locator).toBeHidden();

// Text
await expect(locator).toHaveText('exact text');
await expect(locator).toContainText('partial');

// Attributes and state
await expect(locator).toHaveAttribute('href', '/about');
await expect(locator).toBeEnabled();
await expect(locator).toBeChecked();

// Count
await expect(page.getByRole('listitem')).toHaveCount(3);

// Page-level
await expect(page).toHaveURL(/dashboard/);
await expect(page).toHaveTitle('Home');
```

---

## Parallel Execution

### TypeScript

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  workers: process.env.CI ? 2 : undefined, // auto-detect locally
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
});
```

### Python

```bash
# pytest-playwright uses pytest-xdist for parallelism
pip install pytest-xdist
pytest -n auto  # auto-detect worker count
```

### WRONG -- tests that break under parallelism

```python
# WRONG: depends on shared database row
def test_delete_user(page: Page) -> None:
    page.goto("/admin/users")
    page.get_by_role("button", name="Delete user-42").click()
    expect(page.get_by_text("user-42")).to_be_hidden()

def test_edit_user(page: Page) -> None:
    # fails if test_delete_user ran first
    page.goto("/admin/users/42/edit")
    expect(page.get_by_label("Name")).to_be_visible()
```

### CORRECT -- tests create their own data

```python
# CORRECT: each test sets up its own state
def test_delete_user(page: Page) -> None:
    # create a user via API, then test deletion
    user_id = create_test_user(name="delete-me")
    page.goto(f"/admin/users/{user_id}")
    page.get_by_role("button", name="Delete").click()
    expect(page.get_by_text("delete-me")).to_be_hidden()
```

---

## Configuration

### TypeScript (playwright.config.ts)

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? 'blob' : 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 5'] } },
    { name: 'mobile-safari', use: { ...devices['iPhone 13'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### Python (conftest.py / pytest.ini)

```ini
# pytest.ini
[pytest]
base_url = http://localhost:3000
```

```python
# conftest.py
import pytest

@pytest.fixture(scope="session")
def browser_context_args() -> dict:
    return {
        "viewport": {"width": 1280, "height": 720},
        "locale": "en-US",
    }
```

---

## Debugging Failed Tests

```bash
# TypeScript -- show trace viewer for last failure
npx playwright show-trace test-results/*/trace.zip

# TypeScript -- run in debug mode (step through)
npx playwright test --debug

# Python -- run headed with slowmo
pytest --headed --slowmo 500

# Both -- generate report
npx playwright show-report     # TypeScript
pytest --html=report.html      # Python (with pytest-html)
```
