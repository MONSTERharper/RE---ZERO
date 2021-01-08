from typing import *


class Adventure(object):
    def __init__(
            self,
            name: str = None,
            context: str = None,
    ):
        self.name: str = name
        self.context: str = context
        self.memory: str = ''
        self.actions: List[str] = []
        self.results: List[str] = []

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'context': self.context,
            'memory': self.memory,
            'actions': self.actions,
            'results': self.results
        }

    def from_dict(self, d: Dict[str, Any]):
        self.name = d['name']
        self.context = d['context']
        self.memory = d['memory']
        self.actions = d['actions']
        self.results = d['results']

    @property
    def story(self) -> list:
        """
        The user actions and AI results in chronological order, not including the story context.

        :return: A list of action and result strings, interspersed, starting with the first action.
        """
        return [s for p in zip(self.actions, self.results) for s in p]

    @property
    def full_story(self) -> list:
        
        #The user actions and AI results in chronological order, including the story context.
        """
        :return: The story context string, followed by a list of action and result strings, interspersed, starting
        with the first action.
        """
        return ([self.context] if self.context else []) + self.story

    def get_ai_story(self, start: Optional[int] = None, end: Optional[int] = None) -> list:
        """
        Retrieves a clipped portion of the adventure, including the story's memory, for purposes of AI generation.

        :Parameters start: Where to start remembering the story from.
        :Parameters end: Where the "end" of the story is.
        :return: The story context string, followed by a list of the last `self.memory` action and result strings,
        interspersed.
        """
        start = 0 if start is None else start
        end = len(self.story) if end is None else end
        result = [self.context] if self.context else []
        result += [self.memory]
        result += self.story[start:end]
        return result
