import tempfile
import time
from unittest.mock import patch, mock_open

import json
import pytest

from src.touch_sensor.touch_sensor import TouchSensor

DEBOUNCE_TIME = 0.001


@pytest.fixture
def touch_sensor():
    with tempfile.NamedTemporaryFile() as tmp_fifo:
        fifo_path = tmp_fifo.name
        yield TouchSensor(debounce=DEBOUNCE_TIME, screen_pipe_path=fifo_path)


class TestDebounceBehavior:

    @pytest.fixture(params=[
        (0.0, False), 
        (DEBOUNCE_TIME - 0.0001, False), 
        (DEBOUNCE_TIME, True), 
        (DEBOUNCE_TIME + 0.0001, True)
    ])
    def test_values(self, request):
        return request.param

    def test_basic_debounce_behavior(self, touch_sensor, test_values):
        wait_time, expected = test_values
        touch_sensor.tap()
        time.sleep(wait_time)
        assert touch_sensor.tap() == expected

    def test_reset_debounce_time_behavior(self, touch_sensor, test_values):
        wait_time, expected = test_values
        touch_sensor.tap()
        touch_sensor.tap()  # Reset debounce time
        time.sleep(wait_time)
        assert touch_sensor.tap() == expected


class TestSendingRequestToScreenPipe:  

    @pytest.fixture
    def mock_fifo(self):
        return mock_open()  # Simulate file object

    @pytest.parametrize('type', [('success'), ('failure')])
    def test_sending_single_request_to_screen_pipe(self, 
                                                   type, 
                                                   mock_fifo, 
                                                   touch_sensor
    ):
        sample_data = {
            'type': type, 
            'data': {
                'timestamp': time.srtftime('%Y-%m-%dT%X', time.gmtime(0))
            }
        }
        
        # Ensures that when TouchSensor calls open, it uses the mocked version
        with patch('src.touch_sensor.touch_sensor.open', mock_fifo):
            touch_sensor.send_to_screen(type, time.gmtime(0))
            mock_fifo().write.assert_called_once_with(sample_data)