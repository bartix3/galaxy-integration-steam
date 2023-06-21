from typing import NamedTuple, Union, Dict


class NextStepSettings(NamedTuple):
    window_title: str
    window_width: int
    window_height : int
    start_uri: str 
    end_uri_regex: str

    def to_dict(self) -> Dict[str, Union[int, str]]:
        return { 
            "window_title" : self.window_title, 
            "window_width" : self.window_width, 
            "window_height" : self.window_height,
            "start_uri" : self.start_uri,
            "end_uri_regex" : self.end_uri_regex
        }