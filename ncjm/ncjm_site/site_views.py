import json
from django.http import JsonResponse, HttpResponseRedirect, HttpRequest
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.db.models import Q
from django.core.paginator import Paginator

from ncjm.models import JokeBase, CornyJoke, LongJoke, Tag
from ncjm.ncjm.models.CornyJoke import AlreadyReactedException
from .forms import AddCornyJokeForm, AddLongJokeForm

def index(request, joke_id=None, joke_slug=None):
    joke = None

    if joke_id:
        joke = get_object_or_404(JokeBase, pk=joke_id)
    elif joke_slug:
        joke = get_object_or_404(JokeBase, slug=joke_slug)
    #TODO: add joke type switcher
    if not joke or joke.is_deleted or not joke.is_approved:
        # grab a random nondeleted, approved joke
        joke = JokeBase.objects.filter(
            is_approved=True,
            is_deleted=False,
        ).order_by("?").first()

    # grab the number of approved jokes
    total_approved_jokes = JokeBase.objects.filter(
        is_approved=True,
        is_deleted=False,
    ).count()

    # grab the number of jokes in the queue
    jokes_in_queue = JokeBase.objects.filter(
        is_approved=False,
        is_deleted=False,
    ).count()

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
        form_type = request.POST.get("form_type", "cornyjoke")
        if form_type == "longjoke":
            form = AddLongJokeForm(request.POST)
        else:
            form = AddCornyJokeForm(request.POST)

        try:
            # handle valid form submission
            if form.is_valid():
                form.save()

                submitter_name = form.cleaned_data["submitter_name"]
                new_form = AddCornyJokeForm(
                    initial={"submitter_name": submitter_name},
                )

                context = {
                    "status": "success",
                    "form": new_form,
                }

            # handle ValidationErrors
            else:
                errors = []
                for field, error_list in form.errors.items():
                    for error in error_list:
                        errors.append(error)
                context = {
                    "status": "error",
                    "errors": errors,
                    "form": form,
                }
        # handle ValueErrors and other non-validation exceptions
        except Exception as e:
            context = {
                "status": "error",
                "errors": e,
                "form": form,
                "form_type": form_type,
            }
        
        return render(request, "add_joke.html", context=context)

    cornyjoke_form = AddCornyJokeForm()
    longjoke_form = AddLongJokeForm()
    context = {
        "cornyjoke_form": cornyjoke_form,
        "longjoke_form": longjoke_form,
    }
    return render(request, "add_joke.html", context=context)

def search(request):
    search_term = request.GET.get("q", "")
    jokes_results = []

    if search_term:
        tags = Tag.objects.filter(tag_text__icontains=search_term)
        jokes_results = CornyJoke.objects.filter(
            Q(tags__in=tags) | Q(submitter_name__icontains=search_term),
            is_deleted=False,
        ).distinct()

    paginator = Paginator(jokes_results, 10)  # Show 10 jokes per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    for joke in page_obj:
        joke.full_url_by_id = request.build_absolute_uri(f"/id/{joke.id}/")
        joke.full_url_by_slug = request.build_absolute_uri(f"/slug/{joke.slug}/")


    context = {
        "search_term": search_term,
        "page_obj": page_obj,
    }

    return render(request, "search.html", context)

def add_reaction(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            joke_id = data.get("joke_id")
            reaction_emoji = data.get("reaction_emoji")

            joke = get_object_or_404(JokeBase, pk=joke_id)
            joke.add_reaction(
                reaction_emoji=reaction_emoji,
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT"),
            )
            new_count = joke.reactions.get(reaction_emoji, 0)
            return JsonResponse({
                "status": "success",
                "new_count": new_count,
            })

        except AlreadyReactedException as e:
            return JsonResponse({
                "status": "error",
                "message": "You have already reacted to this joke.",
            })

        except PermissionDenied as e:
            return JsonResponse({
                "status": "error",
                "message": "Error processing your request. Please refresh the page and try again."
            })

    return HttpResponseRedirect(reverse("index"))