from django.shortcuts import render, redirect,  get_object_or_404
from accounts.models import TrainerProfile, ParentProfile
from .models import Conversation, Message
from django.contrib.auth.models import User
from django.utils import timezone

def conversations_list_view(request):
    user = request.user
    if not user.is_authenticated:
        return redirect("accounts:login_view")

    is_trainer_user = user.groups.filter(name="trainer").exists()
    trainer_profile = getattr(user, "trainer_profile", None)

    if not (is_trainer_user and trainer_profile):
        return redirect("accounts:login_view")

    conversations = (
        Conversation.objects
        .filter(trainer=trainer_profile)
        .select_related("parent__user")
    )

    context = {
        "trainer": {
            "name": user.get_full_name() or user.username,
            "academy_name": getattr(trainer_profile.academy, "name", ""),
            "profile_image": getattr(trainer_profile, "profile_image", None),
        },
        "conversations": conversations
    }

    return render(request, "communication/conversations_list.html", context)





def conversation_detail_view(request, conversation_id):
    user = request.user
    if not user.is_authenticated:
        return redirect("accounts:login_view")

    is_trainer_user = user.groups.filter(name="trainer").exists()
    trainer_profile = getattr(user, "trainer_profile", None)
    if not (is_trainer_user and trainer_profile):
        return redirect("accounts:login_view")

    conversation = get_object_or_404(
        Conversation.objects.select_related("parent__user"),
        id=conversation_id,
        trainer=trainer_profile
    )

    # ✅ إرسال رسالة جديدة
    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        if body:
            Message.objects.create(
                conversation=conversation,
                sender=user,
                body=body,
                sent_at=timezone.now()
            )
            return redirect("communication:conversation_detail", conversation_id=conversation.id)

    messages = conversation.messages.select_related("sender").order_by("sent_at")

    context = {
        "trainer": {
            "name": user.get_full_name() or user.username,
            "academy_name": getattr(trainer_profile.academy, "name", ""),
            "profile_image": getattr(trainer_profile, "profile_image", None),
        },
        "conversation": conversation,
        "messages": messages,
    }

    return render(request, "communication/conversation_detail.html", context)