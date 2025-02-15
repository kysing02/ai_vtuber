import logging
import threading
import time
from asyncio import AbstractEventLoop
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Callable, List
from scripts.adapters.openai_adapter import OpenAIAdapter

class WorldTime:
    """
    ワールドの時間を管理するモジュール。
    タイマを設定することができる。

    スケジュールされたタスクや時間の進みは別のスレッドで処理が行われる。
    """
    def __init__(self,
                 adapter: OpenAIAdapter,
                 loop: AbstractEventLoop,
                 start_time: datetime = datetime(2025, 4, 1, 6, 0), 
                 time_step: timedelta = timedelta(minutes=1.0),
                 ):
        self.adapter = adapter
        self.callback_schedules: List[CallbackSchedule] = []
        self.current_time = start_time
        self.loop = loop
        self.time_step = time_step
        self.__proceed_time_event = threading.Event()
        self.__stop_event = threading.Event()
        
        self.__proceed_time_event.set()  # 初期状態で時間進行イベントをセットする
        logging.info(f"ワールドの時間が{start_time}に設定した")

    def proceed_time_in_background(self):
        """毎秒ごとに時間を更新する。`proceed_time()`, `pause()`, `resume()`, `stop()`で時間を制御できる。"""
        time.sleep(1)
        while not self.__stop_event.is_set():
            self.__proceed_time_event.wait()  # 時間進行イベントを待つ
            self.proceed_time(timedelta(minutes=1))
            time.sleep(1)

    def get_date_str(self) -> str:
        """ワールドの現在日付を取得する。（例：2025年4月1日）

        Returns:
            str: ワールドの現在日付（文字列）
        """
        current_time_str = self.current_time.strftime("%Y年%m月%d日")
        return current_time_str
    
    def get_time_str(self) -> str:
        """ワールドの現在時間を取得する。（例：午前12時00分）

        Returns:
            str: ワールドの現在時間（文字列）
        """
        current_time_str = self.current_time.strftime("%p%I時%M分")
        current_time_str = current_time_str.replace("AM", "午前").replace("PM", "午後")
        return current_time_str

    def proceed_time(self, steps: timedelta = None):
        """ワールドの時間を進める。

        Args:
            steps (timedelta, optional): ワールド時間をどれぐらい進むか。
            デフォールト値はNone。Noneの場合は`self.time_step`を使用する。
        """
        if steps is None:
            steps = self.time_step
        while steps > timedelta(0):
            steps -= timedelta(minutes=1)
            self.current_time += timedelta(minutes=1)
            self.__check_timer()
        logging.debug(f"現在時間：{self.get_date_str()}")

    def add_timer(self, datetime: datetime, callback: Callable):
        """指定した時間にコールバックを実行するタスクのスケジュールを追加する

        Args:
            datetime (datetime): 実行する時間
            callback (Callable): 実行する関数
        """
        newCallbackSchedule = CallbackSchedule(datetime=datetime, callback=callback)
        self.callback_schedules.append(newCallbackSchedule)
        self.callback_schedules.sort(key=lambda x: x.datetime)

    def __check_timer(self):
        """
        `CallbackSchedule`のリストをチェックし、時間になったスケジュールを実行する。
        
        `async`関数は`asyncio.run_coroutine_threadsafe()`によって実行され、
        `sync`関数は`self.loop.run_in_executor()`によって実行される。
        """
        for callback_schedule in self.callback_schedules:
            if self.current_time >= callback_schedule.datetime:
                callback = callback_schedule.callback
                if asyncio.iscoroutinefunction(callback):
                    asyncio.run_coroutine_threadsafe(callback(), self.loop)
                else:
                    self.loop.run_in_executor(None, callback)
                self.callback_schedules.pop(0)
                continue
            else:
                break

    def pause(self):
        """時間スレッドを一時停止する"""
        logging.info("時間が一時停止しました")
        self.__proceed_time_event.clear()

    def resume(self):
        """時間スレッドを再開する"""
        logging.info("時間が再開しました")
        self.__proceed_time_event.set()

    def stop(self):
        """スレッドを停止する"""
        logging.info("時間スレッドを停止しています")
        self.__stop_event.set()
        self.__proceed_time_event.set()

class CallbackSchedule(BaseModel):
    """
    時間スケジュールクラス。
    ある時間になったら、自動的に指定されたタスクが実行される。

    注意すべきことは、タスクが`WorldTime`クラスによって実行され、初期化したときに指定したループを使用する。

    """
    datetime: datetime
    callback: Callable

if __name__ == "__main__":
    import asyncio

    async def test():
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s | %(levelname)-6s | %(filename)s:%(lineno)d | %(message)s",
            datefmt="%m-%d %H:%M:%S"
        )
        world_time = WorldTime(adapter=OpenAIAdapter(), 
                               loop=asyncio.get_running_loop(), 
                               start_time=datetime(2025, 4, 1, 0, 0))
        proceed_time_thread = threading.Thread(target=world_time.proceed_time_in_background, daemon=True)
        proceed_time_thread.start()

        async def test_callback():
            print("10秒、今は：", world_time.get_date_str())

        world_time.add_timer(datetime=datetime(2025, 4, 1, 0, 10), callback=test_callback)
        world_time.add_timer(datetime=datetime(2025, 4, 1, 0, 12), callback= lambda: print("12秒、今は：", world_time.get_date_str()))
        await asyncio.sleep(5)
        world_time.pause()  # 時間を一次的に停止する
        await asyncio.sleep(5)
        world_time.resume()  # 時間を再開する
        await asyncio.sleep(5)
        world_time.proceed_time(timedelta(minutes=30))
        world_time.stop() # 時間を停止する
        input("Enterキーを押して終了する。。。\n")

    asyncio.run(test())