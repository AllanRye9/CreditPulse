  import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';

class HomeScreen extends StatelessWidget {
  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: ['email'],
  );

  void _handleSignIn(BuildContext context) async {
    try {
      // await _googleSignIn.signOut();
      final user = await _googleSignIn.signIn();
      if (user != null) {
        Navigator.pushReplacementNamed(context, '/email');
      } else {
        // User canceled the sign-in
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Sign in cancelled')),
        );
      }
    } catch (error) {
      print('Sign in failed: $error');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Sign in failed: $error')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
  appBar: AppBar(title: Text("Welcome to CrediSync")),
  body: Center(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        ElevatedButton.icon(
          onPressed: () => _handleSignIn(context),
          icon: Icon(Icons.login),
          label: Text("Sign in with Google"),
        ),
        SizedBox(height: 16), // space between buttons
        ElevatedButton.icon(
          onPressed: () {
            Navigator.pushNamed(context, '/sms');
          },
          icon: Icon(Icons.message),
          label: Text('View SMS Credit Insights'),
        ),
      ],
    ),
  ),
);

  }
}
