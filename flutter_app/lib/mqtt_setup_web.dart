import 'package:mqtt_client/mqtt_client.dart';
import 'package:mqtt_client/mqtt_browser_client.dart';

MqttClient setupMqttClient(String broker, String clientId) {
  final isHttpsPage = Uri.base.scheme == 'https';
  final scheme = isHttpsPage ? 'wss' : 'ws';
  final port = isHttpsPage ? 8884 : 8000;
  final client = MqttBrowserClient('$scheme://$broker/mqtt', clientId);

  client.port = port;
  client.websocketProtocols = MqttClientConstants.protocolsSingleDefault;
  return client;
}
