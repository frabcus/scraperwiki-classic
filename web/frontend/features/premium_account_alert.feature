Feature: Premium Account Alert
  As a free ScraperWiki user (who doesn't read the blog or follow their twitter)
  I want to be informed when I next visit scraperwiki.com about their new 
  premium accounts.
  So that I can see whether I'd be interested in buying one.

  Scenario: As a free user I should see a message purveying premium accounts
    Given I am not logged in
    And I am a "Free" user
    When I visit the home page
    Then I should see "Interested in a premium account?"

  Scenario: As an anonymous user I should see an alert purveying premium accounts
    Given I am not logged in
    When I visit the home page
    Then I should see "Interested in a premium account?"

  Scenario: I should be able to stop being shown the premium accounts alert
    Given I am not logged in
    And I am a "Free" user
    When I visit the home page
    And I close the alert
    And I visit the home page
    Then I should not see "Interested in a premium account?"

  Scenario: If I click on the Buy button on the premium account alert
    Given I am not logged in
    And I am a "Free" user
    When I visit the home page
    And I click the "Buy one!" button
    And I visit the home page
    Then I should not see "Interested in a premium account?"
