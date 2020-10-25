from django.test import TestCase, override_settings
from django.test import Client
from .models import User, Post, Group, Comment, Follow
from .forms import PostForm
from . import views
from django.urls import reverse
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import Mock
 
 
class ScriptsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
                        first_name = 'sarah',
                        last_name = 'connor',
                        username='sarah77', 
                        email='connor.s@skynet.com', 
                        password='12345'
                        )
        self.group = Group.objects.create(title='original_group', slug='original')
        self.not_login_user = Client()
        self.login_user = Client()
        self.login_user.force_login(self.user)
        cache.clear()
 
    def check(self, url, text, author, group):
        response = self.login_user.get(url)
        paginator = response.context.get('paginator')
        if paginator is not None:
            self.assertEqual(response.context['paginator'].count, 1)
            post_on_page = response.context['page'][0]
        else:
            post_on_page = response.context['post']
        self.assertEqual(post_on_page.text, text)
        self.assertEqual(post_on_page.author, author)
        self.assertEqual(str(post_on_page.group), str(group))
 
    def test_profile(self):
        url=reverse(
                    'profile', 
                    kwargs={'username': self.user.username}
                    )
        response = self.login_user.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['author'], User)
        self.assertEqual(response.context['author'].username, self.user.username)
 
    def test_post_autorized(self):
        post = self.login_user.post( 
                                reverse('new_post'), 
                                {'text': 'test_text', 'group': self.group.id}, 
                                follow=True 
                                )
        object = Post.objects.get(pk=1)
        all_objects = Post.objects.count()
        self.assertEqual(all_objects, 1)
        self.assertEqual(object.text, 'test_text')
        self.assertEqual(object.author, self.user)
        self.assertEqual(object.group, self.group)
 
    def test_post_NotAutorized(self):
        try_post = self.not_login_user.post(reverse('new_post'))
        self.assertEqual(try_post.status_code, 302)
        self.assertRedirects(try_post, (
                            f'{reverse("login")}?next='
                            f'{reverse("new_post")}'
                            )
                        )
        all_objects = Post.objects.count()
        self.assertEqual(all_objects, 0)
 
    def test_post_on_pages(self):
        post = Post.objects.create(text='GOGOGOGOGO', author=self.user, group=self.group)
        urls = [
            reverse('index'),
            reverse('post', kwargs={'username': self.user.username, 'post_id': post.id}),
            reverse('profile', kwargs={'username': self.user.username})
        ]

        for test in urls:
            self.check(test, post.text, self.user, self.group)
 
    def test_edit_post(self):
        post = Post.objects.create(text='GOGOGOGOGO', author=self.user, group=self.group)
        group_new = Group.objects.create(title='test_group_after_edit', slug='test_edit')
        urls = [
            reverse('group_posts', kwargs={'slug': group_new.slug}),
            reverse('profile', kwargs={'username': self.user.username}),
            reverse('post', kwargs={'username': self.user.username, 'post_id': post.id}),
            reverse('index'),
        ]
        new_data = {
            'text': 'new_text_after_edit',
            'group': group_new.id,
            }
        response = self.login_user.post(reverse('post_edit', 
                            kwargs={
                                'username': self.user.username, 
                                'post_id': post.id
                                }
                            ),
                            new_data,
                            follow=True
                            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, new_data['group'], status_code=200)
 
        for test in urls:
            self.check(test, new_data['text'], self.user, group_new.title)
 
        response = self.login_user.post(reverse(
                                   'group_posts',
                                   kwargs={'slug': 'original'}
                                   )
                                )
        self.assertEqual(response.context['paginator'].count, 0)
 
 
