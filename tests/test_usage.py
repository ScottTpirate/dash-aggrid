import pytest
from dash.testing.application_runners import ThreadedRunner, import_app
from dash.testing.browser import Browser


def test_demo_grid_renders_rows():
    """Ensure the demo grid actually renders AG Grid rows in the browser."""
    app = import_app("demo_app")

    try:
        browser = Browser("chrome", headless=True, percy_run=False)
    except Exception as err:  # pylint: disable=broad-except
        pytest.skip(f"Selenium Chrome driver not available: {err}")

    try:
        with browser:
            with ThreadedRunner() as runner:
                runner.start(app)
                browser.server_url = runner.url
                browser.wait_for_element("#inventory-grid .ag-center-cols-container .ag-row")
                rows = browser.find_elements("#inventory-grid .ag-center-cols-container .ag-row")
                assert len(rows) > 0
                browser.wait_for_element("#sales-grid .ag-center-cols-container .ag-row")
                sales_rows = browser.find_elements("#sales-grid .ag-center-cols-container .ag-row")
                assert len(sales_rows) > 0
                browser.wait_for_element("#analytics-grid .ag-center-cols-container .ag-row")
                analytics_rows = browser.find_elements("#analytics-grid .ag-center-cols-container .ag-row")
                assert len(analytics_rows) > 0
    finally:
        try:
            browser.driver.quit()
        except Exception:
            pass
