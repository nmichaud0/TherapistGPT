from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .therapist import Therapy
import json


@shared_task
def play_conversation_time_consuming(therapy_parameters, api_key, user_input):

    if isinstance(therapy_parameters, str):
        therapy_parameters = json.loads(therapy_parameters)

    therapy_object = Therapy(api_key=api_key)
    therapy_object.update_parameters(therapy_parameters)

    return {'assistant_message': therapy_object.play_conversation(user_input),
            'therapy_parameters': therapy_object.get_parameters()}
