from time import sleep
from binance.client import Client
from binance.exceptions import BinanceAPIException
from pandas import DataFrame


class FutureAgent:
    def __init__(self, api_key, api_secret, test=False):

        self.agent = Client(api_key=api_key, api_secret=api_secret, testnet=test)

        self.leverage = 1
        # 현재 잔고 조회
        self.withdrawAvailable = 1
        self.shutdown = False
        self.time_steps = 0
        self.position = 'BUY'

        self.symbol = 'BTCUSDT'

        # 현재 내가 진입한 포지션 가격
        self.position_price = 1
        # 지금 내가 들고 있는 개수
        self.quantity = 7
        # 현재가
        self.current_price = 1
        # 내가 지정한 종료가
        self.stop_price = 38000
        self.profit_price = 37000
        self.isposition = False
        self.account = 1
        self.current_percent = 1
        self.check_account()
        self.seed_money = self.account

    # 포지션 변경(내부값)
    def reverse_position(self):

        if self.position == 'SELL':
            self.position = 'BUY'
        else:
            self.position = 'SELL'

    def orderbook(self):
        try:
            return self.agent.futures_order_book(symbol=self.symbol)
        except BinanceAPIException as e:
            self.shutdown = True
            print("Agent: 호가창 조회 에러!-" + str(e))
            self.safe_shutdown()
            return

    # 안전하게 현물로 포지션 종결가 체결
    def safe_shutdown(self):

        if self.shutdown is True:
            try:

                self.agent.futures_cancel_all_open_orders(symbol=self.symbol)
                if self.isposition is True:
                    print("포지션 포착 종료중")

                    checker = self.agent.futures_get_all_orders()

                    self.agent.futures_create_order(symbol=self.symbol, side=self.position, type='MARKET',
                                                    quantity=self.quantity)
                    sleep(3)
                    self.isposition = False
                    if checker[-3]['status'] == 'NEW':
                        self.safe_shutdown()

                print("Agent: 셧다운이 감지되었습니다. 모든 포지션을 빠르게 종료해 손실을 차단했습니다.")

            except BinanceAPIException as e:
                print(e)
        else:
            print("Agent: DEADLY_ERROR!!! You Need to Close Your Position By Direct Immediately")
        return

    # 해당 모델의 손해가 지정 %가 넘어버렸을 경우 재빠르게 종료
    def finisher(self, percent=-5):
        if self.percent() <= percent:
            self.safe_shutdown()
        return

    def select_symbol(self, symbol):
        self.symbol = symbol
        return self.symbol

    # 에이전트 스탭
    def step(self, position, retry=False):

        if position[1] == 'HOLD':
            return 0
        else:
            try:
                self.agent.futures_cancel_all_open_orders(symbol=self.symbol)
                self.check_current()
                self.position = position[1]
                self.reverse_position()
                self.agent.futures_create_order(symbol=self.symbol, type='LIMIT', timeInForce='GTC',
                                                    price=position[0], side=position[1], quantity=position[2])

                self.agent.futures_create_order(symbol=self.symbol, type='STOP_MARKET', timeInForce='GTC',
                                                    stopPrice=self.stop_price, side=self.position, quantity=position[2])

                self.agent.futures_create_order(symbol=self.symbol, type='TAKE_PROFIT_MARKET',  timeInForce='GTC',
                                                stopPrice=self.profit_price, side=self.position, quantity=position[2])

                self.position_price = position[0]
                self.quantity = position[2]
                self.time_steps += 1
                self.check_account()
                self.isposition = True
                return self.percent()
            except BinanceAPIException as e:
                if retry is True:
                    print("Agent: 주문 에러 형성! 강제종료에 진입합니다." + str(e))
                    self.shutdown = True
                    self.safe_shutdown()

                    return
                else:
                    print("Agent: 주문이 안됬어요! 다시 시도해볼게요.")
                    self.step(position, retry=True)

    # 현 계좌 체크
    def check_account(self):
        try:
            account = self.agent.futures_account_balance()
            account = DataFrame.from_dict(account)

            account = account.loc[account['asset'] == 'USDT']

            self.account = float(account['balance'].values)
            self.withdrawAvailable = float(account['withdrawAvailable'].values)
        except BinanceAPIException as e:
            self.shutdown = True
            print("Agent: 계좌와 연동에 실패했습니다! api를 확인해주세요!" + str(e))
            self.safe_shutdown()
        return

    # 포지션 종료가 형성
    def define_TPSL(self, profit_position, stop_position):
        self.profit_price = profit_position
        self.stop_price = stop_position
        return

    # 레버리지 변경
    def change_leverage(self, leverage):
        self.leverage = leverage
        self.agent.futures_change_leverage(leverage=self.leverage, symbol=self.symbol)
        return

    # 순수익 측정
    def interests(self):
        return self.account - self.seed_money

    # 마진거래 채결중 현재 수익/손실 측정
    def percent(self):
        self.check_current()
        return self.leverage * (100 - 100 * (self.current_price / self.position_price))

    # 현재가 조회
    def check_current(self):
        try:
            self.current_price = float(self.agent.futures_symbol_ticker(symbol=self.symbol)['price'])
            return self.current_price

        except BinanceAPIException as e:
            print("Agent:현재가 조회 에러" + str(e))
            self.shutdown = True
            self.safe_shutdown()
            return

    # 묶여있지 않고 부를 수 있는금액
    def callable_usdt(self):
        self.check_account()
        return self.withdrawAvailable

    # 주문 가능 총량 !!!!!!! 이거 함수 있나 체크 필요
    def order_able(self):
        self.check_current()
        self.check_account()
        return self.leverage * self.account - 1e-2  # 주문오류 방지를 위한 극소량차감
