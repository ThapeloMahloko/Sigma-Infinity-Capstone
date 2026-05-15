import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'mqtt_service.dart';

void main() {
  runApp(const SmartFarmApp());
}

class SmartFarmApp extends StatelessWidget {
  const SmartFarmApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Smart Farm Dashboard',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF071411),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF0b1f1a),
          elevation: 0,
        ),
        textTheme: GoogleFonts.interTextTheme(
          Theme.of(context).textTheme.apply(
            bodyColor: Colors.white,
            displayColor: Colors.white,
          ),
        ),
      ),
      home: const DashboardScreen(),
    );
  }
}

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final MqttService _mqttService = MqttService();
  bool _isConnected = false;

  // Sensor Data
  double temperature = 0.0;
  double humidity = 0.0;
  double soil = 0.0;
  double water = 0.0;
  double light = 0.0;
  double rain = 0.0;
  double fanSpeed = 0.0;
  
  String alarmStatus = 'DISARMED';
  String feedStatus = 'CLOSED';
  String motionStatus = 'NO MOTION';

  @override
  void initState() {
    super.initState();
    _setupMqtt();
  }

  Future<void> _setupMqtt() async {
    _mqttService.onMessage = _handleMessage;
    bool connected = await _mqttService.connect();
    if (connected) {
      setState(() {
        _isConnected = true;
      });
      _mqttService.subscribeToSensors();
    }
  }

  void _handleMessage(String topic, String payload) {
    if (!mounted) return;

    setState(() {
      if (topic == 'sitech/farm/temp') {
        temperature = double.tryParse(payload) ?? temperature;
      } else if (topic == 'sitech/farm/humidity') {
        humidity = double.tryParse(payload) ?? humidity;
      } else if (topic == 'sitech/farm/soil') {
        soil = double.tryParse(payload) ?? soil;
      } else if (topic == 'sitech/farm/water') {
        water = double.tryParse(payload) ?? water;
      } else if (topic == 'sitech/farm/light') {
        light = double.tryParse(payload) ?? light;
      } else if (topic == 'sitech/farm/rain') {
        rain = double.tryParse(payload) ?? rain;
      } else if (topic == 'sitech/farm/fan_speed') {
        fanSpeed = double.tryParse(payload) ?? fanSpeed;
      } else if (topic == 'sitech/farm/alarm_status') {
        alarmStatus = payload;
      } else if (topic == 'sitech/farm/feed_status') {
        feedStatus = payload;
      } else if (topic == 'sitech/farm/alert') {
        motionStatus = payload;
      }
    });
  }

  void _sendCommand(String topic, String message) {
    if (_isConnected) {
      _mqttService.publishMessage(topic, message);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Cannot send command. MQTT disconnected.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Smart Farm Dashboard', style: TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              children: [
                Icon(
                  _isConnected ? Icons.cloud_done : Icons.cloud_off,
                  color: _isConnected ? const Color(0xFF42d392) : Colors.red,
                  size: 20,
                ),
                const SizedBox(width: 8),
                Text(
                  _isConnected ? 'Connected' : 'Offline',
                  style: const TextStyle(color: Color(0xFF8fb8aa)),
                )
              ],
            ),
          )
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          const Text(
            'LIVE SMART AGRICULTURE',
            style: TextStyle(
              fontSize: 12,
              letterSpacing: 2,
              color: Color(0xFF8fb8aa),
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'System Status',
            style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          _buildStatusCard(),
          const SizedBox(height: 24),
          const Text(
            'Sensor Readings',
            style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          GridView.count(
            crossAxisCount: MediaQuery.of(context).size.width > 600 ? 4 : 2,
            crossAxisSpacing: 16,
            mainAxisSpacing: 16,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            childAspectRatio: 1.2,
            children: [
              _buildSensorCard('TEMPERATURE', '${temperature.toStringAsFixed(1)}°C'),
              _buildSensorCard('HUMIDITY', '${humidity.toStringAsFixed(1)}%'),
              _buildSensorCard('SOIL MOISTURE', '${soil.toStringAsFixed(1)}%'),
              _buildSensorCard('WATER LEVEL', '${water.toStringAsFixed(1)}%'),
              _buildSensorCard('LIGHT', '${light.toStringAsFixed(1)}%'),
              _buildSensorCard('RAIN', '${rain.toStringAsFixed(1)}%'),
              _buildSensorCard('FAN SPEED', '${fanSpeed.toInt()}'),
            ],
          ),
          const SizedBox(height: 32),
          const Text(
            'Quick Controls',
            style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 16,
            runSpacing: 16,
            children: [
              _buildControlButton('Pump ON', Icons.water_drop, () => _sendCommand('sitech/farm/control/pump', 'ON')),
              _buildControlButton('Pump OFF', Icons.water_drop_outlined, () => _sendCommand('sitech/farm/control/pump', 'OFF'), isDanger: true),
              _buildControlButton('Fan ON', Icons.mode_fan_off_sharp, () => _sendCommand('sitech/farm/control/fan_speed', '130')),
              _buildControlButton('Fan OFF', Icons.mode_fan_off_sharp, () => _sendCommand('sitech/farm/control/fan_speed', '0'), isDanger: true),
              _buildControlButton('Alarm ON', Icons.warning, () => _sendCommand('sitech/farm/control/alarm', 'ON')),
              _buildControlButton('Alarm OFF', Icons.notifications_off, () => _sendCommand('sitech/farm/control/alarm', 'OFF'), isDanger: true),
              _buildControlButton('Feed OPEN', Icons.restaurant, () => _sendCommand('sitech/farm/control/feed', 'OPEN')),
              _buildControlButton('Feed CLOSE', Icons.restaurant_menu, () => _sendCommand('sitech/farm/control/feed', 'CLOSE'), isDanger: true),
            ],
          ),
          const SizedBox(height: 40),
        ],
      ),
    );
  }

  Widget _buildStatusCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF0c1f1a),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFF16352d)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'SYSTEM STATUS',
            style: TextStyle(fontSize: 12, color: Color(0xFF8fb8aa)),
          ),
          const SizedBox(height: 8),
          Text(
            'Alarm: $alarmStatus | Feeder: $feedStatus | Motion: $motionStatus',
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }

  Widget _buildSensorCard(String title, String value) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0c1f1a),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFF16352d)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            title,
            style: const TextStyle(fontSize: 12, color: Color(0xFF8fb8aa)),
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  Widget _buildControlButton(String label, IconData icon, VoidCallback onPressed, {bool isDanger = false}) {
    return ElevatedButton.icon(
      onPressed: onPressed,
      icon: Icon(icon, color: Colors.white, size: 20),
      label: Text(label, style: const TextStyle(color: Colors.white)),
      style: ElevatedButton.styleFrom(
        backgroundColor: isDanger ? Colors.red.withOpacity(0.8) : const Color(0xFF42d392).withOpacity(0.4),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(999),
          side: BorderSide(color: isDanger ? Colors.red : const Color(0xFF42d392)),
        ),
      ),
    );
  }
}
