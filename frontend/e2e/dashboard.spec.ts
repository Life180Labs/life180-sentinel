import { expect, test } from "@playwright/test";

test.describe("Dashboard", () => {
  test("shows the Sentinel header", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Life180 Sentinel")).toBeVisible();
  });

  test("shows the evaluate form", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByPlaceholder("https://github.com/owner/repo")).toBeVisible();
    await expect(page.getByRole("button", { name: "Evaluate" })).toBeVisible();
  });

  test("evaluate button is disabled when input is empty", async ({ page }) => {
    await page.goto("/");
    const button = page.getByRole("button", { name: "Evaluate" });
    await expect(button).toBeDisabled();
  });

  test("evaluate button enables when URL is typed", async ({ page }) => {
    await page.goto("/");
    await page.getByPlaceholder("https://github.com/owner/repo").fill("https://github.com/test/repo");
    await expect(page.getByRole("button", { name: "Evaluate" })).toBeEnabled();
  });
});
