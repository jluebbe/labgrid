#!/usr/bin/env python3
import logging
import asyncio
import itertools
import inspect
from functools import wraps
from enum import Enum
import attr

import grpc

from .common import ResourceEntry, ResourceMatch, Place, Reservation, ReservationState, queue_as_aiter, TAG_KEY, TAG_VAL
from .scheduler import TagSet, schedule
from ..util import atomic_replace, yaml

from .generated import labgrid_coordinator_pb2
from .generated import labgrid_coordinator_pb2_grpc

class Action(Enum):
    ADD = 0
    DEL = 1
    UPD = 2


@attr.s(eq=False)
class RemoteSession:
    """class encapsulating a session, used by Exporter and ClientSession"""
    coordinator = attr.ib()
    peer = attr.ib()
    name = attr.ib()
    queue = attr.ib()
    version = attr.ib()

@attr.s(eq=False)
class ExporterSession(RemoteSession):
    """An Exporter is opened for each Exporter connecting to the
    coordinator, allowing the Exporter to get and set resources"""
    groups = attr.ib(default=attr.Factory(dict), init=False)

    def set_resource(self, groupname, resourcename, resource):
        """This is called when Exporters update resources or when they disconnect."""
        logging.info("set_resource %s %s %s", groupname, resourcename, resource)
        group = self.groups.setdefault(groupname, {})
        old = group.get(resourcename)
        if resource is not None:
            new = ResourceImport(
                data=ResourceImport.data_from_pb2(resource),
                path=(self.name, groupname, resource.cls, resourcename)
            )
            if old:
                old.data.update(new.data)
                new = old
            else:
                group[resourcename] = new
        else:
            new = None
            try:
                del group[resourcename]
            except KeyError:
                pass

        msg = labgrid_coordinator_pb2.ClientOutMessage()
        if new:
            msg.update.resource.CopyFrom(new.as_pb2())
            msg.update.resource.path.exporter_name = self.name
            msg.update.resource.path.group_name = groupname
            msg.update.resource.path.resource_name = resourcename
        else:
            msg.update.del_resource.exporter_name = self.name
            msg.update.del_resource.group_name = groupname
            msg.update.del_resource.resource_name = resourcename

        for client in self.coordinator.clients.values():
            client.queue.put_nowait(msg)

        if old and new:
            assert old is new
            return Action.UPD, new
        elif old and not new:
            return Action.DEL, old
        elif not old and new:
            return Action.ADD, new

        assert not old and not new

    def get_resources(self):
        """Method invoked by the client, get the resources from the coordinator"""
        result = {}
        for groupname, group in self.groups.items():
            result_group = result[groupname] = {}
            for resourcename, resource in group.items():
                result_group[resourcename] = resource.asdict()
        return result


@attr.s(eq=False)
class ClientSession(RemoteSession):
    def subscribe_places(self):
        # send initial places
        for place in self.coordinator.places.values():
            place: Place
            out_msg = labgrid_coordinator_pb2.ClientOutMessage()
            out_msg.update.place.CopyFrom(place.as_pb2())
            self.queue.put_nowait(out_msg)

    def subscribe_resources(self):
        pass
        # FIXME
        #self.queue.put_nowait(out_msg)


