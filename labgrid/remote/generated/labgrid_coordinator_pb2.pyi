from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ClientInMessage(_message.Message):
    __slots__ = ("sync", "startup", "subscribe")
    SYNC_FIELD_NUMBER: _ClassVar[int]
    STARTUP_FIELD_NUMBER: _ClassVar[int]
    SUBSCRIBE_FIELD_NUMBER: _ClassVar[int]
    sync: Sync
    startup: StartupDone
    subscribe: Subscribe
    def __init__(self, sync: _Optional[_Union[Sync, _Mapping]] = ..., startup: _Optional[_Union[StartupDone, _Mapping]] = ..., subscribe: _Optional[_Union[Subscribe, _Mapping]] = ...) -> None: ...

class Sync(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    def __init__(self, id: _Optional[int] = ...) -> None: ...

class StartupDone(_message.Message):
    __slots__ = ("version", "name")
    VERSION_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    version: str
    name: str
    def __init__(self, version: _Optional[str] = ..., name: _Optional[str] = ...) -> None: ...

class Subscribe(_message.Message):
    __slots__ = ("is_unsubscribe", "all_places", "all_resources")
    IS_UNSUBSCRIBE_FIELD_NUMBER: _ClassVar[int]
    ALL_PLACES_FIELD_NUMBER: _ClassVar[int]
    ALL_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    is_unsubscribe: bool
    all_places: bool
    all_resources: bool
    def __init__(self, is_unsubscribe: bool = ..., all_places: bool = ..., all_resources: bool = ...) -> None: ...

class ClientOutMessage(_message.Message):
    __slots__ = ("sync", "update")
    SYNC_FIELD_NUMBER: _ClassVar[int]
    UPDATE_FIELD_NUMBER: _ClassVar[int]
    sync: Sync
    update: UpdateResponse
    def __init__(self, sync: _Optional[_Union[Sync, _Mapping]] = ..., update: _Optional[_Union[UpdateResponse, _Mapping]] = ...) -> None: ...

class UpdateResponse(_message.Message):
    __slots__ = ("resource", "del_resource", "place", "del_place")
    RESOURCE_FIELD_NUMBER: _ClassVar[int]
    DEL_RESOURCE_FIELD_NUMBER: _ClassVar[int]
    PLACE_FIELD_NUMBER: _ClassVar[int]
    DEL_PLACE_FIELD_NUMBER: _ClassVar[int]
    resource: Resource
    del_resource: Resource.Path
    place: Place
    del_place: str
    def __init__(self, resource: _Optional[_Union[Resource, _Mapping]] = ..., del_resource: _Optional[_Union[Resource.Path, _Mapping]] = ..., place: _Optional[_Union[Place, _Mapping]] = ..., del_place: _Optional[str] = ...) -> None: ...

class ExporterInMessage(_message.Message):
    __slots__ = ("resource", "startup", "response")
    RESOURCE_FIELD_NUMBER: _ClassVar[int]
    STARTUP_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    resource: Resource
    startup: StartupDone
    response: ExporterResponse
    def __init__(self, resource: _Optional[_Union[Resource, _Mapping]] = ..., startup: _Optional[_Union[StartupDone, _Mapping]] = ..., response: _Optional[_Union[ExporterResponse, _Mapping]] = ...) -> None: ...

class Resource(_message.Message):
    __slots__ = ("path", "cls", "params", "extra", "acquired", "avail")
    class Path(_message.Message):
        __slots__ = ("exporter_name", "group_name", "resource_name")
        EXPORTER_NAME_FIELD_NUMBER: _ClassVar[int]
        GROUP_NAME_FIELD_NUMBER: _ClassVar[int]
        RESOURCE_NAME_FIELD_NUMBER: _ClassVar[int]
        exporter_name: str
        group_name: str
        resource_name: str
        def __init__(self, exporter_name: _Optional[str] = ..., group_name: _Optional[str] = ..., resource_name: _Optional[str] = ...) -> None: ...
    class ParamsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: MapValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[MapValue, _Mapping]] = ...) -> None: ...
    class ExtraEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: MapValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[MapValue, _Mapping]] = ...) -> None: ...
    PATH_FIELD_NUMBER: _ClassVar[int]
    CLS_FIELD_NUMBER: _ClassVar[int]
    PARAMS_FIELD_NUMBER: _ClassVar[int]
    EXTRA_FIELD_NUMBER: _ClassVar[int]
    ACQUIRED_FIELD_NUMBER: _ClassVar[int]
    AVAIL_FIELD_NUMBER: _ClassVar[int]
    path: Resource.Path
    cls: str
    params: _containers.MessageMap[str, MapValue]
    extra: _containers.MessageMap[str, MapValue]
    acquired: str
    avail: bool
    def __init__(self, path: _Optional[_Union[Resource.Path, _Mapping]] = ..., cls: _Optional[str] = ..., params: _Optional[_Mapping[str, MapValue]] = ..., extra: _Optional[_Mapping[str, MapValue]] = ..., acquired: _Optional[str] = ..., avail: bool = ...) -> None: ...

