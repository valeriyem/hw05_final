from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow

AMOUNT_OF_POSTS: int = 10


# @cache_page(60 * 20)
def index(request):
    post_list = Post.objects.order_by('-pub_date')
    paginator = Paginator(post_list, AMOUNT_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.order_by('-pub_date')
    paginator = Paginator(post_list, AMOUNT_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    propose_author = get_object_or_404(User, username=username)
    post_list = propose_author.posts.all()
    paginator = Paginator(post_list, AMOUNT_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    posts_count = post_list.count()
    # print(Follow.objects.filter(user=request.user).filter(author=propose_author))
    if Follow.objects.filter(user=request.user).filter(
            author=propose_author).exists():
        following = True
    else:
        following = False
    context = {
        'page_obj': page_obj,
        'username': username,
        'author': propose_author,
        'posts_count': posts_count,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    propose_post = get_object_or_404(Post, pk=post_id)
    propose_author = propose_post.author
    posts_count = propose_author.posts.count()
    form = CommentForm()
    comments = propose_post.comments.all()
    context = {
        'post': propose_post,
        'author': propose_author,
        'posts_count': posts_count,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=post.author.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, pk=post_id)
    if request.user.id != post.author.id:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        post.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/create_post.html',
                  {'form': form,
                   'post': post,
                   'is_edit': is_edit}
                  )


@login_required
def add_comment(request, post_id):
    # Получите пост и сохраните его в переменную post.
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    print('VELEL')
    print(request.user)
    post_list = Post.objects.filter(
        author__following__user=request.user).order_by('-pub_date')
    paginator = Paginator(post_list, AMOUNT_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


def is_subscribed(user, author):
    if user.is_authenticated:
        return Follow.objects.filter(user=user, author=author).exists()


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author and not is_subscribed(request.user, author):
        Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username)