def locked(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        async with self.lock:
            return await func(self, *args, **kwargs)
    return wrapper


@attr.s(eq=False)
class ResourceImport(ResourceEntry):
    """Represents a local resource exported from an exporter.

    The ResourceEntry attributes contain the information for the client.
    """
    path = attr.ib(kw_only=True, validator=attr.validators.instance_of(tuple))


class Coordinator(labgrid_coordinator_pb2_grpc.LabgridServicer):
    def __init__(self) -> None:
        self.places = {}
        self.reservations = {}

        self.lock = asyncio.Lock()
        self.exporters: Dict[str, ExporterSession] = {}
        self.clients: Dict[str, ClientSession] = {}
        self.save_scheduled = False
        self.load()

        self.poll_task = asyncio.get_event_loop().create_task(self.poll())

    @locked
    async def ReleasePlace(self, request, context):
        name = request.placename
        peer = context.peer()
        try:
            username = self.clients[peer].name
        except KeyError:
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, f"Peer {peer} does not have a valid session")
        print(request)
        fromuser = request.fromuser if request.HasField("fromuser") else None;
        try:
            place = self.places[name]
        except KeyError:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Place {name} does not exist")
        if not place.acquired:
            if fromuser:
                return labgrid_coordinator_pb2.ReleasePlaceResponse()
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, f"Place {name} is not acquired")
        if fromuser and place.acquired != fromuser:
            return labgrid_coordinator_pb2.ReleasePlaceResponse()

        await self._release_resources(place, place.acquired_resources)

        place.acquired = None
        place.allowed = set()
        place.touch()
        self._publish_place(place)
        self.save_later()
        self.schedule_reservations()
        print(f"{place.name}: place released")
        return labgrid_coordinator_pb2.ReleasePlaceResponse()

    @locked
    async def AddPlace(self, request, context):
        name = request.name
        if not name or not isinstance(name, str):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"name was not a string")
        if name in self.places:
            await context.abort(grpc.StatusCode.ALREADY_EXISTS, f"Place {name} already exists")
        logging.debug("Adding %s", name)
        place = Place(name)
        self.places[name] = place
        self._publish_place(place)
        self.save_later()
        return labgrid_coordinator_pb2.AddPlaceResponse()

    @locked
    async def DeletePlace(self, request, context):
        name = request.name
        if not name or not isinstance(name, str):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"name was not a string")
        if name not in self.places:
            await context.abort(grpc.StatusCode.ALREADY_EXISTS, f"Place {name} does not exist")
        logging.debug("Deleting %s", name)
        del self.places[name]
        msg = labgrid_coordinator_pb2.ClientOutMessage()
        msg.update.del_place = name
        for client in self.clients.values():
            client.queue.put_nowait(msg)
        self.save_later()
        return labgrid_coordinator_pb2.DeletePlaceResponse()

    def _get_places(self):
        return {k: v.as_pb2() for k, v in self.places.items()}

    @locked
    async def GetPlaces(self, unused_request, unused_context):
        logging.debug("GetPlaces")
        try:
            return labgrid_coordinator_pb2.GetPlacesResponse(places=[x.as_pb2() for x in self.places.values()])
        except Exception:
            logging.exception("error during get places")

    async def _match_places(self, pattern):
        """search for substring matches of pattern in place names and aliases

        Aliases in the format "namespace:alias" only match if the namespace is
        the current user name.
        """
        result = set()

        # reservation token lookup
        token = None
        if pattern.startswith('+'):
            token = pattern[1:]
            if not token:
                return []
            for name, place in self.places.items():
                if place.reservation == token:
                    result.add(name)
            if not result:
                raise UserError(f"reservation token {token} matches nothing")
            return list(result)

        # name and alias lookup
        for name, place in self.places.items():
            if pattern in name:
                result.add(name)
            for alias in place.aliases:
                if ':' in alias:
                    namespace, alias = alias.split(':', 1)
                    if namespace != self.getuser():
                        continue
                    if alias == pattern:  # prefer user namespace
                        return [name]
                if pattern in alias:
                    result.add(name)
        return list(result)

    async def poll(self):
        loop = asyncio.get_event_loop()
        while not loop.is_closed():
            try:
                await asyncio.sleep(15.0)
                await self._poll_step()
            except asyncio.CancelledError:
                break
            except Exception:  # pylint: disable=broad-except
                traceback.print_exc()

    async def _poll_step(self):
        # save changes
        logging.debug("Poll-Step: Save")
        if self.save_scheduled:
            await self.save()

    def save_later(self):
        logging.debug("Setting Save-later")
        self.save_scheduled = True

    def _get_resources(self):
        result = {}
        for session in self.exporters.values():
            result[session.name] = session.get_resources()
        return result

    async def save(self):
        logging.debug("Running Save")
        self.save_scheduled = False

        resources = self._get_resources()
        resources = yaml.dump(resources)
        resources = resources.encode()
        places = self._get_places()
        places = yaml.dump(places)
        places = places.encode()

        loop = asyncio.get_event_loop()
        logging.debug("Awaiting resources")
        await loop.run_in_executor(None, atomic_replace, 'resources.yaml', resources)
        logging.debug("Awaiting places")
        await loop.run_in_executor(None, atomic_replace, 'places.yaml', places)

    def load(self):
        try:
            self.places = {}
            with open('places.yaml', 'r') as f:
                self.places = yaml.load(f.read())
            for placename, config in self.places.items():
                config['name'] = placename
                # FIXME maybe recover previously acquired places here?
                if 'acquired' in config:
                    del config['acquired']
                if 'acquired_resources' in config:
                    del config['acquired_resources']
                if 'allowed' in config:
                    del config['allowed']
                if 'reservation' in config:
                    del config['reservation']
                config['matches'] = [ResourceMatch(**match) for match in config['matches']]
                place = Place(**config)
                self.places[placename] = place
        except FileNotFoundError:
            pass
        logging.info("loaded %s place(s)", len(self.places))

    async def ClientStream(self, request_iterator, context):
        peer = context.peer()
        logging.info(f"client connected: {peer}")
        assert peer not in self.clients
        out_msg_queue = asyncio.Queue()

        async def request_task():
            name = None
            version = None
            try:
                async for in_msg in request_iterator:
                    in_msg: labgrid_coordinator_pb2.ClientInMessage
                    logging.debug(f"client in_msg {in_msg}")
                    kind = in_msg.WhichOneof("kind")
                    if kind == "sync":
                        out_msg = labgrid_coordinator_pb2.ClientOutMessage()
                        out_msg.sync.id = in_msg.sync.id
                        out_msg_queue.put_nowait(out_msg)
                    elif kind == "startup":
                        version = in_msg.startup.version
                        name = in_msg.startup.name
                        session = self.clients[peer] = ClientSession(self, peer, name, out_msg_queue, version)
                        logging.debug("Received startup from %s with %s", name, version)
                    elif kind == "subscribe":
                        if in_msg.subscribe.all_places:
                            session.subscribe_places()
                        if in_msg.subscribe.all_resources:
                            session.subscribe_resources()
                    else:
                        logging.warning("received unknown kind %s from client %s (version %s)", kind, name, version)
                logging.debug(f"client request_task done: {context.done()}")
            except Exception:
                logging.exception("error in client message handler")

        runnning_request_task = asyncio.get_event_loop().create_task(request_task())

        try:
            async for out_msg in queue_as_aiter(out_msg_queue):
                out_msg: labgrid_coordinator_pb2.ClientOutMessage
                logging.debug(f"client output {out_msg}")
                yield out_msg
        finally:
            try:
                session = self.clients.pop(peer)
            except KeyError:
                logging.info("Never received startup from peer %s that disconnected", peer)
                return

            runnning_request_task.cancel()
            await runnning_request_task
            logging.debug(f"client aborted {session}, cancelled: {context.cancelled()}")

    def _add_default_place(self, name):
        if name in self.places:
            return
        if not name.isdigit():
            return
        place = Place(name)
        print(place)
        place.matches.append(ResourceMatch(exporter="*", group=name, cls="*"))
        self.places[name] = place

    def schedule_reservations(self):
        # The primary information is stored in the reservations and the places
        # only have a copy for convenience.

        # expire reservations
        for res in list(self.reservations.values()):
            if res.state is ReservationState.acquired:
                # acquired reservations do not expire
                res.refresh()
            if not res.expired:
                continue
            if res.state is not ReservationState.expired:
                res.state = ReservationState.expired
                res.allocations.clear()
                res.refresh()
                print(f'reservation ({res.owner}/{res.token}) is now {res.state.name}')
            else:
                del self.reservations[res.token]
                print(f'removed {res.state.name} reservation ({res.owner}/{res.token})')

        # check which places are already allocated and handle state transitions
        allocated_places = set()
        for res in self.reservations.values():
            acquired_places = set()
            for group in list(res.allocations.values()):
                for name in group:
                    place = self.places.get(name)
                    if place is None:
                        # the allocated place was deleted
                        res.state = ReservationState.invalid
                        res.allocations.clear()
                        res.refresh(300)
                        print(f'reservation ({res.owner}/{res.token}) is now {res.state.name}')
                    if place.acquired is not None:
                        acquired_places.add(name)
                    assert name not in allocated_places, "conflicting allocation"
                    allocated_places.add(name)
            if acquired_places and res.state is ReservationState.allocated:
                # an allocated place was acquired
                res.state = ReservationState.acquired
                res.refresh()
                print(f'reservation ({res.owner}/{res.token}) is now {res.state.name}')
            if not acquired_places and res.state is ReservationState.acquired:
                # all allocated places were released
                res.state = ReservationState.allocated
                res.refresh()
                print(f'reservation ({res.owner}/{res.token}) is now {res.state.name}')

        # check which places are available for allocation
        available_places = set()
        for name, place in self.places.items():
            if place.acquired is None and place.reservation is None:
                available_places.add(name)
        assert not (available_places & allocated_places), "inconsistent allocation"
        available_places -= allocated_places

        # check which reservations should be handled, ordered by priority and age
        pending_reservations = []
        for res in sorted(self.reservations.values(), key=lambda x: (-x.prio, x.created)):
            if res.state is not ReservationState.waiting:
                continue
            pending_reservations.append(res)

        # run scheduler
        place_tagsets = []
        for name in available_places:
            tags = set(self.places[name].tags.items())
            # support place names
            tags |= {('name', name)}
            # support place aliases
            place_tagsets.append(TagSet(name, tags))
        filter_tagsets = []
        for res in pending_reservations:
            filter_tagsets.append(TagSet(res.token, set(res.filters['main'].items())))
        allocation = schedule(place_tagsets, filter_tagsets)

        # apply allocations
        for res_token, place_name in allocation.items():
            res = self.reservations[res_token]
            res.allocations = {'main': [place_name]}
            res.state = ReservationState.allocated
            res.refresh()
            print(f'reservation ({res.owner}/{res.token}) is now {res.state.name}')

        # update reservation property of each place and notify
        old_map = {}
        for place in self.places.values():
            old_map[place.name] = place.reservation
            place.reservation = None
        new_map = {}
        for res in self.reservations.values():
            if not res.allocations:
                continue
            assert len(res.allocations) == 1, "only one filter group is implemented"
            for group in res.allocations.values():
                for name in group:
                    assert name not in new_map, "conflicting allocation"
                    new_map[name] = res.token
                    place = self.places.get(name)
                    assert place is not None, "invalid allocation"
                    place.reservation = res.token
        for name in old_map.keys() | new_map.keys():
            if old_map.get(name) != new_map.get(name):
                self._publish_place(place)

    async def _acquire_resources(self, place, resources):
        #FIXME fix implementation
        return True
        resources = resources.copy() # we may modify the list
        # all resources need to be free
        for resource in resources:
            if resource.acquired:
                return False

        # acquire resources
        acquired = []
        try:
            for resource in resources:
                # this triggers an update from the exporter which is published
                # to the clients
                await self.call(f'org.labgrid.exporter.{resource.path[0]}.acquire',
                                resource.path[1], resource.path[3], place.name)
                acquired.append(resource)
        except:
            print(f"failed to acquire {resource}", file=sys.stderr)
            # cleanup
            await self._release_resources(place, acquired)
            return False

        for resource in resources:
            place.acquired_resources.append(resource)

        return True

    async def _update_acquired_places(self, action, resource, callback=True):
        """Update acquired places when resources are added or removed."""
        if action not in [Action.ADD, Action.DEL]:
            return  # currently nothing needed for Action.UPD

        # collect affected places
        places = []
        for place in self.places.values():
            if not place.acquired:
                continue
            if not place.hasmatch(resource.path):
                continue
            places.append(place)

        if action is Action.ADD:
            # only add if there is no conflict
            if len(places) != 1:
                return
            place = places[0]
            await self._acquire_resources(place, [resource])
            self._publish_place(place)
        else:
            for place in places:
                await self._release_resources(place, [resource], callback=callback)
                self._publish_place(place)

    def _publish_place(self, place):
        msg = labgrid_coordinator_pb2.ClientOutMessage()
        msg.update.place.CopyFrom(place.as_pb2())

        for client in self.clients.values():
            client.queue.put_nowait(msg)

    async def _release_resources(self, place, resources, callback=True):
        # FIXME: use the internal queue to push this to the correct resources
        return

        resources = resources.copy() # we may modify the list

        for resource in resources:
            try:
                place.acquired_resources.remove(resource)
            except ValueError:
                pass

        for resource in resources:
            try:
                # this triggers an update from the exporter which is published
                # to the clients
                if callback:
                    await self.call(f'org.labgrid.exporter.{resource.path[0]}.release',
                                    resource.path[1], resource.path[3])
            except:
                print(f"failed to release {resource}", file=sys.stderr)
                # at leaset try to notify the clients
                try:
                    self._publish_resource(resource)
                except:
                    pass

    async def ExporterStream(self, request_iterator, context):
        peer = context.peer()
        logging.info(f"exporter connected: {peer}")
        assert peer not in self.exporters
        command_queue = asyncio.Queue()
        pending_commands = []

        async def request_task():
            name = None
            version = None
            try:
                async for in_msg in request_iterator:
                    in_msg: labgrid_coordinator_pb2.ExporterInMessage
                    logging.debug(f"exporter in_msg %s", in_msg)
                    kind = in_msg.WhichOneof("kind")
                    if kind == "response":
                        cmd = pending_commands.pop(0)
                        cmd.set()  # set event flag
                        logging.debug(f"Command %s is done", cmd)
                    elif kind == "startup":
                        version = in_msg.startup.version
                        name = in_msg.startup.name
                        session = self.exporters[peer] = ExporterSession(self, peer, name, command_queue, version)
                        logging.debug("Exporters: %s", self.exporters)
                        logging.debug("Received startup from %s with %s", name, version)
                    elif kind == "resource":
                        logging.debug("Received resource from %s with %s", name, in_msg.resource)
                        action, resource = session.set_resource(
                            in_msg.resource.path.group_name,
                            in_msg.resource.path.resource_name,
                            in_msg.resource
                        )
                        if action is Action.ADD:
                            async with self.lock:
                                self._add_default_place(in_msg.resource.path.group_name)
                        if action in (Action.ADD, Action.DEL):
                            async with self.lock:
                                await self._update_acquired_places(action, resource)
                        self.save_later()
                    else:
                        logging.warning("received unknown kind %s from exporter %s (version %s)", kind, name, version)

                logging.debug(f"exporter request_task done: {context.done()}")
            except Exception:
                logging.exception("error in exporter message handler")

        runnning_request_task = asyncio.get_event_loop().create_task(request_task())

        try:
            async for cmd in queue_as_aiter(command_queue):
                logging.debug(f"exporter cmd {cmd}")
                out_msg = labgrid_coordinator_pb2.ExporterOutMessage()
                out_msg.request.group_name = "foo-group"
                out_msg.request.resource_name = "foo-resource"
                out_msg.request.place_name = "foo-place"
                pending_commands.append(cmd)
                yield out_msg
        except asyncio.exceptions.CancelledError:
            logging.info(f"exporter disconnected {context.peer()}")
        finally:
            runnning_request_task.cancel()
            await runnning_request_task

            try:
                session = self.exporters.pop(peer)
            except KeyError:
                logging.info("Never received startup from peer %s that disconnected", peer)
                return

            for groupname, group in session.groups.items():
                for resourcename in group.copy():
                    action, resource = session.set_resource(groupname, resourcename, None)
                    await self._update_acquired_places(action, resource, callback=False)

            logging.debug(f"exporter aborted {context.peer()}, cancelled: {context.cancelled()}")
            logging.debug("Exporters: %s", self.exporters)

    async def AcquirePlace(self, request, context):
        peer = context.peer()
        name = request.placename
        try:
            username = self.clients[peer].name
        except KeyError:
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, f"Peer {peer} does not have a valid session")
        print(request)

        try:
            place = self.places[name]
        except KeyError:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Place {name} does not exist")
        if place.acquired:
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, f"Place {name} is already acquired")
        if place.reservation:
            res = self.reservations[place.reservation]
            if not res.owner == username:
                await context.abort(grpc.StatusCode.PERMISSION_DENIED, f"Place {name} was not reserved for {username}")
        # FIXME use the session object instead? or something else which
        # survives disconnecting clients?
        place.acquired = username
        resources = []
        for _, session in sorted(self.exporters.items()):
            for _, group in sorted(session.groups.items()):
                for _, resource in sorted(group.items()):
                    if not place.hasmatch(resource.path):
                        continue
                    resources.append(resource)
        if not await self._acquire_resources(place, resources):
            # revert earlier change
            place.acquired = None
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, f"Failed to acquire resources for {name}")
        place.touch()
        self._publish_place(place)
        self.save_later()
        self.schedule_reservations()
        print(f"{place.name}: place acquired by {place.acquired}")
        return labgrid_coordinator_pb2.AcquirePlaceResponse()

    @locked
    async def AddPlaceAlias(self, request, context):
        placename = request.placename
        alias = request.alias
        try:
            place = self.places[placename]
        except KeyError:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Place {placename} does not exist")
        place.aliases.add(alias)
        place.touch()
        self._publish_place(place)
        self.save_later()
        return labgrid_coordinator_pb2.AddPlaceAliasResponse()

    @locked
    async def DeletePlaceAlias(self, request, context):
        placename = request.placename
        alias = request.alias
        try:
            place = self.places[placename]
        except KeyError:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Place {placename} does not exist")
        try:
            place.aliases.remove(alias)
        except ValueError:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Failed to remove {alias} from {placename}")
        place.touch()
        self._publish_place(place)
        self.save_later()
        return labgrid_coordinator_pb2.DeletePlaceAliasResponse()

    @locked
    async def SetPlaceTags(self, request, context):
        placename = request.placename
        tags = dict(request.tags)
        try:
            place = self.places[placename]
        except KeyError:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Place {placename} does not exist")
        assert isinstance(tags, dict)
        for k, v in tags.items():
            assert isinstance(k, str)
            assert isinstance(v, str)
            if not TAG_KEY.match(k):
                await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Key {k} in {tags} is invalid")
            if not TAG_VAL.match(v):
                await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Value {v} in {tags} is invalid")
        for k, v in tags.items():
            if not v:
                try:
                    del place.tags[k]
                except KeyError:
                    pass
            else:
                place.tags[k] = v
        place.touch()
        self._publish_place(place)
        self.save_later()
        return labgrid_coordinator_pb2.SetPlaceTagsResponse()

    @locked
    async def SetPlaceComment(self, request, context):
        placename = request.placename
        comment = request.comment
        try:
            place = self.places[placename]
        except KeyError:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Place {placename} does not exist")
        place.comment = comment
        place.touch()
        self._publish_place(place)
        self.save_later()
        return labgrid_coordinator_pb2.SetPlaceCommentResponse()

    @locked
    async def AddPlaceMatch(self, request, context):
        placename = request.placename
        pattern = request.pattern
        rename = request.rename if request.HasField("rename") else None;
        try:
            place = self.places[placename]
        except KeyError:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Place {placename} does not exist")
        rm = ResourceMatch(*pattern.split('/'), rename=rename)
        if rm in place.matches:
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, f"Match {rm} already exists")  # FIXME: functional change, previously client skipped match while complaining
        place.matches.append(rm)
        place.touch()
        self._publish_place(place)
        self.save_later()
        return labgrid_coordinator_pb2.AddPlaceMatchResponse()

    @locked
    async def DeletePlaceMatch(self, request, context):
        placename = request.placename
        pattern = request.pattern
        rename = request.rename if request.HasField("rename") else None;
        try:
            place = self.places[placename]
        except KeyError:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Place {placename} does not exist")
        rm = ResourceMatch(*pattern.split('/'), rename=rename)
        try:
            place.matches.remove(rm)
        except ValueError:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Match {rm} does not exist in {placename}")
        place.touch()
        self._publish_place(place)
        self.save_later()
        return labgrid_coordinator_pb2.DeletePlaceMatchResponse()

    @locked
    async def AllowPlace(self, request, context):
        placename = request.placename
        user = request.user
        peer = context.peer()
        try:
            username = self.clients[peer].name
        except KeyError:
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, f"Peer {peer} does not have a valid session")
        try:
            place = self.places[placename]
        except KeyError:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Place {placename} does not exist")
        if not place.acquired:
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, f"Place {name} is not acquired")
        if not place.acquired == username:
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, f"Place {name} is not acquired by {username}")
        place.allowed.add(user)
        place.touch()
        self._publish_place(place)
        self.save_later()
        return labgrid_coordinator_pb2.AllowPlaceResponse()

    @locked
    async def CreateReservation(self, request, context):
        peer = context.peer()
        spec = request.spec
        prio = request.prio
        filter_ = {}
        for pair in spec.split():
            try:
                k, v = pair.split('=')
            except ValueError:
                await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Could not split {pair} in {spec}")
            if not TAG_KEY.match(k):
                await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Key {k} in {pair} is invalid")
            if not TAG_VAL.match(v):
                await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Value {v} in {pair} is invalid")
            filter_[k] = v

        filters = {'main': filter_} # currently, only one group is implemented

        owner = self.clients[peer].name
        res = Reservation(owner=owner, prio=prio, filters=filters)
        self.reservations[res.token] = res
        self.schedule_reservations()
        return res.as_pb2()

    async def test_exporter_command(self):
        logging.debug(f"testing exporter cmd")
        for peer, exporter in self.exporters.items():
            logging.debug(f"testing exporter cmd for '{peer}' sending")
            event = asyncio.Event()
            exporter.queue.put_nowait(event)
            await event.wait()
            logging.debug(f"testing exporter cmd for '{peer}': done")

