import openai
import paho.mqtt.client as mqtt
import requests
import os
import json
from dotenv import load_dotenv
from langchain import LlamaCpp, LLMChain, PromptTemplate
from langchain.agents import ZeroShotAgent, AgentExecutor

load_dotenv()
import threading
import time
import setproctitle

prompt_history = []

class localLangChain:
    agent_chain = None
    # functions
    from langchain.agents import Tool
    from langchain.tools import DuckDuckGoSearchRun
    search = DuckDuckGoSearchRun()
    # def search(query):
    #     print("searching for", query)
    #     return "the creator is Jan Lunge, a software engineer from Germany"
    #
    def getTime(query):
        print("getting time", query)
        return time.strftime("%H:%M:%S", time.localtime())
    def remember(query):
        print("remembering", query)
        return "you will remember " + query

    tools = [
        Tool(
            name="Remember",
            func=remember,
            description="useful for when you need to remember something"
        ),
        Tool(
            name="Current Search",
            func=search,
            description="useful for when you need to answer questions about current events or the current state of the world"
        ),
        Tool(
            name="time",
            func=getTime,
            description="useful for getting the current time"
        ),
    ]
    # modes
    # simple = LLMChain with prompt template and memory
    # advanced = LLMAgent with tools history and memory
    # and select between local model and OpenAI
    from langchain.memory import ConversationBufferMemory
    memory = ConversationBufferMemory(memory_key="chat_history")
    mode = os.getenv('AI_MODE')
    provider = os.getenv("AI_PROVIDER")
    from langchain import OpenAI
    if provider == "local":
        print("local mode")
        llm = LlamaCpp(model_path="./models/" + os.getenv('MODEL_PATH'), verbose=False)
    else:
        print("openai mode")
        llm = OpenAI(temperature=0)
    # TODO: local history does not use the same template as the local model HUMAN/AI vs USER/ASSISTANT
    if(mode == "simple"):
        print("simple mode")
        from langchain.callbacks.manager import CallbackManager
        from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
        callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
        callback_manager = callback_manager
        prompt = PromptTemplate(template="""
{chat_history}
USER: {input}
ASSISTANT:
""", input_variables=["input", "chat_history"])
        llm_chain = LLMChain(prompt=prompt, llm=llm, verbose=True, memory=memory)
        agent_chain = llm_chain
    elif(mode == "agent"):
        print("agent mode")
        from langchain.agents import AgentType
        from langchain.agents import initialize_agent
        suffix = """Begin
        {chat_history}
        Question: {input}
        {agent_scratchpad}"""  # Let's work this out in a step by step way to be sure we have the right answer.!
        prefix = """Have a conversation with a human, answering the following questions as best you can. Most human tasks dont require tools like remembering or answering, You have access to the following tools:"""
        prompt = ZeroShotAgent.create_prompt(
            tools,
            prefix=prefix,
            suffix=suffix,
            input_variables=["input", "chat_history", "agent_scratchpad"],
        )

        # agent = ZeroShotAgent(llm_chain=llm_chain, tools=tools, verbose=True)
        # agent_chain = AgentExecutor.from_agent_and_tools(
        #    agent=agent, tools=tools, verbose=True, memory=memory
        # )
    # llm_chain.run(question)
        agent_chain = initialize_agent(tools, llm, agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION, verbose=True,
                                       memory=memory)

