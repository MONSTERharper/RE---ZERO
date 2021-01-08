import re
import os


class StopThreadException(BaseException):
    """
    Dummy exception for stopping threads using the func_timeout StoppableThread.
    """
    pass


def get_save_name(adventure_name: str) -> str:
    """
    SAVING PART, Ayush
    :Parameters adventure_name: The full name of the adventure to get a save name for.
    :return: A formatted string that is the save file name of the adventure.
    """
    adventure_name = re.sub(r'\s+', '_', adventure_name.strip())
    adventure_name = re.sub(r'[^a-zA-Z0-9_-]', '', adventure_name)
    return adventure_name


def is_model_valid(model_path: str) -> bool:
    """
    To check path of the pytorch model

    :Parameters model_path: The model path to check.
    :return: `True` if the path is valid, `False` otherwise.
    """
    return os.path.isfile(os.path.join(model_path, 'pytorch_model.bin')) \
        and os.path.isfile(os.path.join(model_path, 'config.json')) \
        and os.path.isfile(os.path.join(model_path, 'vocab.json'))