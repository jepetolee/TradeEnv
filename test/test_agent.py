from ScalpingEnv.agent import FutureAgent
from pandas import DataFrame

agent = FutureAgent(api_key="",
                    api_secret="")

print(agent.select_symbol('XRPUSDT'))
print(agent.check_current())
print(agent.callable_usdt())
agent.change_leverage(7)
agent.define_TPSL(agent.current_price + 0.01, agent.current_price - 0.01)
agent.step([agent.current_price, 'SELL', int(agent.order_able())])
orders = agent.agent.futures_get_all_orders(symbol=agent.symbol)
print(orders[-3])
print(orders[-2])
print(orders[-1])
agent.shutdown = True
# print(agent.order_able())
agent.safe_shutdown()
# agent.safe_shutdown(reversed_once=True)
orders2 = agent.agent.futures_account_trades()
print(orders2[-1])
