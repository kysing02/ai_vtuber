import sys
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Callable, List
from openai_adapter import OpenAIAdapter

class WorldTime:
    def __init__(self,
                 adapter: OpenAIAdapter,
                 start_time: datetime=datetime(2025, 4, 1, 0, 0), 
                 time_step: timedelta=timedelta(minutes=1.0),
                 ):
        self.adapter = adapter
        self.current_time = start_time
        self.time_step = time_step
        self.callback_schedules: List[CallbackSchedule] = []
        print(f"ワールドの時間が{start_time}に設定した")
    
    def get_time_str(self) -> str:
        return self.current_time.strftime("%Y/%m/%d %H時%M分")
    
    def proceed_time(self, steps: timedelta=None):
        if steps is None:
            steps = self.time_step
        while (steps > timedelta(0)):
            steps -= timedelta(minutes=1)
            self.current_time += timedelta(minutes=1)
            self.__check_timer()
    
    def add_timer(self, datetime: datetime, callback: Callable):
        newCallbackSchedule = CallbackSchedule(datetime=datetime, callback=callback)
        self.callback_schedules.append(newCallbackSchedule)
        self.callback_schedules.sort(key=lambda x: x.datetime)

    def __check_timer(self) -> None:
        for callback_schedule in self.callback_schedules:
            if self.current_time >= callback_schedule.datetime:
                callback_schedule.callback()
                self.callback_schedules.pop(0)
                continue
            else:
                break      

class CallbackSchedule(BaseModel):
    datetime: datetime
    callback: Callable

if __name__ == "__main__":
    worldTime = WorldTime()
    # print(worldTime.get_time_str())
    # worldTime.proceed_time(timedelta(hours=1, minutes=30))
    # print(worldTime.get_time_str())
    # worldTime.add_timer(datetime=datetime(2025, 1, 1, 1, 35), callback=lambda :print("Hello 35"))
    # worldTime.proceed_time(timedelta(minutes=25))
    # print(worldTime.get_time_str())