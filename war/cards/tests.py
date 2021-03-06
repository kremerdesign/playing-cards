from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.test import TestCase
from cards.forms import EmailUserCreationForm
from cards.models import Card, Player, WarGame
from cards.test_utils import run_pyflakes_for_package, run_pep8_for_package
from cards.utils import create_deck


class BasicMathTestCase(TestCase):
    def test_math(self):
        a = 1
        b = 1
        self.assertEqual(a + b, 2)


class UtilTestCase(TestCase):
    def test_create_deck_count(self):
        """Test that we created all 52 cards"""
        create_deck()
        self.assertEqual(Card.objects.count(), 52)


class ModelTestCase(TestCase):
    def setUp(self):
        self.card = Card.objects.create(suit=Card.CLUB, rank="jack")

    def test_get_ranking(self):
        """Test that we get the proper ranking for a card"""
        self.assertEqual(self.card.get_ranking(), 11)

    def test_get_war_result_usercard_greater_than_dealercard(self):
        """Test that we get the proper result for usercard greater than dealercard"""
        dealercard = Card.objects.create(suit=Card.CLUB, rank="ten")
        result = Card.get_war_result(self.card, dealercard)
        self.assertEqual(result, 1)

    def test_get_war_result_usercard_less_than_dealercard(self):
        """Test that we get the proper result for usercard less than dealercard"""
        dealercard = Card.objects.create(suit=Card.CLUB, rank="ace")
        result = Card.get_war_result(self.card, dealercard)
        self.assertEqual(result, -1)

    def test_get_war_result_usercard_equal_to_dealercard(self):
        """Test that we get the proper result for usercard equal to dealercard"""
        dealercard = Card.objects.create(suit=Card.CLUB, rank="jack")
        result = Card.get_war_result(self.card, dealercard)
        self.assertEqual(result, 0)


class FormTestCase(TestCase):
    def test_clean_username_exception(self):
        """Test that we get the proper result from username already being used"""
        # Create a player so that this username we're testing is already taken
        Player.objects.create_user(username='test-user')
        # set up the form for testing
        form = EmailUserCreationForm()
        form.cleaned_data = {'username': 'test-user'}
        # use a context manager to watch for the validation error being raised
        with self.assertRaises(ValidationError):
            form.clean_username()

    def test_clean_username_success(self):
        """Test that we get the proper result from username not already taken"""
        form = EmailUserCreationForm()
        form.cleaned_data = {'username': 'test-user'}

        self.assertEqual(form.clean_username(), 'test-user')


class ViewTestCase(TestCase):
    def setUp(self):
        create_deck()

    def test_home_page(self):
        """
        self.client is a helper for calling urls
        ex: self.client.get()
        ex: self.client.post()
        reverse(viewname) returns url for viewname
        response is html response
        """
        response = self.client.get(reverse('home'))
        self.assertIn('<p>Suit: spade, Rank: two</p>', response.content)
        self.assertEqual(response.context['cards'].count(), 52)

    def test_register_page(self):
        username = 'new-user'
        data = {
            'username': username,
            'email': 'test@test.com',
            'password1': 'test',
            'password2': 'test'
        }
        response = self.client.post(reverse('register'), data)

        # Check this user was created in the database
        self.assertTrue(Player.objects.filter(username=username).exists())

        # Check it's a redirect to the profile page
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertTrue(response.get('location').endswith(reverse('profile')))

    def create_war_game(self, user, result=WarGame.LOSS):
        """Helper method should not include word test or will be run with tests"""
        WarGame.objects.create(result=result, player=user)

    def test_profile_page(self):
        # Create user and log them in
        password = 'password'
        user = Player.objects.create_user(username='test-user', email='test@test.com', password=password)
        self.client.login(username=user.username, password=password)

        # Set up some war game entries
        self.create_war_game(user)
        self.create_war_game(user, WarGame.WIN)

        # Make the url call and check the html and games queryset length
        response = self.client.get(reverse('profile'))
        self.assertInHTML('<p>Your email address is {}</p>'.format(user.email), response.content)
        self.assertEqual(len(response.context['games']), 2)

    def test_faq_page(self):
        response = self.client.get(reverse('faq'))
        self.assertIn('<p>Q: Can I win real money on this website?</p>', response.content)

    def test_filters_page(self):
        response = self.client.get(reverse('filters'))
        self.assertIn('We have 52 cards!', response.content)
        self.assertEqual(response.context['cards'].count(), 52)

    def test_login_page_success(self):
        username = 'test-user'
        password = 'password'
        user = Player.objects.create_user(username=username, email='test@test.com', password=password)
        # self.client.login(username=user.username, password=password)
        data = {
            'username': username,
            'password': password,
        }
        response = self.client.post(reverse('login'), data)

        # Check it's a redirect to the profile page
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertTrue(response.get('location').endswith(reverse('profile')))
        self.assertTrue(user.is_authenticated())


class SyntaxTest(TestCase):
    def test_syntax(self):
        """
        Run pyflakes/pep8 across the code base to check for potential errors.
        """
        packages = ['cards']
        warnings = []
        # Eventually should use flake8 instead so we can ignore specific lines via a comment
        for package in packages:
            warnings.extend(run_pyflakes_for_package(package, extra_ignore=("_settings",)))
            warnings.extend(run_pep8_for_package(package, extra_ignore=("_settings",)))
        if warnings:
            self.fail("{0} Syntax warnings!\n\n{1}".format(len(warnings), "\n".join(warnings)))
