from django.shortcuts import get_object_or_404, render
from django.db.models import Q
from django.core.paginator import Paginator

from ncjm.models import Joke, Tag
from .forms.AddAJokeForm import AddAJokeForm

def index(request, joke_id=None, joke_slug=None):
    if joke_id:
        joke = get_object_or_404(Joke, pk=joke_id)
    elif joke_slug:
        joke = get_object_or_404(Joke, slug=joke_slug)
    else:
        # grab a random nondeleted, approved joke
        joke = Joke.objects.filter(
            is_deleted=False,
            is_approved=True,
        ).order_by("?").first()

    # grab the number of approved jokes
    total_approved_jokes = Joke.objects.filter(is_approved=True).count()

    # grab the number of jokes in the queue
    jokes_in_queue = Joke.objects.filter(is_approved=False).count()

    context = {
        "joke": joke,
        "total_approved_jokes": total_approved_jokes,
        "jokes_in_queue": jokes_in_queue,
    }

    return render(
        request=request,
        template_name="index.html",
        context=context
    )

def add_joke(request):
    if request.method == "POST":
        form = AddAJokeForm(request.POST)
        if form.is_valid():
            form.save()

            submitter_name = form.cleaned_data["submitter_name"]
            new_form = AddAJokeForm(
                initial={"submitter_name": submitter_name},
            )

            context = {
                "status": "success",
                "form": new_form,
            }
            return render(request, "add_joke.html", context=context)

    form = AddAJokeForm()
    return render(request, "add_joke.html", {"form": form})

def search(request):
    search_term = request.GET.get("q", "")
    jokes_results = []

    if search_term:
        tags = Tag.objects.filter(tag_text__icontains=search_term)
        jokes_results = Joke.objects.filter(
            Q(tags__in=tags) | Q(submitter_name__icontains=search_term)
        ).distinct()

    paginator = Paginator(jokes_results, 10)  # Show 10 jokes per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "search_term": search_term,
        "page_obj": page_obj,
    }

    return render(request, "search.html", context)
