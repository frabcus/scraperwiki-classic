Feature: As a salesperson, I want to invite people to a vault by email
  (when they don't have an account on scraperwiki.com) -
  so that they can create an account and see the vault instantly.

  Scenario: A vault owner can invite a person
    Given I am a "Corporate" user
    And I have a vault
    And I am on the vaults page
    When I click the vault members button
    And I click the "Add another user" button
    And I type "t.test@testersonandsons.com" into the username box
    And I click the "Add!" button
    Then an invitation email gets sent to "t.test@testersonandsons.com"
    And I should see "Invitation sent!"

  Scenario: An invited person can sign up to scraperwiki
    Given I have been invited to scraperwiki
    And there is a sign up link in the invitation email
    When I go to the invitation link in the email
    Then I should be on the login page
    When I fill in the registration form
    And I click the "Create my account" button
    Then I should be on the vaults page
    And I should have access to the vault I was invited to
