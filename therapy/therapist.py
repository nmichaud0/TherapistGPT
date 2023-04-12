import tiktoken
import os
from datetime import datetime
import yaml
from .gpt_utils import MessagesHandler, GPT, TimeHandling
import warnings
from typing import Callable
import json
import ast

DEBUG = False

BASE_DIR = os.path.join(os.getcwd(), 'therapy')

ENCODER = tiktoken.encoding_for_model('text-davinci-003')
SERVER_PARAMETERS = yaml.safe_load(open('parameters.yaml', 'r'))  # TODO Check path


class TC:
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    RESET = '\033[0m'


def AnamnesisTooLong(anamnesis_length: int, max_length: int = 2048, loops: int = 10):
    warnings.warn(f'Anamnesis length is {anamnesis_length} tokens, which is greater than the maximum allowed length of '
                  f"{max_length} tokens, couldn't shorten it more after {loops} loops.")


def CommandNotFound(command: str, available_commands: list):
    warnings.warn(f'Command {command} not found. Available commands are: {available_commands}.'
                  f' Continuing conversation.')


def get_now():
    return datetime.now()


def get_full_time(now: datetime):
    return now.strftime('%c')


def get_hour_minute(now: datetime):
    return now.strftime('%H:%M')


def get_token(text: str):

    return len(ENCODER.encode(text))


class PromptHandler:
    def __init__(self):
        self.prompt_paths = os.path.join(BASE_DIR, 'prompts')
        self.assistant_path = os.path.join(self.prompt_paths, 'assistant')
        self.system_path = os.path.join(self.prompt_paths, 'system')
        self.prebuilt_path = os.path.join(self.prompt_paths, 'prebuilts')
        self.evidence_based_path = os.path.join(self.prompt_paths, 'evidence_based_data')

        self.prompt_type_to_path_map = {
            'assistant': self.assistant_path,
            'system': self.system_path,
            'prebuilts': self.prebuilt_path,
            'evidence_based_data': self.evidence_based_path
        }

        self.assistant_prompts = self.get_prompts(self.assistant_path)
        self.system_prompts = self.get_prompts(self.system_path)
        self.prebuilt_prompts = self.get_prompts(self.prebuilt_path)
        self.evidence_based_prompts = self.get_prompts(self.evidence_based_path)

    @staticmethod
    def get_prompts(path: str):
        return [os.path.join(BASE_DIR, path, prompt) for prompt in os.listdir(path)]

    def get_prompt(self, prompt_type: str):
        if prompt_type not in self.prompt_type_to_path_map:
            raise ValueError(f'Prompt type {prompt_type} does not exist.')

        path = self.prompt_type_to_path_map[prompt_type]

        return self.get_prompts(path)

    def get_prompt_content(self, prompt_type: str, prompt_name: str):
        if prompt_type not in self.prompt_type_to_path_map:
            raise ValueError(f'Prompt type {prompt_type} does not exist.')

        path = os.path.join(self.prompt_type_to_path_map[prompt_type], prompt_name)
        return self.get_prompt_content_from_path(path)

    @staticmethod
    def get_prompt_content_from_path(path: str):
        with open(path, 'r') as f:
            return f.read()


