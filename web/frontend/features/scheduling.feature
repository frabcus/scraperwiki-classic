Feature: As a person who writes code on ScraperWiki
  I want to schedule my code to run automatically
  So that I can gather data regularly without thinking about it.

  Scenario: I can see my scraper's schedule
    Given that I have a scraper
    When I visit its overview page
    Then I should see the scheduling panel
    And I should see the button to edit the schedule

  Scenario: I can set one of my scrapers to run daily
    Given that I have a scraper
    And I am on the scraper overview page
    When I click the "Edit" button in the scheduling panel
    Then I should see the following scheduling options:
      | Don't schedule  |
      | Run every month |
      | Run every week  |
      | Run every day   |
      | Run every hour  |
