Feature: As a user
  I want to be able to manage my profile
  So that I can write a bio and stuff.

   Scenario: I can edit my profile if I'm logged in
    Given I am a "Free" user
    And I am on my profile page
    When I click the "Edit Profile & Settings" button
    Then I should be on my edit profile page
    And I should see "YOUR PROFILE"