def run():
    def generatePrompt(text):
        prompt = ""
        max_items = 3  # Maximum number of items to take from prompt history
        items_to_take = min(max_items, len(prompt_history))

        items_taken = prompt_history[-items_to_take:]
        print("history used:", items_taken)
        for i in items_taken:
            prompt += "USER: " + i["user"] + " ASSISTANT: " + i["assistant"] + "\n"
        prompt += "USER: " + text + " ASSISTANT:"
        print(prompt)
        return prompt

    def computeLocal(text):
        # import fastchat
        # fastchat.load_model()
        agent_chain = localLangChain.agent_chain
        result = agent_chain.run(input=text)
        print(result)
        return result
        prompt = generatePrompt(text)
        output = llm(prompt, max_tokens=200, stop=["USER:", "\n"])
        response = output['choices'][0]["text"]
        print(response)
        prompt_history.append({"user":text, "assistant":response})
        return response

    def compute_OpenAI(text):
        openai.api_key = os.getenv('OPENAI_API_KEY')
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a homeassistant please, answer in one sentence and keep things short."
                    # generateProompt(goal, history)
                },
                {
                    "role": "system",
                    "content": text  # generateProompt(goal, history)
                },
            ],
            temperature=0.5,
            max_tokens=1000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            n=1,
            stop=["\nUser:"],
        )

        bot_response = response["choices"][0]["message"]["content"]
        return bot_response
    # Set OpenAI API credentials
    setproctitle.setproctitle('Orbit-Module AI')

    # MQTT broker information
    mqtt_broker = os.getenv('MQTT_BROKER')
    mqtt_port = int(os.getenv('MQTT_PORT'))
    mqtt_topic = "speech_detected"

    def timer_function(duration):
        duration = int(duration)
        print('timer runs', duration)
        time.sleep(duration)
        print('timer done')

    commands = {
        'timer': timer_function,
    }

    # Pre-prompt for calling external APIs
    def generateProompt(goal, history):
        return f"""You are Atlas, a home assistant
    CONSTRAINTS:

    1. If you are unsure how you previously did something or want to recall past events, thinking about similar events will help you remember.
    2. minimal user assistance, if you did not find relevant information after searching the files you can ask the user. do not ask for approval.
    3. Exclusively use the commands listed in double quotes e.g. "command name"
    4. Check with the provided history of your current executed actions if your goal has already archived, if so run the command "task_complete" with the reason "goal already archived"


    COMMANDS:

    - set timer: "timer", args: "duration": "<duration in seconds>"
    - wait for trigger to happen: "wait"
    - Task Complete (Shutdown): "task_complete", args: "reason": "<reason>"

    PERFORMANCE EVALUATION:

    1. Continuously review and analyze your actions to ensure you are performing to the best of your abilities. 
    2. Constructively self-criticize your big-picture behavior constantly.
    3. Reflect on past decisions and strategies to refine your approach.
    4. Every command has a cost, so be smart and efficient. Aim to complete tasks in the least number of steps.

    You should only respond in JSON format as described below

    RESPONSE FORMAT:
    {{
        "thoughts":
        {{
            "text": "thought",
            "reasoning": "reasoning",
            "plan": "- short bulleted\n- list that conveys\n- long-term plan",
            "criticism": "constructive self-criticism",
            "speak": "thoughts summary to say to user", 
            "current_step": "next command summary written as if it is aleady done"
        }},
        "command": {{
            "name": "command name",
            "args":{{
                "arg name": "value"
            }}
        }}
    }}

    Ensure the response can be parsed by Python json.loads


    GOAL:
    {goal}

    HISTORY:
    {history}

    Determine which next command to use, and respond using the format specified above:"""

    # Initialize MQTT client
    mqtt_client = mqtt.Client()

    # Define callback function for MQTT client to process incoming messages
    def on_message(client, userdata, message):
        # Get the text from the incoming MQTT message
        text = message.payload.decode()
        print("User Input for AI: {}".format(text))
        if text.strip() == "":
            return
        history = ""
        ended = False
        maxIterations = 2
        currentIteration = 0
        # Generate a response using OpenAI's GPT-3 model
        # while not ended and currentIteration < maxIterations:
        currentIteration += 1
        goal = text
        #print("proompt:", generateProompt(goal, history))

        provider = os.getenv("AI_PROVIDER")
        # response = ""
        # if(provider == "openai"):
        #     response = compute_OpenAI(text)
        # elif(provider == "local"):
        response = computeLocal(text)
        print("AI response:", response)
            #bot_response = json.loads(bot_response)
            #print("Bot's response:", json.dumps(bot_response, indent=2))
            # final bot response
        mqtt_client.publish("assistant_response", response)
            # if bot_response['command']['name'] == "task_complete":
            #     ended = True
            # else:
            #     # run the command and get the output
            #     if bot_response['command']['name'] in commands:
            #         command = commands[bot_response['command']['name']](bot_response['command']['args']['duration'])
            #     # run it in a seperate thread
            #     my_thread = threading.Thread(target=command)
            #     my_thread.start()
            #     # my_thread.join()
            #     command_output = "done"
            #     # add command output to history
            #     history += "\n"+ bot_response['thoughts']['current_step'] + command_output



    # Connect to MQTT broker and subscribe to topic
    mqtt_client.connect(mqtt_broker, mqtt_port)
    mqtt_client.subscribe(mqtt_topic)

    # Set MQTT client's message callback function
    mqtt_client.on_message = on_message

    print('✅ AI waiting for recognized text')
    # Start MQTT client loop to listen for messages
    mqtt_client.loop_forever()

if __name__ == "__main__":
    run()