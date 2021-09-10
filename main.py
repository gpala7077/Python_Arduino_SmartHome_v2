import pandas as pd
from modules.home_manager import Home
from config.configurations import house_id


def main():
    print('Starting SmartHome_v2')
    home = Home(house_id)
    home.start()
    print(home.get_status())


if __name__ == '__main__':
    main()
