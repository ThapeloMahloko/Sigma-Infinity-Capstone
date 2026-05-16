// ignore_for_file: avoid_print

import 'dart:async';
import 'package:mqtt_client/mqtt_client.dart';
import 'mqtt_setup.dart';

class MqttService {
  static const String sensorTopicFilter = 'sitech/farm/#';

  MqttClient? client;
  final String broker = 'broker.hivemq.com';
  final String clientId = 'sf${DateTime.now().millisecondsSinceEpoch}';

  StreamSubscription<List<MqttReceivedMessage<MqttMessage>>>? _updatesSubscription;

  // Callback for when new sensor data arrives
  Function(String topic, String payload)? onMessage;
  Function(bool connected)? onConnectionChanged;

  bool get isConnected => client?.connectionStatus?.state == MqttConnectionState.connected;

  Future<bool> connect() async {
    if (isConnected) return true;

    client = setupMqttClient(broker, clientId);
    
    client!.setProtocolV311();
    client!.logging(on: false);
    client!.keepAlivePeriod = 30;
    
    // Direct assignments instead of cascade to avoid runtime errors
    client!.autoReconnect = true;
    client!.resubscribeOnAutoReconnect = true;
    
    // Callbacks outside cascade
    client!.onDisconnected = _onDisconnected;
    client!.onConnected = _onConnected;
    client!.onAutoReconnect = _onAutoReconnect;
    client!.onAutoReconnected = _onAutoReconnected;
    client!.onSubscribed = _onSubscribed;
    client!.onSubscribeFail = _onSubscribeFail;

    final connMess = MqttConnectMessage()
        .withClientIdentifier(clientId)
        .startClean();
    print('MQTT: Client connecting to $broker as $clientId');
    client!.connectionMessage = connMess;

    try {
      await client!.connect();
    } on NoConnectionException catch (e) {
      print('MQTT: Client exception - $e');
      _safeDisconnect();
      return false;
    } catch (e) {
      print('MQTT: General connection exception - $e');
      _safeDisconnect();
      return false;
    }

    if (isConnected) {
      print('MQTT: Client connected');
      await _listenForUpdates();
      onConnectionChanged?.call(true);
      return true;
    }

    print('MQTT: ERROR Client connection failed - status is ${client!.connectionStatus}');
    _safeDisconnect();
    return false;
  }

  Future<void> _listenForUpdates() async {
    await _updatesSubscription?.cancel();
    _updatesSubscription = client!.updates?.listen((messages) {
      if (messages.isEmpty) return;

      // Iterate all messages in the batch, not just the first!
      for (final message in messages) {
        final recMess = message.payload;
        if (recMess is! MqttPublishMessage) continue;

        final payload = MqttPublishPayload.bytesToStringAsString(recMess.payload.message);
        final topic = message.topic;
        print('MQTT: Received message: topic is <$topic>, payload is <-- $payload -->');
        onMessage?.call(topic, payload);
      }
    });
  }

  bool subscribeToSensors() {
    if (!isConnected) {
      print('MQTT: Cannot subscribe. Client is disconnected.');
      return false;
    }

    print('MQTT: Subscribing to $sensorTopicFilter');
    return client!.subscribe(sensorTopicFilter, MqttQos.atMostOnce) != null;
  }

  bool publishMessage(String topic, String message) {
    if (!isConnected) {
      print('MQTT: Cannot publish. Client is disconnected.');
      return false;
    }

    try {
      final builder = MqttClientPayloadBuilder();
      builder.addString(message);
      client!.publishMessage(topic, MqttQos.atMostOnce, builder.payload!);
      print('MQTT: Published to $topic: $message');
      return true;
    } catch (e) {
      print('MQTT: Publish failed for $topic - $e');
      return false;
    }
  }

  // Convenience methods
  void pumpOn() => publishMessage('sitech/farm/control/pump', 'ON');
  void pumpOff() => publishMessage('sitech/farm/control/pump', 'OFF');
  void fanOn() => publishMessage('sitech/farm/control/fan_speed', '130');
  void fanOff() => publishMessage('sitech/farm/control/fan_speed', '0');
  void alarmOn() => publishMessage('sitech/farm/control/alarm', 'ON');
  void alarmOff() => publishMessage('sitech/farm/control/alarm', 'OFF');
  void feedOpen() => publishMessage('sitech/farm/control/feed', 'OPEN');
  void feedClose() => publishMessage('sitech/farm/control/feed', 'CLOSE');

  void disconnect() {
    _updatesSubscription?.cancel();
    _updatesSubscription = null;
    _safeDisconnect();
  }

  void _safeDisconnect() {
    try {
      client?.disconnect();
    } catch (_) {
    } finally {
      client = null; // Null out _client after disconnect so isConnected reports correctly
    }
  }

  void _onConnected() {
    print('MQTT: Connected');
    onConnectionChanged?.call(true);
  }

  void _onDisconnected() {
    print('MQTT: Disconnected');
    onConnectionChanged?.call(false);
  }

  void _onAutoReconnect() {
    print('MQTT: Reconnecting...');
    onConnectionChanged?.call(false);
  }

  void _onAutoReconnected() {
    print('MQTT: Reconnected');
    onConnectionChanged?.call(true);
    subscribeToSensors();
  }

  void _onSubscribed(String topic) {
    print('MQTT: Subscribed to topic $topic');
  }

  void _onSubscribeFail(String topic) {
    print('MQTT: Failed to subscribe to topic $topic');
  }
}
