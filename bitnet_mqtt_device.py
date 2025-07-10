#!/usr/bin/env python3
"""
Enhanced BitNet MQTT Device for Raspberry Pi
Integrates with Makerspace Certificate Service for device registration and certificate management
"""

import os
import sys
import json
import time
import uuid
import signal
import socket
import logging
import argparse
import threading
import subprocess
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import ssl
from cryptography import x509
from cryptography.x509.oid import NameOID

import paho.mqtt.client as mqtt


class DeviceRegistration:
    """Handles device registration with the Makerspace certificate service"""
    
    def __init__(self, service_url: str, device_config: Dict[str, Any]):
        self.service_url = service_url.rstrip('/')
        self.device_config = device_config
        self.logger = logging.getLogger(f"{__name__}.DeviceRegistration")
        
    def register_device(self) -> Optional[Dict[str, str]]:
        """Register this device with the certificate service and get certificates"""
        try:
            # Generate device registration payload (server expects camelCase deviceId)
            registration_data = {
                "deviceId": self.device_config["device_id"]
            }
            
            self.logger.info(f"Registering device {self.device_config['device_id']}")
            self.logger.debug(f"Registration payload: {json.dumps(registration_data, indent=2)}")
            
            # Send registration request
            response = requests.post(
                f"{self.service_url}/register-device",
                json=registration_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info("Device registration successful")
                self.logger.debug(f"Registration response: {json.dumps(result, indent=2)}")
                
                # Store the registration info for MQTT client configuration
                self.device_config["client_name"] = result["registration"]["clientName"]
                self.device_config["auth_name"] = result["registration"]["authenticationName"]
                
                # Extract certificates from the response
                if 'certificate' in result:
                    cert_info = result['certificate']
                    certificates = {
                        'client_cert': cert_info.get('certificate', ''),
                        'client_key': cert_info.get('privateKey', ''),
                        'public_key': cert_info.get('publicKey', '')
                    }
                    
                    # Also fetch CA certificate separately if available
                    try:
                        ca_response = requests.get(f"{self.service_url}/ca-certificate", timeout=10)
                        if ca_response.status_code == 200:
                            certificates['ca_cert'] = ca_response.text
                    except Exception as e:
                        self.logger.warning(f"Could not fetch CA certificate: {e}")
                    
                    return certificates
                else:
                    self.logger.error("No certificate data in registration response")
                    return None
            else:
                self.logger.error(f"Registration failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to register device: {e}")
            return None
    
    def get_certificates(self, device_id: str) -> Optional[Dict[str, str]]:
        """Retrieve certificates for the device"""
        try:
            response = requests.get(
                f"{self.service_url}/api/devices/{device_id}/certificates",
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get certificates: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve certificates: {e}")
            return None
    
    def _get_mac_address(self) -> str:
        """Get the MAC address of the primary network interface"""
        try:
            mac = uuid.getnode()
            return ':'.join(f'{(mac >> i) & 0xff:02x}' for i in range(0, 48, 8)[::-1])
        except:
            return "unknown"
    
    def _get_local_ip(self) -> str:
        """Get the local IP address"""
        try:
            # Create a socket to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "unknown"


class CertificateManager:
    """Manages device certificates for MQTT TLS authentication"""
    
    def __init__(self, cert_dir: Path):
        self.cert_dir = Path(cert_dir)
        self.cert_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(f"{__name__}.CertificateManager")
        
    def save_certificates(self, cert_data: Dict[str, str], device_id: str) -> Dict[str, Path]:
        """Save certificates to files"""
        try:
            cert_files = {}
            
            # Save client certificate
            if 'client_cert' in cert_data:
                cert_file = self.cert_dir / f"{device_id}.crt"
                cert_file.write_text(cert_data['client_cert'])
                cert_files['cert'] = cert_file
                self.logger.info(f"Saved client certificate to {cert_file}")
            
            # Save client private key
            if 'client_key' in cert_data:
                key_file = self.cert_dir / f"{device_id}.key"
                key_file.write_text(cert_data['client_key'])
                key_file.chmod(0o600)  # Secure permissions
                cert_files['key'] = key_file
                self.logger.info(f"Saved private key to {key_file}")
            
            # Save CA certificate
            if 'ca_cert' in cert_data:
                ca_file = self.cert_dir / "ca.crt"
                ca_file.write_text(cert_data['ca_cert'])
                cert_files['ca'] = ca_file
                self.logger.info(f"Saved CA certificate to {ca_file}")
            
            return cert_files
            
        except Exception as e:
            self.logger.error(f"Failed to save certificates: {e}")
            return {}
    
    def validate_certificates(self, cert_files: Dict[str, Path]) -> bool:
        """Validate that certificates are valid and not expired"""
        try:
            if 'cert' not in cert_files or not cert_files['cert'].exists():
                return False
                
            # Load and validate client certificate
            cert_data = cert_files['cert'].read_bytes()
            cert = x509.load_pem_x509_certificate(cert_data)
            
            # Check if certificate is still valid
            now = datetime.utcnow()
            if cert.not_valid_after <= now:
                self.logger.warning("Client certificate has expired")
                return False
            
            if cert.not_valid_before > now:
                self.logger.warning("Client certificate is not yet valid")
                return False
            
            # Check if expiring soon (within 7 days)
            if cert.not_valid_after <= now + timedelta(days=7):
                self.logger.warning("Client certificate expires soon")
            
            self.logger.info("Certificates are valid")
            return True
            
        except Exception as e:
            self.logger.error(f"Certificate validation failed: {e}")
            return False


class MqttMessage:
    """Represents an MQTT message with metadata"""
    
    def __init__(self, device_id: str, content: str, timestamp: datetime = None, message_type: str = "general"):
        self.device_id = device_id
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.message_type = message_type
        self.id = str(uuid.uuid4())
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "message_type": self.message_type
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MqttMessage':
        """Create message from dictionary"""
        msg = cls(
            device_id=data["device_id"],
            content=data["content"],
            message_type=data.get("message_type", "general")
        )
        if "timestamp" in data:
            msg.timestamp = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
        if "id" in data:
            msg.id = data["id"]
        return msg


class BitNetInference:
    """Handles BitNet inference execution"""
    
    def __init__(self, bitnet_path: str = "../BitNet"):
        self.bitnet_path = Path(bitnet_path).resolve()
        self.inference_script = self.bitnet_path / "run_inference.py"
        self.logger = logging.getLogger(f"{__name__}.BitNetInference")
        
    def validate_setup(self) -> bool:
        """Verify that BitNet repository and required files exist"""
        if not self.bitnet_path.exists():
            self.logger.error(f"BitNet repository not found at: {self.bitnet_path}")
            return False
            
        if not self.inference_script.exists():
            self.logger.error(f"Inference script not found at: {self.inference_script}")
            return False
            
        build_dir = self.bitnet_path / "build"
        if not build_dir.exists():
            self.logger.error(f"Build directory not found at: {build_dir}")
            return False
            
        return True
    
    def generate_response(self, prompt: str, **kwargs) -> Optional[str]:
        """Generate response using BitNet inference"""
        if not self.validate_setup():
            return None
            
        # Build command arguments
        cmd = [
            sys.executable,
            str(self.inference_script),
            "-p", prompt,
            "-n", str(kwargs.get('n_predict', 128)),
            "-t", str(kwargs.get('threads', 2)),
        ]
        
        model_path = kwargs.get('model_path')
        if model_path:
            cmd.extend(["-m", model_path])
            
        if kwargs.get('conversation', False):
            cmd.append("-cnv")
            
        # Log the command that will be executed
        full_cmd = f"cd {self.bitnet_path} && {' '.join(cmd)}"
        self.logger.info(f"Executing inference command: {full_cmd}")
        
        try:
            # Execute the BitNet inference command
            result = subprocess.run(
                cmd,
                cwd=self.bitnet_path,
                capture_output=True,
                text=True,
                timeout=kwargs.get('timeout', 1000)  # Default 1000 second timeout
            )
            
            if result.returncode == 0:
                # Successful execution
                response = result.stdout.strip()
                self.logger.info(f"BitNet inference successful ({len(response)} chars)")
                return response
            else:
                # Command failed
                self.logger.error(f"BitNet inference failed with return code {result.returncode}")
                self.logger.error(f"STDERR: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.error("BitNet inference timed out")
            return None
        except Exception as e:
            self.logger.error(f"Error executing BitNet inference: {e}")
            return None


class BitNetMqttDevice:
    """Main service that combines MQTT communication with BitNet inference and certificate management"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.device_id = self._generate_device_id()
        self.running = False
        self.mqtt_client = None
        self.bitnet = BitNetInference(config.get('bitnet_path', '../BitNet'))
        self.message_history = []
        self.is_connected = False
        self.join_message_sent = False
        
        # Certificate management
        self.cert_manager = CertificateManager(config.get('cert_dir', './certs'))
        self.device_registration = DeviceRegistration(
            config.get('cert_service_url', 'https://makerspace-cert-service.proudwave-5e4592e9.westus2.azurecontainerapps.io'),
            {
                "device_id": self.device_id,
                "device_type": config.get('device_type', 'raspberry_pi'),
                "capabilities": config.get('capabilities', ['mqtt', 'bitnet']),
                "location": config.get('location', 'unknown'),
                "description": config.get('description', f'BitNet MQTT device {self.device_id}')
            }
        )
        
        self.setup_logging()
        self.logger = logging.getLogger(f"{__name__}.BitNetMqttDevice")
        
    def setup_logging(self):
        """Configure logging for the service"""
        log_level = getattr(logging, self.config.get('log_level', 'INFO').upper())
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.get('log_file', 'bitnet_mqtt_device.log')),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _generate_device_id(self) -> str:
        """Generate unique device identifier"""
        custom_id = self.config.get('device_id')
        if custom_id:
            return custom_id
            
        hostname = socket.gethostname()
        mac_suffix = hex(uuid.getnode())[-6:]
        return f"bitnet-{hostname}-{mac_suffix}"
    
    def ensure_certificates(self) -> bool:
        """Ensure device has valid certificates, registering if necessary"""
        try:
            # Check if we have existing certificates
            cert_files = {
                'cert': self.cert_manager.cert_dir / f"{self.device_id}.crt",
                'key': self.cert_manager.cert_dir / f"{self.device_id}.key",
                'ca': self.cert_manager.cert_dir / "ca.crt"
            }
            
            # Validate existing certificates
            if all(f.exists() for f in cert_files.values()):
                if self.cert_manager.validate_certificates(cert_files):
                    self.logger.info("Using existing valid certificates")
                    return True
                else:
                    self.logger.warning("Existing certificates are invalid, re-registering")
            
            # Register device and get certificates
            self.logger.info("Registering device with certificate service")
            cert_data = self.device_registration.register_device()
            
            if not cert_data:
                self.logger.error("Device registration failed")
                return False
            
            # Save certificates
            saved_files = self.cert_manager.save_certificates(cert_data, self.device_id)
            if not saved_files:
                self.logger.error("Failed to save certificates")
                return False
            
            self.logger.info("Device registration and certificate setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error ensuring certificates: {e}")
            return False
    
    def _should_respond(self, message: MqttMessage) -> bool:
        """Determine if the service should respond to a message"""
        # Don't respond to own messages
        if message.device_id == self.device_id:
            self.logger.debug(f"Not responding to own message from {message.device_id}")
            return False
            
        # Apply custom response criteria
        response_criteria = self.config.get('response_criteria', {})
        
        # Check message type filter
        allowed_types = response_criteria.get('message_types', ['general'])
        if message.message_type not in allowed_types:
            self.logger.debug(f"Message type '{message.message_type}' not in allowed types {allowed_types}")
            return False
            
        # Check content filters
        content_filters = response_criteria.get('content_filters', [])
        content_match = False
        for filter_item in content_filters:
            if filter_item.lower() in message.content.lower():
                content_match = True
                break
                
        if content_filters and not content_match:
            self.logger.debug(f"Content '{message.content}' doesn't match any filters {content_filters}")
            # Continue to check default_respond setting
        elif content_match:
            self.logger.debug(f"Content matched filter, will respond")
            return True
                
        # Check response probability
        response_probability = response_criteria.get('probability', 1.0)
        if response_probability < 1.0:
            import random
            if random.random() > response_probability:
                self.logger.debug(f"Failed probability check ({response_probability})")
                return False
                
        # Default behavior based on configuration
        default_respond = response_criteria.get('default_respond', True)
        self.logger.debug(f"Using default_respond setting: {default_respond}")
        return default_respond
    
    def _generate_prompt(self, message: MqttMessage, context: List[MqttMessage]) -> str:
        """Generate prompt for BitNet based on message and context"""
        prompt_template = self.config.get('prompt_template', 
            "You are a helpful AI assistant in an IoT network. "
            "Device {device_id} said: '{content}'. "
            "Recent context: {context}. "
            "Provide a helpful, concise response."
        )
        
        # Prepare context string
        context_str = ""
        if context:
            recent_messages = context[-3:]  # Last 3 messages for context
            context_str = " | ".join([f"{msg.device_id}: {msg.content}" for msg in recent_messages])
        
        prompt = prompt_template.format(
            device_id=message.device_id,
            content=message.content,
            context=context_str,
            own_device_id=self.device_id
        )
        
        return prompt
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            self.logger.info("Connected to MQTT broker")
            self.is_connected = True
            topic = self.config['mqtt']['topic']
            client.subscribe(topic)
            self.logger.info(f"Subscribed to topic: {topic}")
            
            # Send initial presence message only once per service start
            if not self.join_message_sent:
                presence_msg = MqttMessage(
                    device_id=self.device_id,
                    content=f"Device {self.device_id} joined the network with BitNet capabilities",
                    message_type="presence"
                )
                self.publish_message(presence_msg)
                self.join_message_sent = True
        else:
            self.logger.error(f"Failed to connect to MQTT broker: {rc}")
            self.is_connected = False
    
    def on_mqtt_message(self, client, userdata, msg):
        """Callback for received MQTT messages"""
        try:
            raw_payload = msg.payload.decode()
            self.logger.debug(f"Raw MQTT payload: {raw_payload}")
            
            payload = json.loads(raw_payload)
            self.logger.debug(f"Parsed JSON payload: {payload}")
            
            # Check if payload has required fields
            if 'device_id' not in payload:
                self.logger.warning(f"Missing 'device_id' in payload: {payload}")
                return
            if 'content' not in payload:
                self.logger.warning(f"Missing 'content' in payload: {payload}")
                return
                
            message = MqttMessage.from_dict(payload)
            
            self.logger.info(f"Received message from {message.device_id}: {message.content[:100]}...")
            
            # Add to message history
            self.message_history.append(message)
            if len(self.message_history) > 100:  # Keep last 100 messages
                self.message_history.pop(0)
            
            # Decide whether to respond
            if self._should_respond(message):
                self._handle_response(message)
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to decode MQTT message: {e}. Raw payload: {msg.payload.decode()}")
        except KeyError as e:
            self.logger.error(f"Missing required field {e} in MQTT message: {payload}")
        except Exception as e:
            self.logger.error(f"Error processing MQTT message: {e}. Payload: {msg.payload.decode()}")
    
    def on_mqtt_log(self, client, userdata, level, buf):
        """Callback for MQTT logging"""
        self.logger.debug(f"MQTT Log: {buf}")
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        self.is_connected = False
        if rc != 0:
            self.logger.warning(f"Unexpected MQTT disconnection (code: {rc})")
        else:
            self.logger.info("MQTT client disconnected")
    
    def _handle_response(self, message: MqttMessage):
        """Handle generating and sending a response to a message"""
        def response_worker():
            try:
                self.logger.info(f"Generating response to message from {message.device_id}")
                
                # Generate prompt with context
                prompt = self._generate_prompt(message, self.message_history[:-1])
                
                # Get BitNet inference parameters
                inference_params = self.config.get('bitnet_params', {})
                
                # Generate response
                response_content = self.bitnet.generate_response(prompt, **inference_params)
                
                if response_content:
                    # Create response message
                    response_msg = MqttMessage(
                        device_id=self.device_id,
                        content=response_content,
                        message_type="response"
                    )
                    
                    # Add delay to avoid flooding
                    delay = self.config.get('response_delay', 2.0)
                    time.sleep(delay)
                    
                    # Publish response
                    self.publish_message(response_msg)
                    self.logger.info(f"Published response to {message.device_id}")
                else:
                    self.logger.warning("Failed to generate response")
                    
            except Exception as e:
                self.logger.error(f"Error in response worker: {e}")
        
        # Run response generation in background thread
        thread = threading.Thread(target=response_worker, daemon=True)
        thread.start()
    
    def publish_message(self, message: MqttMessage):
        """Publish a message to MQTT topic"""
        if self.mqtt_client and self.mqtt_client.is_connected():
            topic = self.config['mqtt']['topic']
            payload = json.dumps(message.to_dict())
            self.mqtt_client.publish(topic, payload)
            self.logger.debug(f"Published message: {message.content[:50]}...")
        else:
            self.logger.error("MQTT client not connected")
    
    def start(self) -> bool:
        """Start the MQTT BitNet service"""
        # Ensure certificates are available
        if not self.ensure_certificates():
            self.logger.error("Failed to ensure certificates")
            return False
        
        # Validate BitNet setup
        if not self.bitnet.validate_setup():
            self.logger.error("BitNet setup validation failed")
            return False
            
        self.logger.info(f"Starting BitNet MQTT Device with ID: {self.device_id}")
        
        # Get the actual client name and auth name from registration
        client_name = self.config.get("client_name", f"device-{self.device_id}")
        auth_name = self.config.get("auth_name", f"{self.device_id}-authnID")
        
        self.logger.info(f"Using MQTT client name: {client_name}")
        self.logger.info(f"Using MQTT auth name: {auth_name}")
        
        # Setup MQTT client
        self.mqtt_client = mqtt.Client(client_id=client_name)
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.on_log = self.on_mqtt_log  # Enable detailed logging
        self.mqtt_client.on_disconnect = self.on_mqtt_disconnect  # Handle disconnections
        
        # For Azure Event Grid MQTT with certificate authentication, 
        # the username should match the authentication name
        self.mqtt_client.username_pw_set(auth_name, "")
            
        # Configure TLS with certificates
        mqtt_config = self.config['mqtt']
            
        # Configure TLS with certificates
        if mqtt_config.get('use_tls', True):
            cert_files = {
                'cert': self.cert_manager.cert_dir / f"{self.device_id}.crt",
                'key': self.cert_manager.cert_dir / f"{self.device_id}.key",
                'ca': self.cert_manager.cert_dir / "ca.crt"
            }
            
            try:
                # Configure TLS context for client certificate authentication
                context = ssl.create_default_context()
                context.check_hostname = False  # Azure Event Grid uses certificate-based auth
                context.verify_mode = ssl.CERT_NONE  # Don't verify server cert with CA
                
                # Load only the client certificate and key for authentication
                context.load_cert_chain(str(cert_files['cert']), str(cert_files['key']))
                
                self.mqtt_client.tls_set_context(context)
                self.logger.info("TLS configured with client certificate authentication")
                
            except Exception as e:
                self.logger.error(f"Failed to configure TLS: {e}")
                return False
        
        try:
            # Connect to MQTT broker
            self.mqtt_client.connect(
                mqtt_config['broker'],
                mqtt_config.get('port', 8883),
                mqtt_config.get('keepalive', 60)
            )
            
            self.running = True
            self.mqtt_client.loop_start()
            
            self.logger.info("Service started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start service: {e}")
            return False
    
    def stop(self):
        """Stop the MQTT BitNet service"""
        self.logger.info("Stopping BitNet MQTT Device")
        self.running = False
        
        if self.mqtt_client:
            # Send goodbye message
            goodbye_msg = MqttMessage(
                device_id=self.device_id,
                content=f"Device {self.device_id} leaving the network",
                message_type="presence"
            )
            self.publish_message(goodbye_msg)
            time.sleep(1)  # Give time for message to send
            
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            
        # Reset connection state flags for potential restart
        self.is_connected = False
        self.join_message_sent = False
        
        self.logger.info("Service stopped")
    
    def send_manual_message(self, content: str, message_type: str = "manual"):
        """Send a manual message to the MQTT topic"""
        message = MqttMessage(
            device_id=self.device_id,
            content=content,
            message_type=message_type
        )
        self.publish_message(message)
    
    def run_forever(self):
        """Run the service until interrupted"""
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        finally:
            self.stop()


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in configuration file: {e}")
        sys.exit(1)


def create_default_config() -> Dict[str, Any]:
    """Create default configuration"""
    return {
        "mqtt": {
            "broker": "makerspace-eventgrid.westus2-1.ts.eventgrid.azure.net",
            "port": 8883,
            "topic": "devices/bitnet/messages",
            "keepalive": 60,
            "use_tls": True
        },
        "cert_service_url": "https://makerspace-cert-service.proudwave-5e4592e9.westus2.azurecontainerapps.io",
        "cert_dir": "./certs",
        "device_type": "raspberry_pi",
        "capabilities": ["mqtt", "bitnet", "ai_inference"],
        "location": "makerspace",
        "description": "BitNet-enabled IoT device for intelligent responses",
        "bitnet_path": "../BitNet",
        "bitnet_params": {
            "n_predict": 128,
            "threads": 2,
            "ctx_size": 2048,
            "temperature": 0.8,
            "conversation": False,
            "model_path": None,
            "timeout": 60
        },
        "response_criteria": {
            "default_respond": True,
            "probability": 0.8,
            "message_types": ["general", "question"],
            "content_filters": ["help", "what", "how", "explain", "?"]
        },
        "response_delay": 2.0,
        "log_level": "INFO",
        "log_file": "bitnet_mqtt_device.log",
        "prompt_template": "You are a helpful AI assistant in a makerspace IoT network. Device {device_id} said: '{content}'. Recent context: {context}. Provide a helpful, concise response about making, building, or technology."
    }


def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description='BitNet MQTT Device with Certificate Management')
    parser.add_argument(
        "--config", 
        type=str, 
        help="Path to configuration JSON file"
    )
    parser.add_argument(
        "--create-config",
        type=str,
        help="Create default configuration file at specified path"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Service command
    service_parser = subparsers.add_parser('service', help='Run MQTT service')
    service_parser.add_argument("--daemon", action='store_true', help="Run as daemon")
    
    # Send message command
    send_parser = subparsers.add_parser('send', help='Send manual message to MQTT topic')
    send_parser.add_argument("message", type=str, help="Message content to send")
    send_parser.add_argument("--type", type=str, default="manual", help="Message type")
    
    # Test inference command
    test_parser = subparsers.add_parser('test', help='Test BitNet inference')
    test_parser.add_argument("prompt", type=str, help="Test prompt")
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate BitNet setup and certificates')
    
    # Register command
    register_parser = subparsers.add_parser('register', help='Register device and get certificates')
    
    args = parser.parse_args()
    
    # Handle config creation
    if args.create_config:
        config = create_default_config()
        with open(args.create_config, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Default configuration created at: {args.create_config}")
        return
    
    # Load configuration
    if args.config:
        config = load_config(args.config)
    else:
        config = create_default_config()
        print("Using default configuration. Use --create-config to save a template.")
    
    if not args.command:
        parser.print_help()
        return
        
    # Handle commands
    if args.command == 'validate':
        device = BitNetMqttDevice(config)
        print("Validating BitNet setup...")
        if device.bitnet.validate_setup():
            print("✓ BitNet setup is valid")
        else:
            print("✗ BitNet setup validation failed")
            
        print("Validating certificates...")
        if device.ensure_certificates():
            print("✓ Certificates are valid")
        else:
            print("✗ Certificate validation failed")
            
    elif args.command == 'register':
        device = BitNetMqttDevice(config)
        print(f"Registering device {device.device_id}...")
        if device.ensure_certificates():
            print("✓ Device registration and certificate setup completed")
        else:
            print("✗ Device registration failed")
            
    elif args.command == 'test':
        device = BitNetMqttDevice(config)
        bitnet_params = config.get('bitnet_params', {})
        response = device.bitnet.generate_response(args.prompt, **bitnet_params)
        if response:
            print("Response:")
            print(response)
        else:
            print("Failed to generate response")
            sys.exit(1)
            
    elif args.command == 'send':
        device = BitNetMqttDevice(config)
        if device.start():
            time.sleep(2)  # Wait for connection
            device.send_manual_message(args.message, args.type)
            time.sleep(2)  # Wait for message to send
            device.stop()
        else:
            sys.exit(1)
            
    elif args.command == 'service':
        device = BitNetMqttDevice(config)
        
        def signal_handler(sig, frame):
            print("\nReceived interrupt signal, stopping service...")
            device.stop()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        if device.start():
            print(f"Service started with device ID: {device.device_id}")
            print("Press Ctrl+C to stop...")
            device.run_forever()
        else:
            print("Failed to start service")
            sys.exit(1)


if __name__ == "__main__":
    main()
