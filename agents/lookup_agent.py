from langchain import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, Tool, AgentType

from tools.tools import get_url


def lookup(game_information: str) -> str:
    llm = ChatOpenAI(temperature=0, model="gpt-4")
    template = """given the Game Information {game_information} I want you to get it me a links to it's competitor games google play pages.
                        Your answer should contain only a URLs and should be separated by a comma."""
    tools_for_agent = [
        Tool(
            name="Crawl Google 4 competitors",
            func=get_url,
            description="useful for when you need get the competitor game google play page URL",
        )
    ]
    agent = initialize_agent(
        tools=tools_for_agent,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
    )
    promt_template = PromptTemplate(
        template=template, input_variables=["game_information"]
    )

    urls = agent.run(promt_template.format(game_information=game_information))
    return urls
