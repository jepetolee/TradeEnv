# TradeEnv
 Reinforcement Learning Enviroment with Binance API Future Options
 
 ## awesome functions
 In future Options, you'll need to risk taking a lot (on leverage 100X you can bankrupt only 1%!!!!)
 you can restrict your lose percentage by using finisher()!!! 
 
 
## How to Use it
 1. install all requirements
 2. clone this repo and move it your projects file

### examples
```
from ScalpingEnv.agent import FutureAgent

agent = FutureAgent(api_key="",api_secret="",test=True)

current_price = agent.check_current()

print(agent.percent())
```

### requirements
```
pandas 1.3.5
python-binance 0.3.1
```
