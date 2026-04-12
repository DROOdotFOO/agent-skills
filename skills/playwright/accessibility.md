---
title: Accessibility Testing
impact: HIGH
impactDescription: Shipping inaccessible UIs excludes users and creates legal liability -- automated checks catch the low-hanging fruit
tags: playwright, accessibility, a11y, axe-core, aria, keyboard, wcag
---

# Accessibility Testing

## axe-core Integration

### TypeScript (@axe-core/playwright)

```bash
npm install -D @axe-core/playwright
```

```typescript
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('homepage has no a11y violations', async ({ page }) => {
  await page.goto('/');

  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});

// Scan specific region
test('nav is accessible', async ({ page }) => {
  await page.goto('/');

  const results = await new AxeBuilder({ page })
    .include('nav')
    .analyze();
  expect(results.violations).toEqual([]);
});

// Exclude known issues (tech debt, not a free pass)
test('page accessible excluding banner', async ({ page }) => {
  await page.goto('/');

  const results = await new AxeBuilder({ page })
    .exclude('.legacy-banner')
    .analyze();
  expect(results.violations).toEqual([]);
});

// Check against specific WCAG levels
test('meets WCAG 2.1 AA', async ({ page }) => {
  await page.goto('/');

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
    .analyze();
  expect(results.violations).toEqual([]);
});
```

### Python (axe-playwright-python)

```bash
pip install axe-playwright-python
```

```python
from axe_playwright_python.sync_playwright import Axe


def test_homepage_accessible(page: Page) -> None:
    page.goto("/")
    results = Axe().run(page)
    assert results.violations_count == 0, results.generate_report()


def test_form_accessible(page: Page) -> None:
    page.goto("/contact")
    results = Axe().run(page, context="form")
    assert results.violations_count == 0, results.generate_report()
```

---

## ARIA Locators

Playwright's role-based locators use the accessibility tree. Writing tests with `getByRole` doubles as accessibility verification -- if the locator cannot find the element, your HTML likely has ARIA problems.

### WRONG -- missing ARIA roles

```html
<!-- WRONG: divs with click handlers, no role or keyboard support -->
<div class="btn" onclick="submit()">Submit</div>
<div class="nav-item" onclick="goto('/about')">About</div>
<div class="checkbox" onclick="toggle()">Accept terms</div>
```

```typescript
// Tests use CSS because roles don't exist
await page.click('.btn');           // works, but the app is inaccessible
await page.click('.nav-item');
```

### CORRECT -- semantic HTML or ARIA

```html
<!-- CORRECT: semantic elements with proper roles -->
<button type="submit">Submit</button>
<nav><a href="/about">About</a></nav>
<label><input type="checkbox" /> Accept terms</label>
```

```typescript
// Role locators prove accessibility
await page.getByRole('button', { name: 'Submit' }).click();
await page.getByRole('link', { name: 'About' }).click();
await page.getByRole('checkbox', { name: 'Accept terms' }).check();
```

---

## Keyboard Navigation Testing

### Tab order

```typescript
test('tab order follows logical flow', async ({ page }) => {
  await page.goto('/login');

  // Tab through the form
  await page.keyboard.press('Tab');
  await expect(page.getByLabel('Email')).toBeFocused();

  await page.keyboard.press('Tab');
  await expect(page.getByLabel('Password')).toBeFocused();

  await page.keyboard.press('Tab');
  await expect(page.getByRole('button', { name: 'Sign in' })).toBeFocused();
});
```

### Keyboard interactions

```typescript
test('dropdown navigable with keyboard', async ({ page }) => {
  await page.goto('/settings');

  // Open dropdown with Enter
  await page.getByRole('combobox', { name: 'Theme' }).press('Enter');
  await expect(page.getByRole('option', { name: 'Dark' })).toBeVisible();

  // Navigate with arrows
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');

  await expect(page.getByRole('combobox', { name: 'Theme' })).toHaveText('Dark');
});

test('modal traps focus', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Open dialog' }).click();

  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();

  // Tab should cycle within dialog, not escape to background
  await page.keyboard.press('Tab');
  const focused = page.locator(':focus');
  await expect(focused).toBeVisible();
  // Verify focused element is inside dialog
  await expect(dialog.locator(':focus')).toBeVisible();

  // Escape closes dialog
  await page.keyboard.press('Escape');
  await expect(dialog).toBeHidden();
});
```

### Python keyboard testing

```python
def test_tab_order(page: Page) -> None:
    page.goto("/login")

    page.keyboard.press("Tab")
    expect(page.get_by_label("Email")).to_be_focused()

    page.keyboard.press("Tab")
    expect(page.get_by_label("Password")).to_be_focused()

    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Sign in")).to_be_focused()
```

---

## Color Contrast

axe-core checks contrast automatically with the `color-contrast` rule. For manual verification:

```typescript
test('text meets contrast requirements', async ({ page }) => {
  await page.goto('/');

  const results = await new AxeBuilder({ page })
    .withRules(['color-contrast'])
    .analyze();

  if (results.violations.length > 0) {
    const details = results.violations[0].nodes.map(n => ({
      html: n.html,
      issue: n.failureSummary,
    }));
    console.error('Contrast failures:', JSON.stringify(details, null, 2));
  }

  expect(results.violations).toEqual([]);
});
```

---

## Accessibility Test Strategy

Run axe scans on every page/route, not just the homepage. A common pattern:

```typescript
const routes = ['/', '/about', '/login', '/dashboard', '/settings'];

for (const route of routes) {
  test(`${route} has no a11y violations`, async ({ page }) => {
    await page.goto(route);
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();
    expect(results.violations).toEqual([]);
  });
}
```

### WRONG -- single a11y test for entire app

```typescript
// WRONG: only checks homepage, misses form pages with most issues
test('app is accessible', async ({ page }) => {
  await page.goto('/');
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});
```

### CORRECT -- test each route and interactive state

```typescript
// CORRECT: test routes AND interactive states (modals, expanded sections)
test('contact form accessible with validation errors', async ({ page }) => {
  await page.goto('/contact');
  await page.getByRole('button', { name: 'Send' }).click(); // trigger validation

  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);

  // Verify error messages are associated with inputs
  await expect(page.getByLabel('Email')).toHaveAttribute('aria-invalid', 'true');
  await expect(page.getByLabel('Email')).toHaveAttribute(
    'aria-describedby',
    expect.stringMatching(/error/)
  );
});
```
