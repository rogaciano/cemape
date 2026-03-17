def user_profile(request):
    if request.user.is_authenticated:
        try:
            return {'profile': request.user.profile}
        except Exception:
            pass
    return {'profile': None}
