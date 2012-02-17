Feature: As a user
  I want to be able to create a scraper
  So that I can start writing and running my code

   Scenario: I can create a scraper if I'm logged in
    Given I am a "Free" user
    And I am on the homepage
    And I click the button "Create a scraper"
    And I choose to write my scraper in "Python"
    Then I should be on the scraper code editing page

   Scenario: I can save a scraper if I'm logged in
    Given I am a "Free" user
    And I create a scraper
    When I save the scraper as "Testing" 
    Then I should be on my "Testing" scraper page

 
