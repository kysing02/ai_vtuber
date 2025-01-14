from datetime import datetime, timedelta
from typing import Callable, List
from pydantic import BaseModel

class WorldTime:
    @staticmethod
    def create_real_time():
        return RealTime()
    @staticmethod
    def create_simulated_time():
        return SimulatedTime()

class RealTime:
    def __init__(self):
        pass
    
    def get_time(self):
        return datetime.now().strftime("%Y/%m/%d %H時%M分")

class SimulatedTime:
    def __init__(self, 
                 start_time: datetime=datetime(2025, 1, 1, 0, 0), 
                 default_time_step: timedelta=timedelta(minutes=1.0)):
        self.current_time = start_time
        self.default_time_step = default_time_step
        self.callback_schedules: List[CallbackSchedule] = []
        print(f"ワールドの時間が{start_time}に設定した")
    
    def get_time(self):
        return self.current_time.strftime("%Y/%m/%d %H時%M分")
    
    def proceed_time(self, steps: timedelta=None):
        if steps is None:
            steps = self.default_time_step
        while True:
            remaining_steps = self.__check_timer(steps)
            if remaining_steps <= timedelta(0):
                break
            self.current_time += steps
            print("Debug: " + worldTime.get_time())
    
    def add_timer(self, datetime: datetime, callback: Callable):
        newCallbackSchedule = CallbackSchedule(datetime=datetime, callback=callback)
        self.callback_schedules.append(newCallbackSchedule)
        self.callback_schedules.sort(key=lambda x: x.datetime)

    def __check_timer(self, steps: timedelta) -> timedelta:
        for callback_schedule in self.callback_schedules:
            if self.current_time >= callback_schedule.datetime:
                callback_schedule.callback()
                remaining_steps: timedelta = self.current_time + steps - callback_schedule.datetime
                return remaining_steps
            else:
                return timedelta(0)
        return timedelta(0)

class CallbackSchedule(BaseModel):
    datetime: datetime
    callback: Callable

if __name__ == "__main__":
    worldTime = WorldTime.create_simulated_time()
    print(worldTime.get_time())
    worldTime.proceed_time(timedelta(hours=1, minutes=30))
    print(worldTime.get_time())
    worldTime.add_timer(datetime=datetime(2025, 1, 1, 1, 35), callback=lambda :print("Hello 35"))
    worldTime.add_timer(datetime=datetime(2025, 1, 1, 1, 35), callback=lambda :print("Hello 50"))
    print(worldTime.get_time())
    print(worldTime.callback_schedules)