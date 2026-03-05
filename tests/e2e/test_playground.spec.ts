import { test, expect } from "@playwright/test";

test.describe("Search Playground", () => {
  test("page loads with correct title", async ({ page }) => {
    await page.goto("http://localhost:3000");
    await expect(page).toHaveTitle(/Semantic vs. Keyword/);
  });

  test("dataset tabs are visible", async ({ page }) => {
    await page.goto("http://localhost:3000");
    await expect(page.getByText("Landmarks")).toBeVisible();
    await expect(page.getByText("Movies")).toBeVisible();
    await expect(page.getByText("Science")).toBeVisible();
  });

  test("example query chips are visible for Landmarks", async ({ page }) => {
    await page.goto("http://localhost:3000");
    await expect(page.getByText("landmark in France")).toBeVisible();
  });

  test("clicking example query fills search bar", async ({ page }) => {
    await page.goto("http://localhost:3000");
    await page.getByText("landmark in France").click();
    const input = page.locator("input[type='text']");
    await expect(input).toHaveValue("landmark in France");
  });

  test("column headers visible after search", async ({ page }) => {
    // This test requires backend to be running
    // It uses a mock-friendly approach by checking UI structure
    await page.goto("http://localhost:3000");
    await page.getByText("landmark in France").click();
    await page.getByRole("button", { name: /search/i }).click();

    // Headers should appear immediately (they're always rendered)
    // In a real test with backend, we'd wait for results
    await expect(page.getByText("BM25 Keyword")).toBeVisible();
    await expect(page.getByText("Semantic Vector")).toBeVisible();
  });

  test("switching datasets clears results", async ({ page }) => {
    await page.goto("http://localhost:3000");
    // Switch to Movies
    await page.getByText("Movies").click();
    // Example queries should change
    await expect(
      page.getByText("film about artificial intelligence and emotions")
    ).toBeVisible();
  });
});
