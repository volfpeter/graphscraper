"""
This module contains an event dispatcher interface along with a simple implementation and the base event class.
"""

# Imports
# ------------------------------------------------------------

import types

# Module constants
# ------------------------------------------------------------

__author__ = "Peter Volf"

# Classes
# ------------------------------------------------------------


class EventDispatcherBase(object):
    """Defines the interface all event dispatchers must implement."""

    # Public methods
    # ------------------------------------------------------------

    def add_event_listener(self, event_type: str, event_handler: types.MethodType) -> None:
        """
        Registers the given event handler on the dispatcher for the given event type.

        Args:
            event_type (str): The type of the event to add the event handler to.
                              Must not be `None` or empty string.
            event_handler (types.MethodType): The event handler to register for the given event
                                              type of the dispatcher. Must not be `None`.

        Raises:
            ValueError: If any of the parameters have an incorrect type.
        """
        raise NotImplementedError("EventDispatcherBase is abstract, "
                                  "its child classes must override all its methods.")

    def dispatch_event(self, event: "Event") -> None:
        """
        Dispatches the given event.

        It is the duty of this method to set the target of the dispatched event by calling
        `event.set_target(self)`.

        Args:
            event (Event): The event to dispatch. Must not be `None`.

        Raises:
            TypeError: If the event is `None` or its type is incorrect.
        """
        raise NotImplementedError("EventDispatcherBase is abstract, "
                                  "its child classes must override all its methods.")

    def remove_event_listener(self, event_type: str, event_handler: types.MethodType) -> None:
        """
        Removes the given event listener registered on the dispatcher for the given event type.

        Args:
            event_type (str): The type of the event to remove the event handler from.
                              Must not be `None` or empty string.
            event_handler (types.MethodType): The event handler to remove from the given event type
                                              of the dispatcher. Must not be `None`.

        Raises:
            ValueError: If any of the parameters are invalid.
        """
        raise NotImplementedError("EventDispatcherBase is abstract, "
                                  "its child classes must override all its methods.")


class EventDispatcher(EventDispatcherBase):
    """A simple `EventDispatcherBase` implementation."""

    # Initialization
    # ------------------------------------------------------------

    def __init__(self):
        """Constructor."""
        # TODO: use a dict[str, set] instead.
        self._registered_listeners: dict[str, dict[types.MethodType, bool]] = {}

    # Public methods
    # ------------------------------------------------------------

    def add_event_listener(self, event_type: str, event_handler: types.MethodType) -> None:
        """
        Registers the given event handler on the dispatcher for the given event type.

        Args:
            event_type (str): The type of the event to add the event handler to.
                              Must not be `None` or empty string.
            event_handler (types.MethodType): The event handler to register for the given event
                                              type of the dispatcher. Must not be `None`.

        Raises:
            ValueError: If any of the parameters have an incorrect type.
        """
        # TODO: we should also accept types.FunctionType,
        # don't forget the documentation here and in the interface.
        if not isinstance(event_type, str) or event_type == "" or\
           not isinstance(event_handler, types.MethodType):
            raise ValueError("Invalid arguments: {}, {}".format(event_type, event_handler))

        listeners: dict[types.MethodType, bool] = self._registered_listeners.get(event_type)
        if listeners is None:
            listeners = {event_handler: True}
            self._registered_listeners[event_type] = listeners
        else:
            listener = listeners.get(event_handler)
            # One listener function can only be added once.
            if listener is not None:
                return

            listeners[event_handler] = True

    def dispatch_event(self, event: "Event") -> None:
        """
        Dispatches the given event.

        It is the duty of this method to set the target of the dispatched event by calling
        `event.set_target(self)`.

        Args:
            event (Event): The event to dispatch. Must not be `None`.

        Raises:
            TypeError: If the event is `None` or its type is incorrect.
        """
        # Set the target of the event if it doesn't have one already. It could happen that
        # we are simply redispatching an event.
        if event.target is None:
            event.set_target(self)

        listeners: dict[types.MethodType, bool] = self._registered_listeners.get(event.type)
        if listeners is None:
            return

        for listener in listeners:
            listener(event)

    def remove_event_listener(self, event_type: str, event_handler: types.MethodType) -> None:
        """
        Removes the given event listener registered on the dispatcher for the given event type.

        Args:
            event_type (str): The type of the event to remove the event handler from.
                              Must not be `None` or empty string.
            event_handler (types.MethodType): The event handler to remove from the given event
                                              type of the dispatcher. Must not be `None`.

        Raises:
            ValueError: If any of the parameters are invalid.
        """
        # TODO: we should also accept types.FunctionType,
        # don't forget the documentation here and in the interface.
        if not isinstance(event_type, str) or event_type == "" or\
           not isinstance(event_handler, types.MethodType):
            raise ValueError("Invalid arguments: {}, {}".format(event_type, event_handler))

        listeners: dict[types.MethodType, bool] = self._registered_listeners.get(event_type)
        listener: types.MethodType = None if listeners is None else listeners.get(event_handler)
        if listener is not None:
            del listeners[event_handler]


class Event(object):
    """The base event class."""

    # Initialization
    # ------------------------------------------------------------

    def __init__(self, event_type: str):
        """
        Constructor.

        Args:
            event_type (str): The type - string identifier - of the event.
                              Must not be `None` or empty string.
        """
        if not isinstance(event_type, str) or event_type == "":
            raise TypeError("Invalid event type: {}".format(event_type))

        self._event_type: str = event_type
        self._target: EventDispatcherBase = None

    # Public properties
    # ------------------------------------------------------------

    @property
    def target(self) -> EventDispatcherBase:
        """
        The event dispatcher object that dispatched this event.
        """
        return self._target

    @property
    def type(self) -> str:
        """
        The type of the event.
        """
        return self._event_type

    # Public methods
    # ------------------------------------------------------------

    def set_target(self, target: EventDispatcherBase) -> None:
        """
        This method should be called by the event dispatcher that dispatches this event
        to set its target property.

        Args:
            target (EventDispatcherBase): The event dispatcher that will dispatch this event.

        Raises:
            PermissionError: If the target property of the event has already been set.
            TypeError: If `target` is not an `EventDispatcherBase` instance.
        """
        if self._target is not None:
            raise PermissionError("The target property already has a valid value.")

        if not isinstance(target, EventDispatcherBase):
            raise TypeError("Invalid target type: {}".format(target))

        self._target = target
