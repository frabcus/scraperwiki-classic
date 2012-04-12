Feature: As a site visitor
  I want to able to see the ScraperWiki home page
  So that I should see what ScraperWiki does, and what's new at a glance

  Scenario: I should search the site
    Given I am on the home page
    When I enter "test" in the search box
    Then I should be on the search test page

  Scenario: If I'm a Data Developer, I should find out more about what SW offers me
    Given I am on the home page
    When I click the "« Find out more" link
    Then I should see "Why developers love ScraperWiki" 

  Scenario: If I'm a Data Requester, I should find out about how to request data
    Given I am on the home page
    When I click the "Find out more »" link
    Then I should see "Why people who need data love ScraperWiki"
    And I should see a "Request data!" link

  Scenario: I should see the popular tags of scrapers
    Given the "test_scraper" has the tag "testalicious"
    When I visit the home page
    Then I should see "POPULAR TAGS"
    And I should see a "testalicious" link

  Scenario: I should see the latest blog post
    When I visit the home page
    Then I should see "FROM THE BLOG"