class Mistakes(TestCase):
    def setUp(self):
        self.client = Client()
 
 
    def test_wrong_url_returns_404(self):
        response = self.client.get('something/really/weird/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "misc/404.html")
 
 
class Imagines(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
                        first_name = 'sarah',
                        last_name = 'connor',
                        username='sarah88', 
                        email='connor.s@skynet.com', 
                        password='12345'
                        )
        self.group = Group.objects.create(title='test_group_imagine', slug='test_group')
        self.login_user = Client()
        self.login_user.force_login(self.user)
        cache.clear()
 

    def test_img(self):
        small_gif = (
                b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
                b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
                b'\x02\x4c\x01\x00\x3b'
                )
        uploaded = SimpleUploadedFile('small.gif', small_gif, content_type='image/gif')
        post = self.login_user.post(reverse('new_post'),
                                {
                                'username': self.user.username,
                                'text': 'new_post_with_img',
                                'image': uploaded,
                                'group': self.group.id
                                },
                            follow=True
                        )  
        urls = [
            reverse('index'),
            reverse('profile', kwargs={
                                    'username': self.user.username
                                    }
                                ),
            reverse('group_posts', kwargs={
                                    'slug': self.group.slug
                                    }
                                ),
            reverse('post', kwargs={
                                        'username': self.user.username, 
                                        'post_id': 1
                                        }
                                    )
            ]
        for url in urls:
            response = self.login_user.get(url)
            self.assertContains(response, '<img')
  
    def test_wrong_format(self):
        mock_file = Mock()
        mock_file.name = 'my_filename.doc'
        mock_file.save()
        response = self.login_user.post(reverse('new_post'), 
                                {
                                'username': self.user.username,
                                'text': 'new_post_with_img',
                                'image': mock_file,
                                'group': self.group.id
                                },
                            follow=True
                        )
        self.assertNotContains(response, '<img')
        self.assertFormError(response,
                             'form',
                             'image',
                             'Загрузите правильное изображение. '
                             'Файл, который вы загрузили, '
                             'поврежден или не является изображением.'
                            )


class Cache(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
                        first_name = 'sarah',
                        last_name = 'connor',
                        username='sarah899', 
                        email='connor.s@skynet.com', 
                        password='12345'
                        )
        self.login_user = Client()
        self.login_user.force_login(self.user)
    
    def test_cache(self):
        first_enter = self.login_user.get(reverse('index'))
        Post.objects.create(author=self.user, text='new_post_test_cache')
        text = Post.objects.get(pk=1).text
        second_enter = self.login_user.get(reverse('index'))
        self.assertNotContains(second_enter, text)
        cache.clear()
        third_enter = self.login_user.get(reverse('index'))
        self.assertContains(third_enter, text)


class Followings(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
                        username='sarah899'
                        )
        self.login_user = Client()
        self.login_user.force_login(self.user)
        self.author = User.objects.create_user(
                        username='david595'
                        )
        self.group = Group.objects.create(title='test_follow_group', slug='test_group')
    
    def test_user_can_follow(self):
        self.login_user.post(reverse('profile_follow', 
                             kwargs={'username': self.author.username}
                            )
                        )
        relation = Follow.objects.order_by('user').first()
        all_relations = Follow.objects.count()
        self.assertEqual(all_relations, 1)
        self.assertEqual(relation.user, self.user)
        self.assertEqual(relation.author, self.author)

    def test_user_can_unfollow(self):
        Follow.objects.create(user=self.user, author=self.author)
        self.login_user.post(reverse('profile_unfollow',  
                             kwargs={'username': self.author.username} 
                            ) 
                        )
        all_relations = Follow.objects.count()
        self.assertEqual(all_relations, 0)
    
    def test_follower_posts(self):
        self.login_user.post(reverse('profile_follow', 
                             kwargs={'username': self.author.username}
                            )
                        )
        post = Post.objects.create(
                        text='post_by_following_author',
                        author=self.author,
                        group=self.group
                        )
        response_with_follow = self.login_user.post(reverse('follow_index')) 
        self.assertIn(post, response_with_follow.context['posts_list'])
        self.assertEqual(response_with_follow.context['paginator'].count, 1)
        post_on_page = response_with_follow.context['page'][0]
        self.assertEqual(post_on_page.text, post.text)
        self.assertEqual(post_on_page.author, post.author)
        self.assertEqual(str(post_on_page.group), str(post.group))

    def test_unfollower_posts(self):
        post = Post.objects.create(text='post_by_following_author', author=self.author)
        response_without_follow = self.login_user.post(reverse('follow_index'))
        self.assertEqual(response_without_follow.context['paginator'].count, 0)
    

class Commentators(TestCase):
    def setUp(self):
        self.not_login_user = Client()
        self.user = User.objects.create_user(
                        username='sarah899'
                        )
        self.author = User.objects.create_user(
                            username='david595'
                            )
        self.login_user = Client()
        self.login_user.force_login(self.user)
    
    def test_anonymous_can_not_comment(self):
        post = Post.objects.create(text='test post', author=self.author)
        try_comment = self.not_login_user.post(reverse('add_comment', 
                                    kwargs={
                                        'username': self.author, 
                                        'post_id': post.id
                                        }
                                    )
                                )
        all_comments = Comment.objects.count()
        self.assertEqual(all_comments, 0)
        self.assertEqual(try_comment.status_code, 302)
        self.assertRedirects(try_comment, (
                            f'{reverse("login")}?next=/'
                            f'{self.author.username}/'
                            f'{post.id}/comment'
                            )
                        )
    
    def test_creating_comments(self):
        post = Post.objects.create(text='test post', author=self.author)
        comment = self.login_user.post(reverse('add_comment', 
                                    kwargs={
                                        'username': self.author, 
                                        'post_id': post.id
                                        }
                                    ),
                                    {'text': 'test_text'},
                                    follow=True
                                )
        new_comment = Comment.objects.order_by('author').first()
        all_comments = Comment.objects.count()
        self.assertEqual(all_comments, 1)
        self.assertEqual(new_comment.text, 'test_text')
        self.assertEqual(new_comment.post, post)
        self.assertEqual(new_comment.author, self.user)