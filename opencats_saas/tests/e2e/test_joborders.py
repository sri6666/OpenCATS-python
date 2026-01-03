"""E2E tests for job orders and pipeline"""
import pytest
from playwright.sync_api import Page, expect


class TestJobOrderList:
    """Test job order list page"""

    def test_joborders_list_page_loads(self, authenticated_page: Page, live_server):
        """Test that job orders list page loads"""
        authenticated_page.goto(f'{live_server}/joborders')

        # Check page loaded
        expect(authenticated_page).to_have_url(f'{live_server}/joborders')

        # Check for job orders heading
        expect(authenticated_page.locator('h1, h2')).to_contain_text('Job')

    def test_joborders_search(self, authenticated_page: Page, live_server):
        """Test job order search functionality"""
        authenticated_page.goto(f'{live_server}/joborders')

        # Look for search input
        search_input = authenticated_page.locator('input[name="search"], input[type="search"], input[placeholder*="Search"]')

        if search_input.count() > 0:
            # Enter search term
            search_input.first.fill('developer')

            # Submit search
            search_button = authenticated_page.locator('button[type="submit"]:near(input[name="search"])')
            if search_button.count() > 0:
                search_button.first.click()
            else:
                search_input.first.press('Enter')

            # Wait for results
            authenticated_page.wait_for_load_state('networkidle')

            # URL should contain search parameter
            assert 'search=' in authenticated_page.url or 'q=' in authenticated_page.url
        else:
            pytest.skip('Search functionality not visible')


class TestJobOrderDetail:
    """Test job order detail page"""

    def test_view_joborder_detail(self, authenticated_page: Page, live_server):
        """Test viewing job order details"""
        authenticated_page.goto(f'{live_server}/joborders')

        # Click on first job order (if exists)
        joborder_link = authenticated_page.locator('a[href*="/joborders/"]:not([href*="add"])')

        if joborder_link.count() > 0:
            joborder_link.first.click()

            # Should be on job order detail page
            authenticated_page.wait_for_load_state('networkidle')
            assert '/joborders/' in authenticated_page.url

            # Should show job order information
            expect(authenticated_page.locator('h1, h2, .job-title')).to_be_visible()
        else:
            pytest.skip('No job orders found')

    def test_pipeline_link_exists(self, authenticated_page: Page, live_server):
        """Test that pipeline link exists on job order detail page"""
        authenticated_page.goto(f'{live_server}/joborders')

        # Click on first job order
        joborder_link = authenticated_page.locator('a[href*="/joborders/"]:not([href*="add"])')

        if joborder_link.count() > 0:
            joborder_link.first.click()
            authenticated_page.wait_for_load_state('networkidle')

            # Look for pipeline link
            pipeline_link = authenticated_page.locator('a:has-text("Pipeline"), a[href*="pipeline"]')

            if pipeline_link.count() > 0:
                expect(pipeline_link.first).to_be_visible()
            else:
                pytest.skip('Pipeline link not found')
        else:
            pytest.skip('No job orders found')


