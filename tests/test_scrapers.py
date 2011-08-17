import os, sys, unittest, uuid, time
from selenium import selenium
from selenium_test import SeleniumTest
from urlparse import urlparse

langlinkname = { "python":"Python", "ruby":"Ruby", "php":"PHP" }

class TestScrapers(SeleniumTest):
    """
    Creates and runs some scrapers in the three main supported languages. 
    
    Create
    Run
    Check
    
    Also checks some language-independant features including privacy and
    comments.
    """
    login_text = "Log in"
    logged_in_text = "Logged in"
    new_scraper_link = "Create new scraper"


    def test_ruby_create(self):
        self._language_create("ruby")

    def test_php_create(self):
        self._language_create("php")

    def test_python_create(self):
        self._language_create("python")

    def test_common_features(self):
        self._common_create()


        
    
    
    def _load_data(self, language, obj):
        thefile = os.path.join( os.path.dirname( __file__ ), 'sample_data/%s_%s.txt' % (language, obj,))
            
        f = open(thefile)
        # The file seems to be directly inserted into the source of the page, so some characters need
        # to be html encoded.
        code = f.read().replace('&','&amp').replace('<','&lt').replace('>','&gt').replace('\n', '<br>')
        f.close()
    
        return code

    
    def _add_comment(self, name):
        s = self.selenium
              
        s.click('link=Discussion (0)')    
        self.wait_for_page('visiting discussion')
        comment = 'A test comment'

        s.type('id_comment', comment)
        s.click('id_submit')
        time.sleep(2)

        self.failUnless(s.is_text_present(comment))
        self.failUnless(s.is_text_present("Discussion (1)"))        

        s.open('/scrapers/%s/' % name)        
        self.wait_for_page('view the scraper page')        
        
        
    def _check_dashboard_count(self, count=2):
        """ 
        Go to the current user's dashboard and verify the 
        number of scrapers there 
        """
        s = self.selenium
                
        s.click('link=Your dashboard')
        self.wait_for_page('visit dashboard')
        
        scraper_count = int(s.get_xpath_count('//li[@class="code_object_line"]'))    
        self.failUnless( count == scraper_count, msg='There are %s items instead of %s' % (scraper_count,count,) )
        

    def _check_clear_data(self, name):
        s = self.selenium     
                
        s.open('/scrapers/%s/' % name)        
        self.wait_for_page('view the scraper page to check we cleared the data')        
        s.click('btnClearDatastore')
        s.get_confirmation()
        self.wait_for_page('clear the datastore')
                    
        if s.is_text_present('Exception Location'):
            print s.get_body_text()
            self.fail('An error occurred deleting data')
            
        self.failIf(s.is_text_present( 'This dataset has a total of' ), 
                        msg='The data does not appear to have been deleted')


    def _check_delete_scraper(self, name):
        s = self.selenium     
                
        s.open('/scrapers/%s/' % name)
        self.wait_for_page('view the scraper page so we can delete it')                
        s.click('btnDeleteScraper')
        s.get_confirmation()        
        self.wait_for_page('delete the scraper')
        
        if s.is_text_present('Exception Location'):
            print s.get_body_text()
            self.fail('An error occurred deleting data')
        
        self.assertEqual('/', urlparse(s.get_location()).path, 'Did not redirect to front page after deleting scraper')


    def _check_delete_view(self, name):
        s = self.selenium     
                
        s.open('/views/%s/' % name)
        self.wait_for_page('view the page to delete the view')                
        s.click('btnDeleteScraper')
        s.get_confirmation()        
        self.wait_for_page()
        
        if s.is_text_present('Exception Location'):
            print s.get_body_text()
            self.fail('An error occurred deleting data')
        
        self.assertEqual('/', urlparse(s.get_location()).path, 'Did not redirect to front page after deleting view')


    def _wait_for_run(self):
        """ We'll click run and then wait for 3 seconds, each time checking 
            whether we have in fact finished.  
        """
        s = self.selenium
        
        run_enabled = "selenium.browserbot.getCurrentWindow().document.getElementById('run').disabled == false"
        s.wait_for_condition(run_enabled, 10000)
        s.click('run')
        success,total_checks,reconnects = False, 12, 1

        # Dev server is slow, allow a page refresh on problems and give a longer timeout (allow https or http)
        if "dev.scraperwiki.com" in s.browserURL:
            reconnects = 5
            total_checks = 40

        while not (s.is_text_present('Starting run ...') and s.is_text_present('runfinished')):
            if total_checks == 0 and reconnects == 0:
                self.fail('Running the scraper seemed to fail')
                return
            elif ((s.is_text_present('Connection to execution server lost') and (reconnects > 0))
                    or (s.is_text_present('runfinished') and not s.is_text_present('Starting run') and (reconnects > 0))
                    or (total_checks == 0) and (reconnects > 0)):
                # Refresh and start anew, something went wrong
                s.refresh()
                self.wait_for_page()
                time.sleep(1)
                s.wait_for_condition(run_enabled, 10000)
                s.click('run')
                reconnects -= 1
                total_checks = 40
            time.sleep(3)
            total_checks -= 1
            
        if self.selenium.is_text_present('seconds elapsed'):
            # If the scraper has executed check that we have the expected output
            self.failUnless( s.is_text_present('hello') and s.is_text_present('world') ) 
            self.failIf( s.is_text_present('Traceback') )
            success = True
            print 'Scraper returned some data!!!'
        
        self.failUnless(success)

    
    def _user_login(self, username, password):
        """ Logout if already logged in and log back in as specified user """
        s = self.selenium
        # Pause here to force sync and bypass intermittent issues such 
        # as blank JS alerts interrupting selenium and logout failure
        time.sleep(1)
        s.open("/logout")
        self.wait_for_page()
        s.type('id_nav_user_or_email', username)
        s.type('id_nav_password', password)
        s.click('nav_login_submit')
        self.wait_for_page()
        
    
    def _activate_users(self, userlist):
        """ 
        Set all usernames in userlist to be activated. Requires Django admin account to be specified, 
        all the usernames to be on the first page of users and for alert types to have been set up.
        """
        s = self.selenium
        self._user_login(SeleniumTest._adminuser['username'],SeleniumTest._adminuser['password'])
        
        for username in userlist:
            s.open("/admin/auth/user/?q=" + username)
            self.wait_for_page()
            s.click("link=" + username)
            self.wait_for_page()
            s.click("id_is_active")
            s.click("//div[@class='submit-row']/input[@value='Save']")
            self.wait_for_page()
            
            
    def _add_scraper_editor(self, username, expected_msg):
        """ 
        Set the specified username as an editor on the currently open scraper summary page.
        Assumes the current user has permissions to do so and that the scraper is private/public.
        """
        error_showing = "selenium.browserbot.getCurrentWindow().document.getElementById('contributorserror').style.display != 'none'"
        finished_loading = "selenium.browserbot.getCurrentWindow().document.getElementById('contributors_loading').style.display == 'none'"
        add_editor_visible = "selenium.browserbot.getCurrentWindow().document.getElementById('addneweditor').children[1].style.display != 'none'"

        s = self.selenium
        s.click("link=Add a new editor")
        s.type("//div[@id='addneweditor']/span/input[@role='textbox']", username)
        s.click("xpath=//div[@id='addneweditor']/span/input[@class='addbutton']")
        s.wait_for_condition(error_showing + " || (" + finished_loading + " && " + add_editor_visible + ")", 10000)
        self.failUnless(s.is_text_present(expected_msg))


    def _editor_demote_self(self, scrapername, owner, editor):
        """ 
        Get the 'editor' account to demote themselves from 
        being an editor of 'scrapername', then login as 'owner'
        """
        s = self.selenium
        self._user_login(editor['username'], editor['password'])
        s.open("/scrapers/%s/" % scrapername)
        self.wait_for_page()
        s.click("xpath=//input[@class='detachbutton']")
        self.failIf(s.is_text_present(editor['username'] + " (editor)"))
        self._user_login(owner['username'], owner['password'])
        s.open("/scrapers/%s/" % scrapername)
        self.wait_for_page()


    def _check_editor_permissions(self, scrapername, owner, editor, privacy, on_editor_list):
        """
        Check that the account 'editor' has the expected permissions for 'scrapername', given
        the privacy setting of the scraper ('privacy') and whether they are on the editors list
        ('on_editor_list'), then log in as 'owner'.
        """
        s = self.selenium
        self._user_login(editor['username'], editor['password'])
        s.open("/dashboard")
        if on_editor_list:
            self.failUnless(s.is_text_present(scrapername))
            s.open("/scrapers/%s/edit/" % scrapername)
            self.wait_for_page()
            s.wait_for_condition("selenium.browserbot.getCurrentWindow().document.getElementById('protected_warning').style.display == 'none'", 10000)
            self.failIf(s.get_attribute('btnCommitPopup@style') == "display:none;")
        else:
            self.failIf(s.is_text_present(scrapername))
            s.open("/scrapers/%s/edit/" % scrapername)
            self.wait_for_page()
            if privacy == 'private':
                self.failUnless(s.is_text_present("Sorry, this scraper is private"))
            elif privacy == 'protected':
                s.wait_for_condition("selenium.browserbot.getCurrentWindow().document.getElementById('btnCommitPopup').style.display == 'none'", 10000)
                # TODO: Check direct 'post'ing of data
            else:
                self.fail()
        self._user_login(owner['username'], owner['password'])
        s.open("/scrapers/%s/" % scrapername)
        self.wait_for_page()
        
    
    def _set_scraper_privacy(self, privacy, scraper_name='', owner = {}):
        """ 
        Set the currently open scraper to be the specified privacy. Assumes a
        Django admin account has been specified if setting as private. Needs
        scraper_name and the owner account if setting as private.
        """
        privacy_set = "selenium.browserbot.getCurrentWindow().document.getElementById('privacy_status').children[0].style.display != 'none'"
        s = self.selenium
        if privacy == 'public' or privacy == 'protected':
            s.click('show_privacy_choices')
            s.click('privacy_' + privacy)
            s.wait_for_condition(privacy_set, 10000)
            self.failUnless(s.is_text_present("This scraper is " + privacy))
        elif privacy == 'private':
            self._user_login(SeleniumTest._adminuser['username'], SeleniumTest._adminuser['password'])
            s.open("/admin/codewiki/scraper/?q=" + scraper_name)
            self.wait_for_page()
            s.click('link=' + scraper_name)
            self.wait_for_page()
            s.select("id_privacy_status", "label=Private")
            s.click("//div[@class='submit-row']/input[@value='Save']")
            self.wait_for_page()
            self._user_login(owner['username'], owner['password'])
            s.open("/scrapers/" + scraper_name)
            self.wait_for_page()
            self.failUnless(s.is_text_present("This scraper is private"))
        else:
            self.fail()


    def _check_editors_list_changes(self, scraper_name, owner, editor, privacy):
        """
        Perform possible combinations of actions with adding/removing editors and check
        that an editor user has the appropriate permissions at each stage.
        """
        s = self.selenium
        self._check_editor_permissions(scraper_name, owner, editor, privacy, False)
        # Add existing user as editor
        self._add_scraper_editor(editor['username'], "test scraper_editor (editor)")
        self._check_editor_permissions(scraper_name, owner, editor, privacy, True)
        # Try to add existing editor again
        self._add_scraper_editor(editor['username'], "test scraper_editor (editor)")
        self.failUnless("int(s.get_xpath_count('//ul[@id=\'contributorslist\']/li')) == 2")
        self._check_editor_permissions(scraper_name, owner, editor, privacy, True)
        # Try to add owner as editor
        self._add_scraper_editor(owner['username'], "Failed: user is already owner")
        s.click("xpath=//div[@id='addneweditor']/span/input[@class='cancelbutton']")
        # Try to add non-existent user as editor
        self._add_scraper_editor("se_nonexistent_user", "Failed: username 'se_nonexistent_user' not found")
        s.click("xpath=//div[@id='addneweditor']/span/input[@class='cancelbutton']")
        # Demote existing editor        
        self.failUnless("int(s.get_xpath_count('//input[@class=\"demotebutton\"]')) == 1")
        s.click("xpath=//input[@class='demotebutton']")
        self.failIf(s.is_text_present(editor['username'] + " (editor)"))
        self._check_editor_permissions(scraper_name, owner, editor, privacy, False)
        # Check editor demoting self from scraper
        self._add_scraper_editor(editor['username'], "test scraper_editor (editor)")
        self._check_editor_permissions(scraper_name, owner, editor, privacy, True)
        self._editor_demote_self(scraper_name, owner, editor)
        self._check_editor_permissions(scraper_name, owner, editor, privacy, False)


    def _check_scraper_privacy(self, scraper_name, owner, editor):
        """ Make sure different scraper privacy settings work as expected """
        s = self.selenium
        s.open("/scrapers/" + scraper_name)
        self.wait_for_page()
        self.failUnless(s.is_text_present("test user (owner)"))
        # Set scraper protected and check editor permission changing
        self._set_scraper_privacy('protected')
        self._check_editors_list_changes(scraper_name, owner, editor, 'protected')
        
        # Do the same for private scraper
        if SeleniumTest._adminuser:
            self._set_scraper_privacy('private', scraper_name, owner)
            self._check_editors_list_changes(scraper_name, owner, editor, 'private')
        
        # Check added user stays as follower when setting scraper public
        self._add_scraper_editor(editor['username'], "test scraper_editor (editor)")
        self._set_scraper_privacy('public')
        self.failUnless('s.is_text_present("test scraper_editor (editor)")')
        self.failUnless("int(s.get_xpath_count('//input[@class=\"demotebutton\"]')) == 0")
        
        
    def _language_create(self, language):
        # Language specific tests
        s = self.selenium
        s.open("/logout")
        self._create_user()
        
        # Scraper creation and tests
        scraper_name = self._create_scraper(language)
        self._wait_for_run()
        s.click('link=Scraper')
        self.wait_for_page()
        self._check_clear_data( scraper_name )
        # Check for precreated e-mail scraper and new scraper
        self._check_dashboard_count()

        # View creation
        view_name = self._create_view(language, scraper_name)
        # Clear up the evidence of testing
        self._check_delete_scraper( scraper_name )
        self._check_delete_view( view_name )        
        # Only e-mail scraper should be left
        self._check_dashboard_count(count=1)


    def _common_create(self):
        """ Perform a language-agnostic set of tests on a scraper """
        if not SeleniumTest._adminuser:
            print "Cannot perform some tests without a Django admin account specified"
        s = self.selenium
        owner = {'username':'', 'password':''}
        editor = {'username':'', 'password':''}
        owner['password'] = str( uuid.uuid4() )[:18].replace('-', '_')
        editor['password'] = str( uuid.uuid4() )[:18].replace('-', '_')
        s.open("/logout")
        editor['username'] = self._create_user(name="test scraper_editor", password=editor['password'])
        s.open("/logout")
        owner['username'] = self._create_user(password=owner['password'])
        scraper_name = self._create_scraper("python")
        s.click('link=Scraper')
        self.wait_for_page()
        self._add_comment(scraper_name)
        if SeleniumTest._adminuser:
            self._activate_users([owner['username'], editor['username']])
        self._user_login(owner['username'], owner['password'])
        self._check_scraper_privacy(scraper_name, owner, editor)
                     

    def _create_user(self, name="test user", password = str( uuid.uuid4() )[:18].replace('-', '_') ):
        s = self.selenium
        s.click("link=%s" % self.login_text)
        self.wait_for_page()

        username = "se_test_%s" % str( uuid.uuid4() )[:18].replace('-', '_')

        d = {}
        d["id_name"] = name
        d["id_username"] = username
        d["id_email"] = "%s@scraperwiki.com" % username
        d["id_password1"]  = password
        d["id_password2"]  = password
        
        self.type_dictionary( d )
        s.click( 'id_tos' )
        s.click('register')
        self.wait_for_page()
        
        self.failUnless(s.is_text_present(self.logged_in_text), msg='User is not signed in and should be')

        return username


    def _create_scraper(self, language):
        scraper_name = 'se_test_%s' % str( uuid.uuid4() )[:18].replace('-', '_')
        
        s = self.selenium
        # Unfortunately we were dependant on specifying an 
        # existing user as we haven't yet activated the new account 
        # that we created earlier. So for now, we'll create a new 
        # user for each scraper/view pair
        
        link_name = '%s scraper' % langlinkname[language]
        
        s.answer_on_next_prompt( scraper_name )        
        s.click('link=%s' % self.new_scraper_link)        
        time.sleep(1)
        s.click( 'link=%s' % link_name )
        self.wait_for_page()

        # Prompt and wait for save button to activate
        s.type_keys('//body[@class="editbox"]', "\16")
        s.wait_for_condition("selenium.browserbot.getCurrentWindow().document.getElementById('btnCommitPopup').disabled == false", 10000)
        
        # Load the scraper code and insert directly into page source
        code = self._load_data(language, 'scraper')
        s.type('//body[@class="editbox"]', "%s" % code)

        s.click('btnCommitPopup')
        self.wait_for_page()
        time.sleep(1)
        
        return scraper_name
        
        
    def _create_view(self, language, shortname):
        """ Must be on the scraper homepage """
        s = self.selenium
        view_name = 'se_test_%s' % str( uuid.uuid4() )[:18].replace('-', '_')
        
        link_name = '%s view' % langlinkname[language]

        s.open('/scrapers/%s' % shortname)
        s.wait_for_page_to_load("30000")      
                
        s.answer_on_next_prompt( view_name )        
        s.click('//a[@class="editor_view"]')        
        time.sleep(1)        
        s.click( 'link=%s' % link_name )

        self.wait_for_page()

        # Prompt save button to activate
        self.selenium.type_keys('//body[@class="editbox"]',"                       ")
        time.sleep(1)

        code = self._load_data(language, 'view')
        code = code.replace('{{sourcescraper}}', view_name)
        
        s.type('//body[@class="editbox"]', "%s" % code)        
        s.click('btnCommitPopup')
        self.wait_for_page()
        time.sleep(1)

        return view_name


        
