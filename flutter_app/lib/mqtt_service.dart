import 'dart:io';
import 'package:mqtt_client/mqtt_client.dart';
import 'package:mqtt_client/mqtt_server_client.dart';

class MqttService {
  MqttServerClient? client;
  final String broker = 'broker.hivemq.com';
  final String clientId = 'smart_farm_flutter_${DateTime.now().millisecondsSinceEpoch}';
  
  // Callback for when new sensor data arrives
  Function(String topic, String payload)? onMessage;

  Future<bool> connect() async {
    client = MqttServerClient(broker, '');
    client!.port = 1883;
    client!.logging(on: false);
    client!.keepAlivePeriod = 60;
    client!.onDisconnected = onDisconnected;
    client!.onConnected = onConnected;
    client!.onSubscribed = onSubscribed;

    final connMess = MqttConnectMessage()
        .withClientIdentifier(clientId)
        .withWillQos(MqttQos.atLeastOnce);
    print('MQTT: Client connecting....');
    client!.connectionMessage = connMess;

    try {
      await client!.connect();
    } on NoConnectionException catch (e) {
      print('MQTT: Client exception - $e');
      client!.disconnect();
      return false;
    } on SocketException catch (e) {
      print('MQTT: Socket exception - $e');
      client!.disconnect();
      return false;
    }

    if (client!.connectionStatus!.state == MqttConnectionState.connected) {
      print('MQTT: Client connected');
      client!.updates!.listen((List<MqttReceivedMessage<MqttMessage?>>? c) {
        final recMess = c![0].payload as MqttPublishMessage;
        final pt = MqttPublishPayload.bytesToStringAsString(recMess.payload.message);
        final topic = c[0].topic;
        print('MQTT: Received message: topic is <$topic>, payload is <-- $pt -->');
        if (onMessage != null) {
          onMessage!(topic, pt);
        }
      });
      return true;
    } else {
      print('MQTT: ERROR Client connection failed - disconnecting, status is ${client!.connectionStatus}');
      client!.disconnect();
      return false;
    }
  }

  void subscribeToSensors() {
    print('MQTT: Subscribing to sitech/farm/#');
    client!.subscribe('sitech/farm/#', MqttQos.atMostOnce);
  }

  void publishMessage(String topic, String message) {
    final builder = MqttClientPayloadBuilder();
    builder.addString(message);
    client!.publishMessage(topic, MqttQos.atLeastOnce, builder.payload!);
    print('MQTT: Published to $topic: $message');
  }

  void onConnected() {
    print('MQTT: Connected');
  }

  void onDisconnected() {
    print('MQTT: Disconnected');
  }

  void onSubscribed(String topic) {
    print('MQTT: Subscribed to topic $topic');
  }
}