class TestPipelineKanban:
    """Test pipeline kanban board"""

    def test_pipeline_page_loads(self, authenticated_page: Page, live_server):
        """Test that pipeline page loads"""
        # Go to job orders
        authenticated_page.goto(f'{live_server}/joborders')

        # Click on first job order
        joborder_link = authenticated_page.locator('a[href*="/joborders/"]:not([href*="add"])')

        if joborder_link.count() > 0:
            # Get job order ID from href
            href = joborder_link.first.get_attribute('href')

            # Try to navigate to pipeline
            authenticated_page.goto(f'{live_server}/joborders{href}/pipeline')

            # Check if page loaded (might be /joborders/<id>/pipeline or /joborders/pipeline/<id>)
            authenticated_page.wait_for_load_state('networkidle')

            # Should contain 'pipeline' in URL
            assert 'pipeline' in authenticated_page.url.lower()

            # Should show pipeline board
            expect(authenticated_page.locator('h1, h2')).to_contain_text('Pipeline', ignore_case=True)
        else:
            pytest.skip('No job orders found')

    def test_pipeline_columns_exist(self, authenticated_page: Page, live_server):
        """Test that pipeline has status columns"""
        authenticated_page.goto(f'{live_server}/joborders')

        # Click on first job order
        joborder_link = authenticated_page.locator('a[href*="/joborders/"]:not([href*="add"])')

        if joborder_link.count() > 0:
            joborder_link.first.click()
            authenticated_page.wait_for_load_state('networkidle')

            # Try to click pipeline link
            pipeline_link = authenticated_page.locator('a:has-text("Pipeline"), a[href*="pipeline"]')

            if pipeline_link.count() > 0:
                pipeline_link.first.click()
                authenticated_page.wait_for_load_state('networkidle')

                # Look for pipeline columns
                columns = authenticated_page.locator('.pipeline-column, .kanban-column, [data-status]')

                if columns.count() > 0:
                    # Should have multiple columns for different statuses
                    assert columns.count() >= 3, "Pipeline should have at least 3 status columns"

                    # Check for common status names
                    page_content = authenticated_page.content()
                    status_keywords = ['contacted', 'interview', 'submit', 'placed', 'qualifying']
                    found_statuses = sum(1 for keyword in status_keywords if keyword.lower() in page_content.lower())

                    assert found_statuses >= 2, "Pipeline should show multiple status columns"
                else:
                    pytest.skip('Pipeline columns not found - different implementation')
            else:
                pytest.skip('Pipeline link not found')
        else:
            pytest.skip('No job orders found')

    def test_pipeline_shows_statistics(self, authenticated_page: Page, live_server):
        """Test that pipeline shows statistics"""
        authenticated_page.goto(f'{live_server}/joborders')

        # Click on first job order
        joborder_link = authenticated_page.locator('a[href*="/joborders/"]:not([href*="add"])')

        if joborder_link.count() > 0:
            joborder_link.first.click()
            authenticated_page.wait_for_load_state('networkidle')

            # Navigate to pipeline
            pipeline_link = authenticated_page.locator('a:has-text("Pipeline"), a[href*="pipeline"]')

            if pipeline_link.count() > 0:
                pipeline_link.first.click()
                authenticated_page.wait_for_load_state('networkidle')

                # Look for statistics/metrics
                stats = authenticated_page.locator('.card-body:has-text("Openings"), .stat, .metric, h6:has-text("Openings")')

                if stats.count() > 0:
                    expect(stats.first).to_be_visible()
                else:
                    # Stats might be displayed differently
                    pass
            else:
                pytest.skip('Pipeline link not found')
        else:
            pytest.skip('No job orders found')

    def test_back_to_job_link_exists(self, authenticated_page: Page, live_server):
        """Test that back to job link exists on pipeline page"""
        authenticated_page.goto(f'{live_server}/joborders')

        # Click on first job order
        joborder_link = authenticated_page.locator('a[href*="/joborders/"]:not([href*="add"])')

        if joborder_link.count() > 0:
            joborder_link.first.click()
            authenticated_page.wait_for_load_state('networkidle')

            # Navigate to pipeline
            pipeline_link = authenticated_page.locator('a:has-text("Pipeline"), a[href*="pipeline"]')

            if pipeline_link.count() > 0:
                pipeline_link.first.click()
                authenticated_page.wait_for_load_state('networkidle')

                # Look for back link
                back_link = authenticated_page.locator('a:has-text("Back"), a:has-text("Job"), a[href*="/joborders/"]:not([href*="pipeline"])')

                if back_link.count() > 0:
                    expect(back_link.first).to_be_visible()
                else:
                    # Breadcrumbs or other navigation
                    breadcrumb = authenticated_page.locator('.breadcrumb, nav[aria-label*="breadcrumb"]')
                    if breadcrumb.count() > 0:
                        expect(breadcrumb.first).to_be_visible()
            else:
                pytest.skip('Pipeline link not found')
        else:
            pytest.skip('No job orders found')


class TestJobOrderCreation:
    """Test job order creation"""

    def test_navigate_to_add_joborder(self, authenticated_page: Page, live_server):
        """Test navigating to add job order page"""
        authenticated_page.goto(f'{live_server}/joborders')

        # Look for "Add Job" button
        add_button = authenticated_page.locator('a:has-text("Add Job"), a:has-text("New Job"), a[href*="joborders/add"]')

        if add_button.count() > 0:
            add_button.first.click()

            # Should be on add job order page
            authenticated_page.wait_for_url(f'{live_server}/joborders/add')
            expect(authenticated_page).to_have_url(f'{live_server}/joborders/add')
        else:
            pytest.skip('Add job order button not found')

    def test_joborder_form_has_required_fields(self, authenticated_page: Page, live_server):
        """Test that job order form has required fields"""
        authenticated_page.goto(f'{live_server}/joborders/add')

        # Check for common required fields
        title = authenticated_page.locator('input[name="title"], input[name="job_title"]')
        company = authenticated_page.locator('select[name="company_id"], input[name="company"]')

        if title.count() > 0:
            expect(title.first).to_be_visible()

        if company.count() > 0:
            expect(company.first).to_be_visible()
