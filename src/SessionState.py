import json
from typing import Optional
import uuid

class SessionState:
    """Object to handle session state information for the user"""
    
    @property
    def session(self) -> str:
        """Getter for 'session'-Attribut."""
        return self._session

    @session.setter
    def session(self, value):
        """Setter for 'session'-Attribut, makes sures it is always a string for serialization."""
        self._session = self._ensure_str(value)

    def _ensure_str(self, value) -> str:
        """Validates that types assigned to session are always strings."""
        if not isinstance(value, str):
            raise TypeError(f"session must be of Type str sein, but {type(value).__name__} was assigned.")
        return value

    def __init__(self, token: int=0, session: str=None):
        """State object for storing application data in browser."""
        self.token: int = token        
        self.session: str = str(uuid.uuid4()) if session==None else session

    def __str__(self) -> str:
        """String representation for logging."""
        # gradio is using the (str) function to save the state instead of the repr
        return repr(self) # f"SessionState(token={self.token}, session={self.session})"

    def __repr__(self) -> str:
        """Return a string representation of the SessionState."""
        return json.dumps(self.to_dict())
        #return f"SessionState(token={self.token}, session='{self.session}')"

    @classmethod
    def to_gradio_state(self) -> str:
        """Create SessionState from dictionary after deserialization."""
        return repr(self)

    def to_dict(self) -> dict:
        """Convert SessionState to dictionary for serialization."""
        return {
            'token': self.token,
            'session': str(self.session)
        }

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> 'SessionState':
        """Create SessionState from dictionary after deserialization."""
        if not data:
            return cls()
        return cls(
            token=data.get('token', 0),
            session=data.get('session', str(uuid.uuid4()))
        )

    @classmethod
    def from_gradio_state(cls, data: str) -> 'SessionState':
        """Create SessionState from dictionary string after deserialization."""
        if not data:
            return cls()
        if not isinstance(data, str):
            data = repr(data)
        try:
            d = json.loads(data)    
            return cls.from_dict(d)
        except Exception:
            raise Exception(f"SessionState can't be converted from given value {data}")

