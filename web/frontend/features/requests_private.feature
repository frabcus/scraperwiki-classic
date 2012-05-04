Feature: As a person who wants to pay ScraperWiki to get data for me
  I want a simple request data page with the stages of the process explained
  So that I know what to ask for and what the next stage is

  Scenario: I should see the data request form
    When I visit the request page
    Then I should see a form to request data

  Scenario: I make a valid data request
    Given I am on the request page
    When I say I want "Every cheese on http://www.cheese.com/. For each one the name, description, country, milk type, texture and fat content."
    And I enter my name "Stilton Mouse"
    And I enter my phone number "+44 1234 56789"
    And I click the "Send your request" button
    Then I should see "Thank you"


