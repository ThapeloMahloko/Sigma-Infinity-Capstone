// ignore_for_file: avoid_print

import 'dart:async';

import 'package:mqtt_client/mqtt_client.dart';

import 'mqtt_setup.dart';

class MqttService {
  static const String sensorTopicFilter = 'sitech/farm/#';

  MqttClient? client;
  final String broker = 'broker.hivemq.com';
  final String clientId = 'sf${DateTime.now().millisecondsSinceEpoch}';

  StreamSubscription<List<MqttReceivedMessage<MqttMessage>>>?
  _updatesSubscription;

  // Callback for when new sensor data arrives
  Function(String topic, String payload)? onMessage;
  Function(bool connected)? onConnectionChanged;

  bool get isConnected =>
      client?.connectionStatus?.state == MqttConnectionState.connected;

  Future<bool> connect() async {
    if (isConnected) return true;

    client = setupMqttClient(broker, clientId);
    client!
      ..setProtocolV311()
      ..logging(on: false)
      ..keepAlivePeriod = 30
      ..connectTimeoutPeriod = 5000
      ..autoReconnect = true
      ..resubscribeOnAutoReconnect = true
      ..onDisconnected = _onDisconnected
      ..onConnected = _onConnected
      ..onAutoReconnect = _onAutoReconnect
      ..onAutoReconnected = _onAutoReconnected
      ..onSubscribed = _onSubscribed
      ..onSubscribeFail = _onSubscribeFail;

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

    print(
      'MQTT: ERROR Client connection failed - status is ${client!.connectionStatus}',
    );
    _safeDisconnect();
    return false;
  }

  Future<void> _listenForUpdates() async {
    await _updatesSubscription?.cancel();
    _updatesSubscription = client!.updates?.listen((messages) {
      if (messages.isEmpty) return;

      final recMess = messages.first.payload;
      if (recMess is! MqttPublishMessage) return;

      final payload = MqttPublishPayload.bytesToStringAsString(
        recMess.payload.message,
      );
      final topic = messages.first.topic;
      print(
        'MQTT: Received message: topic is <$topic>, payload is <-- $payload -->',
      );
      onMessage?.call(topic, payload);
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

  void disconnect() {
    _updatesSubscription?.cancel();
    _updatesSubscription = null;
    _safeDisconnect();
  }

  void _safeDisconnect() {
    try {
      client?.disconnect();
    } catch (_) {
      // The mqtt_client package can throw if disconnect happens mid-setup.
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
