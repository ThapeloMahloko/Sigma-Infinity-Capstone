import 'package:mqtt_client/mqtt_client.dart';
import 'package:mqtt_client/mqtt_browser_client.dart';

MqttClient setupMqttClient(String broker, String clientId) {
  final client = MqttBrowserClient('wss://$broker/mqtt', clientId);
  client.port = 8884;
  client.websocketProtocols = MqttClientConstants.protocolsSingleDefault;
  return client;
}
