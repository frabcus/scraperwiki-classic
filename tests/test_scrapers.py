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

    def test_common_features_scraper(self):
        self._common_create('scraper')

    def test_common_features_view(self):
        self._common_create('view')
        
    
    
    def _load_data(self, language, obj):
        thefile = os.path.join( os.path.dirname( __file__ ), 'sample_data/%s_%s.txt' % (language, obj,))
            
        f = open(thefile)
        # The file seems to be directly inserted into the source of the page, so some characters need
        # to be html encoded.
        code = f.read().replace('&','&amp').replace('<','&lt').replace('>','&gt').replace('\n', '<br>')
        f.close()
    
        return code

    
    def _add_comment(self, code_name, code_type):
        s = self.selenium
              
        s.click('link=Discussion (0)')    
        self.wait_for_page('visiting discussion')
        comment = 'A test comment'

        s.type('id_comment', comment)
        s.click('id_submit')
        time.sleep(2)

        self.failUnless(s.is_text_present(comment))
        self.failUnless(s.is_text_present("Discussion (1)"))        

        s.open('/%ss/%s/' % (code_type, code_name))        
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
        

    def _check_clear_data(self, scraper_name):
        s = self.selenium     
                
        s.open('/scrapers/%s/' % scraper_name)        
        self.wait_for_page('view the scraper page to check we cleared the data')        
        s.click('btnClearDatastore')
        s.get_confirmation()
        self.wait_for_page('clear the datastore')
                    
        if s.is_text_present('Exception Location'):
            print s.get_body_text()
            self.fail('An error occurred deleting data')
            
        self.failIf(s.is_text_present( 'This dataset has a total of' ), 
                        msg='The data does not appear to have been deleted')


    def _check_delete_code(self, code_name, code_type):
        s = self.selenium     
        
        s.open('/%ss/%s/' % (code_type, code_name))
        self.wait_for_page('view the %s page so we can delete it' % code_type)                
        s.click('btnDeleteScraper')
        s.get_confirmation()        
        self.wait_for_page('delete the %s' % code_type)
        
        if s.is_text_present('Exception Location'):
            print s.get_body_text()
            self.fail('An error occurred deleting data')
        elif s.is_text_present(code_name):
            self.fail('%s was not deleted successfully' % code_type)
        
        self.assertEqual('/dashboard/', urlparse(s.get_location()).path, 'Did not redirect to dashboard after deleting %s' % code_type)


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
        time.sleep(1) # likewise
        s.type('id_nav_user_or_email', username)
        s.type('id_nav_password', password)
        s.click('nav_login_submit')
        self.wait_for_page()
        
    
    def _activate_users(self, userlist):
        """ 
        Set all usernames in userlist to be activated. Requires Django admin account to be specified 
        and for alert types to have been set up.
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
            
            
    def _add_code_editor(self, username, expected_msg):
        """ 
        Set the specified username as an editor on the currently open scraper/view summary page.
        Assumes the current user has permissions to do so and that the scraper/view is private/public.
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


    def _editor_demote_self(self, code_name, code_type, owner, editor):
        """ 
        Get the 'editor' account to demote themselves from 
        being an editor of 'code_name', then login as 'owner'
        """
        s = self.selenium
        self._user_login(editor['username'], editor['password'])
        s.open("/%ss/%s/" % (code_type, code_name))
        self.wait_for_page()
        s.click("xpath=//input[@class='detachbutton']")
        self.failIf(s.is_text_present(editor['username'] + " (editor)"))
        self._user_login(owner['username'], owner['password'])
        s.open("/%ss/%s/" % (code_type, code_name))
        self.wait_for_page()


    def _check_editor_permissions(self, code_name, code_type, owner, editor, privacy, on_editor_list):
        """
        Check that the account 'editor' has the expected permissions for 'code_name', given
        the privacy setting of the scraper ('privacy') and whether they are on the editors list
        ('on_editor_list'), then log in as 'owner'.
        """
        s = self.selenium
        self._user_login(editor['username'], editor['password'])
        s.open("/dashboard")
        if on_editor_list:
            self.failUnless(s.is_text_present(code_name))
            s.open("/%ss/%s/edit/" % (code_type, code_name))
            self.wait_for_page()
            s.wait_for_condition("selenium.browserbot.getCurrentWindow().document.getElementById('protected_warning').style.display == 'none'", 10000)
            self.failIf(s.get_attribute('btnCommitPopup@style') == "display:none;")
        else:
            self.failIf(s.is_text_present(code_name))
            s.open("/%ss/%s/edit/" % (code_type, code_name))
            self.wait_for_page()
            if privacy == 'private':
                self.failUnless(s.is_text_present("Sorry, this %s is private" % code_type))
            elif privacy == 'protected':
                s.wait_for_condition("selenium.browserbot.getCurrentWindow().document.getElementById('btnCommitPopup').style.display == 'none'", 10000)
                # TODO: Check direct 'post'ing of data
            else:
                self.fail()
        self._user_login(owner['username'], owner['password'])
        s.open("/%ss/%s/" % (code_type, code_name))
        self.wait_for_page()
        
    
    def _set_code_privacy(self, privacy, code_type, code_name = '', owner = {}):
        """ 
        Set the currently open scraper/view to be the specified privacy. Assumes a
        Django admin account has been specified if setting as private. Needs
        code_name and the owner account if setting as private.
        """
        privacy_set = "selenium.browserbot.getCurrentWindow().document.getElementById('privacy_status').children[0].style.display != 'none'"
        s = self.selenium
        if privacy == 'public' or privacy == 'protected':
            s.click('show_privacy_choices')
            s.click('privacy_' + privacy)
            s.wait_for_condition(privacy_set, 10000)
            self.failUnless(s.is_text_present("This %s is " % code_type + privacy))
        elif privacy == 'private':
            
            self._user_login(SeleniumTest._adminuser['username'], SeleniumTest._adminuser['password'])
            s.open("/admin/codewiki/%s/?q=" % code_type + code_name)
            self.wait_for_page()
            s.click('link=' + code_name)
            self.wait_for_page()
            s.select("id_privacy_status", "label=Private")
            s.click("//div[@class='submit-row']/input[@value='Save']")
            self.wait_for_page()
            self._user_login(owner['username'], owner['password'])
            s.open("/%ss/" % code_type + code_name)
            self.wait_for_page()
            self.failUnless(s.is_text_present("This %s is private" % code_type))
        else:
            self.fail()


    def _check_editors_list_changes(self, code_name, code_type, owner, editor, privacy):
        """
        Perform possible combinations of actions with adding/removing editors and check
        that an editor user has the appropriate permissions at each stage.
        """
        s = self.selenium
        self._check_editor_permissions(code_name, code_type, owner, editor, privacy, False)
        # Add existing user as editor
        self._add_code_editor(editor['username'], "test %s_editor (editor)" % code_type)
        self._check_editor_permissions(code_name, code_type, owner, editor, privacy, True)
        # Try to add existing editor again
        self._add_code_editor(editor['username'], "test %s_editor (editor)" % code_type)
        self.failUnless("int(s.get_xpath_count('//ul[@id=\'contributorslist\']/li')) == 2")
        self._check_editor_permissions(code_name, code_type, owner, editor, privacy, True)
        # Try to add owner as editor
        self._add_code_editor(owner['username'], "Failed: user is already owner")
        s.click("xpath=//div[@id='addneweditor']/span/input[@class='cancelbutton']")
        # Try to add non-existent user as editor
        self._add_code_editor("se_nonexistent_user", "Failed: username 'se_nonexistent_user' not found")
        s.click("xpath=//div[@id='addneweditor']/span/input[@class='cancelbutton']")
        # Demote existing editor        
        self.failUnless("int(s.get_xpath_count('//input[@class=\"demotebutton\"]')) == 1")
        s.click("xpath=//input[@class='demotebutton']")
        self.failIf(s.is_text_present(editor['username'] + " (editor)"))
        self._check_editor_permissions(code_name, code_type, owner, editor, privacy, False)
        # Check editor demoting self from scraper
        self._add_code_editor(editor['username'], "test %s_editor (editor)" % code_type)
        self._check_editor_permissions(code_name, code_type, owner, editor, privacy, True)
        self._editor_demote_self(code_name, code_type, owner, editor)
        self._check_editor_permissions(code_name, code_type, owner, editor, privacy, False)


    def _check_code_privacy(self, code_name, code_type, owner, editor):
        """ Make sure different scraper privacy settings work as expected """
        s = self.selenium
        s.open("/%ss/" % code_type + code_name)
        self.wait_for_page()
        self.failUnless(s.is_text_present("test user (owner)"))
        # Set scraper protected and check editor permission changing
        self._set_code_privacy('protected', code_type)
        self._check_editors_list_changes(code_name, code_type, owner, editor, 'protected')
        
        # Do the same for private scraper
        if SeleniumTest._adminuser:
            self._set_code_privacy('private', code_type, code_name, owner)
            self._check_editors_list_changes(code_name, code_type, owner, editor, 'private')
        
        # Check added user stays as follower when setting scraper public
        self._add_code_editor(editor['username'], "test %s_editor (editor)" % code_type)
        self._set_code_privacy('public', code_type)
        self.failUnless('s.is_text_present("test %s_editor (editor)")' % code_type)
        self.failUnless("int(s.get_xpath_count('//input[@class=\"demotebutton\"]')) == 0")
        
        
    def _language_create(self, language):
        # Language specific tests
        s = self.selenium
        s.open("/logout")
        self._create_user()
        
        # Scraper creation and tests
        scraper_name = self._create_code(language, 'scraper')
        self._wait_for_run()
        s.click('link=Scraper')
        self.wait_for_page()
        self._check_clear_data( scraper_name )
        # Check for precreated e-mail scraper and new scraper
        self._check_dashboard_count()

        # View creation
        view_name = self._create_code(language, 'view', scraper_name)
        # Clear up the evidence of testing
        self._check_delete_code( scraper_name, 'scraper' )
        self._check_delete_code( view_name, 'view' )        
        # Only e-mail scraper should be left
        self._check_dashboard_count(count=1)


    def _common_create(self, code_type):
        """ Perform a language-agnostic set of tests on a scraper """
        if not SeleniumTest._adminuser:
            print "Cannot perform some tests (including privacy tests) without a Django admin account specified"
        s = self.selenium
        owner = {'username':'', 'password':''}
        editor = {'username':'', 'password':''}
        owner['password'] = str( uuid.uuid4() )[:18].replace('-', '_')
        editor['password'] = str( uuid.uuid4() )[:18].replace('-', '_')
        s.open("/logout")
        editor['username'] = self._create_user(name="test %s_editor" % code_type, password=editor['password'])
        s.open("/logout")
        owner['username'] = self._create_user(password=owner['password'])
        code_name = self._create_code("python", code_type, '')
        s.click('link=' + code_type.capitalize())
        self.wait_for_page()

        # edit description
        s.click('css=#aEditAboutScraper')
        s.type('css=#divAboutScraper textarea', "This is a changed description")
        s.click("//div[@id='divAboutScraper']//button[text()='Save']")
        time.sleep(1) # XXX how to wait just until the JS has run?
        self.failUnless(s.is_text_present("This is a changed description"))

        # edit tags
        s.click('css=#aEditTags')
        s.type('css=#divEditTags input', "great,testy,rabbit")
        s.click("//div[@id='divEditTags']//button[text()='Save tags']")
        time.sleep(1) # XXX how to wait just until the JS has run?
        self.failUnless(s.is_text_present("rabbit"))

        # comments
        self._add_comment(code_name, code_type)

        # privacy
        if SeleniumTest._adminuser:
            self._activate_users([owner['username'], editor['username']])
            self._user_login(owner['username'], owner['password'])
            self._check_code_privacy(code_name, code_type, owner, editor)
                     


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


    def _create_code(self, language, code_type, view_attach_scraper_name = ''):
        code_name = 'se_test_%s' % str( uuid.uuid4() )[:18].replace('-', '_')
        
        s = self.selenium
        # Unfortunately we were dependant on specifying an 
        # existing user as we haven't yet activated the new account 
        # that we created earlier. So for now, we'll create a new 
        # user for each scraper/view pair
        
        link_name = '%s %s' % (langlinkname[language], code_type)
        
        s.open('/dashboard/')
        self.wait_for_page()
        
        s.answer_on_next_prompt( code_name )        
        s.click('//a[@class="editor_%s"]' % code_type)        
        time.sleep(1)        
        s.click( 'link=%s' % link_name )
        self.wait_for_page()

        # Prompt and wait for save button to activate
        s.type_keys('//body[@class="editbox"]', "\16")
        s.wait_for_condition("selenium.browserbot.getCurrentWindow().document.getElementById('btnCommitPopup').disabled == false", 10000)
        
        # Load the scraper/view code and insert directly into page source, inserting the attachment scraper name if a view
        code = self._load_data(language, code_type)
        if code_type == 'view':
            code = code.replace('{{sourcescraper}}', code_name)
        s.type('//body[@class="editbox"]', "%s" % code)

        s.click('btnCommitPopup')
        self.wait_for_page()
        time.sleep(1)
        
        return code_name


