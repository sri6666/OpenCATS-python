"""
UI/Frontend Tests using Selenium
Tests user interface and browser interactions
"""
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time


@pytest.fixture(scope='module')
def browser():
    """Create a browser instance for testing"""
    # Use headless Chrome for CI/CD environments
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)

    yield driver

    driver.quit()


@pytest.fixture
def live_server_url():
    """URL of the live test server"""
    # This should be updated to match your test server
    return 'http://localhost:5000'


class TestAuthenticationUI:
    """Tests for authentication UI"""

    def test_login_page_loads(self, browser, live_server_url):
        """Test that login page loads correctly"""
        browser.get(f'{live_server_url}/auth/login')

        assert 'Login' in browser.title or 'OpenCATS' in browser.title

        # Check for login form elements
        username_field = browser.find_element(By.NAME, 'username')
        password_field = browser.find_element(By.NAME, 'password')
        submit_button = browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')

        assert username_field is not None
        assert password_field is not None
        assert submit_button is not None

    def test_login_success(self, browser, live_server_url):
        """Test successful login"""
        browser.get(f'{live_server_url}/auth/login')

        # Fill in login form
        username_field = browser.find_element(By.NAME, 'username')
        password_field = browser.find_element(By.NAME, 'password')

        username_field.send_keys('admin')
        password_field.send_keys('admin123')

        # Submit form
        submit_button = browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_button.click()

        # Wait for redirect to dashboard
        time.sleep(2)

        # Should be redirected to dashboard
        assert 'dashboard' in browser.current_url.lower() or 'login' not in browser.current_url.lower()

    def test_login_failure(self, browser, live_server_url):
        """Test failed login with wrong credentials"""
        browser.get(f'{live_server_url}/auth/login')

        # Fill in login form with wrong credentials
        username_field = browser.find_element(By.NAME, 'username')
        password_field = browser.find_element(By.NAME, 'password')

        username_field.send_keys('wronguser')
        password_field.send_keys('wrongpass')

        # Submit form
        submit_button = browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_button.click()

        time.sleep(2)

        # Should show error message
        page_source = browser.page_source.lower()
        assert 'invalid' in page_source or 'incorrect' in page_source or 'error' in page_source

    def test_logout(self, browser, live_server_url):
        """Test logout functionality"""
        # First login
        browser.get(f'{live_server_url}/auth/login')
        username_field = browser.find_element(By.NAME, 'username')
        password_field = browser.find_element(By.NAME, 'password')
        username_field.send_keys('admin')
        password_field.send_keys('admin123')
        submit_button = browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_button.click()
        time.sleep(2)

        # Now logout
        browser.get(f'{live_server_url}/auth/logout')
        time.sleep(1)

        # Should be redirected to login
        assert 'login' in browser.current_url.lower()


class TestCandidateUI:
    """Tests for candidate management UI"""

    @pytest.fixture(autouse=True)
    def login(self, browser, live_server_url):
        """Auto-login before each test"""
        browser.get(f'{live_server_url}/auth/login')
        username_field = browser.find_element(By.NAME, 'username')
        password_field = browser.find_element(By.NAME, 'password')
        username_field.send_keys('admin')
        password_field.send_keys('admin123')
        submit_button = browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_button.click()
        time.sleep(2)

    def test_candidates_list_page(self, browser, live_server_url):
        """Test candidates list page loads"""
        browser.get(f'{live_server_url}/candidates')
        time.sleep(1)

        assert 'Candidates' in browser.page_source
        # Check for search box
        assert browser.find_elements(By.CSS_SELECTOR, 'input[type="text"]')

    def test_add_candidate_form(self, browser, live_server_url):
        """Test add candidate form"""
        browser.get(f'{live_server_url}/candidates/add')
        time.sleep(1)

        # Check form fields exist
        first_name = browser.find_element(By.NAME, 'first_name')
        last_name = browser.find_element(By.NAME, 'last_name')
        email = browser.find_element(By.NAME, 'email1')

        assert first_name is not None
        assert last_name is not None
        assert email is not None

    def test_create_new_candidate(self, browser, live_server_url):
        """Test creating a new candidate through UI"""
        browser.get(f'{live_server_url}/candidates/add')
        time.sleep(1)

        # Fill in form
        first_name = browser.find_element(By.NAME, 'first_name')
        last_name = browser.find_element(By.NAME, 'last_name')
        email = browser.find_element(By.NAME, 'email1')

        first_name.send_keys('UI Test')
        last_name.send_keys('Candidate')
        email.send_keys('uitest@example.com')

        # Submit form
        submit_button = browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_button.click()
        time.sleep(2)

        # Should redirect to candidates list or view page
        assert 'candidates' in browser.current_url.lower()

    def test_search_candidates(self, browser, live_server_url):
        """Test candidate search functionality"""
        browser.get(f'{live_server_url}/candidates')
        time.sleep(1)

        # Find search box
        search_box = browser.find_element(By.NAME, 'search')
        search_box.send_keys('Alice')

        # Submit search
        search_button = browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        search_button.click()
        time.sleep(2)

        # Results should be filtered
        assert 'candidates' in browser.current_url.lower()


