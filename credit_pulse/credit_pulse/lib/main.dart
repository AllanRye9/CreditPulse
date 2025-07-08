import 'package:flutter/material.dart';
import 'home_screen_view.dart';
import 'dashboard_screen.dart';
import 'gmail_sign_in_view.dart';
import 'sms_reader_screen.dart';

void main() {
  runApp(CrediSyncApp());
}

class CrediSyncApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CrediSync AI Assistant',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(primarySwatch: Colors.indigo),
      initialRoute: '/email',
      routes: {
        '/': (context) => HomeScreen(),
        '/email':(context)=>GmailSignInView(),
        // '/dashboard': (context) => DashboardScreen(),
         '/sms': (context) => SmsReaderScreen(),
      },
    );
  }
}
