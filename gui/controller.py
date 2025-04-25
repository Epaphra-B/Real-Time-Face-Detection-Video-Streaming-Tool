# gui/controller.py
class Controller:
    def __init__(self):
        self.ratio = "16:9"

    def change_ratio(self, value):
        self.ratio = value
        print(f"Changed ratio to: {value}")
