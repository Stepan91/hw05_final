from django.test import TestCase
from django.test import Client
from .models import User, Post, Group, Comment
from .forms import PostForm
from . import views
from django.urls import reverse
from django.core.cache import cache
 
 
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
        object = Post.objects.get(id=1)
        all_objects = Post.objects.all().count()
        self.assertEqual(all_objects, 1)
        self.assertEqual(object.text, 'test_text')
        self.assertEqual(object.author, self.user)
        self.assertEqual(object.group, self.group)
 
 
    def test_post_NotAutorized(self):
        try_post = self.not_login_user.post(reverse("new_post"))
        self.assertEqual(try_post.status_code, 302)
        self.assertRedirects(try_post, (
                            f'{reverse("login")}?next='
                            f'{reverse("new_post")}'
                            )
                        )
        all_objects = Post.objects.all().count()
        self.assertEqual(all_objects, 0)
 
 
    def test_post_on_pages(self):
        post = Post.objects.create(text='GOGOGOGOGO', author=self.user, group=self.group)
        urls = [
            reverse("index"),
            reverse("post", kwargs={"username": self.user.username, "post_id": post.id}),
            reverse("profile", kwargs={"username": self.user.username})
        ]
        cache.clear()
        for test in urls:
            self.check(test, post.text, self.user, self.group)
 
 
    def test_edit_post(self):
        post = Post.objects.create(text='GOGOGOGOGO', author=self.user, group=self.group)
        group_new = Group.objects.create(title='test_group_after_edit', slug='test_edit')
        urls = [
            reverse("group_posts", kwargs={"slug": "test_edit"}),
            reverse("profile", kwargs={"username": self.user.username}),
            reverse("post", kwargs={"username": self.user.username, "post_id": post.id}),
            reverse("index"),
        ]
        new_data = {
            'text': 'new_text_after_edit',
            'group': group_new.id,
            }
        response = self.login_user.post(reverse('post_edit', 
                            kwargs={
                                "username": self.user.username, 
                                "post_id": post.id
                                }
                            ),
                            new_data,
                            follow=True
                            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, new_data['group'], status_code=200)
 
        cache.clear()
        for test in urls:
            self.check(test, new_data['text'], self.user, group_new.title)
 
        response = self.login_user.post(reverse(
                                   "group_posts",
                                   kwargs={"slug": "original"}
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
 
 
    def test_img(self):
        with open('posts/media/posts/priroda.jpg','rb') as img:
            post = self.login_user.post(reverse('new_post'), 
                                {
                                'username': self.user.username,
                                'text': 'new_post_with_img',
                                'image': img,
                                'group': self.group.id
                                },
                            follow=True
                        )
        response = self.login_user.get(reverse("post", kwargs={
                                        "username": self.user.username, 
                                        "post_id": 1
                                        }
                                    )
                                )
        self.assertContains(response, '<img')
        cache.clear()
        response = self.login_user.get(reverse("index"))
        self.assertContains(response, '<img')
 
        response = self.login_user.get(reverse("profile", kwargs={
                                    "username": self.user.username
                                    }
                                )
                            )
        self.assertContains(response, '<img')
 
        response = self.login_user.get(reverse("group_posts", kwargs={
                                    "slug": "test_group"
                                    }
                                )
                            )
        self.assertContains(response, '<img')
 
 
    def test_wrong_format(self):
        with open('posts/media/posts/er_doc.docx','rb') as img:
            response = self.login_user.post(reverse('new_post'), 
                                {
                                'username': self.user.username,
                                'text': 'new_post_with_img',
                                'image': img,
                                'group': self.group.id
                                },
                            follow=True
                        )
        self.assertNotContains(response, '<img')
        self.assertFormError(response,
                             "form",
                             "image",
                             "Загрузите правильное изображение. "
                             "Файл, который вы загрузили, "
                             "поврежден или не является изображением."
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
        first_enter = self.login_user.get(reverse("index"))
        post = self.login_user.post(reverse('new_post'), 
                                {
                                'username': self.user.username,
                                'text': 'new_post_test_cache',
                                },
                            follow=True
                            )
        second_enter = self.login_user.get(reverse("index"))
        self.assertNotContains(second_enter, 'new_post_test_cache')
        cache.clear()
        third_enter = self.login_user.get(reverse("index"))
        self.assertEqual(third_enter.context['paginator'].count, 1)
        post_on_page = third_enter.context['page'][0]
        self.assertEqual(post_on_page.text, 'new_post_test_cache')
        self.assertEqual(post_on_page.author, self.user)


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
    

    def test_can_follow_and_unfollow(self):
        response_before_follow = self.login_user.get(reverse('profile', 
                                 kwargs={
                                     'username' : self.author.username
                                    }
                                )
                            )
        self.assertEqual(response_before_follow.context['follower'], 0)
        self.login_user.post(reverse('profile_follow', 
                             kwargs={'username': self.author.username}
                            )
                        )
        response_after_follow = self.login_user.get(reverse('profile', 
                                kwargs={
                                    'username' : self.author.username
                                    }
                                )
                            )
        self.assertEqual(response_after_follow.context['follower'], 1)

        self.login_user.post(reverse('profile_unfollow', 
                             kwargs={'username': self.author.username}
                            )
                        )
        response_after_unfollow = self.login_user.get(reverse('profile', 
                                kwargs={
                                    'username' : self.author.username
                                    }
                                )
                            )
        self.assertEqual(response_after_unfollow.context['follower'], 0)
    

    def test_follower_posts(self):
        self.login_user.post(reverse('profile_follow', 
                             kwargs={'username': self.author.username}
                            )
                        )
        post = Post.objects.create(text='post_by_following_author', author=self.author)
        response_with_follow = self.login_user.post(reverse('follow_index'))
        self.assertIn(post, response_with_follow.context['posts_list'])
        
        self.login_user.post(reverse('profile_unfollow', 
                             kwargs={'username': self.author.username}
                            )
                        )
        response_without_follow = self.login_user.post(reverse('follow_index'))
        self.assertNotIn(post, response_without_follow.context['posts_list'])
    

class Commentators(TestCase):
    def setUp(self):
        self.not_login_user = Client()
        self.author = User.objects.create_user(
                            username='david595'
                            )
    
    
    def test_only_autorized_user_can_comment(self):
        post = Post.objects.create(text='test post', author=self.author)
        try_comment = self.not_login_user.post(reverse('add_comment', 
                                    kwargs={
                                        'username': self.author, 
                                        'post_id': post.id
                                        }
                                    )
                                )
        self.assertEqual(try_comment.status_code, 302)
        self.assertRedirects(try_comment, (
                            f'{reverse("login")}?next=/'
                            f'{self.author.username}/'
                            f'{post.id}/comment'
                            )
                        )
        all_comments = Comment.objects.all().count()
        self.assertEqual(all_comments, 0)

    


    

        

        


        

                        




        

