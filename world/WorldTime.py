from datetime import datetime, timedelta

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
                 start_time=datetime(2025, 1, 1, 0, 0), 
                 default_time_step=timedelta(minutes=1.0)):
        self.current_time = start_time
        self.default_time_step = default_time_step
        print(f"ワールドの時間が{start_time}に設定した")
    
    def get_time(self):
        return self.current_time.strftime("%Y/%m/%d %H時%M分")
    
    def proceed_time(self, steps: timedelta=None):
        if steps is None:
            steps = self.default_time_step
        self.current_time += steps

if __name__ == "__main__":
    worldTime = WorldTime.create_simulated_time()
    print(worldTime.get_time())
    worldTime.proceed_time(timedelta(hours=1, minutes=30))
    print(worldTime.get_time())