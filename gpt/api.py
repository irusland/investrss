from slyme import SlymeDriver
import time


def main():
    slyme = SlymeDriver(pfname="Default")
    time.sleep(5)
    # driver.implicitly_wait() doesn't account for element loading
    # - attempting to instantly access elements may result in a StaleElement error

    # perform actions
    slyme.select_latest_chat()
    # ...
