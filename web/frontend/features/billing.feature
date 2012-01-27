Feature: As a person who writes code on ScraperWiki
  I want to pay for private scrapers with a credit card
  So that I can have private scrapers easily and using the
  payment method I'm used to.

  Scenario: I can see available plans
    When I visit the pricing page
    Then I should see the "Individual" payment plan
    And I should see the "Small Business" payment plan
    And I should see the "Corporate" payment plan
  
  Scenario: I can choose to purchase the Individual plan
    Given I'm logged in
    And the "Self Service Vaults" feature exists
    And I have the "Self Service Vaults" feature enabled
    When I visit the pricing page
    And I click on the "Individual" "Buy now" button
    Then I should be on the payment page
    And I should see "Individual"
    And I should see "$9"
  
  Scenario: I can choose to purchase the Small Business plan
    Given I'm logged in
    And the "Self Service Vaults" feature exists
    And I have the "Self Service Vaults" feature enabled
    When I visit the pricing page
    And I click on the "Small Business" "Buy now" button
    Then I should be on the payment page
    And I should see "Small Business"
    And I should see "$29"

  Scenario: I can choose to purchase the Corporate plan
    Given I'm logged in
    And the "Self Service Vaults" feature exists
    And I have the "Self Service Vaults" feature enabled
    When I visit the pricing page
    And I click on the "Corporate" "Buy now" button
    Then I should be on the payment page
    And I should see "Corporate"
    And I should see "$299"

