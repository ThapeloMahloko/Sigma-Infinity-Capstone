// ignore_for_file: avoid_print

import 'dart:async';
import 'dart:io';

import 'package:mqtt_client/mqtt_client.dart';
import 'package:mqtt_client/mqtt_server_client.dart';

Future<void> main() async {
  const broker = 'broker.hivemq.com';
  const topic = 'sitech/farm/temp';
  const testPayload = '25.5';
  final clientId = 'probe${DateTime.now().millisecondsSinceEpoch}';

  final client = MqttServerClient(broker, clientId)
    ..port = 1883
    ..setProtocolV311()
    ..keepAlivePeriod = 20
    ..logging(on: false)
    ..connectionMessage = MqttConnectMessage()
        .withClientIdentifier(clientId)
        .startClean();

  print('Connecting to $broker:1883 as $clientId...');

  try {
    await client.connect();
  } catch (error) {
    print('Connect failed: $error');
    client.disconnect();
    exitCode = 1;
    return;
  }

  if (client.connectionStatus?.state != MqttConnectionState.connected) {
    print('Connect failed: ${client.connectionStatus}');
    client.disconnect();
    exitCode = 1;
    return;
  }

  print('Connected. Subscribing to $topic...');
  final received = Completer<String>();

  client.updates?.listen((messages) {
    if (messages.isEmpty) return;
    final message = messages.first.payload;
    if (message is! MqttPublishMessage) return;

    final payload = MqttPublishPayload.bytesToStringAsString(
      message.payload.message,
    );
    print('Received ${messages.first.topic}: $payload');

    if (!received.isCompleted && messages.first.topic == topic) {
      received.complete(payload);
    }
  });

  client.subscribe(topic, MqttQos.atMostOnce);
  await Future<void>.delayed(const Duration(seconds: 1));

  final builder = MqttClientPayloadBuilder()..addString(testPayload);
  print('Publishing $topic: $testPayload');
  client.publishMessage(topic, MqttQos.atMostOnce, builder.payload!);

  try {
    final payload = await received.future.timeout(const Duration(seconds: 10));
    print('MQTT probe passed. Echo payload: $payload');
  } on TimeoutException {
    print('MQTT probe timed out waiting for $topic.');
    exitCode = 1;
  } finally {
    client.disconnect();
  }
}
