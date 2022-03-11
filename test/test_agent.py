from ScalpingEnv.agent import FutureAgent

agent = FutureAgent(api_key="",api_secret="",test=True)

#current_price = agent.check_current()

print(agent.percent())
