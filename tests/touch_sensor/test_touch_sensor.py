import json
import tempfile
import time
from typing import Generator, Tuple
from unittest.mock import call, MagicMock, mock_open, patch

import pytest

from src.touch_sensor.touch_sensor import TouchSensor


DEBOUNCE_TIME = 0.001  # Time in seconds


@pytest.fixture
def touch_sensor() -> Generator[TouchSensor, None, None]:
    """Fixture to provide a TouchSensor instance for testing.
    
    This fixture creates a named temporary file to simulate a FIFO file
    used by the TouchSensor instance for inter-process communication.
    
    Yields:
        A TouchSensor instance initialized with a temporary FIFO path and
        a specified debounce time.
    """
    with tempfile.NamedTemporaryFile() as tmp_fifo:
        screen_pipe_path = str(tmp_fifo.name)
        yield TouchSensor(
            debounce=DEBOUNCE_TIME, 
            screen_pipe_path=screen_pipe_path, 
            cloud_db_pipe_path=''  # TODO: Change when testing cloud DB
        )


class TestDebounceBehavior:
    """Test suite for testing the debounce behavior of the TouchSensor."""

    @pytest.fixture(params=[
        (0.0, False), 
        (DEBOUNCE_TIME - 0.0001, False), 
        (DEBOUNCE_TIME, True), 
        (DEBOUNCE_TIME + 0.0001, True)
    ])
    def test_values(self, request) -> Tuple[float, bool]:
        """Parameterized fixture providing test values for debounce tests.
        
        Args:
            request: The fixture request object provided by pytest.
            
        Returns:
            A tuple containing a wait time and the expected result of a tap
            after that wait time.
        """
        return request.param

    def test_basic_debounce_behavior(
        self, 
        touch_sensor: TouchSensor, 
        test_values: Tuple[float, bool]
    ) -> None:
        """Tests that a tap is registered or ignored according to the debounce logic.
        
        Args:
            touch_sensor: The TouchSensor fixture for testing.
            test_values: A tuple of wait time and expected boolean result.
        """
        wait_time, expected = test_values
        touch_sensor.tap()
        time.sleep(wait_time)
        assert touch_sensor.tap() == expected

    def test_reset_debounce_time_behavior(
        self, 
        touch_sensor: TouchSensor, 
        test_values: Tuple[float, bool]
    ) -> None:
        """Tests the reset of the debounce timer when a tap is registered.
                
        Args:
            touch_sensor: The TouchSensor fixture for testing.
            test_values: A tuple of wait time and expected boolean result.
        """
        wait_time, expected = test_values
        touch_sensor.tap()
        touch_sensor.tap()  # Debounce timer reset
        time.sleep(wait_time)
        assert touch_sensor.tap() == expected


class TestSendingRequestToScreenPipe:
    """Test suite for testing the communication of the TouchSensor with the screen pipe."""

    @pytest.fixture
    def mock_fifo(self) -> MagicMock:
        """Fixture that provides a mock file object for simulating FIFO file operations.

        Returns:
            A MagicMock instance simulating a file object.
        """
        return mock_open()

    @pytest.mark.parametrize('type', [('success'), ('failure')])
    def test_sending_single_tap_to_screen_pipe(
        self, 
        type: str, 
        mock_fifo: MagicMock, 
        touch_sensor: TouchSensor
    ) -> None:
        """Tests the TouchSensor's ability to send a single tap event to the screen pipe.

        This test verifies that the TouchSensor correctly formats and sends tap data 
        based on the given type (success or failure) to the screen pipe.

        Args:
            type: The type of tap event to send, can be 'success' or 'failure'.
            mock_fifo: The mock file object fixture for intercepting file operations.
            touch_sensor: The TouchSensor instance used for testing.
        """
        sample_data = {
            'type': type, 
            'data': {
                'timestamp': time.strftime('%Y-%m-%dT%X', time.gmtime(0))
            }
        }
        
        with patch('src.touch_sensor.touch_sensor.open', mock_fifo):
            touch_sensor.pipe_data_to_screen(type, time.gmtime(0))
            mock_fifo().write.assert_called_once_with(json.dumps(sample_data))

    def test_rapid_succesive_taps(
        self, 
        mock_fifo: MagicMock, 
        touch_sensor: TouchSensor
    ) -> None:
        """Tests the TouchSensor's handling of rapid successive tap events.

        This test simulates rapid taps and checks if each tap event is being sent
        to the screen pipe in the correct order without missing any events.

        Args:
            mock_fifo: The mock file object fixture for intercepting file operations.
            touch_sensor: The TouchSensor instance used for testing.
        """
        with patch('src.touch_sensor.touch_sensor.open', mock_fifo):
            n = 10

            # Simulate 10 rapid taps
            for i in range(n):
                touch_sensor.pipe_data_to_screen('success', time.gmtime(i))

            expected_calls = []
            for i in range(n):
                sample_tap_data = json.dumps(
                    {
                        'type': 'success',
                        'data': {
                            'timestamp': time.strftime('%Y-%m-%dT%X', time.gmtime(i))
                        }
                    }
                )
                expected_calls.append(call().write(sample_tap_data))
            
            mock_fifo.assert_has_calls(expected_calls, any_order=False)