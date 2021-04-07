from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.http import JsonResponse

from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from unittest.mock import patch

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from .models import Product, Profile
from .scripts.dbfeed import Dbfeed


class PurBeurreSeleniumTestCase(StaticLiveServerTestCase):

    def setUp(self):
        self.driver = webdriver.Firefox()
        self.wait = WebDriverWait(self.driver, 1000)
        self.addCleanup(self.driver.quit)

        Product.objects.create(
            name='fake product',
            brands='fake brand',
            tags='fake, test',
            ingredients='fake, fake',
            additives='E111, E222',
            allergens='fake',
            labels='fake label',
            stores='super fake',
            link="https://fake-product.html",
            nutriscore="e",
            image_url='http://fake.jpg',
            keywords="fake keywords",
            compared_to="fake"
            )
        Product.objects.create(
            name='test product',
            brands='test brand',
            tags='fake, test',
            ingredients='test, test',
            additives='E111, E222',
            allergens='test',
            labels='test label',
            stores='super test',
            link="https://test-product.html",
            nutriscore="a",
            image_url='http://test.jpg',
            keywords="test try",
            compared_to="test"
            )

    def test_create_account_and_add_fav(self):
        self.driver.get(self.live_server_url)
        self.assertIn('Pur Beurre', self.driver.title)

        create_account = self.driver.find_element_by_id('create')
        ActionChains(self.driver).click(create_account).perform()
        self.wait.until(lambda driver:
                        self.driver.find_element_by_id("submit_new_user"))

        assert self.driver.current_url.endswith('/substitute/signup/')

        username = self.driver.find_element_by_id('id_username')
        email = self.driver.find_element_by_id('id_email')
        password1 = self.driver.find_element_by_id('id_password1')
        password2 = self.driver.find_element_by_id('id_password2')
        submit = self.driver.find_element_by_id('submit_new_user')

        username.send_keys('fake-user')
        email.send_keys('fake@foo.bar')
        password1.send_keys('nofxat411')
        password2.send_keys('nofxat411')
        submit.send_keys(Keys.RETURN)

        self.wait.until(lambda driver:
                        self.driver.find_element_by_id("search_input"))

        assert self.driver.current_url == '{}/'.format(self.live_server_url)

        search = self.driver.find_element_by_id('search_input')
        submit = self.driver.find_element_by_id('submit_search')

        search.send_keys('fake keywords')
        submit.send_keys(Keys.RETURN)

        self.wait.until(lambda driver:
                        self.driver.find_element_by_id("substitutes"))

        assert self.driver.current_url.endswith(
            '/substitute/results/fake+keywords/')

        self.driver.find_element_by_class_name("add-fav").click()
        self.wait.until(lambda driver:
                        self.driver.find_element_by_id("myfav"))
        myfav_link = self.driver.find_element_by_id("myfav")
        ActionChains(self.driver).click(myfav_link).perform()

        self.wait.until(lambda driver:
                        self.driver.find_element_by_id("favorites"))

        assert self.driver.current_url.endswith('/substitute/favorites/')


class SignUpPageTestCase(TestCase):

    def test_signup_page_returns_200(self):
        response = self.client.get(reverse('substitute:signup'))
        self.assertEqual(response.status_code, 200)

    def test_signup_add_new_profile(self):
        old_profile = Profile.objects.count()
        self.client.post(reverse('substitute:signup'), {
            'username': 'fake-user',
            'email': 'fake@fake.com',
            'password1': 'Fake1234',
            'password2': 'Fake1234'
        })
        new_profile = Profile.objects.count()
        self.assertEqual(new_profile, old_profile+1)


class LogoutPageTestCase(TestCase):

    def test_logout_page_returns_200(self):
        response = self.client.get(reverse('substitute:logout'))
        self.assertEqual(response.status_code, 200)


class MyAccountPageTestCase(TestCase):

    def test_myaccount_page_returns_200(self):
        response = self.client.get(reverse('substitute:myaccount'))
        self.assertEqual(response.status_code, 200)


class LegalNoticePageTestCase(TestCase):

    def test_legalnotice_page_returns_200(self):
        response = self.client.get(reverse('substitute:legal_notice'))
        self.assertEqual(response.status_code, 200)


