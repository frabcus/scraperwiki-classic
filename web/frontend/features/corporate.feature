Feature: As a corporate buyer
  I want to understand ScraperWiki's corporate services offering
  in clear business terms, with a simple enquiry form and *no coding*
  So that I can decide whether to become a corporate customer

  Scenario: I can see an overview of ScraperWiki's corporate offering
    Given I am a "Free" user
    And I visit the corporate home page
    Then I should see how ScraperWiki helps me with "Competition"
    And I should see how ScraperWiki helps me with "Collaboration"
    And I should see how ScraperWiki helps me with "Control"
    And I should see how ScraperWiki helps me with "Community"
    And I should see the "features & services" link
    And I should see the "Get in touch" link
    And I should see a phone number
    And I should see an email address
    
  Scenario: I can see a detailed breakdown of corporate services
    Given I am a "free" user
    And I visit the corporate features page
    Then I should see all the corporate services
    And I should see the "Get in touch" link
    And I should see a phone number
    And I should see an email address
    
  Scenario: I can get in touch with the corporate team
    Given I am a "free" user
    And I visit the corporate contact page
    Then I should see a phone number
    And I should see an email address
    And I should see a call-back form
    And I should see a "name" field
    And I should see a "company" field
    And I should see a "number" field

  Scenario: I get in touch with the corporate team
    Given I am a "free" user
    And I visit the corporate contact page
    When I fill in my corporate contact details
    And I click the "Call me back" button
    Then an e-mail should be sent
    And I should be on the corporate contact thanks page
    
  Scenario: I will love the corporate site on an iPhone
    Given I am a "free" user
    And I am using an iPhone
    When I visit the corporate contact page
    Then I should see a mobile optimized site
    And I should see a phone number
    And the phone number should automatically start a call
    And I should see a "number" field
    And the "number" field should bring up the numeric keypad



