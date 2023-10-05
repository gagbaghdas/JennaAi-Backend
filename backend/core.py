import os

from langchain import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from ingestion import get_summary
import re


def get_prompts(text: str) -> list:
    subject = get_subject(text)
    if len(subject) == 0:
        subject = text

    print(subject)

    promt_template = """
        Given the game details {game_information} and a text excerpt {subject} from the game design document,
        generate up to four insightful SHORT prompts to explore valuable ideas later on.
        Each prompt should:
        - be as short as possible while still being relevant and insightful)
        - be relevant to text excerpt (IMPORTANT)
        - be relevant to the game details, genre and platform
        Output the prompts separated by a '###' symbol.
        """
    response_string = run_llm(promt_template, include_game_info=True, subject=subject)
    response_list = response_string.split("###")
    response_list = remove_numbering(response_list)
    return response_list


def get_ideas(text: str) -> dict:
    promt_template = """
        With the game details {game_information} and the given context {text},
        propose 1 alternative strategy to enhance the game.
         Include:
            - Description
            - Benefits 
            - Potential use cases inspired by similar games
        Output the above information in a following format:
        description: <description> ### benefits: <benefits> ### use_case: <use_case>
        """
    result_str = run_llm(promt_template, include_game_info=True, text=text)

    result_dict = {}
    for line in result_str.split("###"):
        pieces = line.split(":", 1)
        if len(pieces) == 2:
            key, value = pieces
            result_dict[key.strip()] = value.strip()
        else:
            print(f"Unexpected format: {line}")

    return result_dict


def get_best_insight(text: str, old_insight: str) -> dict:
    best_insight = get_marketing_insights(text)
    if len(best_insight) == 0:
        return {}

    prompt_template = """
        Given the game details {game_information} and the list of useful insights {best_insight},
        find the most valuable insight and return it.
        Include:
            - Insight Description
            - Benefits 
            - Use cases from similar games
            - Source EXACT link
        Output the above information in a following format:
        description: <description> ### benefits: <benefits> ### use_cases: <use_cases> ### source: <source>
        """
    result_str = run_llm(
        prompt_template, include_game_info=True, best_insight=best_insight
    )
    if len(old_insight) > 0 and not is_new_insight_differ(old_insight, result_str):
        return {}
    # Now parse the result_str into a dictionary
    result_dict = {}
    for line in result_str.split("###"):
        pieces = line.split(":", 1)
        if len(pieces) == 2:
            key, value = pieces
            result_dict[key.strip()] = value.strip()
        else:
            print(f"Unexpected format: {line}")

    return result_dict


def is_new_insight_differ(old_inights, new_insights) -> bool:
    if len(old_inights) == 0 or len(new_insights) == 0:
        return False
    prompt_template = """
        Given the old_inights {old_inights} and the new insights {new_insights} ,
        find if they have significant difference.
        If they have significant difference, return True, otherwise return False.
        """
    result_str = run_llm(
        prompt_template, old_inights=old_inights, new_insights=new_insights
    )
    return result_str == "True"


def get_marketing_insights(text: str) -> list:
    subject = get_subject(text)
    if len(subject) == 0:
        return ""

    promt_template = """
        Given the game details {game_information} and the summary {subject} from the game design document,
        generate insights by researching similar games online.
        Include:
            - Insight Description
            - Benefits 
            - Use cases from similar games
            - Source EXACT link
        Output insights separated by '###' or return an empty string if no insights are found.
        """
    return run_llm(promt_template, include_game_info=True, subject=subject)


def get_subject(text: str) -> list:
    promt_template = """
        Given the game details {game_information} and text excerpt {text} from the game design document,
        1. Identify the subject of the text excerpt.
        2. If relevant to the game details, extract key information, categorize, and summarize.
        Return an empty string if the subject is irrelevant.
        """
    return run_llm(promt_template, include_game_info=True, text=text)


def run_llm(template: str, include_game_info=False, *args, **kwargs) -> any:
    input_variables = list(kwargs.keys())

    if include_game_info:
        game_information = get_summary()
        input_variables.append("game_information")

    prompt_template = PromptTemplate(input_variables=input_variables, template=template)

    llm = ChatOpenAI(temperature=1, model="gpt-4")
    chain = LLMChain(llm=llm, prompt=prompt_template)

    if include_game_info:
        result = chain.run(game_information=game_information, **kwargs)
    else:
        result = chain.run(**kwargs)

    return result


def remove_numbering(prompts_list):
    updated_prompts = []
    for prompt in prompts_list:
        updated_prompt = re.sub(r"(?:\n|^)\d+[\.\s]*", "", prompt)
        updated_prompts.append(updated_prompt.strip())
    return updated_prompts