class IndexPageTestCase(TestCase):

    def test_index_page_returns_200(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_index_page_returns_302(self):
        form = {'query': 'fake'}
        response = self.client.post(reverse('index'), form)
        self.assertEqual(response.status_code, 302)

    def test_parser_returns_expected(self):
        form = {'query': 'le caramel au SEL de Guérande'}
        response = self.client.post(reverse('index'), form)
        self.assertEqual(response.url,
                         '/substitute/results/caramel+sel+guerande/')


class ResultsPageTestCase(TestCase):

    def setUp(self):
        Product.objects.create(
            keywords="fake keywords",
            compared_to="fake"
            )
        self.product = Product.objects.get(keywords="fake keywords")
        Product.objects.create(tags="fake tags")
        self.alternatives = Product.objects.filter(
            tags__icontains=self.product.compared_to).exclude(
                                                id=self.product.id)

    def test_results_page_returns_200(self):
        query = "fake+keywords"
        response = self.client.get(reverse('substitute:results',
                                   args=(query,)))
        self.assertEqual(response.status_code, 200)

    def test_results_page_returns_404(self):
        query = "nothing+will+match"
        response = self.client.get(reverse('substitute:results',
                                   args=(query,)))
        self.assertEqual(response.status_code, 404)


class FavoritesPageTestCase(TestCase):

    def setUp(self):
        self.username = 'fakeuser'
        self.email = 'fake@fake.com'
        self.password = 'Fake1234'
        self.user = User.objects.create_user(self.username, self.email,
                                             self.password)

        Product.objects.create(name="fake product")
        self.product = Product.objects.get(name="fake product")

        Profile.objects.create(user=self.user)
        self.profile = Profile.objects.get(user=self.user)

        self.profile.favorite.add(self.product)

    def test_favorites_page_returns_200(self):
        self.client.login(username=self.username, password=self.password)
        Product.objects.filter(profiles=self.profile)
        response = self.client.get(reverse('substitute:favorites'))
        self.assertEqual(response.status_code, 200)


class DetailPageTestCase(TestCase):

    def setUp(self):
        Product.objects.create(name="fake product")
        self.product = Product.objects.get(name="fake product")

    def test_detail_page_returns_200(self):
        product_id = self.product.id
        response = self.client.get(reverse('substitute:detail',
                                   args=(product_id,)))
        self.assertEqual(response.status_code, 200)


class ToggleFavTestCase(TestCase):

    def setUp(self):
        self.username = 'fakeuser'
        self.email = 'fake@fake.com'
        self.password = 'Fake1234'
        self.user = User.objects.create_user(self.username, self.email,
                                             self.password)
        Product.objects.create(name="fake product")
        self.product = Product.objects.get(name="fake product")

        Profile.objects.create(user=self.user)
        self.profile = Profile.objects.get(user=self.user)

    def test_togglefav_response_loggedin(self):
        self.client.login(username=self.username, password=self.password)
        product_id = self.product.id
        toggle = 'on'
        response = self.client.post(reverse('substitute:togglefav'), {
            'product_id': product_id,
            'toggle': toggle
        })
        result = JsonResponse({"allowed": True})
        self.assertEqual(response.content, result.content)

    def test_togglefav_response_loggedout(self):
        product_id = self.product.id
        toggle = 'on'
        response = self.client.post(reverse('substitute:togglefav'), {
            'product_id': product_id,
            'toggle': toggle
        })
        result = JsonResponse({"allowed": False})
        self.assertEqual(response.content, result.content)

    def test_fav_is_registered(self):
        self.client.login(username=self.username, password=self.password)
        profile = self.profile
        product_id = self.product.id
        toggle = 'on'
        old_fav = profile.favorite.count()
        self.client.post(reverse('substitute:togglefav'), {
            'product_id': product_id,
            'toggle': toggle
        })
        new_fav = profile.favorite.count()
        self.assertEqual(new_fav, old_fav+1)

    def test_fav_is_removed(self):
        self.client.login(username=self.username, password=self.password)
        profile = self.profile
        profile.favorite.add(self.product)
        product_id = self.product.id
        toggle = 'off'
        old_fav = profile.favorite.count()
        self.client.post(reverse('substitute:togglefav'), {
            'product_id': product_id,
            'toggle': toggle
        })
        new_fav = profile.favorite.count()
        self.assertEqual(new_fav, old_fav-1)


class MockResponse:

    def __init__(self):
        self.status_code = 200

    def json(self):
        return {
            "products": [{
                "product_name": "Fake Product",
                "brands": "Fake Brands",
                "categories_tags": ["fake"],
                "ingredients_text_fr": "fake",
                "additives_tags": ["Efake"],
                "allergens_tags": ["fake"],
                "nutriscore_grade": "f",
                "labels": "fake",
                "stores_tags": ["Fake"],
                "url": "https://fake",
                "categories_hierarchy": ["fake1", "fake2", "fake3"],
                "image_url": "https://fakeimage",
                "_keywords": "fake"
            }]
        }


class DBfeedTestCase(TestCase):

    @patch('requests.get', return_value=MockResponse())
    def test_dbfeed_add_product(self, mocked):
        old_prod = Product.objects.count()
        Dbfeed.feed(20, 1)
        new_prod = Product.objects.count()
        self.assertEqual(new_prod, old_prod+1)
