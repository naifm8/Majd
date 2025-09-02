from django.shortcuts import render, redirect,  get_object_or_404
from accounts.models import TrainerProfile, ParentProfile
from .models import Conversation, Message
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.decorators import login_required





def trainer_conversations_view(request):
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

    return render(request, "communication/trainer_conversations_list.html", context)



def trainer_conversation_detail_view(request, conversation_id):
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
            return redirect("communication:trainer_conversation_detail", conversation_id=conversation.id)

    messages = conversation.messages.select_related("sender").order_by("sent_at")

    context = {
        "trainer": {
            "name": user.get_full_name() or user.username,
            "academy_name": getattr(trainer_profile.academy, "name", ""),
            "profile_image": getattr(trainer_profile, "profile_image", None),
        },
        "conversation": conversation,
        "messages": messages,
        "hide_django_messages": True,  # ✅ هذا هو الجديد
    }

    return render(request, "communication/trainer_conversation_detail.html", context)



def parent_conversations_view(request):
    user = request.user
    if not user.is_authenticated:
        return redirect("accounts:login_view")

    is_parent_user = user.groups.filter(name="parent").exists()
    parent_profile = getattr(user, "parent_profile", None)

    if not (is_parent_user and parent_profile):
        return redirect("accounts:login_view")

    conversations = (
        Conversation.objects
        .filter(parent=parent_profile)
        .select_related("trainer__user")
    )

    context = {
        "parent": {
            "name": user.get_full_name() or user.username,
            "academy": getattr(parent_profile.child.academy, "name", "") if hasattr(parent_profile, "child") else "",
            "profile_image": getattr(parent_profile, "profile_image", None),
        },
        "conversations": conversations,
    }

    return render(request, "communication/parent_conversations_list.html", context)



def parent_conversation_detail_view(request, conversation_id):
    user = request.user
    if not user.is_authenticated:
        return redirect("accounts:login_view")

    is_parent_user = user.groups.filter(name="parent").exists()
    parent_profile = getattr(user, "parent_profile", None)

    if not (is_parent_user and parent_profile):
        return redirect("accounts:login_view")

    conversation = get_object_or_404(
        Conversation.objects.select_related("trainer__user"),
        id=conversation_id,
        parent=parent_profile
    )

    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        if body:
            Message.objects.create(
                conversation=conversation,
                sender=user,
                body=body,
                sent_at=timezone.now()
            )
            return redirect("communication:parent_conversation_detail", conversation_id=conversation.id)

    messages = conversation.messages.select_related("sender").order_by("sent_at")

    context = {
        "parent": {
            "name": user.get_full_name() or user.username,
            "academy": getattr(parent_profile.child.academy, "name", "") if hasattr(parent_profile, "child") else "",
            "profile_image": getattr(parent_profile, "profile_image", None),
        },
        "conversation": conversation,
        "messages": messages,
        "hide_django_messages": True,
    }

    return render(request, "communication/parent_conversation_detail.html", context)


@login_required
def start_conversation_view(request):
    user = request.user

    is_trainer = user.groups.filter(name="trainer").exists()
    is_parent = user.groups.filter(name="parent").exists()

    if is_trainer:
        trainer_profile = getattr(user, "trainer_profile", None)

        if request.method == "POST":
            parent_id = request.POST.get("parent_id")
            parent = get_object_or_404(ParentProfile, id=parent_id)

            # ✅ إنشاء المحادثة أو استرجاعها
            convo, _ = Conversation.objects.get_or_create(
                trainer=trainer_profile,
                parent=parent
            )
            return redirect("communication:trainer_conversation_detail", conversation_id=convo.id)

        # قائمة أولياء الأمور
        parents = ParentProfile.objects.select_related("user").all()
        return render(request, "communication/start_conversation_trainer.html", {
            "parents": parents
        })

    elif is_parent:
        parent_profile = getattr(user, "parent_profile", None)

        if request.method == "POST":
            trainer_id = request.POST.get("trainer_id")
            trainer = get_object_or_404(TrainerProfile, id=trainer_id)

            convo, _ = Conversation.objects.get_or_create(
                trainer=trainer,
                parent=parent_profile
            )
            return redirect("communication:parent_conversation_detail", conversation_id=convo.id)

        # قائمة المدربين
        trainers = TrainerProfile.objects.select_related("user").all()
        return render(request, "communication/start_conversation_parent.html", {
            "trainers": trainers
        })

    return redirect("accounts:login_view")