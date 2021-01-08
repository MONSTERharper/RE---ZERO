from typing import *
import json
import threading

from kivy.input import MotionEvent
from kivy.logger import Logger
from kivy.properties import BooleanProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.label import Label
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.screenmanager import Screen
from kivy.uix.settings import SettingsWithTabbedPanel

from zero.common.ai import AI
from zero.common.adventure import Adventure
from zero.main.utils import init_widget
from zero.common.utils import *


class SelectableRecycleBoxLayout(
    FocusBehavior,
    LayoutSelectionBehavior,
    RecycleBoxLayout
):
    """
    Adds selection and focus behaviour to the view.
    """


class SelectableLabel(RecycleDataViewBehavior, Label):
    """
    Adds selection support to the label.
    """
    index: Optional[int] = None
    selected: BooleanProperty = BooleanProperty(False)
    selectable: BooleanProperty = BooleanProperty(True)

    def __init__(self, **kwargs):
        super(SelectableLabel, self).__init__(**kwargs)
        init_widget(self)

    def refresh_view_attrs(self, rv: Any, index: Any, data: Any) -> None:
        """
        Catch and handle the view changes.

        :param rv: The recycle view.
        :param index: The index of this label.
        :param data: The data.
        """
        self.index = index
        super(SelectableLabel, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch: MotionEvent) -> bool:
        """
        Triggered on a touch/mouse press event.

        :param touch: The touch event sent by kivy.
        :return: `True` if there is a touch, `False` otherwise.
        """
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected) -> None:
        """
        Respond to the selection of items in the view.

        :param rv: The recycle view.
        :param index: The index of this label.
        :param is_selected: Whether it is selected or not.
        """
        self.selected = is_selected


class SelectableModelLabel(SelectableLabel):
    """
    Specific implementation of SelectableLabel for the select model menu.
    """
    def apply_selection(self, rv, index, is_selected) -> None:
        super(SelectableModelLabel, self).apply_selection(rv, index, is_selected)
        if is_selected:
            self.screen.on_model_selected(self.text)


class SelectableGameLabel(SelectableLabel):
    """
    Specific implementation of SelectableLabel for the load adventure menu.
    """
    def apply_selection(self, rv, index, is_selected) -> None:
        super(SelectableGameLabel, self).apply_selection(rv, index, is_selected)
        if is_selected:
            self.screen.on_game_selected(self.text)


class MenuScreen(Screen):
    """
    The main menu screen.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from zero.main.app import App
        self.app: App = App.get_running_app()
        self.savefiles: Dict[str, Dict[str, Any]] = {}
        self.selected_model: Optional[str] = None
        self.selected_savefile: Optional[str] = None
        self.init_settings()

    def init_settings(self) -> None:
        """
        Initializes the settings tab  using the default kivy implementation.
        """
        settings = SettingsWithTabbedPanel()
        # this is to remove the unecessary close button
        settings.children[0].remove_widget(settings.children[0].children[0])
        settings.add_json_panel('General', self.app.config, 'zero/main/ui/settings/general.json')
        settings.add_json_panel('AI', self.app.config, 'zero/main/ui/settings/ai.json')
        #self.ids.tab_settings.add_widget(settings)

    def on_enter(self):
        """
        Called upon entering this screen.
        """
        self.app.adventure = Adventure()
        self.init_models()
        self.init_saves()
        self.update_button_start_new()
        self.update_button_start_load()

    def on_update(self):
        """
        Updates all core UI elements on this screen.
        """
        self.update_button_start_new()
        self.update_button_start_load()

    def update_status_text(self, text: str) -> None:
        self.ids.status_text_model.text = \
            self.ids.status_text_new.text = \
            self.ids.status_text_load.text = text

    """
    AI MODEL TAB
    """

    def init_models(self) -> None:
        """
        Fetches the models available for selection and loading.
        """
        self.ids.view_model.data = [{'text': str(m)} for m in self.app.get_valid_models()]

    def load_ai(self) -> None:
        """
        Loads the currently selected AI model.
        """
        threading.Thread(target=self._load_ai_thread).start()

    def on_model_selected(self, model) -> None:
        """
        Selects (but does not load) a given AI model by its name.

        :param model: The name of the model to select.
        """
        self.selected_model = model
        self.ids.button_load_model.disabled = False
        self.on_update()

    def _load_ai_thread(self) -> None:
        """
        Internal thread for loading an AI model so that the main thread isn't blocked.
        """
        self.ids.button_load_model.disabled = True
        model_path = self.app.get_model_path(self.selected_model)
        model_name = os.path.split(model_path)[-1]
        try:
            self.update_status_text(f'Loading Model "{model_name}"')
            Logger.info(f'AI: Loading model at "{model_path}"')
            self.app.ai = None
            self.app.ai = AI(model_path)
            Logger.info(f'AI: Model loaded at "{model_path}"')
        except Exception as e:
            self.app.ai = None
            self.update_status_text(f'Error Loading Model "{model_name}"')
        else:
            self.update_status_text(f'Loaded Model: {model_name} ')
        self.on_update()

    """   
    NEW GAME TAB
    """

    def on_start_new(self) -> None:
        """
        Starts a new game and goes to the in-game screen.
        """
        self.app.adventure.name = self.ids.input_name.text
        self.app.adventure.context = self.ids.input_context.text
        self.app.adventure.actions.append(self.ids.input_prompt.text)
        self.app.sm.current = 'play'

    def update_button_start_new(self) -> None:
        """
        Updates button_start_new depending on the model and text input status.
        """
        self.ids.button_start_new.disabled = not (
            self.app.ai and
            self.ids.input_name.text.strip() and
            self.ids.input_context.text.strip() and
            self.ids.input_prompt.text.strip()
        )

    """
    LOAD GAME TAB
    """

    def init_saves(self) -> None:
        """
        Fetches and loads all the game saves in the user directory for selection.
        """
        paths = [s.path for s in os.scandir(self.app.get_user_path('adventures')) if s.path.endswith('.json')]
        for p in paths:
            with open(p, 'r') as json_file:
                data = json.load(json_file)
                self.savefiles[data['name']] = data
        self.ids.view_game.data = [{'text': str(s)} for s in self.savefiles.keys()]
        self.selected_savefile = None

    def on_game_selected(self, game) -> None:
        """
        Selects (but does not load) a given save by its name.

        :param game: The name of the game to select.
        """
        self.selected_savefile = game
        self.on_update()

    def on_start_load(self) -> None:
        """
        Starts a game from a save and goes to the in-game screen.
        """
        self.app.adventure.from_dict(self.savefiles[self.selected_savefile])
        self.app.sm.current = 'play'

    def update_button_start_load(self) -> None:
        """
        Updates button_start_load depending on the model and text input status.
        """
        self.ids.button_start_load.disabled = not (
            self.app.ai and
            self.selected_savefile
        )
