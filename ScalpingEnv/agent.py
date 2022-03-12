from binance.client import Client, BaseClient
from pandas import DataFrame
from time import sleep
from binance.exceptions import BinanceAPIException


class FutureAgent:
    def __init__(self, api_key, api_secret, test=False):

        self.agent = Client(api_key=api_key, api_secret=api_secret)

        self.leverage = 1
        # 현재 잔고 조회
        self.withdrawAvailable = 1
        self.shutdown = False
        self.time_steps = 0
        self.position = 'SELL'

        self.symbol = 'BTCUSDT'

        # 현재 내가 진입한 포지션 가격
        self.position_price = 1
        # 지금 내가 들고 있는 개수
        self.quantity = 0
        # 현재가
        self.current_price = 1
        # 내가 지정한 종료가
        self.stop_price = 38000

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
            print("Agent: 호가창 조회 에러!-" + e)
            self.safe_shutdown()
            return

    # 안전하게 현물로 포지션 종결가 체결
    def safe_shutdown(self, reversed_once=False):
        if self.shutdown is True:

            try:
                if not reversed_once:
                    self.reverse_position()
                self.agent.futures_cancel_all_open_orders(symbol=self.symbol)
                if self.time_steps != 0:
                    self.agent.futures_create_order(symbol=self.symbol, side=self.position,
                                                    stopPrice=self.stop_price, closePosition='true',
                                                    type=BaseClient.FUTURE_ORDER_TYPE_LIMIT)
                    sleep(0.75)
                    checker = self.agent.futures_get_all_orders()

                    if checker[-1]['status'] == 'NEW':
                        self.force_close_position()

                print("Agent: 셧다운이 감지되었습니다. 모든 포지션을 빠르게 종료해 손실을 차단했습니다.")

            except BinanceAPIException as e:
                print(e)
        else:
            print("Agent: DEADLY_ERROR!!! You Need to Close Your Position By Direct Immediately")
        return

    # 해당 모델의 손해가 지정 %가 넘어버렸을 경우 재빠르게 종료
    def finisher(self, percent=-5):
        if self.percent() <= percent:
            self.force_close_position()
        return

    # 강제로 마켓을 써서 포지션 종료
    def force_close_position(self, error_times=0):
        try:
            self.agent.futures_create_order(symbol=self.symbol, side=self.position,
                                            closePosition='true', stopPrice=self.current_price,
                                            type=BaseClient.FUTURE_ORDER_TYPE_STOP_MARKET, amount=self.quantity)
            self.safe_shutdown(reversed_once=True)
        except BinanceAPIException as e:
            print("마진콜 오류! 빠르게 다시 포지션 종료를 시도합니다." + str(e))

            if error_times >= 10:
                self.shutdown = True
                print("Agent: 이런! 심각한 마진콜 오류입니다. 빠르게 안전한 셧다운을 시도하겠습니다.")
                self.safe_shutdown()
            else:
                self.force_close_position(error_times=error_times + 1)

        return

    # 에이전트 스탭
    def step(self, position, retry=False):
        if position['side'] == 'holding':
            return 0
        else:
            try:

                self.agent.futures_cancel_all_open_orders()
                self.agent.futures_create_order(position)
                self.position = position['side']
                self.position_price = position['price']
                self.quantity = position['origQty']  # !!!! 이게 진짜 갯순지 셀필요 있음
                self.time_steps += 1
                self.order_able()
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
    def define_stop_price(self, stop_position):
        self.stop_price = stop_position
        return

    # 레버리지 변경
    def change_leverage(self, leverage):
        self.leverage = leverage
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

    # 묶여있지 않고 부를 수 있는금액 !!!!! api 확인해서 넣어두기
    def callable_usdt(self):
        self.check_account()
        return self.withdrawAvailable

    # 주문 가능 총량 !!!!!!! 이거 함수 있나 체크 필요
    def order_able(self):
        self.check_current()
        self.check_account()
        return self.leverage * self.callable_usdt() / self.current_price - 1e-2  # 주문오류 방지를 위한 극소량차감
