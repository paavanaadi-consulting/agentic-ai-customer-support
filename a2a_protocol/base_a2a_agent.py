"""
Base A2A agent with protocol capabilities
"""
import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from abc import ABC, abstractmethod
import websockets
import logging

class A2AMessage:
    """A2A protocol message structure"""
    def __init__(self, sender_id: str, receiver_id: str, message_type: str, payload: Dict[str, Any], request_id: str = None):
        self.message_id = str(uuid.uuid4())
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.message_type = message_type
        self.payload = payload
        self.request_id = request_id or str(uuid.uuid4())
        self.timestamp = datetime.now().isoformat()
    def to_dict(self) -> Dict[str, Any]:
        return {
            'message_id': self.message_id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'message_type': self.message_type,
            'payload': self.payload,
            'request_id': self.request_id,
            'timestamp': self.timestamp
        }
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'A2AMessage':
        msg = cls(
            sender_id=data['sender_id'],
            receiver_id=data['receiver_id'],
            message_type=data['message_type'],
            payload=data['payload'],
            request_id=data.get('request_id')
        )
        msg.message_id = data['message_id']
        msg.timestamp = data['timestamp']
        return msg

class A2AAgent(ABC):
    """Base A2A agent with communication capabilities"""
    def __init__(self, agent_id: str, agent_type: str, port: int = None):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.port = port or self._get_default_port()
        self.server = None
        self.connections = {}  # agent_id -> websocket
        self.message_handlers = {}
        self.discovery_registry = {}  # Known agents
        self.logger = logging.getLogger(f"A2A.{agent_id}")
        self.running = False
        self.metrics = {
            'messages_sent': 0,
            'messages_received': 0,
            'successful_collaborations': 0,
            'failed_collaborations': 0
        }
        self._register_default_handlers()
    def _get_default_port(self) -> int:
        port_map = {'query': 8001, 'knowledge': 8002, 'response': 8003, 'coordinator': 8004}
        return port_map.get(self.agent_type, 8000)
    async def start(self):
        self.server = await websockets.serve(self._handle_connection, 'localhost', self.port)
        self.running = True
        self.logger.info(f"A2A agent {self.agent_id} started on port {self.port}")
        asyncio.create_task(self._discover_agents())
    async def stop(self):
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        for ws in self.connections.values():
            await ws.close()
        self.logger.info(f"A2A agent {self.agent_id} stopped")
    async def _handle_connection(self, websocket, path):
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg = A2AMessage.from_dict(data)
                    if msg.sender_id not in self.connections:
                        self.connections[msg.sender_id] = websocket
                        self.logger.info(f"New connection from agent {msg.sender_id}")
                    await self._process_message(msg)
                    self.metrics['messages_received'] += 1
                except json.JSONDecodeError:
                    self.logger.error("Received invalid JSON message")
                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")
        except websockets.exceptions.ConnectionClosed:
            agent_id = None
            for aid, ws in self.connections.items():
                if ws == websocket:
                    agent_id = aid
                    break
            if agent_id:
                del self.connections[agent_id]
                self.logger.info(f"Connection closed for agent {agent_id}")
    async def _process_message(self, message: A2AMessage):
        handler = self.message_handlers.get(message.message_type)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                self.logger.error(f"Error in message handler: {e}")
                await self.send_error_response(message, str(e))
        else:
            self.logger.warning(f"No handler for message type: {message.message_type}")
    def _register_default_handlers(self):
        self.message_handlers.update({
            'discovery_request': self._handle_discovery_request,
            'discovery_response': self._handle_discovery_response,
            'capability_query': self._handle_capability_query,
            'capability_response': self._handle_capability_response,
            'collaboration_request': self._handle_collaboration_request,
            'collaboration_response': self._handle_collaboration_response,
            'task_delegation': self._handle_task_delegation,
            'task_result': self._handle_task_result,
            'error': self._handle_error
        })
    async def send_message(self, receiver_id: str, message_type: str, payload: Dict[str, Any], request_id: str = None) -> bool:
        try:
            if receiver_id not in self.connections:
                await self._connect_to_agent(receiver_id)
            if receiver_id not in self.connections:
                self.logger.error(f"No connection to agent {receiver_id}")
                return False
            message = A2AMessage(
                sender_id=self.agent_id,
                receiver_id=receiver_id,
                message_type=message_type,
                payload=payload,
                request_id=request_id
            )
            websocket = self.connections[receiver_id]
            await websocket.send(json.dumps(message.to_dict()))
            self.metrics['messages_sent'] += 1
            return True
        except Exception as e:
            self.logger.error(f"Error sending message to {receiver_id}: {e}")
            return False
    async def _connect_to_agent(self, agent_id: str):
        if agent_id in self.discovery_registry:
            agent_info = self.discovery_registry[agent_id]
            try:
                uri = f"ws://{agent_info['host']}:{agent_info['port']}"
                websocket = await websockets.connect(uri)
                self.connections[agent_id] = websocket
                asyncio.create_task(self._handle_agent_messages(agent_id, websocket))
                self.logger.info(f"Connected to agent {agent_id}")
            except Exception as e:
                self.logger.error(f"Failed to connect to agent {agent_id}: {e}")
    async def _handle_agent_messages(self, agent_id: str, websocket):
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg = A2AMessage.from_dict(data)
                    await self._process_message(msg)
                    self.metrics['messages_received'] += 1
                except json.JSONDecodeError:
                    self.logger.error(f"Invalid JSON from agent {agent_id}")
                except Exception as e:
                    self.logger.error(f"Error processing message from {agent_id}: {e}")
        except websockets.exceptions.ConnectionClosed:
            if agent_id in self.connections:
                del self.connections[agent_id]
            self.logger.info(f"Connection to agent {agent_id} closed")
    async def _discover_agents(self):
        discovery_ports = [8001, 8002, 8003, 8004, 8005]
        for port in discovery_ports:
            if port != self.port:
                try:
                    uri = f"ws://localhost:{port}"
                    websocket = await websockets.connect(uri)
                    message = A2AMessage(
                        sender_id=self.agent_id,
                        receiver_id="broadcast",
                        message_type="discovery_request",
                        payload={
                            'agent_type': self.agent_type,
                            'capabilities': self.get_capabilities(),
                            'host': 'localhost',
                            'port': self.port
                        }
                    )
                    await websocket.send(json.dumps(message.to_dict()))
                    await websocket.close()
                except Exception:
                    pass
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        pass
    @abstractmethod
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
    async def _handle_discovery_request(self, message: A2AMessage):
        self.discovery_registry[message.sender_id] = {
            'agent_type': message.payload.get('agent_type'),
            'capabilities': message.payload.get('capabilities', []),
            'host': message.payload.get('host', 'localhost'),
            'port': message.payload.get('port')
        }
        await self.send_message(
            receiver_id=message.sender_id,
            message_type="discovery_response",
            payload={
                'agent_type': self.agent_type,
                'capabilities': self.get_capabilities(),
                'host': 'localhost',
                'port': self.port
            },
            request_id=message.request_id
        )
    async def _handle_discovery_response(self, message: A2AMessage):
        self.discovery_registry[message.sender_id] = {
            'agent_type': message.payload.get('agent_type'),
            'capabilities': message.payload.get('capabilities', []),
            'host': message.payload.get('host', 'localhost'),
            'port': message.payload.get('port')
        }
        self.logger.info(f"Discovered agent {message.sender_id} ({message.payload.get('agent_type')})")
    async def _handle_capability_query(self, message: A2AMessage):
        await self.send_message(
            receiver_id=message.sender_id,
            message_type="capability_response",
            payload={
                'capabilities': self.get_capabilities(),
                'available': True,
                'load': self._get_current_load()
            },
            request_id=message.request_id
        )
    async def _handle_capability_response(self, message: A2AMessage):
        if message.sender_id in self.discovery_registry:
            self.discovery_registry[message.sender_id].update({
                'capabilities': message.payload.get('capabilities', []),
                'available': message.payload.get('available', False),
                'load': message.payload.get('load', 0)
            })
    async def _handle_collaboration_request(self, message: A2AMessage):
        task_type = message.payload.get('task_type')
        if self._can_handle_task(task_type):
            await self.send_message(
                receiver_id=message.sender_id,
                message_type="collaboration_response",
                payload={
                    'accepted': True,
                    'estimated_time': self._estimate_task_time(task_type),
                    'confidence': self._get_task_confidence(task_type)
                },
                request_id=message.request_id
            )
        else:
            await self.send_message(
                receiver_id=message.sender_id,
                message_type="collaboration_response",
                payload={
                    'accepted': False,
                    'reason': 'Cannot handle this task type'
                },
                request_id=message.request_id
            )
    async def _handle_collaboration_response(self, message: A2AMessage):
        pass
    async def _handle_task_delegation(self, message: A2AMessage):
        try:
            result = await self.process_task(message.payload)
            await self.send_message(
                receiver_id=message.sender_id,
                message_type="task_result",
                payload={
                    'success': True,
                    'result': result,
                    'processing_time': result.get('processing_time', 0)
                },
                request_id=message.request_id
            )
            self.metrics['successful_collaborations'] += 1
        except Exception as e:
            await self.send_message(
                receiver_id=message.sender_id,
                message_type="task_result",
                payload={
                    'success': False,
                    'error': str(e)
                },
                request_id=message.request_id
            )
            self.metrics['failed_collaborations'] += 1
    async def _handle_task_result(self, message: A2AMessage):
        pass
    async def _handle_error(self, message: A2AMessage):
        self.logger.error(f"Received error from {message.sender_id}: {message.payload}")
    async def send_error_response(self, original_message: A2AMessage, error: str):
        await self.send_message(
            receiver_id=original_message.sender_id,
            message_type="error",
            payload={
                'error': error,
                'original_request': original_message.request_id
            }
        )
    def _can_handle_task(self, task_type: str) -> bool:
        return task_type in self.get_capabilities()
    def _estimate_task_time(self, task_type: str) -> float:
        return 1.0
    def _get_task_confidence(self, task_type: str) -> float:
        return 0.8
    def _get_current_load(self) -> float:
        return len(self.connections) / 10.0
    def get_metrics(self) -> Dict[str, Any]:
        return {
            **self.metrics,
            'connections': len(self.connections),
            'known_agents': len(self.discovery_registry),
            'agent_load': self._get_current_load()
        }