class TestJobOrderUI:
    """Tests for job order management UI"""

    @pytest.fixture(autouse=True)
    def login(self, browser, live_server_url):
        """Auto-login before each test"""
        browser.get(f'{live_server_url}/auth/login')
        username_field = browser.find_element(By.NAME, 'username')
        password_field = browser.find_element(By.NAME, 'password')
        username_field.send_keys('admin')
        password_field.send_keys('admin123')
        submit_button = browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_button.click()
        time.sleep(2)

    def test_jobs_list_page(self, browser, live_server_url):
        """Test job orders list page"""
        browser.get(f'{live_server_url}/joborders')
        time.sleep(1)

        assert 'Job' in browser.page_source

    def test_pipeline_board(self, browser, live_server_url):
        """Test pipeline kanban board"""
        browser.get(f'{live_server_url}/joborders/pipeline/1')
        time.sleep(1)

        # Check for kanban columns
        page_source = browser.page_source.lower()
        assert 'pipeline' in page_source or 'kanban' in page_source or 'board' in page_source


class TestCompanyUI:
    """Tests for company management UI"""

    @pytest.fixture(autouse=True)
    def login(self, browser, live_server_url):
        """Auto-login before each test"""
        browser.get(f'{live_server_url}/auth/login')
        username_field = browser.find_element(By.NAME, 'username')
        password_field = browser.find_element(By.NAME, 'password')
        username_field.send_keys('admin')
        password_field.send_keys('admin123')
        submit_button = browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_button.click()
        time.sleep(2)

    def test_companies_list_page(self, browser, live_server_url):
        """Test companies list page"""
        browser.get(f'{live_server_url}/companies')
        time.sleep(1)

        assert 'Companies' in browser.page_source or 'Company' in browser.page_source

    def test_add_company_form(self, browser, live_server_url):
        """Test add company form"""
        browser.get(f'{live_server_url}/companies/add')
        time.sleep(1)

        # Check form fields
        name_field = browser.find_element(By.NAME, 'name')
        assert name_field is not None


class TestResponsiveDesign:
    """Tests for responsive design"""

    def test_mobile_viewport(self, browser, live_server_url):
        """Test page in mobile viewport"""
        # Set mobile viewport
        browser.set_window_size(375, 667)  # iPhone 6/7/8 size

        browser.get(f'{live_server_url}/auth/login')
        time.sleep(1)

        # Page should still be usable
        username_field = browser.find_element(By.NAME, 'username')
        assert username_field.is_displayed()

    def test_tablet_viewport(self, browser, live_server_url):
        """Test page in tablet viewport"""
        # Set tablet viewport
        browser.set_window_size(768, 1024)  # iPad size

        browser.get(f'{live_server_url}/auth/login')
        time.sleep(1)

        # Page should still be usable
        username_field = browser.find_element(By.NAME, 'username')
        assert username_field.is_displayed()


class TestAccessibility:
    """Tests for accessibility features"""

    def test_form_labels(self, browser, live_server_url):
        """Test that forms have proper labels"""
        browser.get(f'{live_server_url}/auth/login')
        time.sleep(1)

        # All inputs should have labels or aria-labels
        username_field = browser.find_element(By.NAME, 'username')
        password_field = browser.find_element(By.NAME, 'password')

        # Check for label or aria-label attribute
        assert (username_field.get_attribute('aria-label') or
                browser.find_elements(By.CSS_SELECTOR, 'label[for*="username"]'))

    def test_alt_text_for_images(self, browser, live_server_url):
        """Test that images have alt text"""
        browser.get(f'{live_server_url}/')
        time.sleep(1)

        images = browser.find_elements(By.TAG_NAME, 'img')
        for img in images:
            # Each image should have alt attribute
            alt_text = img.get_attribute('alt')
            assert alt_text is not None  # Can be empty but should exist


class TestPerformance:
    """Tests for performance metrics"""

    def test_page_load_time(self, browser, live_server_url):
        """Test that pages load within reasonable time"""
        start_time = time.time()

        browser.get(f'{live_server_url}/auth/login')

        load_time = time.time() - start_time

        # Page should load in less than 5 seconds
        assert load_time < 5.0

    def test_search_response_time(self, browser, live_server_url):
        """Test search response time"""
        # Login first
        browser.get(f'{live_server_url}/auth/login')
        username_field = browser.find_element(By.NAME, 'username')
        password_field = browser.find_element(By.NAME, 'password')
        username_field.send_keys('admin')
        password_field.send_keys('admin123')
        submit_button = browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_button.click()
        time.sleep(2)

        # Go to candidates and search
        browser.get(f'{live_server_url}/candidates')

        start_time = time.time()

        search_box = browser.find_element(By.NAME, 'search')
        search_box.send_keys('test')
        search_button = browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        search_button.click()

        # Wait for results
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'table'))
        )

        search_time = time.time() - start_time

        # Search should complete in less than 3 seconds
        assert search_time < 3.0


# NOTE: To run these tests, you need:
# 1. Chrome/Chromium browser installed
# 2. ChromeDriver installed and in PATH
# 3. Selenium package: pip install selenium
# 4. A running instance of the application
#
# Run with: pytest tests/test_ui.py -v
# Or with live server: pytest tests/test_ui.py -v --live-server=http://localhost:5000