class Therapy(object):
    def __init__(self,
                 api_key: str,
                 model: str = 'gpt-4',
                 max_tokens_per_message: int = 8192,
                 max_token_answer: int = 2048,
                 anamnesis_length: int = 2048,
                 only_fast_model: bool = False):

        self.api_key = api_key
        self.model = model
        self.max_token_per_message = max_tokens_per_message
        self.max_token_answer = max_token_answer
        self.anamnesis_length = anamnesis_length
        self.only_fast_model = only_fast_model

        if self.only_fast_model:
            self.max_token_per_message = 4096
            self.anamnesis_length, self.max_token_answer = 1024, 1024

        self.prompter = PromptHandler()
        self.timer = TimeHandling()

        self.anamnesis = ''
        self.demand = ''

        self.user_informations = {
            'name': None,
            'age': None,
            'gender': None,
            'occupation': None,
            'language': None,
            'marital_status': None,
        }

        self.therapy_informations = {
            'type': 'not_defined',
            'guidelines': 'not_defined',
        }

        self.therapy_types = list(SERVER_PARAMETERS['available-therapies'].values())

        self.therapist_name = SERVER_PARAMETERS['therapist']['name']

        self.action_functions: dict = {
            'start_conversation': self.start_conversation,
            'ask_for_user_info': self.ask_for_user_info,
            'ask_for_demand': self.ask_for_demand,
            'continue_conversation': self.continue_conversation,
            'ask_for_evaluation': self.ask_for_evaluation,
            'choose_therapy_type': self.choose_therapy_type,
            'end_therapy': self.end_therapy,
            'present_therapy_type': self.present_therapy_type,
            'ask_primary_informations': self.ask_primary_informations,
        }

        self.action_functions_for_evaluation: dict = {
            'continue_conversation': self.continue_conversation,
            'ask_for_evaluation': self.ask_for_evaluation,
            'end_therapy': self.end_therapy,
        }

        self.user_feedbacks = {}

        self.GPT = GPT(self.api_key)

        self.MSG_Handler = MessagesHandler()

        self.conversation = []

        # Tracking the interview process

        self.conversation_started = False
        self.user_demand_asked_once = False
        self.user_info_asked = False
        self.demand_asked = False
        self.therapy_type_chosen = False
        self.therapy_ended = False
        self.anamnesis_initiated = False
        self.next_move_ask_evaluation = False
        self.passed_user_name = False
        self.anamnesis_rebuild_count = 0

    def get_parameters(self):

        parameters = {
            'api_key': self.api_key,
            'model': self.model,
            'max_tokens_per_message': self.max_token_per_message,
            'max_token_answer': self.max_token_answer,
            'anamnesis_length': self.anamnesis_length,
            'only_fast_model': self.only_fast_model,
            'user_informations': self.user_informations,
            'therapy_informations': self.therapy_informations,
            'therapy_types': self.therapy_types,
            'user_feedbacks': self.user_feedbacks,
            'conversation': self.MSG_Handler.conversation,
            'conversation_started': self.conversation_started,
            'user_demand_asked_once': self.user_demand_asked_once,
            'user_info_asked': self.user_info_asked,
            'demand_asked': self.demand_asked,
            'therapy_type_chosen': self.therapy_type_chosen,
            'therapy_ended': self.therapy_ended,
            'anamnesis_initiated': self.anamnesis_initiated,
            'next_move_ask_evaluation': self.next_move_ask_evaluation,
            'passed_user_name': self.passed_user_name,
            'anamnesis_rebuild_count': self.anamnesis_rebuild_count,
        }

        return json.dumps(parameters)

    def update_parameters(self, parameters: str or dict):

        if isinstance(parameters, str):
            parameters = json.loads(parameters)

        self.api_key = parameters['api_key']
        self.model = parameters['model']
        self.max_token_per_message = parameters['max_tokens_per_message']
        self.max_token_answer = parameters['max_token_answer']
        self.anamnesis_length = parameters['anamnesis_length']
        self.only_fast_model = parameters['only_fast_model']
        self.user_informations = parameters['user_informations']
        self.therapy_informations = parameters['therapy_informations']
        self.therapy_types = parameters['therapy_types']
        self.user_feedbacks = parameters['user_feedbacks']
        self.MSG_Handler.conversation = parameters['conversation']
        self.conversation_started = parameters['conversation_started']
        self.user_demand_asked_once = parameters['user_demand_asked_once']
        self.user_info_asked = parameters['user_info_asked']
        self.demand_asked = parameters['demand_asked']
        self.therapy_type_chosen = parameters['therapy_type_chosen']
        self.therapy_ended = parameters['therapy_ended']
        self.anamnesis_initiated = parameters['anamnesis_initiated']
        self.next_move_ask_evaluation = parameters['next_move_ask_evaluation']
        self.passed_user_name = parameters['passed_user_name']
        self.anamnesis_rebuild_count = parameters['anamnesis_rebuild_count']

    def play_conversation(self, message) -> str or tuple:

        # Adding user message to conversation
        self.MSG_Handler.create_message(role='user',
                                        message=message,
                                        time=True,
                                        full_time=True,
                                        command='NA',
                                        update_conv=True)

        # User feedbacks
        if self.next_move_ask_evaluation:
            self.user_feedbacks[self.timer.get_full_time()] = message
            self.next_move_ask_evaluation = False

        # TODO: Thread these updates to not block the conversation
        #  Cannot thread because when the data is sent back to the api, the parameters are saved
        #  So, if the thread didn't finish yet, the data won't be saved in the parameters.
        #  A solution would be to wait for all the threads to finish before sending back the data, that would improve
        #  The speed of the app a bit but not significantly as most of the side-queries are made on the fast-model

        # Updating anamnesis
        self.anamnesis_rebuild_count += 1
        if self.anamnesis_initiated and self.anamnesis_rebuild_count >= 5:
            self.anamnesis_rebuild_count = 0
            self.continue_anamnesis()

        elif len(self.MSG_Handler) >= 8:
            self.build_anamnesis()

        # ALL THE LOGIC LIES HERE

        if self.therapy_ended:
            command = 'end_therapy'

        elif not self.conversation_started:

            command = 'start_conversation'

        elif not (self.user_info_asked and self.demand_asked):

            if self.user_demand_asked_once:
                self.check_user_info()
                self.check_demand()

            command = 'choose_therapy_type' if self.user_info_asked and self.demand_asked else\
                      'ask_primary_informations'

        elif not self.therapy_type_chosen:

            command = 'choose_therapy_type'

        else:

            command = self.evaluate_whats_next()

        if command == 'ask_for_evaluation':
            self.next_move_ask_evaluation = True

        if command == 'choose_therapy_type':
            if len(self.MSG_Handler) >= 7:
                # Don't choose therapy unless there are already 7 messages in the conversation

                self.choose_therapy_type()

                command = (
                    'present_therapy_type'
                    if self.therapy_type_chosen
                    else 'continue_conversation'
                )
            else:
                command = 'continue_conversation'

        print(TC.RED + command)
        print(TC.RESET)

        # Define next message
        next_action_func = self.response(command)

        assistant_message = next_action_func()

        # Adding assistant message to conversation
        self.MSG_Handler.create_message(role='assistant',
                                        message=assistant_message,
                                        time=True,
                                        full_time=True,
                                        command=command,
                                        update_conv=True)

        # print(TC.RED, self.user_informations['name'], self.passed_user_name)

        if isinstance(self.user_informations['name'], str) and (not self.passed_user_name):
            self.passed_user_name = True
            return assistant_message, self.user_informations['name'].split()[0]

        return assistant_message

    def build_context(self,
                      user_info: bool = True,
                      demand: bool = True,
                      anamnesis: bool = True,
                      therapy_type: bool = True,
                      user_feedbacks: bool = True,
                      therapy_guidelines: bool = True) -> str:

        context = {}

        if user_info:
            context['user_info'] = f'Client informations: {self.user_informations}'
        if demand:
            context['demand'] = f'Client demand: {self.demand}'
        if anamnesis:
            context['anamnesis'] = f'Client anamnesis: {self.anamnesis}'
        if therapy_type:
            context['therapy_type'] = f"Type of therapy: {self.therapy_informations['type']}"
        if user_feedbacks:
            context['user_feedbacks'] = f'User feedbacks: {self.user_feedbacks}'
        if therapy_guidelines:
            context['therapy_guidelines'] = f"Therapy guidelines: {self.therapy_informations['guidelines']}"

        return str(context)

    def check_user_info(self, bot_tokens_count: int = 300):

        # Query GPT with all the conversation with right prompting and add the info to self.user_informations

        # 300 is an approximation of what will be returned by the bot

        max_pass = self.max_token_per_message - bot_tokens_count
        token_count = 0

        context = self.build_context(user_info=False,
                                     demand=False,
                                     anamnesis=False,
                                     therapy_type=False,
                                     user_feedbacks=False,
                                     therapy_guidelines=False)

        system_prompt = self.prompter.get_prompt_content(prompt_type='system',
                                                         prompt_name='system_check_prompt')

        user_info_prompt = self.prompter.get_prompt_content(prompt_type='assistant',
                                                            prompt_name='user_info_inference')

        user_info_prompt = self.GPT.chain_replacement(tags=['### USER INFOS QUERY', '### CONTEXT ###'],
                                                      replacements=[str(self.user_informations), context],
                                                      content=user_info_prompt)

        token_count += self.GPT.get_token(context)
        token_count += self.GPT.get_token(system_prompt)
        token_count += self.GPT.get_token(user_info_prompt)

        # Check amount of conversation token left to add to the query
        tokens_left = max_pass - token_count

        # Get the last messages
        last_messages = self.MSG_Handler.get_last_messages(token_limit=tokens_left)

        # Convert to GPT format: not necessary but it helps save some tokens (remove meta-data)
        last_messages = self.MSG_Handler.chat_to_GPT(last_messages)

        user_info_prompt = user_info_prompt.replace('### CONVERSATION ###', str(last_messages))

        messages = [self.MSG_Handler.create_message(role='system',
                                                    message=system_prompt,
                                                    time=False,
                                                    update_conv=False),
                    self.MSG_Handler.create_message(role='user',
                                                    message=user_info_prompt,
                                                    time=False,
                                                    update_conv=False)]

        # Query GPT -> max_token = bot_tokens_count

        new_dict_user_info_str = self.GPT.query_API(messages=messages,
                                                    only_content=True,
                                                    max_tokens=bot_tokens_count,
                                                    fast_model=True)

        try:
            new_dict_user_info = ast.literal_eval(new_dict_user_info_str)

            if new_dict_user_info.keys() == self.user_informations.keys():
                self.user_informations = new_dict_user_info

        except (SyntaxError, ValueError):

            warnings.warn(f"{self.GPT.last_model_used} didn't retrieved a coherent python dictionnary:\n"
                          f"\t{new_dict_user_info_str}")

        self.user_info_asked = all(self.user_informations.values())

    def evaluate_whats_next(self):

        system_prompt = self.prompter.get_prompt_content(prompt_type='system',
                                                         prompt_name='system_check_prompt')

        action_prompt = self.prompter.get_prompt_content(prompt_type='assistant',
                                                         prompt_name='action_type_inference')

        context = self.build_context()

        action_list_dict = dict(enumerate(self.action_functions_for_evaluation.keys()))

        action_prompt = self.GPT.chain_replacement(tags=['### CONTEXT ###', '### ACTIONS LIST ###'],
                                                   replacements=[context, str(action_list_dict)],
                                                   content=action_prompt)

        messages = [self.MSG_Handler.create_message(role='system',
                                                    message=system_prompt,
                                                    time=False,
                                                    update_conv=False),
                    self.MSG_Handler.create_message(role='user',
                                                    message=action_prompt,
                                                    time=False,
                                                    update_conv=False)]

        action_type_code = self.GPT.query_API(messages=messages, only_content=True, max_tokens=10,
                                              fast_model=self.only_fast_model)[0]

        # 3 is the default action if GPT couldn't solve the prompt properly --> continue conversation
        action_type_code = int(action_type_code) if action_type_code.isdigit() else 0

        return action_list_dict[action_type_code]

    def continue_anamnesis(self):

        # TODO: Potentially correct anamnesis

        system_prompt = self.prompter.get_prompt_content(prompt_type='system',
                                                         prompt_name='system_check_prompt')

        summarizer_prompt = self.prompter.get_prompt_content(prompt_type='assistant',
                                                             prompt_name='anamnesis_continuation_prompt')

        replacements = {'### ANAMNESIS ###': self.anamnesis,
                        '### CONTEXT ###': self.build_context()}

        summarizer_prompt = self.GPT.chain_replacement(tags=list(replacements.keys()),
                                                       replacements=list(replacements.values()),
                                                       content=summarizer_prompt)

        messages = [self.MSG_Handler.create_message(role='system',
                                                    message=system_prompt,
                                                    time=False,
                                                    update_conv=False),
                    self.MSG_Handler.create_message(role='user',
                                                    message=summarizer_prompt,
                                                    time=False,
                                                    update_conv=False)]

        anamnesis_continuation = self.GPT.query_API(messages=messages, only_content=True,
                                                    fast_model=self.only_fast_model)

        # Check anamnesis length
        potential_anamnesis = self.anamnesis + anamnesis_continuation

        def summarize_anamnesis(anamnesis: str, max_loop: int = 10) -> str:

            """
            Hard pass summarizer, might change later as it is not the best way to do it -- check vector database later
            :param anamnesis:
            :param max_loop: The maximum queries to GPT-4 to summarize the anamnesis
            :return:
            """

            anamnesis = self.GPT.summarize(content=anamnesis,
                                           target_tokens=self.anamnesis_length,
                                           max_loop=max_loop,
                                           return_process=False)

            if get_token(anamnesis) > self.anamnesis_length:
                # warning and pass

                AnamnesisTooLong(anamnesis_length=get_token(anamnesis),
                                 max_length=self.anamnesis_length,
                                 loops=max_loop)

            return anamnesis

        if get_token(potential_anamnesis) > self.anamnesis_length:
            self.anamnesis = summarize_anamnesis(potential_anamnesis, max_loop=10)
        else:
            self.anamnesis = potential_anamnesis

    def response(self, command) -> Callable:

        for action, function in self.action_functions.items():
            if command == action:
                return function

        # Raise a warning if command not found
        CommandNotFound(command=command, available_commands=list(self.action_functions.keys()))

        return self.continue_conversation

    def start_conversation(self) -> str:

        """
        Return the prompt "as is" - without paraphrasing, as we don't have context yet, to start the conversation
        """

        self.conversation_started = True

        return self.prompter.get_prompt_content(prompt_type='prebuilts',
                                                prompt_name='start_conversation').replace('xxx', self.therapist_name)

    def ask_primary_informations(self) -> str:

        base_prompt = self.prompter.get_prompt_content(prompt_type='prebuilts',
                                                       prompt_name='ask_primary_informations')

        info_query = self.prompter.get_prompt_content(prompt_type='prebuilts',
                                                      prompt_name='information_query')

        info_query_dict = json.loads(info_query)

        # Removing infos already known
        keys_to_delete = []
        for info in info_query_dict.keys():

            if (
                info in self.user_informations
                and self.user_informations[info] is not None
            ):
                keys_to_delete.append(info)

            if self.demand_asked and ('therapy' in info):
                keys_to_delete.append(info)

        for key in keys_to_delete:
            del info_query_dict[key]

        # Change base_prompt as user already responded once, assuming user gave at least one information
        if self.user_demand_asked_once:

            base_prompt = self.prompter.get_prompt_content(prompt_type='prebuilts',
                                                           prompt_name='continue_ask_primary_informations')

        query_string = ''.join(
            f'{i + 1}: {v}\n' for i, v in enumerate(info_query_dict.values())
        )
        base_prompt = base_prompt.replace('### INFORMATIONS QUERY ###', query_string)

        self.user_demand_asked_once = True

        return base_prompt

    def ask_for_user_info(self) -> str:

        user_info_prompt = self.prompter.get_prompt_content(prompt_type='prebuilts',
                                                            prompt_name='ask_user_info')

        user_informations_query = str(list(self.user_informations.keys()))[1:-1]

        user_info_prompt = user_info_prompt.replace('### USER INFOS QUERY ###', user_informations_query)

        return user_info_prompt

    def ask_for_demand(self) -> str:

        """
        Return the ask demand with context
        """

        demand_prompt = self.prompter.get_prompt_content(prompt_type='prebuilts',
                                                         prompt_name='ask_user_demand')

        return self.GPT.paraphrase(content=demand_prompt,
                                   context=self.build_context())

    def continue_conversation(self):

        # Handle the token counts between context and messages
        # Query GPT to get the following message with the right context and amount of messages
        # Return the following assistant message

        token_count = 0
        max_pass = self.max_token_per_message - self.max_token_answer

        context = self.build_context()

        token_count += self.GPT.get_token(context)

        system_prompt = self.prompter.get_prompt_content(prompt_type='system',
                                                         prompt_name='system_specialized-therapist_prompt')

        system_prompt = system_prompt.replace('### THERAPY TYPE ###', self.therapy_informations['type'])

        token_count += self.GPT.get_token(system_prompt)

        last_messages = self.MSG_Handler.get_last_messages(token_limit=max_pass - token_count)

        messages = [self.MSG_Handler.create_message(role='system',
                                                    message=system_prompt,
                                                    time=False,
                                                    update_conv=False),
                    self.MSG_Handler.create_message(role='user',
                                                    message=context,
                                                    time=False,
                                                    update_conv=False)]

        messages.extend(iter(last_messages))

        messages = self.MSG_Handler.chat_to_GPT(messages)

        return self.GPT.query_API(
            messages=messages, only_content=True, fast_model=self.only_fast_model
        )

    def ask_for_evaluation(self) -> dict:

        # Get feedback question

        system_prompt = self.prompter.get_prompt_content(prompt_type='system',
                                                         prompt_name='system_check_prompt')

        feedback_prompt = self.prompter.get_prompt_content(prompt_type='assistant',
                                                           prompt_name='get_feedback_answer')

        feedback_prompt = feedback_prompt.replace('### CONTEXT ###', self.build_context())

        messages = [self.MSG_Handler.create_message(role='system',
                                                    message=system_prompt,
                                                    time=False,
                                                    update_conv=False),
                    self.MSG_Handler.create_message(role='user',
                                                    message=feedback_prompt,
                                                    time=False,
                                                    update_conv=False)]

        return self.GPT.query_API(messages=messages, only_content=True, fast_model=self.only_fast_model)

    def choose_therapy_type(self):

        system_prompt = self.prompter.get_prompt_content(prompt_type='system',
                                                         prompt_name='system_check_prompt')

        therapy_type_prompt = self.prompter.get_prompt_content(prompt_type='assistant',
                                                               prompt_name='therapy_type_inference')

        replacements = {'### ANAMNESIS ###': self.anamnesis,
                        '### USER INFORMATIONS ###': str(self.user_informations)[1:-1],
                        '### USER DEMAND ###': self.demand,
                        '### THERAPY TRANSCRIPT ###': str(self.MSG_Handler.conversation),
                        '### THERAPY TYPES ###':
                            str(dict(zip(self.therapy_types, range(len(self.therapy_types)))))[1:-1].replace(',', '\n')
                        }

        therapy_type_prompt = self.GPT.chain_replacement(tags=list(replacements.keys()),
                                                         replacements=list(replacements.values()),
                                                         content=therapy_type_prompt)

        messages = [self.MSG_Handler.create_message(role='system',
                                                    message=system_prompt,
                                                    time=False,
                                                    update_conv=False),
                    self.MSG_Handler.create_message(role='user',
                                                    message=therapy_type_prompt,
                                                    time=False,
                                                    update_conv=False)]

        # Query GPT for therapy type

        therapy_type_code = self.GPT.query_API(messages=messages, only_content=True,
                                               max_tokens=10, fast_model=self.only_fast_model)[0]

        if therapy_type_code.isdigit():

            therapy_type = self.therapy_types[int(therapy_type_code)]

            # Get the guidelines in evidence-based data for the therapy type

            guidelines = self.prompter.get_prompt_content(prompt_type='evidence_based_data',
                                                          prompt_name=therapy_type)

            self.therapy_informations['guidelines'] = guidelines

            self.therapy_informations['type'] = therapy_type

            self.therapy_type_chosen = True

    def present_therapy_type(self):

        therapy_type = self.therapy_informations['type']

        system_prompt = self.prompter.get_prompt_content(prompt_type='system',
                                                         prompt_name='system_check_prompt')

        therapy_message_prompt = self.prompter.get_prompt_content(prompt_type='assistant',
                                                                  prompt_name='present_therapy_type')

        therapy_message_prompt = self.GPT.chain_replacement(tags=['### CONTEXT ###', '### THERAPY TYPE ###'],
                                                            replacements=[self.build_context(), therapy_type],
                                                            content=therapy_message_prompt)

        messages = [self.MSG_Handler.create_message(role='system',
                                                    message=system_prompt,
                                                    time=False,
                                                    update_conv=False),
                    self.MSG_Handler.create_message(role='user',
                                                    message=therapy_message_prompt,
                                                    time=False,
                                                    update_conv=False)]

        return self.GPT.query_API(messages=messages, only_content=True, fast_model=True)

    def end_therapy(self) -> str:

        if self.therapy_ended:
            return 'Therapy already ended.'

        self.therapy_ended = True

        content = self.prompter.get_prompt_content(prompt_type='prebuilts',
                                                   prompt_name='end_therapy')

        return self.GPT.paraphrase(content=content,
                                   context=self.build_context())

    def check_demand(self) -> str:

        system_prompt = self.prompter.get_prompt_content(prompt_type='system',
                                                         prompt_name='system_check_prompt')

        check_demand_prompt = self.prompter.get_prompt_content(prompt_type='assistant',
                                                               prompt_name='check_user_demand')

        context = self.build_context()

        transcript = self.MSG_Handler.conversation
        transcript = f'{context}\nTranscription: {str(self.MSG_Handler.chat_to_GPT(transcript))}'

        check_demand_prompt = check_demand_prompt.replace('### CONTEXT ###', transcript)

        messages = [self.MSG_Handler.create_message(role='system',
                                                    message=system_prompt,
                                                    time=False,
                                                    update_conv=False),
                    self.MSG_Handler.create_message(role='user',
                                                    message=check_demand_prompt,
                                                    time=False,
                                                    update_conv=False)]

        # Query GPT for demand

        # Demand check bugs a lot on GPT-3.5, change to smart-model not fast-model

        demand = self.GPT.query_API(messages=messages, only_content=True, fast_model=self.only_fast_model)

        if demand[0] != '0':
            self.demand_asked = True
        else:
            self.demand = demand

        return self.demand

    def store_informations(self, message: str, role: str, time: str, command: str) -> None:

        self.conversation.append({'role': role, 'message': message, 'time': time, 'command': command})

    def build_anamnesis(self) -> str:

        """
        Build anamnesis from the whole context
        :return:
        """

        system_prompt = self.prompter.get_prompt_content(prompt_type='system',
                                                         prompt_name='system_check_prompt')

        anamnesis_prompt = self.prompter.get_prompt_content(prompt_type='assistant',
                                                            prompt_name='build_anamnesis')

        anamnesis_prompt = anamnesis_prompt.replace('### CONTEXT ###', self.build_context())

        messages = [self.MSG_Handler.create_message(role='system',
                                                    message=system_prompt,
                                                    time=False,
                                                    update_conv=False),
                    self.MSG_Handler.create_message(role='user',
                                                    message=anamnesis_prompt,
                                                    time=False,
                                                    update_conv=False)]

        return self.GPT.query_API(messages=messages, only_content=True, fast_model=self.only_fast_model)
