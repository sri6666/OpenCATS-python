"""E2E tests for authentication flows"""
import pytest
from playwright.sync_api import Page, expect


class TestAuthenticationFlow:
    """Test user authentication flows"""

    def test_login_page_loads(self, page: Page, live_server):
        """Test that login page loads correctly"""
        page.goto(f'{live_server}/auth/login')

        # Check page title
        expect(page).to_have_title('Login - OpenCATS')

        # Check for login form elements
        expect(page.locator('input[name="email"]')).to_be_visible()
        expect(page.locator('input[name="password"]')).to_be_visible()
        expect(page.locator('button[type="submit"]')).to_be_visible()

    def test_login_with_valid_credentials(self, page: Page, live_server):
        """Test successful login with valid credentials"""
        page.goto(f'{live_server}/auth/login')

        # Fill in credentials
        page.fill('input[name="email"]', 'test@example.com')
        page.fill('input[name="password"]', 'password123')

        # Submit form
        page.click('button[type="submit"]')

        # Should redirect to dashboard
        expect(page).to_have_url(f'{live_server}/dashboard')

        # Check for dashboard elements
        expect(page.locator('text=Dashboard')).to_be_visible()

    def test_login_with_invalid_credentials(self, page: Page, live_server):
        """Test login failure with invalid credentials"""
        page.goto(f'{live_server}/auth/login')

        # Fill in invalid credentials
        page.fill('input[name="email"]', 'test@example.com')
        page.fill('input[name="password"]', 'wrongpassword')

        # Submit form
        page.click('button[type="submit"]')

        # Should stay on login page
        expect(page).to_have_url(f'{live_server}/auth/login')

        # Should show error message
        expect(page.locator('.alert-danger, .error, text=Invalid')).to_be_visible()

    def test_login_with_empty_fields(self, page: Page, live_server):
        """Test login form validation"""
        page.goto(f'{live_server}/auth/login')

        # Try to submit empty form
        page.click('button[type="submit"]')

        # Check for HTML5 validation or error messages
        email_input = page.locator('input[name="email"]')
        password_input = page.locator('input[name="password"]')

        # At least one should have validation error
        assert (
            email_input.evaluate('el => el.validity.valid') == False or
            password_input.evaluate('el => el.validity.valid') == False
        )

    def test_logout(self, authenticated_page: Page, live_server):
        """Test logout functionality"""
        # User should be on dashboard
        expect(authenticated_page).to_have_url(f'{live_server}/dashboard')

        # Click logout link/button
        authenticated_page.click('a[href="/auth/logout"], button:has-text("Logout")')

        # Should redirect to login page
        authenticated_page.wait_for_url(f'{live_server}/auth/login')
        expect(authenticated_page).to_have_url(f'{live_server}/auth/login')

    def test_protected_route_without_login(self, page: Page, live_server):
        """Test that protected routes redirect to login"""
        # Try to access dashboard without logging in
        page.goto(f'{live_server}/dashboard')

        # Should redirect to login
        page.wait_for_url(f'{live_server}/auth/login*')
        assert '/auth/login' in page.url

    def test_remember_me_functionality(self, page: Page, live_server):
        """Test remember me checkbox if it exists"""
        page.goto(f'{live_server}/auth/login')

        # Check if remember me checkbox exists
        remember_me = page.locator('input[name="remember"], input[type="checkbox"]')

        if remember_me.count() > 0:
            # Fill in credentials
            page.fill('input[name="email"]', 'test@example.com')
            page.fill('input[name="password"]', 'password123')

            # Check remember me
            remember_me.first.check()

            # Submit form
            page.click('button[type="submit"]')

            # Should redirect to dashboard
            expect(page).to_have_url(f'{live_server}/dashboard')
        else:
            pytest.skip('Remember me functionality not implemented')


class TestNavigationWhenAuthenticated:
    """Test navigation for authenticated users"""

    def test_cannot_access_login_when_authenticated(self, authenticated_page: Page, live_server):
        """Test that authenticated users are redirected from login page"""
        # Try to go to login page
        authenticated_page.goto(f'{live_server}/auth/login')

        # Should redirect to dashboard or stay on current page
        authenticated_page.wait_for_timeout(1000)
        # Either redirected to dashboard or prevented from accessing login
        assert '/auth/login' not in authenticated_page.url or authenticated_page.url == f'{live_server}/dashboard'

    def test_navigation_menu_visible(self, authenticated_page: Page, live_server):
        """Test that navigation menu is visible for authenticated users"""
        authenticated_page.goto(f'{live_server}/dashboard')

        # Check for main navigation items
        expect(authenticated_page.locator('a:has-text("Candidates"), a[href*="candidates"]')).to_be_visible()
        expect(authenticated_page.locator('a:has-text("Job"), a[href*="job"]')).to_be_visible()
        expect(authenticated_page.locator('a:has-text("Companies"), a[href*="companies"]')).to_be_visible()
