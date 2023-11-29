import tempfile
import time
from unittest.mock import patch, mock_open, call

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
    def test_sending_single_tao_to_screen_pipe(self, 
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

    def test_rapid_succesive_taps(self, mock_fifo, touch_sensor):
        with patch('src.touch_sensor.touch_sensor.open', mock_fifo):
            for i in range(10):  # Simulate 10 rapid taps
                touch_sensor.send_to_screen('success', time.gmtime(i))

            # Generate expected calls
            expected_calls = []
            for i in range(10):
                sample_tap_data = json.dumps(
                    {
                        'type': 'success',
                        'data': {
                            'timestamp': time.strftime('%Y-%m-%dT%X', time.gmtime(i))
                        }
                    }
                )
                expected_calls.append(call().write(sample_tap_data))
            
            # Check correctness of written data
            mock_fifo.assert_has_calls(expected_calls, any_order=False)

    # TODO: Test max FIFO capacity reached
    def test_handling_full_buffer_error():
        pass

    # TODO: Test not being able to write to FIFO due to permission issues
    def test_write_failure_due_to_permission_issues():
        pass

    # TODO: Test FIFO path not found
    def test_handling_file_not_found_error():
        pass

    # TODO: Test unexpected system shutdown
    def test_unexpected_system_shutdown():
        pass