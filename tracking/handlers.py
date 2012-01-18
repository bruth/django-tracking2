from datetime import datetime
from tracking.models import Visitor

def track_ended_session(sender, request, user, **kwargs):
    try:
        history = Visitor.objects.get(session_key=request.session.session_key)
    # This should rarely ever occur.. e.g. direct request to logout
    except Visitor.DoesNotExist:
        return

    # Explicitly end this session. This improves the accuracy of the stats.
    history.end_time = datetime.now()
    history.time_on_site = (history.end_time - history.start_time).seconds
    history.save()