async def serve(cleanup) -> None:
    server = grpc.aio.server(
        options=[
            ('grpc.keepalive_time_ms', 30000),  # Send keepalive ping every 30 seconds
            ('grpc.keepalive_timeout_ms', 10000),  # Wait 10 seconds for ping ack before considering the connection dead
            ('grpc.http2.min_time_between_pings_ms', 15000),  # Minimum amount of time between pings
            ('grpc.http2.max_pings_without_data', 0),  # Allow pings even without active streams
            ('grpc.keepalive_permit_without_calls', 1),  # Allow keepalive pings even when there are no calls
        ],
    )
    logging.debug("Created dummy labgrid coordinator")
    coordinator = Coordinator()
    labgrid_coordinator_pb2_grpc.add_LabgridServicer_to_server(
        coordinator, server
    )
    server.add_insecure_port("[::]:20408")
    logging.debug("Starting server")
    await server.start()
    logging.debug("Coordinator ready")
    #await asyncio.sleep(10)
    #await coordinator.test_exporter_command()
    async def server_graceful_shutdown():
        logging.info("Starting graceful shutdown...")
        # Shuts down the server with 0 seconds of grace period. During the
        # grace period, the server won't accept new connections and allow
        # existing RPCs to continue within the grace period.
        await server.stop(5)
    cleanup.append(server_graceful_shutdown())
    await server.wait_for_termination()

def main():
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    cleanup = []
    loop.set_debug(True)
    try:
        loop.run_until_complete(serve(cleanup))
    finally:
        loop.run_until_complete(*cleanup)

if __name__ == "__main__":
    main()
