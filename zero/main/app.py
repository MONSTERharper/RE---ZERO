import importlib
import json
import os
import sys
from threading import Thread
from typing import *

from kivy.app import App as KivyApp
from kivy.config import ConfigParser
from kivy.lang.builder import Builder
from kivy.logger import Logger
from kivy.uix.screenmanager import ScreenManager

from zero.common.ai import AI
from zero.common.adventure import Adventure
from zero.main.ui.menu import MenuScreen
from zero.main.ui.play import PlayScreen
from zero.common.utils import get_save_name, is_model_valid


class App(KivyApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # UI
        self.title: str = 'RE : ZERO'
        self.sm: Optional[ScreenManager] = None
        self.screens: Dict[str, ClassVar] = {}
        # AI
        self.ai: Optional[AI] = None
        self.adventure: Optional[Adventure] = None
        # Threading
        self.threads: Dict[str, Thread] = {}
        # Modules
        self.loaded_modules: Dict[str, str] = {}
        self.input_filters: List[Callable[[str], str]] = []
        self.output_filters: List[Callable[[str], str]] = []
        self.display_filter: Optional[Callable[[List[str]], str]] = None

    def build(self) -> ScreenManager:
        self.init_mods()
        self.init_ui()
        return self.sm

    def build_config(self, _) -> None:
        self.config = ConfigParser()
        self.config.read('config.ini')
        self.config.setdefaults('general', {
            'userdir': 'user',
            'autosave': True
        })
        self.config.setdefaults('ai', {
            'timeout': 20.0,
            'memory': 20,
            'max_length': 60,
            'beam_searches': 1,
            'temperature': 0.8,
            'top_k': 40,
            'top_p': 0.9,
            'repetition_penalty': 1.1
        })
        self.config.setdefaults('modules', {
            'input_filters': 'additional:filters',
            'output_filters': 'additional:filters',
            'display_filter': 'additional:filters'
        })
        self.config.write()

    def init_mods(self) -> None:
        """
        Initializes the game's module system and loads mods based on the current configuration.
        """
        sys.path.append(self.config.get('general', 'userdir'))

        for f in self.config.get('modules', 'input_filters').split(','):
            domain, module = f.split(':')
            Logger.info(f'Modules: Loading {f}.filter_input')
            self.input_filters += [self.load_submodule(domain, module, 'filter_input')]

        for f in self.config.get('modules', 'output_filters').split(','):
            domain, module = f.split(':')
            Logger.info(f'Modules: Loading {f}.filter_output')
            self.output_filters += [self.load_submodule(domain, module, 'filter_output')]

        domain, module = self.config.get('modules', 'display_filter').split(':')
        Logger.info(f'Modules: Loading {f}.filter_display')
        self.display_filter = self.load_submodule(domain, module, 'filter_display')

    def init_ui(self) -> None:
        """
        Initializes the screen manager, loads all screen kivy files and their associated python modules.
        """
        self.sm = ScreenManager()
        self.screens = {'menu': MenuScreen, 'play': PlayScreen }
        for n, s in self.screens.items():
            Builder.load_file(f'zero/main/ui/{n}.kv')
            self.sm.add_widget(s(name=n))
        self.sm.current = 'menu'

    def get_user_path(self, *args: str) -> str:
        """
        Retrieves a path relative to the current user directory.

        :param args: The subdirectories / filenames in the user directory.
        :return: A path in the current user directory.
        """
        return os.path.join(self.config.get('general', 'userdir'), *args)

    def get_model_path(self, model: str) -> str:
        """
        Gets the path to the currently selected (but not necessarily loaded) AI model.

        :param model: The model within the models subdirectory.
        :return: The current selected model path.
        """
        return self.get_user_path('models', model)

    def get_valid_models(self) -> List[str]:
        """
        :return: A list of valid model names, inside {userdir}/models
        """
        return [m.name for m in os.scandir(self.get_user_path('models')) if is_model_valid(m.path)]

    def get_module_path(self, domain: str, module: str) -> str:
        return self.get_user_path('modules', domain, f'{module}.py')

    def load_module(self, domain: str, module: str) -> Any:
        """
        Loads a module and returns it (if it hasn't been loaded already).

        :param domain: The module domain.
        :param module: The module to load from the given domain.
        :return: The loaded module.
        """
        k = f'{domain}:{module}'
        v = self.loaded_modules.get(k)
        if v is None:
            v = importlib.import_module(f'.{module}', f'modules.{domain}')
            self.loaded_modules[k] = v
        return v

    def load_submodule(self, domain: str, module: str, submodule: str) -> str:
        """
        Loads a submodule (a method, class, or variable from a given module).

        :param domain: The module domain.
        :param module: The module to load from the given domain.
        :param submodule: The submodule to load from the given module.
        :return: The loaded submodule.
        """
        m = self.load_module(domain, module)
        return getattr(m, submodule)

    # SAVING AND LOADING

    def save_adventure(self) -> None:
        """
        Saves the current adventure.
        """
        savefile = get_save_name(self.adventure.name)
        with open(self.get_user_path('adventures', f'{savefile}.json'), 'w') as json_file:
            json.dump(self.adventure.to_dict(), json_file, indent=4)

    def load_adventure(self) -> None:
        """
        Loads the current adventure.
        """
        savefile = get_save_name(self.adventure.name)
        with open(self.get_user_path('adventures', f'{savefile}.json'), 'r') as json_file:
            self.adventure.from_dict(json.load(json_file))
