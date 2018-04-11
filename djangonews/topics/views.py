from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.list import ListView
from django.http import HttpResponse, Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from .models import Topic, Comment, Upvote
from .forms import CommentForm, UpvoteForm

from django.utils import timezone

# Create your views here.


def list_topics(request):
    sorting_type = request.GET.get('sort', 'recent')
    if sorting_type == 'recent' or (sorting_type != 'recent' and sorting_type != 'rated') :
        topic_list = Topic.objects.all()
    else:
        topic_list = Topic.objects.order_by('-nbr_upvotes')
    
    # Pagination
    paginator = Paginator(topic_list, 2)
    page = request.GET.get('page')
    topics = paginator.get_page(page)

    return render(request, 'topics/list.html', {'topics': topics})

def detail_topic(request, slug=''):
    try:
        assert len(slug) > 0
        res = Topic.objects.filter(slug=slug)
        assert len(res) == 1
    except AssertionError:
        raise Http404("Article Not Found !")

    topic = res[0]
    res = Upvote.objects.filter(Q(topic=topic) & Q(upvoter=request.user))
    assert len(res) in (0,1)
    user_upvoted_topic = len(res) == 1
    return render(request, 'topics/detail.html',{
            'title': topic.title, 
            'published_at': topic.published_at ,
            'content': topic.content,
            'id': topic.id,
            'author_name': topic.author.get_username(),
            'comments': topic.comments.all(),
            'nbr_upvotes': topic.nbr_upvotes,
            'nbr_comments': len(topic.comments.all()),
            'upvoted': user_upvoted_topic,
            'comment_form': None if request.user.is_authenticated == False else CommentForm(),
            'upvote_form': None if request.user.is_authenticated == False else UpvoteForm() })

def submit_comment(request, id_topic=0):
    try:
        assert request.method == 'POST'
    except AssertionError:
        raise Http404("Wrong Method")
    
    topic = get_object_or_404(Topic, pk=id_topic)
    author = request.user
    comment = Comment(author=author, topic=topic, published_at=timezone.now())
    form = CommentForm(instance=comment, data=request.POST)
    if form.is_valid():
        form.save()
        return redirect('detail_topic', slug=topic.slug)
    else:
        raise Http404('Form invalid')


def upvote_topic(request, id_topic=0):
    try:
        assert request.method == 'POST'
    except AssertionError:
        raise Http404("Wrong Method")

    topic = get_object_or_404(Topic, pk=id_topic)
    user = request.user
    
    try:
        res = Upvote.objects.filter(Q(topic=topic) & Q(upvoter=user))
        assert len(res) == 0
    except AssertionError:
        return redirect('detail_topic', slug=topic.slug)
    
    upvote = Upvote(upvoter=user, topic=topic, timestamp=timezone.now())
    form = UpvoteForm(instance=upvote, data=request.POST)
    if form.is_valid():
        form.save()
        return redirect('detail_topic', slug=topic.slug)
    else:
        raise Http404('Form invalid')