from huey import crontab
from huey.contrib.djhuey import db_periodic_task, db_task
from social_django.models import UserSocialAuth
from stravalib.client import Client
from django.conf import settings
from datetime import timedelta
from apps.activity.models import Activity
import traceback
from datetime import datetime


PROCESS_TIME = timedelta(minutes=5)
PULL_LIMIT = 200
STREAM_TYPES = ['time', 'latlng', 'distance', 'altitude', 'velocity_smooth',
                'heartrate', 'cadence', 'watts', 'temp', 'moving', 'grade_smooth']


def import_activities(athlete_id, reverse=False):
    client = Client()
    auth_user = UserSocialAuth.objects.get_social_auth("strava", athlete_id)

    # FIXME: Open for all?
    if not auth_user or not auth_user.user.is_staff:
        print("User not exists or not a staff")

    client.access_token = auth_user.extra_data['access_token']
    if auth_user.expiration_timedelta() < PROCESS_TIME:
        res = client.refresh_access_token(
            client_id=settings.SOCIAL_AUTH_STRAVA_KEY,
            client_secret=settings.SOCIAL_AUTH_STRAVA_SECRET,
            refresh_token=auth_user.extra_data['refresh_token'],
        )
        auth_user.extra_data['access_token'] = res['access_token']
        auth_user.extra_data['expires'] = int(res['expires_at'] - datetime.utcnow().timestamp())
        auth_user.save()

    # Newest activity
    last_activity = Activity.objects.order_by('start_date').last()
    last_import_time = last_activity and last_activity.start_date
    activities = client.get_activities(after=last_import_time, limit=PULL_LIMIT)

    if reverse:
        # Oldest activity
        last_activity = Activity.objects.order_by('start_date').first()
        last_import_time = last_activity and last_activity.start_date or datetime.utcnow()
        activities = client.get_activities(before=last_import_time, limit=PULL_LIMIT)

    for summary in activities:
        try:
            detail = client.get_activity(summary.id, include_all_efforts=True)
            streams = client.get_activity_streams(summary.id, types=STREAM_TYPES)
            activity = Activity.upsert(auth_user.user_id, detail, streams)
            print("Created Strava activity:", activity)

            activity.get_start_location()
            activity.get_map_file()
        except Exception:
            traceback.print_exc()


@db_task()
def initial_import(athlete_id):
    import_activities(athlete_id, reserve=True)


# TODO: Use webhook for this
@db_periodic_task(crontab(minute='*/5'))
def check_for_new_activities():
    for ua in UserSocialAuth.objects.filter(provider='strava'):
        import_activities(ua.uid)
