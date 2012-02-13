Feature: As a small business or corporate account holder
  I want to create new vaults from my Vaults page
  So that I can partition my work into different private projects

  Scenario: I can't see the 'new vault' button (individual user)
	  Given I am a "Individual" user
    And I have a vault
    When I visit my vaults page
    Then I should not see the "Create a new vault" button

  Scenario: I can see the 'new vault' button (small business user)
    Given I am a "Small Business" user
    When I visit my vaults page
    Then I should see the "Create a new vault" button

  Scenario: I can see the 'new vault' button (corporate user)
    Given I am a "Corporate" user
    When I visit my vaults page
    Then I should see the "Create a new vault" button

  Scenario: I can create a new vault (small business user)
    Given I am a "Small Business" user
    When I visit my vaults page
    And I click the "Create a new vault" button
    Then I should see a new empty vault

  Scenario: I can create a new vault (corporate user)
    Given I am a "Corporate" user
    When I visit my vaults page
    And I click the "Create a new vault" button
    Then I should see a new empty vault
