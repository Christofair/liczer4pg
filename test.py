import logging
import unittest

import app

logger = logging.getLogger(__name__)

class SomeTest(unittest.TestCase):
    loaded_document = None

    @classmethod
    def setUpClass(cls):
        # load document.
        try:
            cls.loaded_document = open("index.html", "r")
        except OSError:
            logger.error("Loading document failed")
            exit(-1)
        except Exception as e:
            logger.error("Exception %s occured" % (e,))
            raise e from None
        self.posts = app.collect_posts(loaded_document)
        self.pattern_events = app.search_and_load_pattern(posts)

    @classmethod
    def tearDownClass(cls):
        if cls.loaded_document:
            cls.loaded_document.close()

    def test_getting_all_typers(self):
        """Check about users who betting in that topic"""
        self.typers = [app.Typer(app.get_owner(post), post) for post in self.posts]
        self.assertEquals(self.typers, ['Nicekovsky', 'Bazukaczekczek', 'Daro', 'Unsub', 'IdoB'])
        pass

    def test_binding_owner_with_post(self):
        """Check a scraped owner of post is correct"""
        # scraped a object of post with user and then check it.
        self.assertEqual(self.typers[0].name, 'Nicekovsky')
        with open('first_post_nicekovsky.html') as postcontent:
            self.assertEqual(self.typers[0].post, postcontent.read())
        pass

    def test_finding_sports_results_in_post(self):
        """Check interpretation of post"""
        # interpretation of post is deciding if there are a results of sports.
        with open('post_string
        pass

    def test_timestamp_of_post(self):
        """Check date of written post"""
        pass

    def test_finding_pattern_to_follow(self):
        """Check pattern in which there are names of teams and timestamps to start match"""
        # For this should be a function with passing a post content to it.
        pass

    def test_getting_single_event(self):
        """Check if single event from post have properly set date,
        and result if there was a result."""
        pass
