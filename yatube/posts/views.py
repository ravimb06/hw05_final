from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from .utils import posts_paginator


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.all()
    page_obj = posts_paginator(request, posts, settings.OBJ_IN_PAGE)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.group_posts.all()
    page_obj = posts_paginator(request, posts, settings.OBJ_IN_PAGE)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    template = 'posts/profile.html'
    posts = user.author_posts.all()
    posts_count = posts.count()
    page_obj = posts_paginator(request, posts, settings.OBJ_IN_PAGE)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author=user
    ).exists()
    context = {
        'page_obj': page_obj,
        'username': user,
        'posts_count': posts_count,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    template = 'posts/create_post.html'
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user)
    context = {
        'form': form,
        'is_edit': False,
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        post.save()
        return redirect('posts:post_detail', post.id)
    context = {
        'form': form,
        'is_edit': True,
        'post_id': post.id,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    title = 'Посты из подписок'
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = posts_paginator(request, post_list, settings.OBJ_IN_PAGE)
    context = {
        'template': template,
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    """Активация подписки на автора."""
    user = get_object_or_404(User, username=username)
    if request.user != user:
        Follow.objects.get_or_create(author=user, user=request.user)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Отписка от автора."""
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=author)
    follow.delete()
    return redirect('posts:profile', username)
