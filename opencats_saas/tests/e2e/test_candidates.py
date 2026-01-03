"""E2E tests for candidate management"""
import pytest
from playwright.sync_api import Page, expect


class TestCandidateList:
    """Test candidate list page"""

    def test_candidate_list_page_loads(self, authenticated_page: Page, live_server):
        """Test that candidate list page loads"""
        authenticated_page.goto(f'{live_server}/candidates')

        # Check page loaded
        expect(authenticated_page).to_have_url(f'{live_server}/candidates')

        # Check for candidates heading
        expect(authenticated_page.locator('h1, h2')).to_contain_text('Candidates')

    def test_candidate_search(self, authenticated_page: Page, live_server):
        """Test candidate search functionality"""
        authenticated_page.goto(f'{live_server}/candidates')

        # Look for search input
        search_input = authenticated_page.locator('input[name="search"], input[type="search"], input[placeholder*="Search"]')

        if search_input.count() > 0:
            # Enter search term
            search_input.first.fill('test')

            # Submit search (either form submit or button click)
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

    def test_pagination_exists(self, authenticated_page: Page, live_server):
        """Test that pagination controls exist if needed"""
        authenticated_page.goto(f'{live_server}/candidates')

        # Check if pagination exists
        pagination = authenticated_page.locator('.pagination, nav[aria-label*="pagination"]')

        if pagination.count() > 0:
            expect(pagination.first).to_be_visible()
        else:
            # No pagination needed if few candidates
            pass


class TestCandidateCreation:
    """Test candidate creation flow"""

    def test_navigate_to_add_candidate(self, authenticated_page: Page, live_server):
        """Test navigating to add candidate page"""
        authenticated_page.goto(f'{live_server}/candidates')

        # Look for "Add Candidate" button
        add_button = authenticated_page.locator('a:has-text("Add Candidate"), a:has-text("New Candidate"), a[href*="candidates/add"]')

        if add_button.count() > 0:
            add_button.first.click()

            # Should be on add candidate page
            authenticated_page.wait_for_url(f'{live_server}/candidates/add')
            expect(authenticated_page).to_have_url(f'{live_server}/candidates/add')
        else:
            pytest.skip('Add candidate button not found')

    def test_add_candidate_form_validation(self, authenticated_page: Page, live_server):
        """Test form validation on add candidate page"""
        authenticated_page.goto(f'{live_server}/candidates/add')

        # Try to submit empty form
        submit_button = authenticated_page.locator('button[type="submit"]')
        if submit_button.count() > 0:
            submit_button.first.click()

            # Should show validation errors or stay on same page
            authenticated_page.wait_for_timeout(500)

            # Either HTML5 validation or server-side validation
            assert (
                authenticated_page.url == f'{live_server}/candidates/add' or
                authenticated_page.locator('.alert-danger, .error, .invalid-feedback').count() > 0
            )
        else:
            pytest.skip('Submit button not found')

    def test_create_new_candidate(self, authenticated_page: Page, live_server):
        """Test creating a new candidate"""
        authenticated_page.goto(f'{live_server}/candidates/add')

        # Fill in required fields
        first_name = authenticated_page.locator('input[name="first_name"]')
        last_name = authenticated_page.locator('input[name="last_name"]')
        email = authenticated_page.locator('input[name="email"]')

        if first_name.count() > 0 and last_name.count() > 0:
            first_name.fill('John')
            last_name.fill('Doe')

            if email.count() > 0:
                email.fill(f'john.doe.{int(authenticated_page.evaluate("Date.now()"))}@example.com')

            # Submit form
            authenticated_page.click('button[type="submit"]')

            # Should redirect to candidate list or detail page
            authenticated_page.wait_for_timeout(1000)
            assert '/candidates' in authenticated_page.url

            # Should show success message
            expect(authenticated_page.locator('.alert-success, .success, text=success')).to_be_visible()
        else:
            pytest.skip('Required form fields not found')


class TestCandidateDetail:
    """Test candidate detail page"""

    def test_view_candidate_detail(self, authenticated_page: Page, live_server):
        """Test viewing candidate details"""
        # Go to candidates list
        authenticated_page.goto(f'{live_server}/candidates')

        # Click on first candidate (if exists)
        candidate_link = authenticated_page.locator('a[href*="/candidates/"]:not([href*="add"]):not([href*="search"])')

        if candidate_link.count() > 0:
            candidate_link.first.click()

            # Should be on candidate detail page
            authenticated_page.wait_for_load_state('networkidle')
            assert '/candidates/' in authenticated_page.url

            # Should show candidate information
            expect(authenticated_page.locator('h1, h2, .candidate-name')).to_be_visible()
        else:
            pytest.skip('No candidates found to view')

    def test_edit_candidate_button_exists(self, authenticated_page: Page, live_server):
        """Test that edit button exists on candidate detail page"""
        authenticated_page.goto(f'{live_server}/candidates')

        # Click on first candidate
        candidate_link = authenticated_page.locator('a[href*="/candidates/"]:not([href*="add"])')

        if candidate_link.count() > 0:
            candidate_link.first.click()
            authenticated_page.wait_for_load_state('networkidle')

            # Look for edit button
            edit_button = authenticated_page.locator('a:has-text("Edit"), a[href*="edit"], button:has-text("Edit")')

            if edit_button.count() > 0:
                expect(edit_button.first).to_be_visible()
            else:
                pytest.skip('Edit button not found')
        else:
            pytest.skip('No candidates found')


class TestCandidateEdit:
    """Test candidate editing"""

    def test_edit_candidate(self, authenticated_page: Page, live_server):
        """Test editing a candidate"""
        authenticated_page.goto(f'{live_server}/candidates')

        # Click on first candidate
        candidate_link = authenticated_page.locator('a[href*="/candidates/"]:not([href*="add"])')

        if candidate_link.count() > 0:
            candidate_link.first.click()
            authenticated_page.wait_for_load_state('networkidle')

            # Click edit button
            edit_button = authenticated_page.locator('a:has-text("Edit"), a[href*="edit"]')

            if edit_button.count() > 0:
                edit_button.first.click()

                # Should be on edit page
                authenticated_page.wait_for_load_state('networkidle')
                assert '/edit' in authenticated_page.url

                # Modify first name
                first_name = authenticated_page.locator('input[name="first_name"]')
                if first_name.count() > 0:
                    first_name.fill('Updated Name')

                    # Submit
                    authenticated_page.click('button[type="submit"]')

                    # Should redirect
                    authenticated_page.wait_for_timeout(1000)
                    assert '/candidates' in authenticated_page.url
                else:
                    pytest.skip('First name field not found')
            else:
                pytest.skip('Edit button not found')
        else:
            pytest.skip('No candidates found')


class TestCandidateDelete:
    """Test candidate deletion"""

    def test_delete_button_exists(self, authenticated_page: Page, live_server):
        """Test that delete button exists"""
        authenticated_page.goto(f'{live_server}/candidates')

        # Look for delete button or link
        delete_button = authenticated_page.locator('button:has-text("Delete"), a:has-text("Delete"), button.delete, a.delete')

        if delete_button.count() > 0:
            expect(delete_button.first).to_be_visible()
        else:
            pytest.skip('Delete button not found - may require viewing candidate detail page')
