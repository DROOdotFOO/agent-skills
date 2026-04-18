---
name: playwright
description: >
  Browser automation and end-to-end testing with Playwright (Python and TypeScript).
  TRIGGER when: user asks about browser automation, e2e testing, web scraping with
  a browser, Playwright setup, page navigation, selectors, screenshots, PDF generation,
  network interception, file uploads, auth flows, mobile viewports, or accessibility
  testing with Playwright. Also when code imports playwright, @playwright/test,
  pytest-playwright, or references playwright.config.
  DO NOT TRIGGER when: user asks about Cypress, Selenium, Puppeteer, or other browser
  automation tools; unit testing without a browser; HTTP-only scraping (use requests/httpx);
  or general pytest usage without Playwright.
metadata:
  author: droo
  version: "1.0"
  tags: playwright, e2e, testing, browser, automation, scraping, accessibility
---

# Playwright Skill

Browser automation and end-to-end testing with Playwright. Covers both Python (pytest-playwright) and TypeScript (@playwright/test).

## Core Principles

- **Auto-waiting by default** -- Playwright waits for elements to be actionable before interacting. Do not add manual sleeps.
- **Test isolation** -- Every test gets a fresh browser context. Do not share state between tests.
- **User-facing selectors** -- Prefer `getByRole`, `getByText`, `getByLabel` over CSS/XPath. These are resilient to DOM changes.
- **Web-first assertions** -- Use Playwright's built-in assertions that auto-retry, not raw `assert` or `expect` from other libraries.

## Quick Reference

### Python Setup

```bash
pip install pytest-playwright
playwright install
```

### TypeScript Setup

```bash
npm init playwright@latest
# or
npx playwright install
```

### Run Tests

```bash
# Python
pytest --headed                  # visible browser
pytest --browser firefox         # specific browser
pytest -k "test_login"           # filter by name

# TypeScript
npx playwright test              # all tests
npx playwright test --ui         # interactive UI mode
npx playwright test --debug      # step-through debugger
npx playwright test login.spec   # specific file
```

## WRONG vs CORRECT: Selector Strategy

### WRONG -- brittle CSS selectors

```python
# WRONG: tightly coupled to DOM structure
page.click("div.header > ul.nav > li:nth-child(3) > a")
page.fill("input#email-field-v2", "user@example.com")
```

### CORRECT -- user-facing locators

```python
# CORRECT: resilient to DOM changes
page.get_by_role("link", name="Settings").click()
page.get_by_label("Email").fill("user@example.com")
```

## WRONG vs CORRECT: Waiting

### WRONG -- manual sleep

```typescript
// WRONG: arbitrary delay, still flaky
await page.click('#submit');
await page.waitForTimeout(3000);
expect(await page.textContent('.result')).toBe('Done');
```

### CORRECT -- auto-retrying assertion

```typescript
// CORRECT: retries until condition met or timeout
await page.getByRole('button', { name: 'Submit' }).click();
await expect(page.getByText('Done')).toBeVisible();
```

## Sub-files

| File | Topic |
|------|-------|
| [testing-patterns.md](testing-patterns.md) | Test structure, fixtures, assertions, parallel execution |
| [selectors-and-waiting.md](selectors-and-waiting.md) | Locator strategies, auto-waiting, explicit waits, anti-patterns |
| [automation-recipes.md](automation-recipes.md) | Screenshots, PDF gen, network interception, auth, file uploads |
| [accessibility.md](accessibility.md) | axe-core integration, ARIA, keyboard navigation testing |

## What You Get

- Reference documentation for Playwright browser automation covering both Python (pytest-playwright) and TypeScript (@playwright/test).
- Selector strategies, auto-waiting patterns, and assertion best practices with WRONG vs CORRECT examples.
- Recipes for common automation tasks: screenshots, PDF generation, network interception, auth flows, file uploads, and accessibility testing.

## See also

- `tdd` -- for TDD workflow when writing Playwright tests
- `design-ux` -- for UI/UX patterns informing what to test
