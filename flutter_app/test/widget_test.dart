import 'package:flutter_test/flutter_test.dart';

import 'package:flutter_app/main.dart';

void main() {
  testWidgets('SmartFarmApp can be constructed', (WidgetTester tester) async {
    expect(const SmartFarmApp(), isA<SmartFarmApp>());
  });
}
