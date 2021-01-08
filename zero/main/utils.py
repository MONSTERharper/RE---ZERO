from kivy.app import App
from kivy.uix.widget import Widget


def init_widget(widget: Widget) -> None:
    """
    Initializes a kivy widget with some standard members.

    :param widget: The widget to initialize.
    :return:
    """
    widget.app = App.get_running_app()
    widget.screen = widget.app.root.current_screen