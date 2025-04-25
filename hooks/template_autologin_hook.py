import asyncio


# example for an auto-login-hook
async def autologin(page):
    login_page = "<url-you-want-to-login-before-AutoMatt-starts>"
    username = "<username>"
    password = "<password>"
    domain = "<domainname>"
    await page.goto(login_page)
    await page.get_by_role("textbox", name="Domain name").click()
    await page.get_by_role("textbox", name="Domain name").fill(domain)
    await page.get_by_role("textbox", name="Username/Email address/Mobile").click()
    await page.get_by_role("textbox", name="Username/Email address/Mobile").fill(username)
    await page.get_by_role("textbox", name="Password").click()
    await page.get_by_role("textbox", name="Password").fill(password)
    await page.get_by_text("Log In").click()
    await asyncio.sleep(2)

