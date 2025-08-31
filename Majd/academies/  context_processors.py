def academy_context(request):
    """Make academy available in all templates (if user is logged in as academy admin)."""
    academy = None
    if hasattr(request.user, "academy_admin_profile"):
        academy = getattr(request.user.academy_admin_profile, "academy", None)

    return {
        "academy": academy
    }