class MapValue(_message.Message):
    __slots__ = ("bool_value", "int_value", "uint_value", "float_value", "string_value")
    BOOL_VALUE_FIELD_NUMBER: _ClassVar[int]
    INT_VALUE_FIELD_NUMBER: _ClassVar[int]
    UINT_VALUE_FIELD_NUMBER: _ClassVar[int]
    FLOAT_VALUE_FIELD_NUMBER: _ClassVar[int]
    STRING_VALUE_FIELD_NUMBER: _ClassVar[int]
    bool_value: bool
    int_value: int
    uint_value: int
    float_value: float
    string_value: str
    def __init__(self, bool_value: bool = ..., int_value: _Optional[int] = ..., uint_value: _Optional[int] = ..., float_value: _Optional[float] = ..., string_value: _Optional[str] = ...) -> None: ...

class ExporterResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: int
    def __init__(self, status: _Optional[int] = ...) -> None: ...

class ExporterOutMessage(_message.Message):
    __slots__ = ("request",)
    REQUEST_FIELD_NUMBER: _ClassVar[int]
    request: ExporterSetAquiredRequest
    def __init__(self, request: _Optional[_Union[ExporterSetAquiredRequest, _Mapping]] = ...) -> None: ...

class ExporterSetAquiredRequest(_message.Message):
    __slots__ = ("group_name", "resource_name", "place_name")
    GROUP_NAME_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_NAME_FIELD_NUMBER: _ClassVar[int]
    PLACE_NAME_FIELD_NUMBER: _ClassVar[int]
    group_name: str
    resource_name: str
    place_name: str
    def __init__(self, group_name: _Optional[str] = ..., resource_name: _Optional[str] = ..., place_name: _Optional[str] = ...) -> None: ...

class AddPlaceRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class AddPlaceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DeletePlaceRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class DeletePlaceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetPlacesRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetPlacesResponse(_message.Message):
    __slots__ = ("places",)
    PLACES_FIELD_NUMBER: _ClassVar[int]
    places: _containers.RepeatedCompositeFieldContainer[Place]
    def __init__(self, places: _Optional[_Iterable[_Union[Place, _Mapping]]] = ...) -> None: ...

class Place(_message.Message):
    __slots__ = ("name", "aliases", "comment", "tags", "matches", "acquired", "acquired_resources", "allowed", "created", "changed", "reservation")
    class TagsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    ALIASES_FIELD_NUMBER: _ClassVar[int]
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    MATCHES_FIELD_NUMBER: _ClassVar[int]
    ACQUIRED_FIELD_NUMBER: _ClassVar[int]
    ACQUIRED_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_FIELD_NUMBER: _ClassVar[int]
    CREATED_FIELD_NUMBER: _ClassVar[int]
    CHANGED_FIELD_NUMBER: _ClassVar[int]
    RESERVATION_FIELD_NUMBER: _ClassVar[int]
    name: str
    aliases: _containers.RepeatedScalarFieldContainer[str]
    comment: str
    tags: _containers.ScalarMap[str, str]
    matches: _containers.RepeatedCompositeFieldContainer[ResourceMatch]
    acquired: str
    acquired_resources: _containers.RepeatedScalarFieldContainer[str]
    allowed: _containers.RepeatedScalarFieldContainer[str]
    created: float
    changed: float
    reservation: str
    def __init__(self, name: _Optional[str] = ..., aliases: _Optional[_Iterable[str]] = ..., comment: _Optional[str] = ..., tags: _Optional[_Mapping[str, str]] = ..., matches: _Optional[_Iterable[_Union[ResourceMatch, _Mapping]]] = ..., acquired: _Optional[str] = ..., acquired_resources: _Optional[_Iterable[str]] = ..., allowed: _Optional[_Iterable[str]] = ..., created: _Optional[float] = ..., changed: _Optional[float] = ..., reservation: _Optional[str] = ...) -> None: ...

class ResourceMatch(_message.Message):
    __slots__ = ("exporter", "group", "cls", "name", "rename")
    EXPORTER_FIELD_NUMBER: _ClassVar[int]
    GROUP_FIELD_NUMBER: _ClassVar[int]
    CLS_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    RENAME_FIELD_NUMBER: _ClassVar[int]
    exporter: str
    group: str
    cls: str
    name: str
    rename: str
    def __init__(self, exporter: _Optional[str] = ..., group: _Optional[str] = ..., cls: _Optional[str] = ..., name: _Optional[str] = ..., rename: _Optional[str] = ...) -> None: ...

class AddPlaceAliasRequest(_message.Message):
    __slots__ = ("placename", "alias")
    PLACENAME_FIELD_NUMBER: _ClassVar[int]
    ALIAS_FIELD_NUMBER: _ClassVar[int]
    placename: str
    alias: str
    def __init__(self, placename: _Optional[str] = ..., alias: _Optional[str] = ...) -> None: ...

class AddPlaceAliasResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DeletePlaceAliasRequest(_message.Message):
    __slots__ = ("placename", "alias")
    PLACENAME_FIELD_NUMBER: _ClassVar[int]
    ALIAS_FIELD_NUMBER: _ClassVar[int]
    placename: str
    alias: str
    def __init__(self, placename: _Optional[str] = ..., alias: _Optional[str] = ...) -> None: ...

class DeletePlaceAliasResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SetPlaceTagsRequest(_message.Message):
    __slots__ = ("placename", "tags")
    class TagsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    PLACENAME_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    placename: str
    tags: _containers.ScalarMap[str, str]
    def __init__(self, placename: _Optional[str] = ..., tags: _Optional[_Mapping[str, str]] = ...) -> None: ...

class SetPlaceTagsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SetPlaceCommentRequest(_message.Message):
    __slots__ = ("placename", "comment")
    PLACENAME_FIELD_NUMBER: _ClassVar[int]
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    placename: str
    comment: str
    def __init__(self, placename: _Optional[str] = ..., comment: _Optional[str] = ...) -> None: ...

class SetPlaceCommentResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AddPlaceMatchRequest(_message.Message):
    __slots__ = ("placename", "pattern", "rename")
    PLACENAME_FIELD_NUMBER: _ClassVar[int]
    PATTERN_FIELD_NUMBER: _ClassVar[int]
    RENAME_FIELD_NUMBER: _ClassVar[int]
    placename: str
    pattern: str
    rename: str
    def __init__(self, placename: _Optional[str] = ..., pattern: _Optional[str] = ..., rename: _Optional[str] = ...) -> None: ...

class AddPlaceMatchResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DeletePlaceMatchRequest(_message.Message):
    __slots__ = ("placename", "pattern", "rename")
    PLACENAME_FIELD_NUMBER: _ClassVar[int]
    PATTERN_FIELD_NUMBER: _ClassVar[int]
    RENAME_FIELD_NUMBER: _ClassVar[int]
    placename: str
    pattern: str
    rename: str
    def __init__(self, placename: _Optional[str] = ..., pattern: _Optional[str] = ..., rename: _Optional[str] = ...) -> None: ...

class DeletePlaceMatchResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AcquirePlaceRequest(_message.Message):
    __slots__ = ("placename",)
    PLACENAME_FIELD_NUMBER: _ClassVar[int]
    placename: str
    def __init__(self, placename: _Optional[str] = ...) -> None: ...

class AcquirePlaceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ReleasePlaceRequest(_message.Message):
    __slots__ = ("placename", "fromuser")
    PLACENAME_FIELD_NUMBER: _ClassVar[int]
    FROMUSER_FIELD_NUMBER: _ClassVar[int]
    placename: str
    fromuser: str
    def __init__(self, placename: _Optional[str] = ..., fromuser: _Optional[str] = ...) -> None: ...

class ReleasePlaceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AllowPlaceRequest(_message.Message):
    __slots__ = ("placename", "user")
    PLACENAME_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    placename: str
    user: str
    def __init__(self, placename: _Optional[str] = ..., user: _Optional[str] = ...) -> None: ...

class AllowPlaceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CreateReservationRequest(_message.Message):
    __slots__ = ("spec", "prio")
    SPEC_FIELD_NUMBER: _ClassVar[int]
    PRIO_FIELD_NUMBER: _ClassVar[int]
    spec: str
    prio: float
    def __init__(self, spec: _Optional[str] = ..., prio: _Optional[float] = ...) -> None: ...

class CreateReservationResponse(_message.Message):
    __slots__ = ("reservation",)
    RESERVATION_FIELD_NUMBER: _ClassVar[int]
    reservation: Reservation
    def __init__(self, reservation: _Optional[_Union[Reservation, _Mapping]] = ...) -> None: ...

class Reservation(_message.Message):
    __slots__ = ("owner", "token", "state", "prio", "filters", "allocations", "created", "timeout")
    class FiltersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class AllocationsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    OWNER_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    PRIO_FIELD_NUMBER: _ClassVar[int]
    FILTERS_FIELD_NUMBER: _ClassVar[int]
    ALLOCATIONS_FIELD_NUMBER: _ClassVar[int]
    CREATED_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    owner: str
    token: str
    state: int
    prio: float
    filters: _containers.ScalarMap[str, str]
    allocations: _containers.ScalarMap[str, str]
    created: float
    timeout: float
    def __init__(self, owner: _Optional[str] = ..., token: _Optional[str] = ..., state: _Optional[int] = ..., prio: _Optional[float] = ..., filters: _Optional[_Mapping[str, str]] = ..., allocations: _Optional[_Mapping[str, str]] = ..., created: _Optional[float] = ..., timeout: _Optional[float] = ...) -> None: ...

class CancelReservationRequest(_message.Message):
    __slots__ = ("token",)
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    token: str
    def __init__(self, token: _Optional[str] = ...) -> None: ...

class CancelReservationResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PollReservationRequest(_message.Message):
    __slots__ = ("token",)
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    token: str
    def __init__(self, token: _Optional[str] = ...) -> None: ...

class PollReservationResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetReservationsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetReservationsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
