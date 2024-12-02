from django.shortcuts import render

from ncjm.models import Joke

def index(request):
    # grab a random nondeleted, approved joke
    random_joke = Joke.objects.filter(
        is_deleted=False,
        is_approved=True,
    ).order_by("?").first()

    # grab the number of approved jokes
    total_approved_jokes = Joke.objects.filter(is_approved=True).count()

    # grab the number of jokes in the queue
    jokes_in_queue = Joke.objects.filter(is_approved=False).count()


    context = {
        "joke": random_joke,
        "total_approved_jokes": total_approved_jokes,
        "jokes_in_queue": jokes_in_queue,
    }

    return render(
        request=request,
        template_name="index.html",
        context=context
    )