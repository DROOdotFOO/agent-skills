---
title: Selectors and Waiting
impact: CRITICAL
impactDescription: Wrong selector strategy and manual waits are the top causes of flaky tests
tags: playwright, selectors, locators, waiting, flaky, auto-wait
---

# Selectors and Waiting

## Locator Priority (best to worst)

1. **Role locators** -- `getByRole('button', { name: 'Submit' })` -- best, matches accessibility tree
2. **Label/placeholder** -- `getByLabel('Email')`, `getByPlaceholder('Search')` -- tied to user-visible text
3. **Text** -- `getByText('Welcome back')` -- visible content
4. **Test ID** -- `getByTestId('submit-btn')` -- stable but not user-facing
5. **CSS** -- `locator('.btn-primary')` -- fragile, breaks on class renames
6. **XPath** -- `locator('//div[@class="header"]')` -- worst, extremely fragile

### WRONG -- CSS/XPath selectors

```typescript
// WRONG: fragile, breaks when designers change class names
await page.click('.MuiButton-root.MuiButton-containedPrimary');
await page.fill('input[data-v-3e4f5a6b]', 'test@example.com');
await page.click('//div[contains(@class, "modal")]//button[2]');
```

### CORRECT -- user-facing locators

```typescript
// CORRECT: resilient, matches what users see
await page.getByRole('button', { name: 'Sign Up' }).click();
await page.getByLabel('Email address').fill('test@example.com');
await page.getByRole('dialog').getByRole('button', { name: 'Confirm' }).click();
```

---

## Filtering and Chaining Locators

```typescript
// Filter by text within a role
page.getByRole('listitem').filter({ hasText: 'Product A' });

// Chain locators for scope
page.getByRole('navigation').getByRole('link', { name: 'About' });

// Filter by child locator
page.getByRole('listitem').filter({
  has: page.getByRole('button', { name: 'Add' }),
});

// nth element (0-indexed) -- use sparingly
page.getByRole('listitem').nth(0);
```

### Python equivalents

```python
# Filter
page.get_by_role("listitem").filter(has_text="Product A")

# Chain
page.get_by_role("navigation").get_by_role("link", name="About")

# Filter by child
page.get_by_role("listitem").filter(
    has=page.get_by_role("button", name="Add")
)
```

---

## Auto-Waiting

Playwright auto-waits before actions. The element must be:
- Attached to DOM
- Visible
- Stable (not animating)
- Enabled (not disabled)
- Receiving events (not obscured)

**You do not need to add waits before clicks, fills, or checks.** The action itself waits.

### WRONG -- unnecessary waits before actions

```python
# WRONG: redundant -- click already waits for the element
page.wait_for_selector("#submit-btn")
page.click("#submit-btn")

# WRONG: sleep is never the answer
import time
time.sleep(2)
page.click("#submit-btn")
```

### CORRECT -- just perform the action

```python
# CORRECT: click auto-waits for element to be actionable
page.get_by_role("button", name="Submit").click()
```

---

## When You DO Need Explicit Waits

Sometimes auto-waiting on the next action is not enough. Use explicit waits for:

### Waiting for navigation

```typescript
// Wait for navigation after click
await Promise.all([
  page.waitForURL('**/dashboard'),
  page.getByRole('button', { name: 'Login' }).click(),
]);

// Or use the simpler pattern (Playwright auto-waits for navigation on click)
await page.getByRole('button', { name: 'Login' }).click();
await page.waitForURL('**/dashboard');
```

### Waiting for network responses

```typescript
// Wait for API call to complete before asserting
const responsePromise = page.waitForResponse('**/api/users');
await page.getByRole('button', { name: 'Load' }).click();
const response = await responsePromise;
expect(response.status()).toBe(200);
```

### Waiting for element state changes

```typescript
// Wait for loading spinner to disappear
await expect(page.getByTestId('spinner')).toBeHidden();

// Wait for element to be detached from DOM
await page.getByTestId('modal').waitFor({ state: 'detached' });
```

### Python equivalents

```python
# Wait for navigation
page.get_by_role("button", name="Login").click()
page.wait_for_url("**/dashboard")

# Wait for network
with page.expect_response("**/api/users") as response_info:
    page.get_by_role("button", name="Load").click()
response = response_info.value
assert response.status == 200

# Wait for element state
expect(page.get_by_test_id("spinner")).to_be_hidden()
page.get_by_test_id("modal").wait_for(state="detached")
```

---

## Common Flaky Patterns and Fixes

### Race condition: action before page is ready

```typescript
// WRONG: page might not have hydrated yet
await page.goto('/app');
await page.getByRole('button', { name: 'Start' }).click(); // fails intermittently

// CORRECT: wait for app-specific ready signal
await page.goto('/app');
await expect(page.getByRole('button', { name: 'Start' })).toBeEnabled();
await page.getByRole('button', { name: 'Start' }).click();
```

### Race condition: asserting stale content

```typescript
// WRONG: text might show old value during transition
await page.getByRole('button', { name: 'Refresh' }).click();
const text = await page.textContent('.count'); // reads stale "0"
expect(text).toBe('5');

// CORRECT: auto-retrying assertion
await page.getByRole('button', { name: 'Refresh' }).click();
await expect(page.locator('.count')).toHaveText('5');
```

### Animation interference

```typescript
// Disable animations globally in config for test stability
// playwright.config.ts
export default defineConfig({
  use: {
    // Reduce motion to prevent animation flakiness
    reducedMotion: 'reduce',
  },
});
```

### Popup/dialog handling

```typescript
// WRONG: dialog appears before handler is registered
await page.getByRole('button', { name: 'Delete' }).click();
page.on('dialog', dialog => dialog.accept()); // too late

// CORRECT: register handler before triggering
page.on('dialog', dialog => dialog.accept());
await page.getByRole('button', { name: 'Delete' }).click();
```

```python
# Python equivalent
page.on("dialog", lambda dialog: dialog.accept())
page.get_by_role("button", name="Delete").click()
```

---

## Frame and Shadow DOM

```typescript
// iframes -- use frameLocator
const frame = page.frameLocator('#payment-iframe');
await frame.getByLabel('Card number').fill('4242424242424242');

// Shadow DOM -- Playwright pierces open shadow DOM by default
// Just use normal locators, they work through shadow roots
await page.getByRole('button', { name: 'Shadow Button' }).click();
```

```python
# Python iframe
frame = page.frame_locator("#payment-iframe")
frame.get_by_label("Card number").fill("4242424242424242")
```
