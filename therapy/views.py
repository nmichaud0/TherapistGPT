from django.shortcuts import render
from .therapist import Therapy
from django.http import JsonResponse
from django.core.cache import cache
import yaml
import openai
import json
from .tasks import play_conversation_time_consuming
from celery.result import AsyncResult

SERVER_PARAMETERS = yaml.safe_load(open('parameters.yaml', 'r'))


def home(request):
    request.session['therapist_state'] = {'Object': 'Shutdown'}
    return render(request, 'home.html')


def chat(request):

    therapy_object = Therapy(api_key=SERVER_PARAMETERS['api-key'])

    request.session['therapist_parameters'] = therapy_object.get_parameters()

    request.session['api-key'] = ''

    request.session['api-key-valid'] = False

    request.session['first_message_sent'] = False

    return render(request, 'chat.html')


def api_message(request):

    if request.method != 'POST':
        return JsonResponse({'response': 'Invalid request method'}, status=400)

    therapy_parameters = request.session.get('therapist_parameters')

    first_msg = request.session.get('first_message_sent')

    if request.session.get('api-key-valid') or (not first_msg):

        if not first_msg:
            request.session['first_message_sent'] = True

        #therapy_object = Therapy(api_key=request.session.get('api-key'))

        #therapy_object.update_parameters(therapy_parameters)

        user_input = request.POST.get('input_text', '')

        # assistant_message = therapy_object.play_conversation(user_input)  # This is the original time-consuming line

        task = play_conversation_time_consuming.delay(therapy_parameters,
                                                      request.session.get('api-key'),
                                                      user_input)
        task_id = task.id

        return JsonResponse({'respone': None, 'task_id': task_id}, status=202)

    else:
        return JsonResponse({'response': False})  # Invalid API Key


def check_task_status(request):

    task = AsyncResult(request.POST.get('task_id'))

    if task.state == 'PENDING':
        response = {'state': task.state,
                    'status': 'Pending...'}
    elif task.state == 'SUCCESS':

        assistant_message = task.result['assistant_message']
        therapy_parameters = task.result['therapy_parameters']

        request.session['therapist_parameters'] = therapy_parameters

        if isinstance(assistant_message, tuple) or isinstance(assistant_message, list):
            response = {'response': assistant_message[0], 'user_name': assistant_message[1]}

        else:
            response = {'response': assistant_message}

        response = {'state': task.state,
                    'response': response}

    else:
        response = {'state': task.state,
                    'status': str(task.info)}

    return JsonResponse(response)


def update_api_key(request):

    if request.method != 'POST':
        return JsonResponse({'response': 'Invalid request method'}, status=400)

    api_key = request.POST.get('api_key', '')

    try:
        openai.api_key = api_key
        openai.Completion.create(
            model='ada',
            prompt='This is a test',
            max_tokens=1,
            temperature=0)

        valid_api_key = True

    except openai.error.AuthenticationError:
        valid_api_key = False

    if valid_api_key:

        valid_gpt4 = check_GPT4(request, api_key)

        therapy_parameters = request.session.get('therapist_parameters')

        if isinstance(therapy_parameters, str):

            therapy_parameters = json.loads(therapy_parameters)

        therapy_parameters['api_key'] = api_key

        if not valid_gpt4:
            therapy_parameters['only_fast_model'] = True

        request.session['therapist_parameters'] = therapy_parameters

        request.session['api-key'] = api_key

        request.session['api-key-valid'] = True

        if valid_gpt4:
            return JsonResponse({'response': {'api_key_valid': True, 'gpt4': True}}, status=200)

        else:
            return JsonResponse({'response': {'api_key_valid': True, 'gpt4': False}}, status=200)

    else:

        return JsonResponse({'response': {'api_key_valid': False, 'gpt4': False}}, status=200)


def check_GPT4(request, api_key):

    therapy_parameters = request.session['therapist_parameters']

    if isinstance(therapy_parameters, str):
        therapy_parameters = json.loads(therapy_parameters)

    try:
        openai.api_key = api_key
        openai.ChatCompletion.create(
            model='gpt-4',
            messages=[{'role': 'user', 'content': 'This is a test'}],
            max_tokens=1)

        valid_gpt4 = True
    except Exception as e:

        valid_gpt4 = False

    return valid_gpt4


def update_model(request):

    if request.method != 'POST':
        return JsonResponse({'response': 'Invalid request method'}, status=400)

    therapy_parameters = request.session.get('therapist_parameters')

    model_requested = request.POST.get('model', '')

    if model_requested == 'GPT3.5':

        return sub_update_model(True, therapy_parameters, request)

    elif model_requested == 'GPT4':

        return sub_update_model(False, therapy_parameters, request)

    else:

        return JsonResponse({'response': 'Invalid model'}, status=400)


def sub_update_model(model, therapy_parameters, request):

    if isinstance(therapy_parameters, str):

        therapy_parameters = json.loads(therapy_parameters)

    therapy_parameters['only_fast_model'] = model

    request.session['therapist_parameters'] = therapy_parameters

    return JsonResponse({'response': 'Model updated'}, status=200)


def download_data(request):

    therapy_parameters = request.session.get('therapist_parameters')

    if isinstance(therapy_parameters, str):
        therapy_parameters = json.loads(therapy_parameters)

    return JsonResponse({'response': therapy_parameters}, status=200)
