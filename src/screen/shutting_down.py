import time
import sys
import os
import logging

from src.screen.screen import Screen
from src.utils.screen_utils import get_image_center
from src.utils.paths import PROJECT_DIR

logging.config.fileConfig(f"{PROJECT_DIR}/config/logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(os.path.basename(__file__).split('.')[0])

def draw_shutting_down(screen: Screen, time_remaining: int) -> None:
        """Draw the dashboard interface on the screen.
        
        Args:
            None

        Returns:
            None
        """
        screen.create_image(screen.dashboard_attributes.dashboard_bg_color)
        image_center = get_image_center(screen.image)
        screen.add_text(f"Shutdown in {time_remaining} seconds",
                      image_center,
                      screen.dashboard_attributes.dashboard_font_family,
                      screen.dashboard_attributes.dashboard_font_size,
                      screen.dashboard_attributes.dashboard_font_color,
                      centered=True)
        screen.draw_image()

if __name__ == '__main__':
    logger.info('Starting shutting_down.py')
    screen = Screen()
    time_remaining = 10
    while True:
        draw_shutting_down(screen, time_remaining)
        if time_remaining == 0:
            break
        time_remaining -= 1
        time.sleep(1)
    sys.exit(0)