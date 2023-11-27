import time

import pytest

DEBOUNCE_TIME = 0.001


@pytest.fixture
def touch_sensor():
    return TouchSensor(debounce=DEBOUNCE_TIME)


class TestDebounceBehavior:

    @pytest.fixture(params=[
        (0.0, False), 
        (DEBOUNCE_TIME - 0.0001, False), 
        (DEBOUNCE_TIME, True), 
        (DEBOUNCE_TIME + 0.0001, True)
    ])
    def test_values(self, request: pytest.FixtureRequest):
        return request.param

    def test_basic_debounce_behavior(self, touch_sensor: Any, test_values: tuple):
        wait_time, expected = test_values
        touch_sensor.tap()
        time.sleep(wait_time)
        assert touch_sensor.tap() == expected

    def test_reset_debounce_time_behavior(self, touch_sensor: Any, test_values: tuple):
        wait_time, expected = test_values
        touch_sensor.tap()
        touch_sensor.tap()  # Reset debounce time
        time.sleep(wait_time)
        assert touch_sensor.tap() == expected
