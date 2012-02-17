Feature: As a corporate account holder
  I want to pay via bank transfer
  So that I can pay using my normal process

  Scenario: I should see a message about paying with a purchase order 
    When I visit the pricing page
    Then I should see a message about paying with a purchase order 
    And I should see a "Contact us" link
